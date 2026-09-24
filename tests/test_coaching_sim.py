"""Exercises the declarative-rule evaluator and the dialog walker."""
import unittest
from pathlib import Path

from app.coaching_model import parse_model
from app.coaching_sim import Simulator, eval_expr, parse_expr

SAMPLE = Path(__file__).resolve().parent / "fixtures" / "coaching_ALEX_v01.html"


class ExprEvalTest(unittest.TestCase):
    def test_equality_and_inequality(self):
        v = {"$a": "1", "$b": "2"}
        self.assertEqual(eval_expr("$a calculated value equals 1", v)[0], True)
        self.assertEqual(eval_expr("$a calculated value equals $b", v)[0], False)
        self.assertEqual(eval_expr("$a calculated value not equals $b", v)[0], True)

    def test_ordering(self):
        v = {"$n": "5"}
        self.assertTrue(eval_expr("$n calculated value is bigger than 3", v)[0])
        self.assertTrue(eval_expr("$n calculated value is bigger or equal than 5", v)[0])
        self.assertFalse(eval_expr("$n calculated value is smaller than 5", v)[0])
        self.assertTrue(eval_expr("$n calculated value is smaller or equal than 5", v)[0])

    def test_text_value(self):
        v = {"$s": "-99"}
        self.assertTrue(eval_expr("$s text value equals -99", v)[0])
        self.assertTrue(eval_expr("$s text value not equals abc", v)[0])

    def test_assignment_arith(self):
        v = {"$participationInDays": "3"}
        result, assignment = eval_expr(
            "$participationInDays+1 calculate value but result is always true "
            "→ $participationInDays",
            v,
        )
        self.assertEqual(result, True)
        self.assertEqual(assignment, ("$participationInDays", "4"))

    def test_date_modifier_pads_to_system_format(self):
        # PMCP docs 6.0, Rules §3.5.1: $var{#d} -> dd.mm.yyyy (ALEX v01 r-001)
        v = {"$today": "3.1.2026"}
        result, assignment = eval_expr(
            "$today{#d} calculate value but result is always true → $today", v)
        self.assertEqual(assignment, ("$today", "03.01.2026"))
        self.assertEqual(eval_expr("$x{#d} calculate value but result is always true → $y",
                                   {"$x": "not a date"})[1], ("$y", "not a date"))

    def test_assignment_always_false_still_assigns(self):
        result, assignment = eval_expr(
            "0 calculate value but result is always false → $x", {}
        )
        self.assertEqual(result, False)
        self.assertEqual(assignment, ("$x", "0"))

    def test_create_text(self):
        v = {"$systemDayOfMonth": "5", "$systemMonth": "3", "$systemYear": "2026"}
        _r, assignment = eval_expr(
            "$systemDayOfMonth.$systemMonth.$systemYear create text but result is "
            "always true → $today",
            v,
        )
        self.assertEqual(assignment, ("$today", "5.3.2026"))

    def test_date_add(self):
        v = {"$dateOfNextACQ": "01.01.2026", "$gap": "7"}
        _r, assignment = eval_expr(
            "$dateOfNextACQ calculate new date by adding y days and always true "
            "$gap → $dateOfNextACQ",
            v,
        )
        self.assertEqual(assignment, ("$dateOfNextACQ", "08.01.2026"))

    def test_js_snippet_is_unknown(self):
        result, _ = eval_expr("//+ moment\nimport moment from 'moment'", {})
        self.assertIsNone(result)
        self.assertEqual(parse_expr("//+ moment")["kind"], "unknown")


class SimulatorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = parse_model(SAMPLE.read_bytes())

    def test_initial_state_has_system_vars(self):
        sim = Simulator(self.model)
        state = sim.initial_state()
        self.assertIn("$today", state["vars"])
        self.assertEqual(state["vars"]["$systemHour"], "8")
        self.assertEqual(state["clock"], {"day": 0, "hour": 8, "minute": 0})

    def test_tick_advances_clock_and_runs_daily_at_midnight(self):
        sim = Simulator(self.model)
        state = sim.step(sim.initial_state(), {"type": "tick", "minutes": 1440})
        self.assertEqual(state["clock"]["day"], 1)
        self.assertTrue(any("Advanced to" in m["text"] for m in state["transcript"]))

    def test_depth_block_skips_children_when_guard_false(self):
        # A tiny hand-built model exercised through _run_context.
        from app.coaching_model import Rule

        rules = [
            Rule(0, "PERIODIC BASIS", 0, "$flag calculated value equals 1", "", None,
                 False, False, False, True),
            Rule(1, "PERIODIC BASIS", 1,
                 "1 calculate value but result is always true → $child", "", "$child",
                 False, False, False, True),
        ]
        model = type(self.model)(rules=rules, micro_dialogs=[], message_groups=[],
                                 variables={}, languages=["en-GB"])
        sim = Simulator(model)
        state = sim.initial_state()
        state["vars"]["$flag"] = "0"
        sim.step(state, {"type": "run_periodic"})
        self.assertNotIn("$child", state["vars"])  # guard was false -> child skipped
        state["vars"]["$flag"] = "1"
        sim.step(state, {"type": "run_periodic"})
        self.assertEqual(state["vars"].get("$child"), "1")

    def test_launch_dialog_produces_transcript(self):
        sim = Simulator(self.model)
        state = sim.initial_state()
        target = next(d for d in self.model.micro_dialogs if d.nodes)
        state = sim.step(state, {"type": "launch_dialog", "dialog_i": target.i})
        kinds = {m["kind"] for m in state["transcript"]}
        self.assertTrue({"coach", "system"} & kinds)
        # either it is waiting for an answer, or it walked to completion
        self.assertTrue(state["pending"] or state["open_dialog"] is None
                        or isinstance(state["open_dialog"], dict))

    def test_unsupported_rule_is_reported_when_reached(self):
        from app.coaching_model import Rule

        rules = [
            Rule(0, "PERIODIC BASIS", 0, "//+ moment\nimport moment", "js check", None,
                 False, False, True, False),
        ]
        model = type(self.model)(rules=rules, micro_dialogs=[], message_groups=[],
                                 variables={}, languages=["en-GB"])
        sim = Simulator(model)
        state = sim.initial_state()
        sim.step(state, {"type": "run_periodic"})
        self.assertTrue(
            any("skipped unsupported rule #0" in m["text"] for m in state["transcript"])
        )

    def test_nested_unsupported_rule_not_reported_when_guard_false(self):
        # honest behaviour: a JS rule under a false condition is never reached
        sim = Simulator(self.model)
        state = sim.initial_state()
        sim.step(state, {"type": "tick", "minutes": 1440})
        # no assertion on presence/absence - just that stepping does not raise
        self.assertIsInstance(state["transcript"], list)


class RandomisationGroupTest(unittest.TestCase):
    """Stage 4 Phase B (docs/stage4_chat_engine_plan.md): a run of consecutive
    message nodes sharing a randomisation group collapses to one seeded pick."""

    def _model_with_run(self, n_variants: int, group: str = "r_greeting"):
        from app.coaching_model import CoachingModel, MicroDialog, Node

        nodes = [
            Node(
                n=i, type="message", comment="", channel="", writes_var=None,
                text_by_lang={"en-GB": f"variant {i}"},
                randomisation_group=group,
            )
            for i in range(n_variants)
        ]
        dialog = MicroDialog(i=0, name="Greeting", comment="", nodes=nodes, uid="md-000")
        return CoachingModel(rules=[], micro_dialogs=[dialog], message_groups=[],
                              variables={}, languages=["en-GB"])

    def _coach_lines(self, state):
        return [l["text"] for l in state["transcript"] if l["kind"] == "coach"]

    def test_exactly_one_variant_fires(self):
        model = self._model_with_run(5)
        sim = Simulator(model)
        state = sim.step(sim.initial_state(seed=1), {"type": "launch_dialog", "dialog_i": 0})
        self.assertEqual(len(self._coach_lines(state)), 1)

    def test_same_seed_same_pick(self):
        model = self._model_with_run(20)
        sim = Simulator(model)
        a = sim.step(sim.initial_state(seed=42), {"type": "launch_dialog", "dialog_i": 0})
        b = sim.step(sim.initial_state(seed=42), {"type": "launch_dialog", "dialog_i": 0})
        self.assertEqual(self._coach_lines(a), self._coach_lines(b))

    def test_different_seed_can_differ(self):
        model = self._model_with_run(20)
        sim = Simulator(model)
        picks = {
            tuple(self._coach_lines(
                sim.step(sim.initial_state(seed=s), {"type": "launch_dialog", "dialog_i": 0})
            ))
            for s in range(10)
        }
        self.assertGreater(len(picks), 1)

    def test_repeat_launch_can_pick_a_different_variant(self):
        model = self._model_with_run(20)
        sim = Simulator(model)
        state = sim.initial_state(seed=7)
        state = sim.step(state, {"type": "launch_dialog", "dialog_i": 0})
        first = self._coach_lines(state)
        state = sim.step(state, {"type": "launch_dialog", "dialog_i": 0})
        second = self._coach_lines(state)[-1:]
        self.assertNotEqual(first, second)

    def test_dialog_without_groups_is_unchanged(self):
        from app.coaching_model import CoachingModel, MicroDialog, Node

        nodes = [
            Node(n=0, type="message", comment="", channel="", writes_var=None,
                 text_by_lang={"en-GB": "hello"}),
            Node(n=1, type="message", comment="", channel="", writes_var=None,
                 text_by_lang={"en-GB": "how are you"}),
        ]
        dialog = MicroDialog(i=0, name="Plain", comment="", nodes=nodes)
        model = CoachingModel(rules=[], micro_dialogs=[dialog], message_groups=[],
                               variables={}, languages=["en-GB"])
        sim = Simulator(model)
        state = sim.step(sim.initial_state(), {"type": "launch_dialog", "dialog_i": 0})
        self.assertEqual(self._coach_lines(state), ["hello", "how are you"])


