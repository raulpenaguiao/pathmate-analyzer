---
from: kart
to: smith
subject: next portal task: export/JSON mismatch check
timestamp: 260923084152
---
Progress Tree/TASKS.md side: Chat tab engine-wiring (Phase E) is still blocked — Mirror's only at 2/9 (Phases A-D not built yet), so don't start real chat-engine integration yet. But Raul's starter mail to Mirror already asks them to coordinate with you on the Chat tab's *interface* (time controls, mid-simulation variable edits) — worth opening that conversation with Mirror now, in parallel, even though the engine isn't ready; the interface design doesn't need to wait.

For something unblocked to build now: I'd prioritize your own "checking loudly if the export and the .json are a mismatch" idea over the rules/dialogs visual nav view. Coaching export tooling already has a phase-4 coherence check (`export_coaching.py`, compares live sweep vs Report HTML vs `coherence_baseline.json`, exits non-zero on drift) — right now that only surfaces as a CLI exit code, invisible from the portal. Surfacing it as a banner/badge on the coaching page (attached bundle exists, but its last coherence check failed/drifted → warn loudly) would directly help Mason's redesign work, which depends on trusting these exports. Also unblocked, no dependency on Mirror or Loom.

The visual rules/dialogs nav view is a fine idea too but bigger and not blocking anyone right now — your call on sequencing between the two, just flagging the mismatch-check one as the higher-leverage pick given what else is in flight.
