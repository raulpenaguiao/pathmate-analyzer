"""Parse the bundled ALEX v01 export and sanity-check the structured model."""
import unittest
from pathlib import Path

from app.coaching_model import parse_model
from app.coaching_stats import compute_stats

SAMPLE = Path(__file__).resolve().parent.parent / "Coaching_ALEX_v01_zum_Ausprobieren.html"


class CoachingModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bytes = SAMPLE.read_bytes()
        cls.model = parse_model(cls.bytes)
        cls.stats = compute_stats(cls.bytes)

    def test_rule_count_matches_stats_minus_context_markers(self):
        # compute_stats counts the 4 "Execution on ... BASIS" marker rows as
        # rules; the model drops them and records their context instead.
        self.assertEqual(len(self.model.rules), self.stats["rules"]["total"] - 4)

    def test_rule_contexts_are_known(self):
        known = {
            "DAILY BASIS",
            "PERIODIC BASIS",
            "UNEXPECTED MESSAGE",
            "USER INTENTION",
        }
        for ctx, _rules in self.model.rules_by_context():
            self.assertIn(ctx, known)

    def test_micro_dialog_and_node_counts_match_stats(self):
        self.assertEqual(
            len(self.model.micro_dialogs),
            self.stats["micro_dialogs"]["dialogs_total"],
        )
        nodes = sum(len(d.nodes) for d in self.model.micro_dialogs)
        self.assertEqual(nodes, self.stats["micro_dialogs"]["items_total"])

    def test_message_group_count_matches_stats(self):
        self.assertEqual(
            len(self.model.message_groups),
            self.stats["message_groups"]["groups_total"],
        )

    def test_nodes_are_flat_no_nesting_exposed(self):
        for dialog in self.model.micro_dialogs:
            for node in dialog.nodes:
                self.assertFalse(hasattr(node, "children"))
                self.assertFalse(hasattr(node, "parent"))
                self.assertFalse(hasattr(node, "depth"))

    def test_anchors_are_unique(self):
        anchors = [r.anchor for r in self.model.rules]
        anchors += [d.anchor for d in self.model.micro_dialogs]
        anchors += [
            n.anchor(d.i) for d in self.model.micro_dialogs for n in d.nodes
        ]
        anchors += [g.anchor for g in self.model.message_groups]
        self.assertEqual(len(anchors), len(set(anchors)))

    def test_variable_index_covers_most_referenced_variables(self):
        # The model indexes variables referenced in rules / dialog nodes /
        # message groups. That is very close to the doc-wide token count.
        self.assertGreater(len(self.model.variables), 300)
        today = self.model.variables.get("$today")
        self.assertIsNotNone(today)
        self.assertTrue(today["writes"])
        self.assertTrue(today["reads"])
        for ref in today["writes"] + today["reads"]:
            self.assertIn(ref.kind, {"rule", "dialog", "msg_group"})
            self.assertTrue(ref.anchor)

    def test_dialog_cross_links_resolve_to_real_dialogs(self):
        names = {d.name for d in self.model.micro_dialogs}
        found_link = False
        for dialog in self.model.micro_dialogs:
            for node in dialog.nodes:
                for branch in node.branches:
                    for target in (branch.jump_dialog, branch.cascade_dialog):
                        if target:
                            found_link = True
                            self.assertIn(target, names)
        self.assertTrue(found_link, "expected at least one dialog-to-dialog link")

    def test_js_snippet_rules_are_marked_unsupported(self):
        js = [r for r in self.model.rules if r.is_js_snippet]
        self.assertTrue(js)
        for rule in js:
            self.assertFalse(rule.supported)


if __name__ == "__main__":
    unittest.main()
