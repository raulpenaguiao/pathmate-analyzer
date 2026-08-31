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

import re
from dataclasses import dataclass, field
from typing import Iterable

from app.pmcp_html import (
    clean_text,
    find_matching_close,
    iter_blocks,
    section_div,
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