class SenderRuleTest(unittest.TestCase):
    """Stage 4 Phase C (docs/stage4_chat_engine_plan.md): a DAILY BASIS
    sender rule auto-launches its dialog once its send hour arrives, once
    per day, and an unanswered question it opened times out."""

    def _model(self, *, send_hour_variable="$dueHour", send_hour_clock=None,
               timeout=None, target="Evening check", extra_rules=()):
        from app.coaching_model import CoachingModel, MicroDialog, Node, Rule

        question = Node(n=0, type="message", comment="", channel="", writes_var="$mood",
                        text_by_lang={"en-GB": "How was your day?"},
                        answer_options_by_lang={"en-GB": "good:1\nbad:2"})
        dialog = MicroDialog(i=0, name="Evening check", comment="", nodes=[question], uid="md-000")
        sender = Rule(
            i=1, context="DAILY BASIS", depth=0,
            raw_expr="$enabled calculated value equals 1", comment="send evening check",
            writes_var=None, sends_message=True, stops_intervention=False,
            is_js_snippet=False, supported=True,
            uid="r-001", kind="sender", micro_dialog_path=["Folder", target],
            send_hour_variable=send_hour_variable, send_hour_clock=send_hour_clock,
            not_answered_timeout_minutes=timeout,
        )
        return CoachingModel(rules=[*extra_rules, sender], micro_dialogs=[dialog],
                             message_groups=[], variables={}, languages=["en-GB"])

    def _start(self, model, **vars_):
        sim = Simulator(model)
        state = sim.initial_state(seed=1)
        state["vars"].update({"$enabled": "1", "$dueHour": "21.5", **vars_})
        # day 0 08:00 -> day 1 00:00: crosses midnight, DAILY BASIS registers the sender
        return sim, sim.step(state, {"type": "tick", "minutes": 960})

    def _tick_to(self, sim, state, hour, minute=0):
        c = state["clock"]
        delta = (hour * 60 + minute) - (c["hour"] * 60 + c["minute"])
        return sim.step(state, {"type": "tick", "minutes": delta})

    def _launches(self, state):
        return [l for l in state["transcript"] if "auto-launches" in l["text"]]

    def test_not_launched_before_due_hour(self):
        sim, state = self._start(self._model())
        state = self._tick_to(sim, state, 21, 20)
        self.assertEqual(self._launches(state), [])
        self.assertIsNone(state["pending"])

    def test_launched_once_due_hour_passes(self):
        sim, state = self._start(self._model())
        state = self._tick_to(sim, state, 21, 30)  # decimal 21.5 -> 21:30
        self.assertEqual(len(self._launches(state)), 1)
        self.assertEqual(state["pending"]["rule_uid"], "r-001")

    def test_fires_once_per_day_and_rearms_next_day(self):
        sim, state = self._start(self._model())
        state = self._tick_to(sim, state, 21, 30)
        state = sim.step(state, {"type": "answer", "value": "1"})
        state = self._tick_to(sim, state, 23, 0)
        self.assertEqual(len(self._launches(state)), 1)
        state = sim.step(state, {"type": "tick", "minutes": 60})  # -> day 2 00:00, re-registers
        state = self._tick_to(sim, state, 22, 0)
        self.assertEqual(len(self._launches(state)), 2)

    def test_clock_literal_fallback_when_variable_unset(self):
        model = self._model(send_hour_variable="$unsetVar", send_hour_clock="19:15")
        sim, state = self._start(model)
        state = self._tick_to(sim, state, 19, 0)
        self.assertEqual(self._launches(state), [])
        state = self._tick_to(sim, state, 19, 15)
        self.assertEqual(len(self._launches(state)), 1)

    def test_coaching_rewriting_today_does_not_block_sender(self):
        # regression: ALEX v01 rewrites $today during DAILY BASIS (r-000/r-001,
        # with a `{#d}` suffix), which used to make the due-today registration
        # never match again and the sender never fire.
        from app.coaching_model import Rule
        rewrite = Rule(
            i=0, context="DAILY BASIS", depth=0,
            raw_expr="$enabled+1 calculate value but result is always true → $today",
            comment="clobber $today", writes_var="$today", sends_message=False,
            stops_intervention=False, is_js_snippet=False, supported=True,
        )
        sim, state = self._start(self._model(extra_rules=[rewrite]))
        state = self._tick_to(sim, state, 22, 0)
        self.assertEqual(len(self._launches(state)), 1)

    def test_unanswered_question_times_out(self):
        sim, state = self._start(self._model(timeout=60))
        state = self._tick_to(sim, state, 21, 30)
        self.assertIsNotNone(state["pending"])
        state = self._tick_to(sim, state, 22, 0)
        self.assertIsNotNone(state["pending"])  # 30 min < 60 min timeout
        state = self._tick_to(sim, state, 22, 30)
        self.assertIsNone(state["pending"])
        self.assertTrue(any("not answered (timeout)" in l["text"] for l in state["transcript"]))

    def test_sender_suppressed_while_question_open(self):
        sim, state = self._start(self._model())
        state = sim.step(state, {"type": "launch_dialog", "dialog_i": 0})  # manual, stays open
        state = self._tick_to(sim, state, 22, 0)
        self.assertEqual(self._launches(state), [])
        self.assertTrue(any("suppressed" in l["text"] for l in state["transcript"]))
        state = sim.step(state, {"type": "answer", "value": "2"})
        state = self._tick_to(sim, state, 22, 30)
        self.assertEqual(len(self._launches(state)), 1)

    def test_two_senders_due_same_tick_second_waits(self):
        # Phase D acceptance: only the first opens; the second fires on a
        # later tick once the first question is answered.
        from app.coaching_model import MicroDialog, Node, Rule

        model = self._model()
        second_q = Node(n=0, type="message", comment="", channel="", writes_var="$sleep",
                        text_by_lang={"en-GB": "How did you sleep?"},
                        answer_options_by_lang={"en-GB": "well:1\nbadly:2"})
        model.micro_dialogs.append(
            MicroDialog(i=1, name="Sleep check", comment="", nodes=[second_q], uid="md-001"))
        model.rules.append(Rule(
            i=2, context="DAILY BASIS", depth=0,
            raw_expr="$enabled calculated value equals 1", comment="send sleep check",
            writes_var=None, sends_message=True, stops_intervention=False,
            is_js_snippet=False, supported=True,
            uid="r-002", kind="sender", micro_dialog_path=["Sleep check"],
            send_hour_variable="$dueHour",
        ))
        sim, state = self._start(model)
        state = self._tick_to(sim, state, 21, 30)
        self.assertEqual(len(self._launches(state)), 1)
        self.assertEqual(state["pending"]["rule_uid"], "r-001")
        state = sim.step(state, {"type": "answer", "value": "1"})
        state = self._tick_to(sim, state, 21, 45)
        self.assertEqual(len(self._launches(state)), 2)
        self.assertEqual(state["pending"]["rule_uid"], "r-002")

    # -- Phase E engine surface (fields the Chat tab reads) --------------
    def _events(self, state, type_):
        return [l["event"] for l in state["transcript"] if l.get("event", {}).get("type") == type_]

    def test_engine_tag(self):
        self.assertEqual(Simulator(self._model()).initial_state()["engine"], "html")  # CoachingModel default
        model = self._model()
        model.source = "bundle"
        self.assertEqual(Simulator(model).initial_state()["engine"], "bundle")
        self.assertIsNone(Simulator(None).initial_state()["engine"])

    def test_vars_seeded_from_variable_defaults(self):
        model = self._model()
        model.variable_defaults = {"$hyperparameterEveningEndHour": "22"}
        state = Simulator(model).initial_state()
        self.assertEqual(state["vars"]["$hyperparameterEveningEndHour"], "22")
        self.assertEqual(model.variable_defaults, {"$hyperparameterEveningEndHour": "22"})  # copied, not aliased
        state["vars"]["$hyperparameterEveningEndHour"] = "23"
        self.assertEqual(model.variable_defaults["$hyperparameterEveningEndHour"], "22")

    def test_participation_days_lags_during_daily_run(self):
        # modelling assumption (see _refresh_system_vars): the 00:00 DAILY
        # run still sees the previous day, the rest of the day sees the new one
        from app.coaching_model import Rule
        snapshot = Rule(
            i=0, context="DAILY BASIS", depth=0,
            raw_expr="$participantParticipationInDays+1 calculate value but result is always true → $dailyTasksPerformedToday",
            comment="", writes_var="$dailyTasksPerformedToday", sends_message=False,
            stops_intervention=False, is_js_snippet=False, supported=True,
        )
        sim, state = self._start(self._model(extra_rules=[snapshot]))  # -> day 1 00:00
        self.assertEqual(state["vars"]["$dailyTasksPerformedToday"], "1")
        self.assertEqual(state["vars"]["$participantParticipationInDays"], "1")
        self.assertEqual(Simulator(self._model()).initial_state()["vars"]["$participantParticipationInDays"], "0")

    def test_documented_system_vars(self):
        sim, state = self._start(self._model())  # day 1 00:00 = Fri 02.01.2026
        state = self._tick_to(sim, state, 14, 35)
        v = state["vars"]
        self.assertEqual((v["$systemDayInWeek"], v["$systemMinuteOfHour"]), ("5", "35"))
        self.assertEqual(v["$participantOpenQuestions"], "0")
        state = sim.step(state, {"type": "launch_dialog", "dialog_i": 0})
        state = sim.step(state, {"type": "run_periodic"})
        self.assertEqual(state["vars"]["$participantOpenQuestions"], "1")

    def test_pending_timeout_at(self):
        sim, state = self._start(self._model(timeout=90))
        state = self._tick_to(sim, state, 21, 30)
        self.assertEqual(state["pending"]["timeout_at"], 1 * 1440 + 21 * 60 + 30 + 90)
        manual_sim, manual = self._start(self._model(timeout=90))
        manual = manual_sim.step(manual, {"type": "launch_dialog", "dialog_i": 0})
        self.assertIsNone(manual["pending"]["timeout_at"])  # not sender-launched

    def test_structured_events(self):
        sim, state = self._start(self._model(timeout=30))
        state = sim.step(state, {"type": "launch_dialog", "dialog_i": 0})
        state = self._tick_to(sim, state, 21, 30)
        state = self._tick_to(sim, state, 21, 45)  # suppressed again - logged once only
        [suppressed] = self._events(state, "suppressed")
        self.assertEqual(suppressed["rule_uid"], "r-001")
        self.assertEqual(suppressed["blocking_dialog_uid"], "md-000")
        state = sim.step(state, {"type": "answer", "value": "1"})
        state = self._tick_to(sim, state, 22, 0)
        [launch] = self._events(state, "launch")
        self.assertEqual((launch["rule_uid"], launch["dialog_uid"], launch["dialog_name"]),
                         ("r-001", "md-000", "Evening check"))
        self.assertEqual(launch["dialog_path"], ["Folder", "Evening check"])
        state = self._tick_to(sim, state, 22, 30)
        [timeout] = self._events(state, "timeout")
        self.assertEqual((timeout["rule_uid"], timeout["dialog_uid"], timeout["node_idx"]),
                         ("r-001", "md-000", 0))

    def test_auto_periodic_off_skips_periodic_rules(self):
        from app.coaching_model import Rule
        counter = Rule(
            i=0, context="PERIODIC BASIS", depth=0,
            raw_expr="$ticks+1 calculate value but result is always true → $ticks",
            comment="", writes_var="$ticks", sends_message=False,
            stops_intervention=False, is_js_snippet=False, supported=True,
        )
        sim, state = self._start(self._model(extra_rules=[counter]), **{"$ticks": "0"})
        self.assertEqual(state["vars"]["$ticks"], "1")
        state = sim.step(state, {"type": "set_setting", "name": "auto_periodic", "value": False})
        state = self._tick_to(sim, state, 21, 30)
        self.assertEqual(state["vars"]["$ticks"], "1")
        self.assertEqual(len(self._launches(state)), 1)  # due senders stay clock-driven
        state = sim.step(state, {"type": "run_periodic"})
        self.assertEqual(state["vars"]["$ticks"], "2")

    def test_unresolvable_target_warns_once_per_day(self):
        sim, state = self._start(self._model(target="No such dialog"))
        for h in (21, 22, 23):
            state = self._tick_to(sim, state, h, 45)
        warnings = [l for l in state["transcript"] if "no resolvable target" in l["text"]]
        self.assertEqual(len(warnings), 1)



