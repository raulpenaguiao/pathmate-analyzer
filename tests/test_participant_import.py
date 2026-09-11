"""Exercises the .pmcp participant-export parser and its hand-off into the
simulator's seeded initial state."""
import io
import json
import unittest
import zipfile

from app.coaching_sim import Simulator
from app.participant_import import ParticipantImportError, parse_pmcp

PARTICIPANT_ID = "aaaaaaaaaaaaaaaaaaaaaaaa"


def _envelope(clazz: str, content: dict) -> bytes:
    return json.dumps({
        "clazz": clazz,
        "packageAndClazz": f"com.pathmate.pmcp.model.persistent.{clazz}",
        "objectId": content.get("_id", ""),
        "content": json.dumps(content),
        "fileReference": None,
        "objectIdSetMethodsWithAppropriateValues": {},
    }).encode("utf-8")


def _make_pmcp(members: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, raw in members.items():
            zf.writestr(name, raw)
    return buf.getvalue()


def _sample_members():
    participant = _envelope("Participant", {
        "_id": PARTICIPANT_ID, "systemUniqueId": "abc123", "nickname": "Sam",
        "intervention": "int-1", "language": "en_GB",
        "createdTimestamp": 1000, "lastLoginTimestamp": 2000, "lastLogoutTimestamp": 2500,
    })
    dialog_status = _envelope("DialogStatus", {
        "_id": "d1", "participant": PARTICIPANT_ID,
        "monitoringDaysParticipated": 2, "screeningSurveyPerformed": True,
        "hasOpenMessagesToBeSent": False, "microDialogCascade": {},
        "safeCascades": ["1500-abc123", "not-a-timestamp-xyz"],
    })
    device = _envelope("DialogOption", {
        "_id": "opt1", "participant": PARTICIPANT_ID, "type": "EXTERNAL_ID",
        "secret": "super-secret-should-never-surface",
        "pushNotificationTokens": ["token-should-never-surface"],
    })
    changing_var = _envelope("ParticipantVariableWithValue", {
        "_id": "v1", "name": "$participantIntention", "value": "go",
        "participant": PARTICIPANT_ID, "timestamp": 1800,
        "formerVariableValues": [{"timestamp": 1200, "value": "coach"}],
    })
    constant_var = _envelope("ParticipantVariableWithValue", {
        "_id": "v2", "name": "$spirometerData", "value": "[]",
        "participant": PARTICIPANT_ID, "timestamp": 1900,
        "formerVariableValues": [
            {"timestamp": 1100, "value": "[]"},
            {"timestamp": 1600, "value": "[]"},
        ],
    })
    noisy_var = _envelope("ParticipantVariableWithValue", {
        "_id": "v3", "name": "$timeDecimal", "value": "9.5",
        "participant": PARTICIPANT_ID, "timestamp": 1950,
        "formerVariableValues": [{"timestamp": 1300, "value": "8.5"}],
    })
    return {
        "M Participant " + PARTICIPANT_ID: participant,
        "M DialogStatus d1": dialog_status,
        "M DialogOption opt1": device,
        "M ParticipantVariableWithValue v1": changing_var,
        "M ParticipantVariableWithValue v2": constant_var,
        "M ParticipantVariableWithValue v3": noisy_var,
    }


class ParsePmcpTest(unittest.TestCase):
    def test_parses_participant_and_variables(self):
        data = parse_pmcp(_make_pmcp(_sample_members()))
        self.assertEqual(data["participant"]["id"], PARTICIPANT_ID)
        self.assertEqual(data["participant"]["nickname"], "Sam")
        self.assertEqual(data["variables"]["$participantIntention"], "go")
        self.assertEqual(data["variables"]["$spirometerData"], "[]")

    def test_constant_valued_variable_excluded_from_timeline(self):
        data = parse_pmcp(_make_pmcp(_sample_members()))
        names = {e["name"] for e in data["timeline"] if e["kind"] == "var_change"}
        self.assertIn("$participantIntention", names)
        self.assertNotIn("$spirometerData", names, "a value that never changes is noise, not an event")

    def test_noisy_system_variable_excluded_even_though_it_changes(self):
        data = parse_pmcp(_make_pmcp(_sample_members()))
        names = {e["name"] for e in data["timeline"] if e["kind"] == "var_change"}
        self.assertNotIn("$timeDecimal", names)
        self.assertEqual(data["variables"]["$timeDecimal"], "9.5", "still kept in the snapshot")

    def test_cascade_completion_parsed_from_safe_cascades(self):
        data = parse_pmcp(_make_pmcp(_sample_members()))
        cascades = [e for e in data["timeline"] if e["kind"] == "cascade_complete"]
        self.assertEqual(len(cascades), 1, "the malformed id without a numeric prefix is dropped")
        self.assertEqual(cascades[0]["timestamp"], 1500)

    def test_timeline_sorted_chronologically(self):
        data = parse_pmcp(_make_pmcp(_sample_members()))
        timestamps = [e["timestamp"] for e in data["timeline"]]
        self.assertEqual(timestamps, sorted(timestamps))

    def test_dialog_option_secrets_never_surface(self):
        data = parse_pmcp(_make_pmcp(_sample_members()))
        blob = json.dumps(data)
        self.assertNotIn("super-secret-should-never-surface", blob)
        self.assertNotIn("token-should-never-surface", blob)
        self.assertEqual(data["device_bindings_count"], 1)

    def test_no_message_text_warning_always_present(self):
        data = parse_pmcp(_make_pmcp(_sample_members()))
        self.assertTrue(any("message text is not recoverable" in w for w in data["warnings"]))

    def test_bad_zip_raises(self):
        with self.assertRaises(ParticipantImportError):
            parse_pmcp(b"not a zip file")

    def test_missing_participant_raises(self):
        members = _sample_members()
        del members["M Participant " + PARTICIPANT_ID]
        with self.assertRaises(ParticipantImportError):
            parse_pmcp(_make_pmcp(members))

    def test_multiple_participants_raises(self):
        members = _sample_members()
        members["M Participant other-id"] = _envelope("Participant", {"_id": "other-id"})
        with self.assertRaises(ParticipantImportError):
            parse_pmcp(_make_pmcp(members))


class InitialStateFromImportTest(unittest.TestCase):
    def test_seeds_vars_and_replays_timeline_as_transcript(self):
        data = parse_pmcp(_make_pmcp(_sample_members()))
        sim = Simulator(model=None, lang="en-GB")
        state = sim.initial_state_from_import(data)

        self.assertEqual(state["clock"], {"day": 0, "hour": 8, "minute": 0})
        self.assertEqual(state["vars"]["$participantIntention"], "go")
        self.assertIsNone(state["open_dialog"])
        self.assertIsNone(state["pending"])

        import_lines = [t for t in state["transcript"] if t["kind"] == "import"]
        self.assertTrue(any("$participantIntention" in t["text"] for t in import_lines))
        self.assertTrue(any("cascade completed" in t["text"] for t in import_lines))

    def test_sim_clock_not_polluted_by_real_calendar_dates(self):
        # the import's $today ("14.09.2026"-style) must not leak past the
        # simulator's own day-0 refresh, or every later tick would compute
        # dates against the wrong calendar.
        data = parse_pmcp(_make_pmcp(_sample_members()))
        sim = Simulator(model=None, lang="en-GB")
        state = sim.initial_state_from_import(data)
        self.assertEqual(state["vars"]["$systemYear"], "2026")
        self.assertEqual(state["vars"]["$systemMonth"], "1")


if __name__ == "__main__":
    unittest.main()
