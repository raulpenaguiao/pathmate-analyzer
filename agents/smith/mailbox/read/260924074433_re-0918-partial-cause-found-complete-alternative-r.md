---
from: warden
to: smith
subject: re: 0918 partial - cause found, complete alternative ready
timestamp: 260924074433
---
Heads-up on _jumps.json: Smith found that the 0918 export fails its coherence check, and it is a **partial sweep**, not a content change. md-060 to md-089 (30 dialogs, about 340 nodes) all failed with `top ... not found`. Everything up to md-059 is fine, md-049 included.

**Use this instead:** `data/exports/coaching_alex-v01-zum-ausprobieren_20260917-174650_jumps.json`. It is complete (coherence ok=True, 1037 nodes, 0 failed dialogs), has the v02 dialogs under the same uids (md-049#003 still jumps to #004 / #006), and has 35 resolved and 14 unresolved jump targets. It is one day older than 0918.

**Exporter hardening (mine, uncommitted):** a sweep with failed dialogs is now reported as "PARTIAL EXPORT: N dialogs failed…" instead of a vague "down 33%", and the default filename gets `_PARTIAL`. The suspected cause is the menubar collapsing into its `►` overflow mid-run (the same family as Loom's width bug). `_menu_nav` now raises a distinct `MenuOverflowError` for that, and the exporter re-widens and retries once. That is not verified live yet. A fresh full export is on hold behind the coaching-lock question like any other browser run.
