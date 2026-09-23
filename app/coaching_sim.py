"""A simplified, rule-driven simulator for a PMCP coaching.

This runs the coaching's *declarative* rules (the ``calculated value equals`` /
``calculate value but result is always true`` mini-language) over a discrete
1-minute clock, walks micro dialogs node by node, and produces a chat transcript.

It is intentionally a simplified model, not the real PMCP engine:

* JS-snippet rules and a few operators (regex, multilingual-array lookups) are
  skipped and reported as ``skipped unsupported rule`` lines.
* The rule -> micro-dialog trigger link is only weakly present in the export, so
  dialogs are launched manually from the UI; once open, the engine walks them.

See ``ALEX_v02_simulator_scope.md`` for the fuller design this is a cut-down of.
"""
from __future__ import annotations

import ast
import hashlib
import random
import re
from datetime import date, datetime, timedelta, timezone

from app.coaching_model import CoachingModel, VARIABLE_RE
from app.rule_grammar import (
    ARROW as _ARROW,
    CMP_OPS as _CMP_OPS,
    ASSIGN_TRUE as _ASSIGN_TRUE,
    ASSIGN_FALSE as _ASSIGN_FALSE,
    DATE_DIFF as _DATE_DIFF,
    DATE_ADD as _DATE_ADD,
    parse_expr,
)

def _rgroup_pick_index(seed, dialog_key, group: str, call_index: int, n: int) -> int:
    """Deterministic pick within a run of `n` sibling variants sharing one
    randomisation group: a stable (non-PYTHONHASHSEED-dependent) hash of
    (seed, dialog, group, call_index), so the same seed replaying the same
    action sequence always makes the same picks (Phase B,
    docs/stage4_chat_engine_plan.md), while a later re-launch of the same
    dialog (a higher call_index) can land on a different variant."""
    if n <= 1:
        return 0
    payload = f"{seed}|{dialog_key}|{group}|{call_index}".encode()
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "big") % n


BASE_DATE = date(2026, 1, 1)
DAY_SLOTS = (6, 12, 18, 22)  # hour boundaries for the "advance to next slot" button
_MAX_TRANSCRIPT = 500
_MAX_DIALOG_STEPS = 400


# ---------------------------------------------------------------------------
# value helpers
# ---------------------------------------------------------------------------

def _num(value) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return 0.0


def _fmt(value) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _fmt_epoch(ts) -> str:
    try:
        dt = datetime.fromtimestamp(int(ts) / 1000, tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return str(ts)
    return dt.strftime("%Y-%m-%d %H:%M")


def _parse_date(text: str) -> date | None:
    m = re.match(r"\s*(\d{1,2})\.(\d{1,2})\.(\d{4})\s*$", str(text))
    if not m:
        return None
    d, mo, y = (int(x) for x in m.groups())
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def _fmt_date(d: date) -> str:
    return f"{d.day:02d}.{d.month:02d}.{d.year}"


_ALLOWED_AST = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Add, ast.Sub, ast.Mult,
    ast.Div, ast.FloorDiv, ast.Mod, ast.Pow, ast.USub, ast.UAdd, ast.Constant,
    ast.Load,
)


def _eval_arith(expr: str, variables: dict) -> str:
    """Substitute ``$vars`` and evaluate a numeric expression. Falls back to the
    substituted string (used by ``create text``) when it isn't arithmetic."""
    substituted = VARIABLE_RE.sub(
        lambda m: _fmt(variables.get(m.group(0), "")) or "0", expr
    )
    cleaned = re.sub(r"\{[^}]*\}", "", substituted).strip()
    try:
        tree = ast.parse(cleaned, mode="eval")
        for node in ast.walk(tree):
            if not isinstance(node, _ALLOWED_AST):
                raise ValueError("non-arithmetic")
        return _fmt(eval(compile(tree, "<arith>", "eval"), {"__builtins__": {}}, {}))
    except Exception:
        # not arithmetic - treat as a literal / text concatenation
        return VARIABLE_RE.sub(lambda m: _fmt(variables.get(m.group(0), "")), expr).strip()


