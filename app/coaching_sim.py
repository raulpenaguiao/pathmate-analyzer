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


def model_fingerprint(model) -> str | None:
    """Short hash of what the state's indices and uids point into: each
    dialog's path/name and node count in order, and each rule's uid and
    expression. It changes whenever a re-export renumbers anything."""
    if model is None:
        return None
    h = hashlib.sha256()
    for d in model.micro_dialogs:
        h.update(f"d|{d.path or d.name}|{len(d.nodes)}\n".encode())
    for r in model.rules:
        h.update(f"r|{r.uid}|{r.raw_expr}\n".encode())
    return h.hexdigest()[:16]


_model_fingerprint = model_fingerprint  # old private name, kept for existing imports


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


def _abs_minutes(clock: dict) -> int:
    return clock["day"] * 1440 + clock["hour"] * 60 + clock["minute"]


def _parse_hhmm(text) -> int | None:
    """"HH:MM" -> minutes since midnight, or None if unparseable/unset -
    used to resolve a sender's due hour (Phase C)."""
    m = re.match(r"^\s*(\d{1,2}):(\d{2})\s*$", str(text or ""))
    if not m:
        return None
    hour, minute = int(m.group(1)), int(m.group(2))
    if not (0 <= hour < 24 and 0 <= minute < 60):
        return None
    return hour * 60 + minute


_DATE_MOD_RE = re.compile(r"(\$[A-Za-z_][A-Za-z0-9_]*)\{#d\}")


def _apply_date_modifiers(text: str, variables: dict) -> str:
    """`$var{#d}` -> the variable's date in PMCP's fixed system format,
    dd.mm.yyyy (PMCP docs 6.0, Rules §3.5.1 / "format modifiers": "$var{#d}
    Date in fixed system format (dd.mm.yyyy)"). ALEX v01 relies on it to
    zero-pad the $today it builds from unpadded system parts. Values that
    aren't a parseable date pass through as-is. The other documented
    modifiers ({#D}, {#t}, {#T}, {%.2f}) aren't handled yet."""
    def repl(m):
        if m.group(1) not in variables:
            return m.group(0)  # unset: leave it to the caller's own substitution
        raw = _fmt(variables[m.group(1)])
        d = _parse_date(raw)
        return _fmt_date(d) if d else raw
    return _DATE_MOD_RE.sub(repl, text)


# the docs' form has a space before the ID; ALEX's export shows a line break
_QUESTIONNAIRE_BUTTON_RE = re.compile(r"^\s*open-component:questionnaire\s+(\S+?):(.+)$", re.S)


_ALLOWED_AST = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Add, ast.Sub, ast.Mult,
    ast.Div, ast.FloorDiv, ast.Mod, ast.Pow, ast.USub, ast.UAdd, ast.Constant,
    ast.Load,
)


