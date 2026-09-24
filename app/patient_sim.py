"""Headless patient-driven runs of the chat engine (Stage 4 Phase F).

This is the seam workstream 5 plugs into. The engine (`coaching_sim.Simulator`)
advances the clock and opens questions, and a `PatientModel` decides how a
simulated patient responds to each one. No HTTP is involved:
`Simulator.step` is already a plain function of (state, action).

Deliberately behaviour-free. How a stored patient model's fields (adherence %,
response time, sleep window, ...) turn into answers is workstream 5's open
design question (docs/stage4_chat_engine_plan.md, Phase F). Nothing here
derives behaviour from them. `AlwaysAnswers` is a test double, not a model.
"""
from __future__ import annotations

from typing import Protocol

from app.coaching_model import CoachingModel
from app.coaching_sim import Simulator

class _Later:
    def __repr__(self) -> str:
        return "LATER"


# respond() sentinel: not now, ask again after the next tick. It's an object,
# not the string "later" the plan sketched, because a real answer option can
# have the value "later" (e.g. a remind-me-later button).
LATER = _Later()


class PatientModel(Protocol):
    def respond(self, pending: dict, clock: dict) -> str | _Later | None:
        """React to the open question `pending` (as in `state["pending"]`:
        `options`, `timeout_at`, ...) at `clock`. Return one of:

        - an answer value (normally one of `pending["options"][k]["value"]`)
          to answer now;
        - `LATER` to leave it open and be asked again after the next tick;
        - `None` to never answer this question. It stays open until the
          engine times it out, or the run ends.
        """
        ...


class AlwaysAnswers:
    """Test double: answers every question immediately with its first option."""

    def respond(self, pending: dict, clock: dict) -> str | None:
        options = pending.get("options") or []
        return options[0]["value"] if options else ""


def _pending_key(pending: dict) -> tuple:
    return (pending.get("dialog_i"), pending.get("node_idx"), pending.get("sent_at"))


def run(
    model: CoachingModel,
    patient: PatientModel,
    days: int,
    *,
    tick_minutes: int = 60,
    seed: int | None = None,
    set_vars: dict[str, str] | None = None,
    state: dict | None = None,
) -> dict:
    """Advance a simulation `days` days in steps of `tick_minutes`, letting
    `patient` respond to every question the engine opens. Returns the final
    state (its `transcript` is the run's record).

    `tick_minutes` is simulation resolution, not patient behaviour. A sender
    can't fire, and a patient can't be asked, between ticks. `set_vars`
    seeds variables before the first tick (e.g. `$onboardingDone`). Pass
    `state` to continue an existing run instead of starting a fresh one.
    """
    sim = Simulator(model)
    if state is None:
        state = sim.initial_state(seed=seed)
    for name, value in (set_vars or {}).items():
        state = sim.step(state, {"type": "set_var", "name": name, "value": value})

    declined: set[tuple] = set()  # questions the patient chose never to answer
    ticks = max(0, days * 1440 // max(1, tick_minutes))
    for _ in range(ticks):
        state = sim.step(state, {"type": "tick", "minutes": tick_minutes})
        # answering can open the next question straight away, so keep asking
        # until the patient defers, declines, or nothing is open
        while state.get("pending") and _pending_key(state["pending"]) not in declined:
            value = patient.respond(state["pending"], dict(state["clock"]))
            if value is None:
                declined.add(_pending_key(state["pending"]))
                break
            if value is LATER:
                break
            state = sim.step(state, {"type": "answer", "value": value})
    return state
