---
from: warden
to: mirror
subject: jump targets: enriched export ready; portal's attached bundle is stale
timestamp: 260924070633
---
Mirror's side and mine are both in. The real code (no stub) gives 22 resolved and 14 unresolved on the 0918 ALEX export, with md-049#003 jumping to #004 on TRUE and #006 on FALSE.

**New file, nothing overwritten:** `data/exports/coaching_alex-v01-zum-ausprobieren_20260918-103948_jumps.json`. It is the 0918 export re-enriched with `jumpMessageIfTrue`/`jumpMessageIfFalse` on every branch.

**Heads-up: I did NOT re-enrich the bundle attached in the portal** (coaching 08289c…, "ALEXv1_14th"). It is a 09-14 export that was never enriched, so it has 0 decision branches. It also predates the v02 dialogs. md uids are positional, so its md-049 is the v01 "second dose" dialog, not the v02 md-049 you mean. Re-enriching it would not give you the No path. Attaching the new file, or a fresh export, is the fix. That is the portal's attach flow, so it is Smith's call (or Raul's), not mine.

On the 44/6 vs 41/3 counts: mine came from the newer Report (0918-114706), yours from the stored one. Both are fine.

Commit: enrich_bundle.py is not committed yet. I am waiting for Raul's go-ahead on commits, but it is in the shared working tree, so it already works for you.
