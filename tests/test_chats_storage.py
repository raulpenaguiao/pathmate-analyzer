"""Exercises the persisted multi-chat storage layer (app.storage's chats
API): creating/listing/renaming/deleting chats, importing a .pmcp as a new
chat, and the legacy single-participant_import migration path."""
import io
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from app import storage
from app.config import Config

PARTICIPANT_ID = "bbbbbbbbbbbbbbbbbbbbbbbb"


def _envelope(clazz: str, content: dict) -> bytes:
    return json.dumps({
        "clazz": clazz,
        "packageAndClazz": f"com.pathmate.pmcp.model.persistent.{clazz}",
        "objectId": content.get("_id", ""),
        "content": json.dumps(content),
        "fileReference": None,
        "objectIdSetMethodsWithAppropriateValues": {},
    }).encode("utf-8")


def _make_pmcp() -> bytes:
    participant = _envelope("Participant", {
        "_id": PARTICIPANT_ID, "systemUniqueId": "sys1", "nickname": "Robin",
        "intervention": "int-1", "language": "en_GB",
        "createdTimestamp": 1000, "lastLoginTimestamp": 2000, "lastLogoutTimestamp": 2500,
    })
    dialog_status = _envelope("DialogStatus", {
        "_id": "d1", "participant": PARTICIPANT_ID,
        "monitoringDaysParticipated": 1, "screeningSurveyPerformed": True,
        "hasOpenMessagesToBeSent": False, "microDialogCascade": {},
        "safeCascades": ["1500-abc"],
    })
    var = _envelope("ParticipantVariableWithValue", {
        "_id": "v1", "name": "$participantIntention", "value": "go",
        "participant": PARTICIPANT_ID, "timestamp": 1800,
        "formerVariableValues": [{"timestamp": 1200, "value": "coach"}],
    })
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("M Participant " + PARTICIPANT_ID, participant)
        zf.writestr("M DialogStatus d1", dialog_status)
        zf.writestr("M ParticipantVariableWithValue v1", var)
    return buf.getvalue()


class ChatsStorageTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._orig_coachings_dir = Config.COACHINGS_DIR
        self._orig_files_dir = Config.COACHING_FILES_DIR
        Config.COACHINGS_DIR = Path(self._tmp) / "coachings"
        Config.COACHING_FILES_DIR = Config.COACHINGS_DIR / "files"
        Config.ensure_dirs()
        self.coaching = storage.save_coaching(
            name="Test coaching", tag="", filename="test.html", file_bytes=b"<html></html>")
        self.cid = self.coaching["id"]

    def tearDown(self):
        Config.COACHINGS_DIR = self._orig_coachings_dir
        Config.COACHING_FILES_DIR = self._orig_files_dir
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_create_and_list_chat(self):
        chat = storage.create_chat(self.cid, name="Chat 1", kind="live", state={"clock": {}, "vars": {}})
        chats = storage.list_chats(self.cid)
        self.assertEqual(len(chats), 1)
        self.assertEqual(chats[0]["id"], chat["id"])
        self.assertEqual(chats[0]["kind"], "live")

    def test_get_chat_returns_state(self):
        chat = storage.create_chat(self.cid, name="Chat 1", kind="live", state={"clock": {"day": 0}, "vars": {"$x": "1"}})
        fetched = storage.get_chat(self.cid, chat["id"])
        self.assertEqual(fetched["state"]["vars"]["$x"], "1")

    def test_update_chat_state_persists_and_bumps_updated_at(self):
        chat = storage.create_chat(self.cid, name="Chat 1", kind="live", state={"clock": {}, "vars": {}})
        ok = storage.update_chat_state(self.cid, chat["id"], {"clock": {"day": 1}, "vars": {"$y": "2"}})
        self.assertTrue(ok)
        fetched = storage.get_chat(self.cid, chat["id"])
        self.assertEqual(fetched["state"]["vars"]["$y"], "2")

    def test_list_chats_sorted_by_most_recently_updated(self):
        first = storage.create_chat(self.cid, name="First", kind="live", state={})
        second = storage.create_chat(self.cid, name="Second", kind="live", state={})
        storage.update_chat_state(self.cid, first["id"], {"touched": True})
        ids_in_order = [c["id"] for c in storage.list_chats(self.cid)]
        self.assertEqual(ids_in_order[0], first["id"])
        self.assertEqual(ids_in_order[1], second["id"])

    def test_rename_chat(self):
        chat = storage.create_chat(self.cid, name="Old name", kind="live", state={})
        self.assertTrue(storage.rename_chat(self.cid, chat["id"], "New name"))
        self.assertEqual(storage.get_chat(self.cid, chat["id"])["name"], "New name")

    def test_delete_chat_removes_summary_and_state_file(self):
        chat = storage.create_chat(self.cid, name="Chat 1", kind="live", state={})
        self.assertTrue(storage.delete_chat(self.cid, chat["id"]))
        self.assertIsNone(storage.get_chat(self.cid, chat["id"]))
        self.assertEqual(storage.list_chats(self.cid), [])

    def test_delete_nonexistent_chat_returns_false(self):
        self.assertFalse(storage.delete_chat(self.cid, "does-not-exist"))

    def test_create_imported_chat_from_pmcp(self):
        chat = storage.create_imported_chat(self.cid, "export.pmcp", _make_pmcp())
        self.assertEqual(chat["kind"], "imported")
        self.assertIn("Robin", chat["name"])
        self.assertEqual(chat["state"]["vars"]["$participantIntention"], "go")
        self.assertTrue(any(t["kind"] == "import" for t in chat["state"]["transcript"]))

    def test_multiple_imports_coexist_as_separate_chats(self):
        storage.create_imported_chat(self.cid, "a.pmcp", _make_pmcp())
        storage.create_imported_chat(self.cid, "b.pmcp", _make_pmcp())
        chats = storage.list_chats(self.cid)
        self.assertEqual(len(chats), 2)
        self.assertTrue(all(c["kind"] == "imported" for c in chats))

    def test_reseed_imported_chat_rebuilds_from_original_pmcp(self):
        chat = storage.create_imported_chat(self.cid, "export.pmcp", _make_pmcp())
        storage.update_chat_state(self.cid, chat["id"], {"clock": {}, "vars": {}, "transcript": []})
        reseeded = storage.reseed_imported_chat(self.cid, chat["id"])
        self.assertEqual(reseeded["vars"]["$participantIntention"], "go")

    def test_reseed_returns_none_for_live_chat_with_no_pmcp_on_disk(self):
        chat = storage.create_chat(self.cid, name="Live", kind="live", state={})
        self.assertIsNone(storage.reseed_imported_chat(self.cid, chat["id"]))

    def test_legacy_participant_import_migrates_into_a_chat(self):
        # Simulate a coaching saved before the chats redesign: a single
        # participant_import attachment written directly into meta, the old
        # way (mirrors what storage.save_participant_import used to do).
        from app.participant_import import parse_pmcp
        data = parse_pmcp(_make_pmcp())
        raw_stored = f"{self.cid}.participant_import.pmcp"
        data_stored = f"{self.cid}.participant_import.json"
        (Config.COACHING_FILES_DIR / raw_stored).write_bytes(_make_pmcp())
        with open(Config.COACHING_FILES_DIR / data_stored, "w") as f:
            json.dump(data, f)
        meta = storage.get_coaching(self.cid)
        meta["participant_import"] = {
            "raw_stored_filename": raw_stored, "data_stored_filename": data_stored,
            "uploaded_at": "2026-01-01T00:00:00+00:00",
            "summary": {"nickname": "Robin", "variables": 1, "timelineEvents": 1, "cascadesCompleted": 1},
        }
        storage._write_json(Config.COACHINGS_DIR / f"{self.cid}.json", meta)

        chats = storage.list_chats(self.cid)
        self.assertEqual(len(chats), 1)
        self.assertEqual(chats[0]["kind"], "imported")
        self.assertIn("Robin", chats[0]["name"])
        # the legacy attachment is gone from meta, replaced by the chat
        self.assertIsNone(storage.get_coaching(self.cid).get("participant_import"))
        # re-listing doesn't duplicate the migrated chat
        self.assertEqual(len(storage.list_chats(self.cid)), 1)

    def test_delete_coaching_removes_chats_dir(self):
        storage.create_chat(self.cid, name="Chat 1", kind="live", state={})
        chats_dir = Config.COACHING_FILES_DIR / f"{self.cid}.chats"
        self.assertTrue(chats_dir.exists())
        storage.delete_coaching(self.cid)
        self.assertFalse(chats_dir.exists())


if __name__ == "__main__":
    unittest.main()