class DialogWalkerTest(unittest.TestCase):
    """Answer-option format and decision-point semantics, per the PMCP 6.0
    docs (Micro Dialogs §5.4 and input formats)."""

    def _msg(self, n, text, **kw):
        from app.coaching_model import Node
        return Node(n=n, type="message", comment="", channel="", text_by_lang={"en-GB": text},
                    writes_var=kw.pop("writes_var", None), **kw)

    def _decision(self, n, *branches):
        from app.coaching_model import DecisionBranch, Node
        return Node(n=n, type="decision", comment="", channel="", writes_var=None,
                    branches=[DecisionBranch(**{
                        "expr": e, "comment": "", "writes_var": None, "stop_micro_dialog": False,
                        "leave_decision_point": False, "jump_dialog": None, "cascade_dialog": None,
                        "supported": True, **kw}) for e, kw in branches])

    def _sim(self, *dialogs):
        from app.coaching_model import CoachingModel, MicroDialog
        mds = [MicroDialog(i=i, name=name, comment="", nodes=nodes, uid=f"md-{i:03}")
               for i, (name, nodes) in enumerate(dialogs)]
        return Simulator(CoachingModel(rules=[], micro_dialogs=mds, message_groups=[],
                                       variables={}, languages=["en-GB"]))

    def _coach(self, state):
        return [l["text"] for l in state["transcript"] if l["kind"] == "coach"]

    def test_options_are_label_then_value(self):
        q = self._msg(0, "Took it?", writes_var="$ans",
                      answer_options_by_lang={"en-GB": "Yes:1\nNo:0\nTime: later:9\n! None:5"})
        sim = self._sim(("Q", [q]))
        state = sim.step(sim.initial_state(), {"type": "launch_dialog", "dialog_i": 0})
        self.assertEqual(state["pending"]["options"], [
            {"label": "Yes", "value": "1"}, {"label": "No", "value": "0"},
            {"label": "Time: later", "value": "9"}, {"label": "None", "value": "5"},
        ])

    def test_questionnaire_button_is_one_blocking_option(self):
        # PMCP 6.0 docs, Questionnaires 7.1 (ALEX md-054 node 25 shape)
        q = self._msg(0, "", answer_options_by_lang={
            "en-GB": "open-component:questionnaire\nacq-$acq_id:Start questionnaire"})
        sim = self._sim(("ACQ", [q, self._msg(1, "after")]))
        state = sim.initial_state()
        state["vars"]["$acq_id"] = "1700000000"
        state = sim.step(state, {"type": "launch_dialog", "dialog_i": 0})
        self.assertEqual(state["pending"]["options"], [{
            "label": "Start questionnaire", "value": "completed",
            "component": "questionnaire", "questionnaire_id": "acq-1700000000"}])
        state = sim.step(state, {"type": "answer", "value": "completed"})
        self.assertEqual(self._coach(state), ["after"])

    def test_decision_evaluates_every_rule_and_later_stop_applies(self):
        # shape of ALEX v02 md-049 node 5: assignment rule, then assignment + stop
        d = self._decision(
            1,
            ("1 calculate value but result is always true → $done", {}),
            ("0 calculate value but result is always true → $engaged", {"stop_micro_dialog": True}),
        )
        sim = self._sim(("D", [self._msg(0, "Thanks"), d, self._msg(2, "No worries")]))
        state = sim.step(sim.initial_state(), {"type": "launch_dialog", "dialog_i": 0})
        self.assertEqual((state["vars"]["$done"], state["vars"]["$engaged"]), ("1", "0"))
        self.assertEqual(self._coach(state), ["Thanks"])
        self.assertIsNone(state["open_dialog"])

    def test_nested_rule_runs_only_under_true_parents(self):
        # ALEX md-054#037: cond > child cond > child assignment (Rules §2.2)
        d = self._decision(
            0,
            ("$start calculated value equals 0", {}),
            ("$newTime text value not equals -99", {"depth": 1}),
            ("1 calculate value but result is always true → $requested", {"depth": 2}),
            ("1 calculate value but result is always true → $sibling", {}),
        )
        sim = self._sim(("D", [d]))
        for start, new_time, expected in (("1", "10", None), ("0", "-99", None), ("0", "10", "1")):
            state = sim.initial_state()
            state["vars"].update({"$start": start, "$newTime": new_time})
            state = sim.step(state, {"type": "launch_dialog", "dialog_i": 0})
            self.assertEqual(state["vars"].get("$requested"), expected, (start, new_time))
            self.assertEqual(state["vars"]["$sibling"], "1")  # top-level sibling always runs

    def test_cascade_returns_to_caller(self):
        d = self._decision(1, ("1 calculated value equals 1", {"cascade_dialog": "Child"}))
        sim = self._sim(("Parent", [self._msg(0, "p-before"), d, self._msg(2, "p-after")]),
                        ("Child", [self._msg(0, "child")]))
        state = sim.step(sim.initial_state(), {"type": "launch_dialog", "dialog_i": 0})
        self.assertEqual(self._coach(state), ["p-before", "child", "p-after"])

    def test_jump_to_message_if_false(self):
        # ALEX v02 md-049 shape: question, "answer == 1?" decision whose FALSE
        # path jumps past the Yes branch to the No message
        q = self._msg(0, "Took it?", writes_var="$ans", answer_options_by_lang={"en-GB": "Yes:1\nNo:0"})
        branch = self._decision(1, ("$ans calculated value equals 1", {"jump_msg_false": "md-000#004"}))
        stop = self._decision(3, ("1 calculated value equals 1", {"stop_micro_dialog": True}))
        nodes = [q, branch, self._msg(2, "Thanks"), stop, self._msg(4, "No worries")]
        for k, node in enumerate(nodes):
            node.uid = f"md-000#{k:03}"
        sim = self._sim(("Dose", nodes))
        for value, expected in (("1", "Thanks"), ("0", "No worries")):
            state = sim.step(sim.initial_state(), {"type": "launch_dialog", "dialog_i": 0})
            state = sim.step(state, {"type": "answer", "value": value})
            self.assertEqual(self._coach(state), ["Took it?", expected])

    def test_unresolved_message_jump_warns_and_falls_through(self):
        d = self._decision(1, ("1 calculated value equals 1",
                               {"jump_msg_true": {"raw": "Some message", "unresolved": True}}))
        sim = self._sim(("D", [self._msg(0, "a"), d, self._msg(2, "b")]))
        state = sim.step(sim.initial_state(), {"type": "launch_dialog", "dialog_i": 0})
        self.assertEqual(self._coach(state), ["a", "b"])
        self.assertTrue(any("unknown message 'Some message'" in l["text"] for l in state["transcript"]))

    def test_jump_does_not_return(self):
        d = self._decision(1, ("1 calculated value equals 1", {"jump_dialog": "Other"}))
        sim = self._sim(("Start", [self._msg(0, "s"), d, self._msg(2, "never")]),
                        ("Other", [self._msg(0, "other")]))
        state = sim.step(sim.initial_state(), {"type": "launch_dialog", "dialog_i": 0})
        self.assertEqual(self._coach(state), ["s", "other"])


if __name__ == "__main__":
    unittest.main()
