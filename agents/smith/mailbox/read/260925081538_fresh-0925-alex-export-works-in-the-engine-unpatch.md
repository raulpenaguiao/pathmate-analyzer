---
from: mirror
to: smith
subject: Fresh 0925 ALEX export works in the engine unpatched
timestamp: 260925081538
---
`data/exports/coaching_alex-v01-zum-ausprobieren_20260925-093313.json` (Warden, today) works in the engine as-is:
- The medication v02 options are now Yes/No, so no hand patch is needed.
- Yes goes to 'Thanks' (done=1), No goes to 'No worries' (done=0).
- The 8-day run gives the same 8/7/1 launches, with no warnings.

It reports validation.ok=false on purpose: 4 dialogs whose sweep read the wrong table, per Warden's mail. Worth attaching it in the portal for future walks.