# ---------------------------------------------------------------------------
# rule expression evaluation (parse_expr itself lives in app/rule_grammar.py,
# shared with the exporter's Rules-tree caption parsing)
# ---------------------------------------------------------------------------

def eval_expr(expr: str, variables: dict) -> tuple[bool | None, tuple[str, str] | None]:
    """Returns (truthiness, assignment). truthiness is None for unsupported."""
    p = parse_expr(expr)
    kind = p["kind"]

    if kind == "cmp":
        lhs = _eval_arith(p["lhs"], variables) if any(c in p["lhs"] for c in "+-*/") else \
            _fmt(variables.get(p["lhs"].strip(), p["lhs"].strip()))
        rhs_tok = p["rhs"].strip()
        rhs = _fmt(variables.get(rhs_tok, rhs_tok)) if rhs_tok.startswith("$") else rhs_tok
        return bool(_CMP_OPS[p["phrase"]](lhs, rhs)), None

    if kind == "assign":
        if not p["target"]:
            return p["result"], None
        return p["result"], (p["target"], _eval_arith(p["lhs"], variables))

    if kind == "date_diff":
        a = _parse_date(_fmt(variables.get(p["lhs"], p["lhs"])))
        b = _parse_date(_fmt(variables.get(p["rhs"], p["rhs"])))
        if a and b and p["target"]:
            return True, (p["target"], str((b - a).days))
        return True, None

    if kind == "date_add":
        start = _parse_date(_fmt(variables.get(p["lhs"], p["lhs"])))
        days = int(_num(_eval_arith(p["rhs"], variables)))
        if start and p["target"]:
            return True, (p["target"], _fmt_date(start + timedelta(days=days)))
        return True, None

    return None, None  # unknown / unsupported


# ---------------------------------------------------------------------------
# Simulator
# ---------------------------------------------------------------------------

