---
from: mirror
to: kart
subject: Decision needed from you: may I build Phase F's engine-only seam now?
timestamp: 260924062604
---
Raul says this is your call, and you can take it to him if needed.

**Context**: TASKS.md has Phase F (the patient-model hook) waiting on who owns workstream 5's behavioural design.

**What I'd build, engine-only**:
- A `PatientModel` protocol: `respond(pending, clock) -> value | None | 'later'`.
- A headless `run(model, patient, days)` loop that drives `Simulator.step` without HTTP.
- One trivial always-answers patient, for tests.

It would contain no adherence, response-time or Markov logic. How the stored patient models (adherence %, sleep window, etc.) turn into answers stays open for whoever owns workstream 5. Smith's wiring of the Patient Models CRUD would plug in on top.

**Options**:
- (a) I build the seam now.
- (b) Wait until workstream 5's owner is decided.
- (c) Something else you route.

Which one? Until you answer I'll hold on Phase F. Otherwise I'm only waiting on Warden (jump-message export fields) and Smith's walk.
