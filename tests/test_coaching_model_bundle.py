"""parse_bundle() - the coaching.json input path for the Stage 4 chat engine.
See docs/stage4_chat_engine_plan.md Phase A. Additive to (never replaces)
the HTML parse_model() path covered by test_coaching_model.py.
"""
import json
import unittest
from pathlib import Path

from app.coaching_model import parse_bundle
from app.coaching_sim import Simulator

SAMPLE = Path(__file__).resolve().parent / "fixtures" / "coaching_bundle_sample.json"


class ParseBundleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(SAMPLE.read_text())
        cls.model = parse_bundle(cls.data)

    def test_dialog_count_matches_bundle_including_folders_and_empties(self):
        # `isFolder` dialogs can still carry their own nodes, and dialogs
        # with no nodeCount/nodeUids at all (an empty placeholder) are still
        # browsable entries - neither is filtered out.
        self.assertEqual(len(self.model.micro_dialogs), len(self.data["microDialogs"]))

    def test_every_node_is_placed_no_node_dropped(self):
        placed = sum(len(d.nodes) for d in self.model.micro_dialogs)
        self.assertEqual(placed, len(self.data["nodes"]))

    def test_empty_dialog_has_no_nodes(self):
        empty = next(d for d in self.model.micro_dialogs if d.name == "Empty placeholder dialog")
        self.assertEqual(empty.nodes, [])

    def test_rule_count_matches_rule_tree(self):
        self.assertEqual(len(self.model.rules), len(self.data["rules"]["ruleTree"]))

    def test_sender_rule_joined_with_sending_rules_fields(self):
        sender = next(r for r in self.model.rules if r.kind == "sender")
        self.assertEqual(sender.uid, "r-002")
        self.assertTrue(sender.sends_message)
        self.assertEqual(sender.micro_dialog_path, ["Greeting"])
        self.assertEqual(sender.send_hour_variable, "$userSetTimeOfGreeting")
        self.assertEqual(sender.not_answered_timeout_minutes, 120)

    def test_raw_expr_is_comment_free_and_evaluable(self):
        onboarding = next(r for r in self.model.rules if r.uid == "r-000")
        self.assertEqual(onboarding.raw_expr, "$onboardingDone calculated value equals 1")
        self.assertEqual(onboarding.comment, "✅ Onboarding done check")
        self.assertNotIn(":", onboarding.raw_expr.split(" calculated", 1)[0])

    def test_assign_rule_raw_expr_reconstructed_with_target(self):
        assign = next(r for r in self.model.rules if r.uid == "r-001")
        self.assertIn("→ $today", assign.raw_expr)
        self.assertEqual(assign.writes_var, "$today")

    def test_unsupported_rule_flagged_and_not_evaluable(self):
        unsupported = next(r for r in self.model.rules if r.uid == "r-003")
        self.assertFalse(unsupported.supported)
        self.assertTrue(unsupported.is_js_snippet)

    def test_randomisation_group_and_uid_carried_on_node(self):
        greeting = self.model.micro_dialogs[0]
        self.assertEqual(greeting.nodes[0].randomisation_group, "r_greeting")
        self.assertEqual(greeting.nodes[0].uid, "md-000#000")

    def test_decision_branch_mapped_from_bundle_shape(self):
        decision_node = self.model.micro_dialogs[0].nodes[1]
        self.assertEqual(len(decision_node.branches), 1)
        branch = decision_node.branches[0]
        self.assertTrue(branch.leave_decision_point)
        self.assertEqual(branch.jump_dialog, "Subtree root with its own quit-check")

    def test_message_groups_are_empty_stage3_gap(self):
        self.assertEqual(self.model.message_groups, [])

    def test_simulator_runs_clean_on_bundle_model(self):
        sim = Simulator(self.model)
        state = sim.initial_state()
        state = sim.step(state, {"type": "tick", "minutes": 1440})
        self.assertFalse(any("Traceback" in l["text"] for l in state["transcript"]))


if __name__ == "__main__":
    unittest.main()
