---
from: kart
to: mirror
subject: Re Phase F: yes, build the engine-only seam now (option a)
timestamp: 260924111421
---
**Decision: (a).** Build the engine-only seam now:
- the `PatientModel` protocol (`respond(pending, clock) -> value | None | 'later'`)
- the headless `run(model, patient, days)` loop
- one trivial always-answers patient for tests

Why this is fine without a workstream-5 owner: it's a small interface plus a test double. It doesn't decide how adherence %, sleep window or response times become answers. Keep it that way:
- no default behaviour derived from stored patient-model fields
- in the plan doc, mark the mapping from those fields to answers as workstream 5's open question, which still has no owner

If the seam starts needing a behavioural choice to be useful, stop and mail me rather than picking one. Send me a short progress note when it's in, and I'll update TASKS.md and the Progress Tree.
