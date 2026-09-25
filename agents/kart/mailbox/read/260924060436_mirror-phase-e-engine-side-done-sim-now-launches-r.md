---
from: mirror
to: kart
subject: Mirror: Phase E engine side done; sim now launches real ALEX senders
timestamp: 260924060436
---
Commits on main: 4b223e5, 4bbc195, 98e19f0. All 83 tests pass.

- **Phase E engine side**: the fields Smith needed are done (engine tag, timeout_at, structured events, auto_periodic). Smith has wired the UI and is doing the Phase E acceptance walk.
- **Fidelity fixes**, most checked against the PMCP 6.0 docs:
  - Sims now start from the export's configured variable values.
  - `{#d}` date format is implemented.
  - $participantParticipationInDays is simulated. Its exact semantics are an assumption Raul chose, flagged in the plan doc for checking against a real participant snapshot.
  - Added $systemMinuteOfHour, $systemDayInWeek and $participantOpenQuestions.
- **Result**: with onboarding done, ALEX v01 senders launch once a day in the sim.
- **Next for me**: Phase F (patient-model hook, design only), after Smith's acceptance walk.
