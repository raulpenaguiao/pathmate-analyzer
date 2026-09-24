"""Stage 4 Phase F: the headless patient-driven run loop (app/patient_sim.py)."""
import unittest

from app.coaching_model import CoachingModel, MicroDialog, Node, Rule
from app.patient_sim import LATER, AlwaysAnswers, run


def _model(timeout=None):
    q1 = Node(n=0, type="message", comment="", channel="", writes_var="$mood",
              text_by_lang={"en-GB": "How was your day?"},
              answer_options_by_lang={"en-GB": "good:1\nlater:later"})
    q2 = Node(n=1, type="message", comment="", channel="", writes_var="$sleep",
              text_by_lang={"en-GB": "Tired?"}, answer_options_by_lang={"en-GB": "yes:1\nno:0"})
    dialog = MicroDialog(i=0, name="Evening check", comment="", nodes=[q1, q2], uid="md-000")
    sender = Rule(
        i=0, context="DAILY BASIS", depth=0, raw_expr="$enabled calculated value equals 1",
        comment="", writes_var=None, sends_message=True, stops_intervention=False,
        is_js_snippet=False, supported=True, uid="r-000", kind="sender",
        micro_dialog_path=["Evening check"], send_hour_clock="20:00",
        not_answered_timeout_minutes=timeout,
    )
    return CoachingModel(rules=[sender], micro_dialogs=[dialog], message_groups=[],
                         variables={}, languages=["en-GB"])


class Scripted:
    """Returns queued responses in order, recording every call."""
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def respond(self, pending, clock):
        self.calls.append((pending["options"][0]["label"], dict(clock)))
        return self.responses.pop(0) if self.responses else None


class PatientRunTest(unittest.TestCase):
    def _answers(self, state):
        return [l["text"] for l in state["transcript"] if l["kind"] == "user"]

    def test_always_answers_runs_whole_dialog_every_day(self):
        state = run(_model(), AlwaysAnswers(), days=3, seed=1, set_vars={"$enabled": "1"})
        self.assertIsNone(state["pending"])
        self.assertEqual((state["vars"]["$mood"], state["vars"]["$sleep"]), ("1", "1"))
        launches = [l for l in state["transcript"] if l.get("event", {}).get("type") == "launch"]
        # day 0 08:00 -> day 3 08:00: 20:00 on days 1 and 2 (day 0 has no midnight run)
        self.assertEqual(len(launches), 2)

    def test_later_defers_to_next_tick(self):
        patient = Scripted(LATER, "1", "0")
        state = run(_model(), patient, days=2, seed=1, set_vars={"$enabled": "1"})
        (_, first), (_, second) = patient.calls[:2]
        self.assertEqual(second["hour"] - first["hour"], 1)  # asked again one tick later
        self.assertEqual((state["vars"]["$mood"], state["vars"]["$sleep"]), ("1", "0"))

    def test_literal_later_option_is_an_answer_not_a_deferral(self):
        patient = Scripted("later", "1")
        state = run(_model(), patient, days=2, seed=1, set_vars={"$enabled": "1"})
        self.assertEqual(state["vars"]["$mood"], "later")
        self.assertEqual(len(patient.calls[:2]), 2)

    def test_none_is_never_asked_again_and_times_out(self):
        patient = Scripted(None)
        state = run(_model(timeout=120), patient, days=2, seed=1, set_vars={"$enabled": "1"})
        self.assertEqual(len([c for c in patient.calls if c[1]["day"] == 1]), 1)
        self.assertTrue(any("not answered (timeout)" in l["text"] for l in state["transcript"]))


if __name__ == "__main__":
    unittest.main()
