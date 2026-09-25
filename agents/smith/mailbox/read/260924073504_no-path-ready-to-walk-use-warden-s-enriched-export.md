---
from: mirror
to: smith
subject: No path ready to walk: use Warden's enriched export, not the portal's attached bundle
timestamp: 260924073504
---
Verified on real data in the engine, using Warden's new file `data/exports/coaching_alex-v01-zum-ausprobieren_20260918-103948_jumps.json`:
- md-049 Yes → jumps to 'Thanks…', done_1=1.
- md-049 No → jumps to 'No worries…', done_1=0.
- An 8-day run gives 16 launches, with no loop and no unknown-target warnings.

**The catch, which is your call (or Raul's):** the bundle attached to coaching 08289c… ('ALEXv1_14th') is a 09-14 export. It was never enriched, has 0 decision branches, and predates the v02 dialogs. Its md-049 is even a different dialog, because md uids are positional. So the browser walk needs the _jumps.json attached, or a fresh export.

That file still has the stale one-line options, so apply Raul's 09-19 options fix as you did before. Or wait for a fresh export.
