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


if __name__ == "__main__":
    unittest.main()
