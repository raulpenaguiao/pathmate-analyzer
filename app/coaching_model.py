"""Structured model of a PMCP coaching export, for the coaching analysis view.

Where :mod:`app.coaching_stats` produces summary *numbers*, this module produces
the browsable *content*: the list of rules, the micro dialogs (as a flat,
order-only list of nodes - the parent/child nesting of dialog nodes is
deliberately not reconstructed), the message groups, and a variable index that
links every ``$variable`` back to the rules / dialog nodes / messages that write
or read it.

Parsing reuses the balanced-tag scanner in :mod:`app.pmcp_html`.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Iterable

from app.pmcp_html import (
    clean_text,
    find_matching_close,
    iter_blocks,
    section_div,
)
from app.rule_grammar import (
    ASSIGN_FALSE as _RULE_ASSIGN_FALSE,
    ASSIGN_TRUE as _RULE_ASSIGN_TRUE,
    DATE_ADD as _RULE_DATE_ADD,
    DATE_DIFF as _RULE_DATE_DIFF,
)

# ---------------------------------------------------------------------------
# Small parsing helpers
# ---------------------------------------------------------------------------

VARIABLE_RE = re.compile(r"\$[A-Za-z_][A-Za-z0-9_]*")
_ARROW = "→"  # normalised form of &rarr; / &#8594;

# Rule expression phrases we can evaluate in the simulator. Everything else
# (JS snippets, regex matching, multilingual-array lookups, "matches key") is
# parsed for display but marked unsupported.
_SUPPORTED_PHRASES = (
    "calculated value equals",
    "calculated value not equals",
    "calculated value is bigger or equal than",
    "calculated value is smaller or equal than",
    "calculated value is bigger than",
    "calculated value is smaller than",
    "text value equals",
    "text value not equals",
    "calculate value but result is always true",
    "calculate value but result is always false",
    "create text but result is always true",
    "create text but result is always false",
    "calculate date difference in days and always true",
    "calculate new date by adding y days and always true",
)
_UNSUPPORTED_MARKERS = (
    "matches regular expression",
    "text value from multilingual array",
    "matches key",
    "calculate date difference in minutes",
    "timestamp value",
)


def _row(inner_html: str, label: str) -> str | None:
    """Balanced ``<td>`` HTML for a ``<th>label</th><td>...</td>`` row.

    Unlike :func:`app.pmcp_html.field`, this walks nested tables so it works for
    rows whose value is itself a ``<table>`` (message text, answer options, the
    ``Rules:`` sub-table, ...)."""
    m = re.search(rf"<th[^>]*>{re.escape(label)}</th><td\s*>", inner_html)
    if not m:
        return None
    start = m.end()
    end = find_matching_close(inner_html, start, "td")
    return inner_html[start:end]


def _row_text(inner_html: str, label: str) -> str:
    raw = _row(inner_html, label)
    return clean_text(raw) if raw is not None else ""


def _is_set(value: str) -> bool:
    return bool(value) and value != "[not set]"


def _var_or_none(value: str) -> str | None:
    value = value.strip()
    return value if value.startswith("$") and _is_set(value) else None


def _lang_map(td_html: str | None) -> dict[str, str]:
    """``{'en-GB': '...', 'ro-RO': '...'}`` from a nested language table."""
    if not td_html:
        return {}
    out: dict[str, str] = {}
    for m in re.finditer(
        r"<th\s*>([a-z]{2}-[A-Z]{2}):</th><td\s*>(.*?)</td>", td_html, re.DOTALL
    ):
        out[m.group(1)] = clean_text(m.group(2))
    return out


def _tokens(*texts: str) -> set[str]:
    found: set[str] = set()
    for t in texts:
        if t:
            found.update(VARIABLE_RE.findall(t))
    return found


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class Ref:
    """A place a variable is written or read: points at a DOM anchor in a tab."""

    kind: str  # 'rule' | 'dialog' | 'msg_group'
    label: str
    anchor: str


@dataclass
class Rule:
    i: int
    context: str  # DAILY BASIS | PERIODIC BASIS | UNEXPECTED MESSAGE | USER INTENTION
    depth: int
    raw_expr: str
    comment: str
    writes_var: str | None
    sends_message: bool
    stops_intervention: bool
    is_js_snippet: bool
    supported: bool

    # -- bundle-only fields (Stage 4, docs/stage4_chat_engine_plan.md Phase A)
    # populated by `parse_bundle`; stay at their defaults on the HTML path.
    uid: str | None = None
    kind: str | None = None  # 'condition' | 'sender'
    parent_uid: str | None = None
    expr: dict | None = None  # structured {kind, lhs, op/phrase, rhs, target, ...}
    micro_dialog_path: list[str] = field(default_factory=list)
    send_hour_variable: str | None = None
    send_hour_clock: str | None = None  # "HH:MM" literal fallback when the variable is unset
    send_hour_literal: str | None = None
    not_answered_timeout_minutes: int | None = None
    does_answer_rules: list = field(default_factory=list)
    does_not_answer_rules: list = field(default_factory=list)

    @property
    def anchor(self) -> str:
        return f"rule-{self.i}"

    @property
    def reads_vars(self) -> list[str]:
        toks = _tokens(self.raw_expr)
        toks.discard(self.writes_var or "")
        return sorted(toks)


@dataclass
class DecisionBranch:
    expr: str
    comment: str
    writes_var: str | None
    stop_micro_dialog: bool
    leave_decision_point: bool
    jump_dialog: str | None
    cascade_dialog: str | None
    supported: bool
    # bundle-only (Warden's exporter, agreed 2026-09-24): "Jump to dialog
    # message if TRUE / FALSE" per rule. A target node uid ("md-049#006"),
    # {"raw": ..., "unresolved": True} when the exporter couldn't resolve
    # it, or None when unset.
    jump_msg_true: str | dict | None = None
    jump_msg_false: str | dict | None = None
    # HTML path: the same targets as the Report shows them, i.e. the target
    # message's text per language (no node id). enrich_bundle.py resolves
    # these to the node uids above.
    jump_message_if_true: dict[str, str] = field(default_factory=dict)
    jump_message_if_false: dict[str, str] = field(default_factory=dict)
    # nesting inside the decision point (PMCP 6.0 docs, Rules §2.2: "AND
    # logic (child rules), OR logic (same hierarchy level)"). The Report
    # draws it as a 20px-per-level left border on the rule's <th>.
    depth: int = 0


@dataclass
class Node:
    n: int
    type: str  # 'message' | 'command' | 'decision'
    comment: str
    channel: str
    writes_var: str | None
    text_by_lang: dict[str, str] = field(default_factory=dict)
    text_html_by_lang: dict[str, str] = field(default_factory=dict)
    answer_type: str = ""
    answer_options_by_lang: dict[str, str] = field(default_factory=dict)
    command_by_lang: dict[str, str] = field(default_factory=dict)
    media_file: str = ""
    trigger_exprs: list[str] = field(default_factory=list)
    branches: list[DecisionBranch] = field(default_factory=list)
    jump_msg_true: str = ""
    jump_msg_false: str = ""

    # -- bundle-only fields (Stage 4 Phase A), see `Rule` above
    uid: str | None = None
    order: int = 0
    randomisation_group: str = ""

    def anchor(self, dialog_i: int) -> str:
        return f"dlg-{dialog_i}-node-{self.n}"

    def all_read_text(self) -> str:
        parts = list(self.text_by_lang.values())
        parts += list(self.answer_options_by_lang.values())
        parts += list(self.command_by_lang.values())
        parts += self.trigger_exprs
        parts += [b.expr for b in self.branches]
        return "\n".join(parts)


@dataclass
class MicroDialog:
    i: int
    name: str
    comment: str
    nodes: list[Node] = field(default_factory=list)
    uid: str | None = None  # bundle-only (Stage 4 Phase A)
    # bundle-only: full menu path ("Folder / Sub / Name"). Unlike `uid`
    # (a position in one export's sweep, renumbered when dialogs are added
    # or moved), this is the stable way to name a dialog across exports.
    path: str | None = None

    @property
    def anchor(self) -> str:
        return f"dlg-{self.i}"


@dataclass
class GroupMessage:
    text_by_lang: dict[str, str]
    channel: str
    writes_var: str | None
    trigger_exprs: list[str]


@dataclass
class MessageGroup:
    i: int
    name: str
    expect_answered: bool
    messages: list[GroupMessage] = field(default_factory=list)

    @property
    def anchor(self) -> str:
        return f"mg-{self.i}"


@dataclass
class CoachingModel:
    rules: list[Rule]
    micro_dialogs: list[MicroDialog]
    message_groups: list[MessageGroup]
    variables: dict[str, dict[str, list[Ref]]]
    languages: list[str]
    source: str = "html"  # "html" (parse_model) | "bundle" (parse_bundle)
    # each variable's configured value from the export's Variables list
    # (bundle path only - the HTML report doesn't carry them); the chat
    # engine seeds a fresh simulation's vars from this.
    variable_defaults: dict[str, str] = field(default_factory=dict)

    # -- convenience accessors used by templates -------------------------------
    def rules_by_context(self) -> list[tuple[str, list[Rule]]]:
        order: list[str] = []
        buckets: dict[str, list[Rule]] = {}
        for r in self.rules:
            if r.context not in buckets:
                buckets[r.context] = []
                order.append(r.context)
            buckets[r.context].append(r)
        return [(ctx, buckets[ctx]) for ctx in order]

    def dialog_anchor(self, name: str) -> str | None:
        for d in self.micro_dialogs:
            if d.name == name:
                return d.anchor
        return None

    @property
    def sorted_variables(self) -> list[tuple[str, dict[str, list[Ref]]]]:
        return sorted(self.variables.items(), key=lambda kv: kv[0].lower())


# ---------------------------------------------------------------------------
# Rules section
# ---------------------------------------------------------------------------

_RULE_DEPTH_RE = re.compile(r'<th style="border-left-width:\s*(\d+)px;">Rule:</th>')
_CONTEXT_RE = re.compile(r"^Execution on (.+?)(?:\s*\(.*\))?$")


def _classify_expr(expr: str) -> tuple[bool, bool]:
    """(is_js_snippet, supported)."""
    stripped = expr.lstrip()
    if stripped.startswith("//") or "import moment" in stripped:
        return True, False
    if any(m in expr for m in _UNSUPPORTED_MARKERS):
        return False, False
    if any(p in expr for p in _SUPPORTED_PHRASES):
        return False, True
    # A bare assignment target ("0 -> $var") or an unrecognised phrase.
    return False, _ARROW in expr


def _parse_rules(rules_div: str) -> list[Rule]:
    rules: list[Rule] = []
    context = "DAILY BASIS"
    idx = 0
    for block in iter_blocks(rules_div, "table", "automatic"):
        expr = clean_text(_row(block, "Rule:")).replace("–", "-")
        ctx_m = _CONTEXT_RE.match(expr)
        if ctx_m:
            context = ctx_m.group(1).strip()
            continue

        depth_m = _RULE_DEPTH_RE.search(block)
        depth = int(depth_m.group(1)) // 20 if depth_m else 0

        stop_raw = _row(block, "Stop Intervention when TRUE:") or ""
        send_raw = _row(block, "Send message when TRUE:") or ""
        is_js, supported = _classify_expr(expr)
        rules.append(
            Rule(
                i=idx,
                context=context,
                depth=depth,
                raw_expr=expr,
                comment=_norm_comment(_row_text(block, "Comment:")),
                writes_var=_var_or_none(_row_text(block, "Variable to store value to:")),
                sends_message='class="yes"' in send_raw,
                stops_intervention='class="yes"' in stop_raw,
                is_js_snippet=is_js,
                supported=supported,
            )
        )
        idx += 1
    return rules


def _norm_comment(text: str) -> str:
    return "" if text == "[not set]" else text


# ---------------------------------------------------------------------------
# Micro dialogs
# ---------------------------------------------------------------------------

_NODE_HEADER_RE = re.compile(
    r"^\s*<tr\s*><th\s*>Micro Dialog (Message|Command Message|Decision Point|Event)</th></tr>"
)
_NODE_KIND = {
    "Message": "message",
    "Command Message": "command",
    "Decision Point": "decision",
    "Event": "event",
}


def _dialog_nodes_html(dialog_html: str) -> str | None:
    m = re.search(
        r"<th[^>]*>Decision Points, Events (?:&|&amp;) Messages:</th><td\s*>", dialog_html
    )
    if not m:
        return None
    start = m.end()
    return dialog_html[start:find_matching_close(dialog_html, start, "td")]


def _parse_branches(rules_td: str) -> tuple[list[DecisionBranch], list[str]]:
    branches: list[DecisionBranch] = []
    exprs: list[str] = []
    for rt in iter_blocks(rules_td, "table", "automatic"):
        expr = clean_text(_row(rt, "Rule:")).replace("–", "-")
        exprs.append(expr)
        _, supported = _classify_expr(expr)
        indent = re.search(r'<th style="border-left-width:\s*(\d+)px;?">Rule:</th>', rt)
        branches.append(
            DecisionBranch(
                expr=expr,
                comment=_norm_comment(_row_text(rt, "Comment:")),
                writes_var=_var_or_none(_row_text(rt, "Variable to store value to:")),
                stop_micro_dialog='class="yes"'
                in (_row(rt, "Stop Micro Dialog when TRUE:") or ""),
                leave_decision_point='class="yes"'
                in (_row(rt, "Leave Decision Point when TRUE:") or ""),
                jump_dialog=_clean_target(_row_text(rt, "Micro Dialog to jump to when TRUE:")),
                cascade_dialog=_clean_target(
                    _row_text(rt, "Micro Dialog to cascade to when TRUE:")
                ),
                supported=supported,
                jump_message_if_true=_lang_map(_row(rt, "Micro Dialog Message to jump to when TRUE:")),
                jump_message_if_false=_lang_map(_row(rt, "Micro Dialog Message to jump to when FALSE:")),
                depth=int(indent.group(1)) // 20 if indent else 0,
            )
        )
    return branches, exprs


def _clean_target(text: str) -> str | None:
    return text if _is_set(text) else None


def _parse_node(node_html: str, n: int) -> Node:
    header = _NODE_HEADER_RE.match(node_html)
    kind = _NODE_KIND.get(header.group(1), "message") if header else "message"

    node = Node(
        n=n,
        type=kind,
        comment=_norm_comment(_row_text(node_html, "Comment:")),
        channel=_row_text(node_html, "Channel to send message:"),
        writes_var=_var_or_none(_row_text(node_html, "Store value to variable:")),
    )

    if kind == "message":
        node.text_by_lang = _lang_map(_row(node_html, "Text (plain):"))
        node.text_html_by_lang = _lang_map(_row(node_html, "Text (html):"))
        node.answer_type = _row_text(node_html, "Answer type:")
        node.answer_options_by_lang = _lang_map(
            _row(node_html, "Answer options (with placeholders):")
        )
        node.media_file = _row_text(node_html, "Linked Media Object File:")
        node.jump_msg_true = _row_text(
            node_html, "Micro Dialog Message to jump to when TRUE:"
        )
        node.jump_msg_false = _row_text(
            node_html, "Micro Dialog Message to jump to when FALSE:"
        )
        rules_td = _row(node_html, "Rules:")
        if rules_td:
            node.trigger_exprs = [
                clean_text(_row(rt, "Rule:")).replace("–", "-")
                for rt in iter_blocks(rules_td, "table", "automatic")
            ]
    elif kind == "command":
        node.command_by_lang = _lang_map(_row(node_html, "Command:"))
        rules_td = _row(node_html, "Rules:")
        if rules_td:
            node.trigger_exprs = [
                clean_text(_row(rt, "Rule:")).replace("–", "-")
                for rt in iter_blocks(rules_td, "table", "automatic")
            ]
    elif kind == "decision":
        rules_td = _row(node_html, "Rules:")
        if rules_td:
            node.branches, node.trigger_exprs = _parse_branches(rules_td)

    return node


def _parse_micro_dialogs(md_div: str) -> list[MicroDialog]:
    dialogs: list[MicroDialog] = []
    for i, dialog_html in enumerate(iter_blocks(md_div, "table", "automatic")):
        dialog = MicroDialog(
            i=i,
            name=_row_text(dialog_html, "Name:") or "(unnamed)",
            comment=_norm_comment(_row_text(dialog_html, "Comment:")),
        )
        nodes_html = _dialog_nodes_html(dialog_html)
        if nodes_html:
            for n, node_html in enumerate(iter_blocks(nodes_html, "table", "automatic")):
                dialog.nodes.append(_parse_node(node_html, n))
        dialogs.append(dialog)
    return dialogs


# ---------------------------------------------------------------------------
# Message groups
# ---------------------------------------------------------------------------

def _parse_message_groups(mg_div: str) -> list[MessageGroup]:
    groups: list[MessageGroup] = []
    for i, group_html in enumerate(iter_blocks(mg_div, "table", "automatic")):
        group = MessageGroup(
            i=i,
            name=_row_text(group_html, "Name:") or "(unnamed)",
            expect_answered='class="yes"'
            in (_row(group_html, "Expect to be answered:") or ""),
        )
        messages_td = _row(group_html, "Messages:")
        if messages_td:
            for msg_html in iter_blocks(messages_td, "table", "automatic"):
                rules_td = _row(msg_html, "Rules:")
                triggers = (
                    [
                        clean_text(_row(rt, "Rule:")).replace("–", "-")
                        for rt in iter_blocks(rules_td, "table", "automatic")
                    ]
                    if rules_td
                    else []
                )
                group.messages.append(
                    GroupMessage(
                        text_by_lang=_lang_map(_row(msg_html, "Text:")),
                        channel=_row_text(msg_html, "Channel to send message:"),
                        writes_var=_var_or_none(
                            _row_text(msg_html, "Store value to variable:")
                        ),
                        trigger_exprs=triggers,
                    )
                )
        groups.append(group)
    return groups


# ---------------------------------------------------------------------------
# Variable index
# ---------------------------------------------------------------------------

def _build_variable_index(
    rules: list[Rule],
    dialogs: list[MicroDialog],
    groups: list[MessageGroup],
) -> dict[str, dict[str, list[Ref]]]:
    index: dict[str, dict[str, list[Ref]]] = {}

    def write(var: str | None, ref: Ref) -> None:
        if var:
            index.setdefault(var, {"writes": [], "reads": []})["writes"].append(ref)

    def read(vars_: Iterable[str], ref: Ref) -> None:
        for var in vars_:
            index.setdefault(var, {"writes": [], "reads": []})["reads"].append(ref)

    for r in rules:
        label = f"Rule #{r.i}" + (f" - {r.comment}" if r.comment else f": {r.raw_expr[:60]}")
        ref = Ref("rule", label, r.anchor)
        write(r.writes_var, ref)
        read(r.reads_vars, ref)

    for d in dialogs:
        for node in d.nodes:
            label = f"{d.name} - node {node.n}" + (
                f" ({node.comment})" if node.comment else ""
            )
            ref = Ref("dialog", label, node.anchor(d.i))
            write(node.writes_var, ref)
            for b in node.branches:
                write(b.writes_var, ref)
            reads = _tokens(node.all_read_text())
            reads.discard(node.writes_var or "")
            read(reads, ref)

    for g in groups:
        for mi, msg in enumerate(g.messages):
            ref = Ref("msg_group", f"{g.name} - message {mi}", g.anchor)
            write(msg.writes_var, ref)
            reads = _tokens(*msg.text_by_lang.values(), *msg.trigger_exprs)
            read(reads, ref)

    return index


# ---------------------------------------------------------------------------
# Bundle (coaching.json) parsing — Stage 4, docs/stage4_chat_engine_plan.md
# Phase A. Additive: does not touch the HTML `parse_model` path above, which
# every other tab keeps using. `export_coaching.py` already parses each
# Rules-tree caption into a structured `expr` dict via
# `app.rule_grammar.parse_rule_caption` (Phase 0, done) - `raw`/`comment` in
# that dict still carry the *caption's* comment prefix, so `raw_expr` here is
# rebuilt bare (comment-free) from the structured fields to match the HTML
# path's convention and stay directly evaluable by `coaching_sim.eval_expr`.
# ---------------------------------------------------------------------------

def _bare_expr_from_parsed(e: dict) -> str:
    kind = e.get("kind")
    if kind == "cmp":
        return f'{e["lhs"]} {e["phrase"]} {e["rhs"]}'
    if kind == "assign":
        phrase = _RULE_ASSIGN_TRUE[0] if e.get("result") else _RULE_ASSIGN_FALSE[0]
        s = f'{e["lhs"]} {phrase}'
        if e.get("target"):
            s += f' {_ARROW} {e["target"]}'
        return s
    if kind == "date_diff":
        s = f'{e["lhs"]} {_RULE_DATE_DIFF} {e["rhs"]}'
        if e.get("target"):
            s += f' {_ARROW} {e["target"]}'
        return s
    if kind == "date_add":
        s = f'{e["lhs"]} {_RULE_DATE_ADD} {e["rhs"]}'
        if e.get("target"):
            s += f' {_ARROW} {e["target"]}'
        return s
    return e.get("raw") or ""  # unsupported (JS snippet / regex / ...)


def _bundle_rule(r: dict, idx: int, sender_by_uid: dict) -> Rule:
    e = r.get("expr") or {}
    kind = e.get("kind")
    supported = kind in ("cmp", "assign", "date_diff", "date_add")
    target = e.get("target") if kind in ("assign", "date_diff", "date_add") else None

    rule = Rule(
        i=idx,
        context=r.get("section") or "DAILY BASIS",
        depth=r.get("depth", 0),
        raw_expr=_bare_expr_from_parsed(e),
        comment=_norm_comment(e.get("comment") or ""),
        writes_var=_var_or_none(target or ""),
        sends_message=(r.get("kind") == "sender"),
        stops_intervention=False,  # not exported yet - Stage 4 open gap
        is_js_snippet=(kind == "unsupported"),
        supported=supported,
        uid=r.get("uid"),
        kind=r.get("kind"),
        parent_uid=r.get("parentUid"),
        expr=e,
    )
    sr = sender_by_uid.get(rule.uid)
    if sr:
        rule.micro_dialog_path = list(sr.get("microDialogPath") or [])
        rule.send_hour_variable = sr.get("sendHourVariable")
        rule.send_hour_clock = sr.get("sendHourClock")
        rule.send_hour_literal = sr.get("sendHourLiteral")
        rule.not_answered_timeout_minutes = sr.get("notAnsweredTimeoutMinutes")
        rule.does_answer_rules = sr.get("doesAnswerRules") or []
        rule.does_not_answer_rules = sr.get("doesNotAnswerRules") or []
    return rule


def _parse_bundle_rules(rules_data: dict) -> list[Rule]:
    tree = sorted(
        rules_data.get("ruleTree") or [],
        key=lambda r: r.get("treeIndex", r.get("order", 0)),
    )
    sender_by_uid = {
        sr["uid"]: sr for sr in (rules_data.get("sendingRules") or []) if sr.get("uid")
    }
    return [_bundle_rule(r, idx, sender_by_uid) for idx, r in enumerate(tree)]


def _bundle_node(n: dict, position: int) -> Node:
    node = Node(
        n=position,
        type=n.get("type") or "message",
        comment=_norm_comment(n.get("comment") or ""),
        channel=n.get("channel") or "",
        writes_var=_var_or_none(n.get("resultVariable") or ""),
        text_by_lang=dict(n.get("textByLang") or {}),
        answer_type=n.get("answerType") or "",
        answer_options_by_lang=dict(n.get("answerOptionsByLang") or {}),
        command_by_lang=dict(n.get("commandByLang") or {}),
        media_file=n.get("mediaFile") or "",
        trigger_exprs=list(n.get("triggerExprs") or []),
        uid=n.get("uid"),
        order=n.get("order", position),
        randomisation_group=n.get("randomisationGroup") or "",
    )
    for b in n.get("branches") or []:
        node.branches.append(
            DecisionBranch(
                expr=b.get("condition") or "",
                comment=_norm_comment(b.get("comment") or ""),
                writes_var=_var_or_none(b.get("writesVar") or ""),
                stop_micro_dialog=bool(b.get("stopMicroDialog")),
                leave_decision_point=bool(b.get("leaveDecisionPoint")),
                jump_dialog=b.get("jumpDialog") or None,
                cascade_dialog=b.get("cascadeDialog") or None,
                supported=bool(b.get("supported", True)),
                jump_msg_true=b.get("jumpMessageIfTrue") or None,
                jump_msg_false=b.get("jumpMessageIfFalse") or None,
                depth=int(b.get("depth") or 0),
            )
        )
    return node


def _parse_bundle_dialogs(micro_dialogs: list[dict], nodes: list[dict]) -> list[MicroDialog]:
    by_dialog: dict[str, list[dict]] = {}
    for n in nodes:
        by_dialog.setdefault(n.get("microDialogUid"), []).append(n)
    for lst in by_dialog.values():
        lst.sort(key=lambda n: n.get("order", 0))

    # `isFolder` marks a dialog with children *nested under it* in the Micro
    # Dialogs tree - it can still carry its own nodes directly (e.g. a
    # top-of-subtree "quit if debug mode" decision point), so it is not "no
    # real content" and must not be filtered out - every node's
    # `microDialogUid` resolves to exactly one entry here, folder or not.
    dialogs: list[MicroDialog] = []
    for i, md in enumerate(micro_dialogs):
        dialog = MicroDialog(i=i, name=md.get("name") or "(unnamed)", comment="", uid=md.get("uid"),
                             path=md.get("path") or None)
        for n_json in by_dialog.get(md.get("uid"), []):
            dialog.nodes.append(_bundle_node(n_json, len(dialog.nodes)))
        dialogs.append(dialog)
    return dialogs


def parse_bundle(data: dict) -> CoachingModel:
    """`coaching.json` (the Stage-3 export) -> `CoachingModel`. The pure-function
    counterpart to `parse_model`, and the only input the Stage-4 chat engine
    is allowed to use - see docs/stage4_chat_engine_plan.md section 1.

    Message groups aren't in the export schema yet (Stage-3 gap, not this
    phase's problem to fix): `CoachingModel.message_groups` is always `[]`
    on this path.
    """
    rules = _parse_bundle_rules(data.get("rules") or {})
    dialogs = _parse_bundle_dialogs(data.get("microDialogs") or [], data.get("nodes") or [])
    groups: list[MessageGroup] = []
    variables = _build_variable_index(rules, dialogs, groups)
    languages = list((data.get("coaching") or {}).get("languages") or []) or ["en-GB"]
    variable_defaults = {
        v["Variable Name"]: str(v.get("Variable Value") or "")
        for v in (data.get("variables") or [])
        if isinstance(v, dict) and v.get("Variable Name")
    }

    return CoachingModel(
        rules=rules,
        micro_dialogs=dialogs,
        message_groups=groups,
        variables=variables,
        languages=languages,
        source="bundle",
        variable_defaults=variable_defaults,
    )


_BUNDLE_CACHE: dict[tuple[str, float], CoachingModel] = {}


def load_bundle_model(coaching_id: str) -> CoachingModel | None:
    """Like `load_model`, but always from the attached `coaching.json` bundle,
    never the HTML - the only entry point the Stage-4 chat engine may use.
    `None` if no bundle is attached to this coaching."""
    from app import storage  # lazy: avoids import cycle at app startup

    path = storage.coaching_bundle_path(coaching_id)
    if path is None or not path.exists():
        return None
    key = (coaching_id, path.stat().st_mtime)
    if key not in _BUNDLE_CACHE:
        _BUNDLE_CACHE.clear()
        data = json.loads(path.read_text(encoding="utf-8"))
        _BUNDLE_CACHE[key] = parse_bundle(data)
    return _BUNDLE_CACHE[key]


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def parse_model(file_bytes: bytes) -> CoachingModel:
    body = file_bytes.decode("utf-8", errors="replace")
    body = body.replace("&rarr;", _ARROW).replace("&#8594;", _ARROW)

    rules = _parse_rules(section_div(body, "Rules"))
    dialogs = _parse_micro_dialogs(section_div(body, "Micro Dialogs"))
    groups = _parse_message_groups(section_div(body, "Message Groups and Messages"))
    variables = _build_variable_index(rules, dialogs, groups)

    languages = sorted(set(re.findall(r"<th\s*>([a-z]{2}-[A-Z]{2}):</th>", body)))

    return CoachingModel(
        rules=rules,
        micro_dialogs=dialogs,
        message_groups=groups,
        variables=variables,
        languages=languages or ["en-GB"],
    )


# Parsed models are ~MBs of source collapsed to a few thousand small objects;
# parsing takes a beat, so cache per (coaching id, file mtime).
_CACHE: dict[tuple[str, float], CoachingModel] = {}


def load_model(coaching_id: str) -> CoachingModel | None:
    from app import storage  # lazy: avoids import cycle at app startup

    path = storage.coaching_file_path(coaching_id)
    if path is None or not path.exists():
        return None
    key = (coaching_id, path.stat().st_mtime)
    if key not in _CACHE:
        _CACHE.clear()  # only ever need the models currently being looked at
        _CACHE[key] = parse_model(path.read_bytes())
    return _CACHE[key]