class Simulator:
    def __init__(self, model: CoachingModel | None, lang: str | None = None):
        self.model = model
        self.lang = lang or (model.languages[0] if model and model.languages else "en-GB")

    # -- state ------------------------------------------------------------
    def initial_state(self, seed: int | None = None) -> dict:
        state = {
            "clock": {"day": 0, "hour": 8, "minute": 0},
            "vars": {},
            "open_dialog": None,
            "pending": None,
            "transcript": [],
            # fixed for the life of this simulation - makes r-group picks
            # (Phase B) reproducible; a fresh reset gets a fresh seed.
            "seed": seed if seed is not None else random.SystemRandom().getrandbits(32),
        }
        self._refresh_system_vars(state)
        self._log(state, "system", "Simulation reset. Clock at day 0, 08:00.")
        return state

    # -- public step ----------------------------------------------------
    def initial_state_from_import(self, import_data: dict) -> dict:
        """Seed a fresh state from a parsed .pmcp participant import (see
        ``app.participant_import``): the real current $variable snapshot,
        plus the reconstructed observable-event history replayed as
        transcript lines so it can be scrolled/navigated. The clock is
        re-based to day 0 like a normal reset - the sim's own relative clock
        has no relation to the real wall-clock dates in the import - so
        continuing forward from here uses the simulator's day/hour, not the
        participant's real calendar.
        """
        state = self.initial_state()
        state["transcript"] = []
        p = import_data.get("participant") or {}
        label = p.get("nickname") or p.get("systemUniqueId") or "participant"
        state["transcript"].append(
            {"kind": "system", "text": f"📥 Imported real participant \"{label}\" — replaying observed history:", "t": ""}
        )
        for event in import_data.get("timeline", []):
            stamp = _fmt_epoch(event.get("timestamp"))
            if event["kind"] == "var_change":
                text = f"{event['name']} → {_fmt(event.get('value'))}"
            elif event["kind"] == "cascade_complete":
                text = f"dialog cascade completed ({event['cascade_id'][:16]}…)"
            else:
                continue
            state["transcript"].append({"kind": "import", "text": text, "t": stamp})
        for w in import_data.get("warnings", []):
            state["transcript"].append({"kind": "system", "text": f"⚠️ {w}", "t": ""})
        state["vars"].update(import_data.get("variables") or {})
        self._refresh_system_vars(state)  # sim's own $today/$system* win back over the real ones
        state["transcript"].append(
            {"kind": "system", "text": "── continuing simulation from here — clock re-based to day 0, 08:00 ──", "t": self._stamp(state)}
        )
        return state

    def step(self, state: dict, action: dict) -> dict:
        kind = action.get("type")
        if kind == "reset":
            return self.initial_state()
        if kind == "set_var":
            name = action["name"]
            if not name.startswith("$"):
                name = "$" + name
            state["vars"][name] = str(action.get("value", ""))
            self._log(state, "system", f"Set {name} = {state['vars'][name]}")
        elif kind == "tick":
            self._tick(state, action)
        elif kind == "run_periodic":
            self._run_context(state, "PERIODIC BASIS")
        elif kind == "launch_dialog":
            self._launch_dialog(state, int(action["dialog_i"]))
        elif kind == "launch_group":
            self._launch_group(state, int(action["group_i"]))
        elif kind == "answer":
            self._answer(state, action.get("value", ""))
        else:
            self._log(state, "system", f"Unknown action: {kind}")

        state["transcript"] = state["transcript"][-_MAX_TRANSCRIPT:]
        return state

    # -- clock ----------------------------------------------------------
    def _tick(self, state: dict, action: dict) -> None:
        clock = state["clock"]
        before = clock["day"] * 1440 + clock["hour"] * 60 + clock["minute"]

        if action.get("to") == "next-slot":
            minutes = self._minutes_to_next_slot(clock)
        else:
            minutes = int(action.get("minutes", 1))

        total = before + max(1, minutes)
        clock["day"], rem = divmod(total, 1440)
        clock["hour"], clock["minute"] = divmod(rem, 60)

        crossed_midnights = clock["day"] - before // 1440
        self._refresh_system_vars(state)
        self._log(state, "system", f"⏩ Advanced to {self._stamp(state)}.")

        for _ in range(max(0, crossed_midnights)):
            self._run_context(state, "DAILY BASIS")
        self._run_context(state, "PERIODIC BASIS")

    def _minutes_to_next_slot(self, clock: dict) -> int:
        now_h = clock["hour"] + clock["minute"] / 60
        for slot in DAY_SLOTS:
            if slot > now_h:
                return int((slot - now_h) * 60)
        return int((24 - now_h + DAY_SLOTS[0]) * 60)

    def _refresh_system_vars(self, state: dict) -> None:
        clock = state["clock"]
        today = BASE_DATE + timedelta(days=clock["day"])
        state["vars"].update({
            "$today": _fmt_date(today),
            "$systemDayOfMonth": str(today.day),
            "$systemMonth": str(today.month),
            "$systemYear": str(today.year),
            "$systemDayOfWeek": str(today.isoweekday()),
            "$systemHour": str(clock["hour"]),
            "$systemMinute": str(clock["minute"]),
        })

    # -- rule execution ----------------------------------------------
    def _run_context(self, state: dict, context: str) -> None:
        rules = [r for r in self.model.rules if r.context == context]
        if not rules:
            return
        variables = state["vars"]
        # stack of (depth, active) - a rule is skipped if any ancestor is inactive
        stack: list[tuple[int, bool]] = []
        fired = 0
        for r in rules:
            while stack and stack[-1][0] >= r.depth:
                stack.pop()
            if any(not active for _d, active in stack):
                stack.append((r.depth, False))
                continue

            if not r.supported:
                self._log(state, "rule", f"⚠️ skipped unsupported rule #{r.i}"
                          + (f" ({r.comment})" if r.comment else ""))
                stack.append((r.depth, False))
                continue

            result, assignment = eval_expr(r.raw_expr, variables)
            if assignment:
                variables[assignment[0]] = assignment[1]
            truthy = bool(result)
            if truthy and assignment:
                fired += 1
            if truthy and r.sends_message:
                self._log(state, "system", f"Rule #{r.i} sends a message"
                          + (f": {r.comment}" if r.comment else ""))
            if truthy and r.stops_intervention:
                self._log(state, "system", f"Rule #{r.i} stops the intervention.")
            stack.append((r.depth, truthy))

        if fired:
            self._log(state, "rule", f"{context}: applied {fired} rule assignment(s).")

    # -- message groups --------------------------------------------
    def _launch_group(self, state: dict, group_i: int) -> None:
        if not (0 <= group_i < len(self.model.message_groups)):
            return
        group = self.model.message_groups[group_i]
        sent = 0
        for msg in group.messages:
            if all(self._passes(expr, state["vars"]) for expr in msg.trigger_exprs):
                self._log(state, "coach", self._pick(msg.text_by_lang) or "(no text)")
                if msg.writes_var:
                    state["vars"].setdefault(msg.writes_var, "")
                sent += 1
        if not sent:
            self._log(state, "system", f'Message group "{group.name}": no message passed its rules.')

    def _passes(self, expr: str, variables: dict) -> bool:
        result, _ = eval_expr(expr, variables)
        return bool(result)

    # -- micro dialogs -------------------------------------------
    def _launch_dialog(self, state: dict, dialog_i: int) -> None:
        if not (0 <= dialog_i < len(self.model.micro_dialogs)):
            return
        dialog = self.model.micro_dialogs[dialog_i]
        state["open_dialog"] = {"dialog_i": dialog_i, "node_idx": 0}
        state["pending"] = None
        self._log(state, "system", f'▶ Micro dialog "{dialog.name}"')
        self._advance(state)

    def _answer(self, state: dict, value: str) -> None:
        pending = state.get("pending")
        if not pending:
            self._log(state, "system", "No question is waiting for an answer.")
            return
        label = next((o["label"] for o in pending["options"] if o["value"] == value), value)
        self._log(state, "user", label)
        node = self._node_at(pending["dialog_i"], pending["node_idx"])
        if node and node.writes_var:
            state["vars"][node.writes_var] = value
        state["open_dialog"] = {"dialog_i": pending["dialog_i"], "node_idx": pending["node_idx"] + 1}
        state["pending"] = None
        self._advance(state)

    def _advance(self, state: dict) -> None:
        steps = 0
        # per-call cache: {"<dialog>:<group>": chosen absolute node index} -
        # computed once per run of sibling r-group variants as the walker
        # reaches its first node, reused for the rest of that run so the
        # scan-ahead only happens once. Not persisted - state carries the
        # cross-call bookkeeping (`_rgroup_calls`) that makes the pick
        # itself reproducible across separate launches of the same dialog.
        resolved_groups: dict[str, int] = {}
        while state.get("open_dialog") and not state.get("pending"):
            steps += 1
            if steps > _MAX_DIALOG_STEPS:
                self._log(state, "system", "Stopped: dialog step limit reached (possible loop).")
                state["open_dialog"] = None
                return

            od = state["open_dialog"]
            dialog = self.model.micro_dialogs[od["dialog_i"]]
            if od["node_idx"] >= len(dialog.nodes):
                self._log(state, "system", f'■ End of "{dialog.name}"')
                state["open_dialog"] = None
                return

            node = dialog.nodes[od["node_idx"]]
            variables = state["vars"]

            if node.type == "message":
                group = node.randomisation_group
                if group:
                    key = f"{dialog.uid or dialog.i}:{group}"
                    if key not in resolved_groups:
                        run_start = od["node_idx"]
                        run_len = 0
                        j = run_start
                        while (
                            j < len(dialog.nodes)
                            and dialog.nodes[j].type == "message"
                            and dialog.nodes[j].randomisation_group == group
                        ):
                            run_len += 1
                            j += 1
                        calls = state.setdefault("_rgroup_calls", {})
                        call_index = calls.get(key, 0)
                        calls[key] = call_index + 1
                        pick = _rgroup_pick_index(
                            state.get("seed", 0), dialog.uid or dialog.i, group, call_index, run_len
                        )
                        resolved_groups[key] = run_start + pick
                        if run_len > 1:
                            self._log(
                                state, "system",
                                f'🎲 r-group "{group}": picked variant {pick + 1} of {run_len}.'
                            )
                    if od["node_idx"] != resolved_groups[key]:
                        od["node_idx"] += 1
                        continue

                if node.trigger_exprs and not all(self._passes(e, variables) for e in node.trigger_exprs):
                    od["node_idx"] += 1
                    continue
                text = self._render_text(self._pick(node.text_by_lang), variables)
                if text:
                    self._log(state, "coach", text)
                if node.answer_options_by_lang:
                    state["pending"] = {
                        "dialog_i": od["dialog_i"],
                        "node_idx": od["node_idx"],
                        "options": self._options(node),
                    }
                    return
                od["node_idx"] += 1

            elif node.type == "command":
                cmd = self._pick(node.command_by_lang)
                self._log(state, "system", f"[command] {cmd}" if cmd else "[command]")
                od["node_idx"] += 1

            elif node.type == "decision":
                self._run_decision(state, dialog, node)

            else:
                od["node_idx"] += 1

    def _run_decision(self, state, dialog, node) -> None:
        od = state["open_dialog"]
        variables = state["vars"]
        for branch in node.branches:
            result, assignment = eval_expr(branch.expr, variables)
            if assignment:
                variables[assignment[0]] = assignment[1]
            if not result:
                continue
            if branch.jump_dialog or branch.cascade_dialog:
                target = branch.jump_dialog or branch.cascade_dialog
                idx = next((d.i for d in self.model.micro_dialogs if d.name == target), None)
                verb = "jumps" if branch.jump_dialog else "cascades"
                if idx is None:
                    self._log(state, "system", f"decision {verb} to unknown dialog '{target}'")
                    od["node_idx"] += 1
                    return
                self._log(state, "system", f'decision {verb} to "{target}"')
                state["open_dialog"] = {"dialog_i": idx, "node_idx": 0}
                return
            if branch.stop_micro_dialog:
                self._log(state, "system", f'decision stops "{dialog.name}"')
                state["open_dialog"] = None
                return
            od["node_idx"] += 1
            return
        od["node_idx"] += 1  # no branch matched -> fall through

    # -- helpers ------------------------------------------------------
    def _node_at(self, dialog_i: int, node_idx: int):
        dialog = self.model.micro_dialogs[dialog_i]
        return dialog.nodes[node_idx] if node_idx < len(dialog.nodes) else None

    def _options(self, node) -> list[dict]:
        raw = self._pick(node.answer_options_by_lang) or ""
        opts = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            if ":" in line:
                value, label = line.split(":", 1)
            else:
                value = label = line
            opts.append({"value": value.strip(), "label": label.strip()})
        return opts or [{"value": "ok", "label": "OK"}]

    def _pick(self, mapping: dict) -> str:
        if not mapping:
            return ""
        return mapping.get(self.lang) or next(iter(mapping.values()), "")

    def _render_text(self, text: str, variables: dict) -> str:
        if not text or text == "[not set]":
            return ""
        return VARIABLE_RE.sub(
            lambda m: _fmt(variables[m.group(0)]) if m.group(0) in variables else m.group(0),
            text,
        )

    def _stamp(self, state: dict) -> str:
        c = state["clock"]
        return f"day {c['day']}, {c['hour']:02d}:{c['minute']:02d}"

    def _log(self, state: dict, kind: str, text: str) -> None:
        state["transcript"].append({"kind": kind, "text": text, "t": self._stamp(state)})