def _eval_arith(expr: str, variables: dict) -> str:
    """Substitute ``$vars`` and evaluate a numeric expression. Falls back to the
    substituted string (used by ``create text``) when it isn't arithmetic."""
    expr = _apply_date_modifiers(expr, variables)
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
            # seeded from the coaching's configured values (bundle only) -
            # without them e.g. ALEX v01's $hyperparameter*EndHour day-slot
            # gates compare against "" and $currentDaySlot reads "night" at 09:00
            "vars": dict(self.model.variable_defaults) if self.model else {},
            "open_dialog": None,
            "pending": None,
            "transcript": [],
            # fixed for the life of this simulation - makes r-group picks
            # (Phase B) reproducible; a fresh reset gets a fresh seed.
            "seed": seed if seed is not None else random.SystemRandom().getrandbits(32),
            # which parser built the model this state was stepped with - a
            # chat must never be continued by the other engine. None when
            # there's no model (a bare participant-import snapshot).
            "engine": self.model.source if self.model else None,
            # state refers to dialogs by index and to rules by uid, both
            # positions in one export. A chat must only be continued on a
            # model with the same fingerprint (see _model_fingerprint).
            "model_fingerprint": model_fingerprint(self.model),
            # auto_periodic: every clock move also runs PERIODIC BASIS
            # (the pre-Phase-E behaviour). Off, PERIODIC BASIS only runs on
            # an explicit `run_periodic` step; DAILY BASIS, due-sender
            # checks and not-answered timeouts are clock-driven either way.
            "settings": {"auto_periodic": True},
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
        elif kind == "set_setting":
            name = action["name"]
            state.setdefault("settings", {})[name] = action.get("value")
            self._log(state, "system", f"Setting {name} = {action.get('value')}")
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
        before = _abs_minutes(clock)

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

        # every clock move can make an open question overdue (Phase C) -
        # check before running any rules, so a stale pending doesn't block a
        # sender that would otherwise fire this same tick.
        self._check_pending_timeout(state)

        for _ in range(max(0, crossed_midnights)):
            # $participantParticipationInDays still reads the previous day
            # during the 00:00 DAILY run and bumps right after it - see
            # _refresh_system_vars for why (a modelling assumption).
            state["vars"]["$participantParticipationInDays"] = str(clock["day"] - 1)
            self._run_context(state, "DAILY BASIS")
            state["vars"]["$participantParticipationInDays"] = str(clock["day"])
        if state.get("settings", {}).get("auto_periodic", True):
            self._run_context(state, "PERIODIC BASIS")
        self._check_due_senders(state)

    def _check_due_senders(self, state: dict) -> None:
        """DAILY-BASIS senders registered as due-today (see _run_context) -
        re-checked on every tick since their one DAILY BASIS evaluation
        moment is typically well before their actual send hour."""
        # Keyed on the engine's own clock day, never on `$today`: the
        # coaching owns that variable and rewrites it during DAILY BASIS
        # (ALEX v01 r-000/r-001 rebuild it unpadded and append a `{#d}`
        # format suffix the engine doesn't interpret), so it never matches
        # the value `_refresh_system_vars` puts back on the next tick.
        today = state["clock"]["day"]
        for rule_uid, registered_day in state.get("_sender_due_today", {}).items():
            if registered_day != today:
                continue  # a stale/previous day's registration, not re-armed yet today
            rule = next((r for r in self.model.rules if r.uid == rule_uid), None)
            if rule is not None:
                self._maybe_auto_launch(state, rule)

    def _check_pending_timeout(self, state: dict) -> None:
        """Phase C: a sender-launched question left unanswered past its
        `not_answered_timeout_minutes` is handled as not-answered - cleared,
        logged, and (best-effort - see docs/stage4_chat_engine_plan.md §5,
        no real coaching has populated `does_not_answer_rules` to verify the
        shape against yet) its does-not-answer handlers are flagged rather
        than evaluated blind."""
        pending = state.get("pending")
        if not pending or not pending.get("rule_uid"):
            return  # no owning sender (manually launched, or an older/legacy state) - no timeout
        rule = next((r for r in self.model.rules if r.uid == pending["rule_uid"]), None)
        timeout_at = pending.get("timeout_at")
        if rule is None or timeout_at is None:
            return
        if _abs_minutes(state["clock"]) < timeout_at:
            return
        dialog = self.model.micro_dialogs[pending["dialog_i"]]
        self._log(state, "system", f'⏱ "{dialog.name}" handled as not answered (timeout).',
                  event={"type": "timeout", "rule_uid": rule.uid, "rule_i": rule.i,
                         **self._dialog_ref(pending["dialog_i"]), "node_idx": pending["node_idx"]})
        state["pending"] = None
        state["open_dialog"] = None
        state["_cascade_stack"] = []  # the whole walk is abandoned, callers included
        if rule.does_not_answer_rules:
            self._log(
                state, "system",
                f"({len(rule.does_not_answer_rules)} does-not-answer rule(s) configured - "
                "not interpreted yet, see the plan doc's §5)."
            )

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
            # same ISO weekday under the name the PMCP docs' Rules example
            # uses ("$systemDayInWeek calculated value equals 1" = Monday),
            # and the one ALEX v01 reads (r-025, r-090)
            "$systemDayInWeek": str(today.isoweekday()),
            # docs 6.0 Variables: "the minute component of the current hour"
            "$systemMinuteOfHour": str(clock["minute"]),
            "$systemHour": str(clock["hour"]),
            "$systemMinute": str(clock["minute"]),
            # The real ALEX v01 export's own rules never reference
            # $systemHour/$systemMinute at all (checked: 0 occurrences) -
            # every hour-of-day gate (incl. "Delayed day start at 3 AM")
            # reads $systemHourOfDay/$systemDecimalMinuteOfHour instead, the
            # latter as a *fraction of an hour* (added directly to the hour
            # to get a decimal-hour value - see "Save current time in
            # decimal format" -> $timeDecimal in the plan doc's §5). Setting
            # both naming conventions since some coaching might genuinely
            # use the other one - found no evidence either way.
            "$systemHourOfDay": str(clock["hour"]),
            "$systemDecimalMinuteOfHour": _fmt(clock["minute"] / 60),
            # PMCP-provided, documented only as "Number of days the
            # participant has been involved in the coaching program" (docs
            # 6.0, Variables). Modelled as the sim's day index (0 on the
            # registration day), except during the 00:00 DAILY run, where it
            # still reads the previous day (see _tick). That's an ASSUMPTION
            # chosen by Raul 2026-09-24 because ALEX v01 depends on it: r-101
            # writes $dailyTasksPerformedToday = P+1 at 00:00, and r-105
            # needs P == $dailyTasksPerformedToday for the rest of the day.
            # Revisit against a real participant snapshot.
            "$participantParticipationInDays": str(clock["day"]),
        })

    # -- rule execution ----------------------------------------------
    def _run_context(self, state: dict, context: str) -> None:
        rules = [r for r in self.model.rules if r.context == context]
        # docs 6.0 Variables: "Open questions for the participant". The
        # engine allows one open question at a time (plan §1), so it's 0/1.
        # Refreshed per rule pass, since answers and launches change it.
        state["vars"]["$participantOpenQuestions"] = "1" if state.get("pending") else "0"
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
                if r.kind == "sender":  # bundle-only - HTML-parsed rules never set .kind
                    if context == "DAILY BASIS":
                        # DAILY BASIS is evaluated once/day (see the crossed-
                        # midnight loop in _tick), typically near day-start -
                        # almost never the sender's actual due hour. Register
                        # it as "due today, once the clock catches up" instead
                        # of gating on the hour right now; _check_due_senders
                        # re-checks the hour on every later tick this same
                        # day. A PERIODIC BASIS sender needs none of this -
                        # that context is already re-evaluated every tick.
                        state.setdefault("_sender_due_today", {})[r.uid] = state["clock"]["day"]
                    else:
                        self._maybe_auto_launch(state, r)
                else:
                    self._log(state, "system", f"Rule #{r.i} sends a message"
                              + (f": {r.comment}" if r.comment else ""))
            if truthy and r.stops_intervention:
                self._log(state, "system", f"Rule #{r.i} stops the intervention.")
            stack.append((r.depth, truthy))

        if fired:
            self._log(state, "rule", f"{context}: applied {fired} rule assignment(s).")

    # -- sender rules -> auto-launch (Phase C) ------------------------
    def _maybe_auto_launch(self, state: dict, rule) -> None:
        if state.get("pending"):
            # Phase D (interruption) isn't implemented as its own feature
            # yet, but a sender firing while a question is already open
            # must not silently clobber it - PMCP "won't overwrite an open
            # question" (docs/stage4_chat_engine_plan.md Phase D). Skipped
            # here; the same rule fires again on a later tick once the
            # open question is answered or times out.
            # logged once per rule per day, not on every tick it keeps retrying
            key = f"{rule.uid}@{state['clock']['day']}"
            logged = state.setdefault("_suppressed_logged", [])
            if key not in logged:
                logged.append(key)
                blocking = state["pending"]
                self._log(state, "rule", f"(rule #{rule.i} suppressed: a question is already open)",
                          event={"type": "suppressed", "rule_uid": rule.uid, "rule_i": rule.i,
                                 "reason": "question_open",
                                 "blocking_rule_uid": blocking.get("rule_uid"),
                                 **{f"blocking_{k}": v for k, v in
                                    self._dialog_ref(blocking["dialog_i"]).items()}})
            return
        if not self._sender_due(state, rule):
            return
        # marked as fired for today even when the target can't be resolved -
        # it was due and attempted, and otherwise the warning below would
        # repeat on every tick for the rest of the day.
        state.setdefault("_sender_last_fired", {})[rule.uid] = state["clock"]["day"]
        dialog_i = self._resolve_dialog_by_path(rule.micro_dialog_path)
        if dialog_i is None:
            self._log(state, "system", f"⚠️ sender rule #{rule.i} has no resolvable target dialog"
                      + (f" ({rule.comment})" if rule.comment else ""),
                      event={"type": "unresolved_target", "rule_uid": rule.uid, "rule_i": rule.i,
                             "dialog_path": list(rule.micro_dialog_path)})
            return
        dialog = self.model.micro_dialogs[dialog_i]
        self._log(state, "system", f'📨 rule #{rule.i} auto-launches "{dialog.name}"'
                  + (f" ({rule.comment})" if rule.comment else ""),
                  event={"type": "launch", "rule_uid": rule.uid, "rule_i": rule.i,
                         **self._dialog_ref(dialog_i), "dialog_path": list(rule.micro_dialog_path)})
        self._launch_dialog(state, dialog_i, rule=rule)

    def _sender_due(self, state: dict, rule) -> bool:
        """Whether `rule`'s configured send hour has arrived and it hasn't
        already fired today. `send_hour_variable` is NOT redundant with the
        condition chain (verified against real data, see the plan doc's
        §5) - it's a genuinely separate gate the engine must enforce."""
        due_minutes = None
        if rule.send_hour_variable:
            val = state["vars"].get(rule.send_hour_variable)
            if val not in (None, "", "-99"):
                # A *computed decimal hour* (e.g. $userSetBedtime-0.17 ->
                # 22.33), not "HH:MM" - the coaching's own rules work in
                # this same decimal-hour space (see $systemHourOfDay +
                # $systemDecimalMinuteOfHour -> $timeDecimal). Falls back to
                # an "HH:MM" parse in case some coaching stores it that way
                # instead - no real example of that seen yet.
                try:
                    due_minutes = round(float(val) * 60) % 1440
                except (TypeError, ValueError):
                    due_minutes = _parse_hhmm(val)
        if due_minutes is None:
            due_minutes = _parse_hhmm(rule.send_hour_literal or rule.send_hour_clock)
        if due_minutes is None:
            return False  # no resolvable schedule - can't tell it's due
        clock = state["clock"]
        if clock["hour"] * 60 + clock["minute"] < due_minutes:
            return False
        last_fired_day = state.get("_sender_last_fired", {}).get(rule.uid)
        return last_fired_day != clock["day"]

    def _resolve_dialog_by_path(self, path: list[str]) -> int | None:
        """`micro_dialog_path` is a list of folder-tree breadcrumbs (or
        `['']` when PMCP never resolved a target) - only the last non-empty
        segment is the actual dialog name, resolved the same way
        `DecisionBranch.jump_dialog`/`cascade_dialog` already are."""
        target = next((seg for seg in reversed(path or []) if seg), None)
        if not target:
            return None
        return next((d.i for d in self.model.micro_dialogs if d.name == target), None)

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
    def _launch_dialog(self, state: dict, dialog_i: int, *, rule=None) -> None:
        if not (0 <= dialog_i < len(self.model.micro_dialogs)):
            return
        dialog = self.model.micro_dialogs[dialog_i]
        # `origin_rule_uid` travels with `open_dialog` (Phase C): only a
        # sender-triggered launch carries one, and only then does a
        # question opened during this walk get a not-answered timeout.
        state["open_dialog"] = {
            "dialog_i": dialog_i, "node_idx": 0,
            "origin_rule_uid": rule.uid if rule is not None else None,
        }
        state["pending"] = None
        state["_cascade_stack"] = []
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
        state["open_dialog"] = {
            "dialog_i": pending["dialog_i"], "node_idx": pending["node_idx"] + 1,
            "origin_rule_uid": pending.get("rule_uid"),
        }
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
                self._end_dialog(state)
                continue

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
                            state.get("seed", 0), dialog.path or dialog.uid or dialog.i,
                            group, call_index, run_len,
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
                    pending = {
                        "dialog_i": od["dialog_i"],
                        "node_idx": od["node_idx"],
                        "options": self._options(node, variables),
                    }
                    # timeout_at: absolute minutes (same unit as
                    # _abs_minutes), None when no not-answered timeout applies
                    pending["timeout_at"] = None
                    rule_uid = od.get("origin_rule_uid")
                    if rule_uid:
                        pending["rule_uid"] = rule_uid
                        pending["sent_at"] = _abs_minutes(state["clock"])
                        rule = next((r for r in self.model.rules if r.uid == rule_uid), None)
                        if rule is not None and rule.not_answered_timeout_minutes:
                            pending["timeout_at"] = pending["sent_at"] + rule.not_answered_timeout_minutes
                    state["pending"] = pending
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
        """PMCP 6.0 docs (Micro Dialogs §5.4): a decision point's rules "are
        processed from top to bottom", and may "define new calculated
        variables". Every rule is evaluated and its assignment applied. The
        first TRUE rule carrying a jump / cascade / stop acts on it (those
        are all "...if TRUE" settings); otherwise the walk falls through to
        the next node. A rule's "Jump to dialog message if TRUE / FALSE"
        (§5.4.2: "the dialogue will immediately continue at the selected
        target message") redirects within the dialog. ASSUMPTION: a
        dialog-level jump/cascade/stop on the same TRUE rule takes
        precedence over its message jump. The docs don't say."""
        od = state["open_dialog"]
        variables = state["vars"]
        # rules nest (Rules §2.2: child rules = AND): a rule only runs when
        # every ancestor was TRUE, the same depth stack as _run_context
        stack: list[tuple[int, bool]] = []
        for branch in node.branches:
            while stack and stack[-1][0] >= branch.depth:
                stack.pop()
            if any(not active for _d, active in stack):
                stack.append((branch.depth, False))
                continue
            result, assignment = eval_expr(branch.expr, variables)
            stack.append((branch.depth, bool(result)))
            if assignment:
                variables[assignment[0]] = assignment[1]
            if result is None:
                continue  # unsupported rule: neither its TRUE nor its FALSE path is known
            if not result:
                if self._jump_to_message(state, dialog, branch.jump_msg_false):
                    return
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
                if branch.cascade_dialog and not branch.jump_dialog:
                    # docs §5.4.3.2: "After the cascaded dialogue finishes,
                    # execution returns to the original dialogue" - resume
                    # just after this decision point
                    state.setdefault("_cascade_stack", []).append(
                        {**od, "node_idx": od["node_idx"] + 1})
                state["open_dialog"] = {
                    "dialog_i": idx, "node_idx": 0,
                    "origin_rule_uid": od.get("origin_rule_uid"),
                }
                return
            if branch.stop_micro_dialog:
                self._log(state, "system", f'decision stops "{dialog.name}"')
                self._end_dialog(state)
                return
            if branch.leave_decision_point:
                # not defined in the PMCP 6.0 docs, and no live precedent yet
                self._log(state, "system", "⚠️ 'leave decision point' is set on a TRUE rule, "
                          "but its meaning is unknown, so it's ignored")
            if self._jump_to_message(state, dialog, branch.jump_msg_true):
                return
        od["node_idx"] += 1  # no rule redirected -> fall through

    def _jump_to_message(self, state, dialog, target) -> bool:
        """Redirect the walk to another node of the same dialog. False (and
        the walk carries on) when there's no target or it can't be found."""
        if not target:
            return False
        idx = None
        if isinstance(target, str):
            idx = next((k for k, n in enumerate(dialog.nodes) if n.uid == target), None)
        if idx is None:
            shown = target.get("raw") if isinstance(target, dict) else target
            self._log(state, "system", f"⚠️ decision jumps to unknown message {shown!r}, ignored")
            return False
        self._log(state, "system", f"decision jumps to message {idx} of \"{dialog.name}\"")
        state["open_dialog"]["node_idx"] = idx
        return True

    # -- helpers ------------------------------------------------------
    def _end_dialog(self, state: dict) -> None:
        """The current dialog is done: resume the dialog that cascaded into
        it, if any (docs §5.4.3.2), else close. ASSUMPTION: a stop inside a
        cascaded dialog ends only that dialog, like reaching its end.
        Nothing in the docs says whether it also stops the caller."""
        stack = state.get("_cascade_stack") or []
        if stack:
            state["open_dialog"] = stack.pop()
            parent = self.model.micro_dialogs[state["open_dialog"]["dialog_i"]]
            self._log(state, "system", f'↩ back to "{parent.name}"')
        else:
            state["open_dialog"] = None

    def _node_at(self, dialog_i: int, node_idx: int):
        dialog = self.model.micro_dialogs[dialog_i]
        return dialog.nodes[node_idx] if node_idx < len(dialog.nodes) else None

    def _options(self, node, variables: dict | None = None) -> list[dict]:
        raw = self._pick(node.answer_options_by_lang) or ""
        m = _QUESTIONNAIRE_BUTTON_RE.match(raw)
        if m:
            # PMCP 6.0 docs (Channels > Questionnaires, 7.1): "open-component:
            # questionnaire [Questionnaire ID]:[Button Title]", a single button,
            # and "the chat will remain blocked until the participant
            # completes the Questionnaire". Its answers reach coaching
            # variables only via PMCMS bindings, which aren't in coaching.json,
            # so the user sets them (set_var) before answering "completed".
            qid = self._render_text(m.group(1), variables or {})
            return [{"label": m.group(2).strip(), "value": "completed",
                     "component": "questionnaire", "questionnaire_id": qid}]
        opts = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            # PMCP 6.0 docs (Micro Dialogs, input formats): "Display
            # Label:Transmitted Value", e.g. "First answer option:1". Split on
            # the LAST colon so a label may itself contain one. A "! " prefix
            # marks an exclusive Select-Many option and isn't displayed.
            if ":" in line:
                label, value = line.rsplit(":", 1)
            else:
                value = label = line
            label = label.strip()
            if label.startswith("! "):
                label = label[2:]
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
            _apply_date_modifiers(text, variables),
        )

    def _stamp(self, state: dict) -> str:
        c = state["clock"]
        return f"day {c['day']}, {c['hour']:02d}:{c['minute']:02d}"

    def _log(self, state: dict, kind: str, text: str, event: dict | None = None) -> None:
        line = {"kind": kind, "text": text, "t": self._stamp(state)}
        if event is not None:
            # structured twin of `text` for the Chat tab (launch / timeout /
            # suppressed / unresolved_target) - `text` stays the fallback
            line["event"] = event
        state["transcript"].append(line)

    def _dialog_ref(self, dialog_i: int) -> dict:
        d = self.model.micro_dialogs[dialog_i]
        # dialog_i / dialog_uid are only valid within this export; use
        # dialog_menu_path to refer to the dialog anywhere else
        return {"dialog_i": d.i, "dialog_uid": d.uid, "dialog_name": d.name,
                "dialog_menu_path": d.path or d.name}
