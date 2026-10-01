"""Which PMCP coaching an attached coaching.json came from (agents/RULES.md
"PMCP coachings"): exact-name lookup, and the backfill for bundles attached
before the summary carried the name."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from app import storage
from app.config import Config


class PmcpCoachingLookupTest(unittest.TestCase):
    def test_exact_names_only(self):
        self.assertEqual(storage.pmcp_coaching("ALEX v01 zum Ausprobieren 2")["short"], "alex-live")
        self.assertTrue(storage.pmcp_coaching("ALEX v01 zum Ausprobieren 2")["live"])
        self.assertEqual(storage.pmcp_coaching("ALEX v01 zum Ausprobieren")["short"], "alex-sandbox")
        self.assertFalse(storage.pmcp_coaching("ALEX v01 zum Ausprobieren")["live"])
        self.assertEqual(
            storage.pmcp_coaching("Minimal Coaching for Development 2 for Raul")["short"], "sandbox")

    def test_unknown_or_prefix_is_none(self):
        for name in (None, "", "ALEX v01", "ALEX v01 zum Ausprobieren 3", "alex v01 zum ausprobieren"):
            self.assertIsNone(storage.pmcp_coaching(name), name)


class BackfillTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self._saved = (Config.COACHINGS_DIR, Config.COACHING_FILES_DIR)
        Config.COACHINGS_DIR = self.tmp / "coachings"
        Config.COACHING_FILES_DIR = self.tmp / "files"
        Config.COACHINGS_DIR.mkdir()
        Config.COACHING_FILES_DIR.mkdir()

    def tearDown(self):
        Config.COACHINGS_DIR, Config.COACHING_FILES_DIR = self._saved
        shutil.rmtree(self.tmp)

    def test_old_summary_gets_name_from_stored_bundle(self):
        (Config.COACHING_FILES_DIR / "b.json").write_text(
            json.dumps({"coaching": {"name": "ALEX v01 zum Ausprobieren 2"}}))
        meta = {"id": "c1", "bundle": {"stored_filename": "b.json", "summary": {"nodes": 1}}}
        (Config.COACHINGS_DIR / "c1.json").write_text(json.dumps(meta))

        got = storage.get_coaching("c1")
        self.assertEqual(got["bundle"]["summary"]["pmcpCoaching"], "ALEX v01 zum Ausprobieren 2")
        persisted = json.loads((Config.COACHINGS_DIR / "c1.json").read_text())
        self.assertEqual(persisted["bundle"]["summary"]["pmcpCoaching"], "ALEX v01 zum Ausprobieren 2")

    def test_missing_bundle_file_leaves_meta_alone(self):
        meta = {"id": "c2", "bundle": {"stored_filename": "gone.json", "summary": {}}}
        (Config.COACHINGS_DIR / "c2.json").write_text(json.dumps(meta))
        self.assertNotIn("pmcpCoaching", storage.get_coaching("c2")["bundle"]["summary"])


if __name__ == "__main__":
    unittest.main()
