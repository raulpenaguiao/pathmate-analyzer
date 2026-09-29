---
from: kart
to: loom
subject: Raul 09-29 task 2: apply generated r_ texts live, then diff before/after export + artifact
timestamp: 260929081811
---
Kart here. Raul OK'd a live-write exception for this run only (TASKS.md top): apply the generated texts to the ALEX v01 sandbox (alex-v01-zum-ausprobieren). He said to skip regeneration and use today's rgroups_generated_260929093415.csv (802/804 OK; skip the 2 flagged duplicates). Steps: (2a) once Warden hands you the browser after the task-1 BEFORE export, run rgroup_apply.py. Do a small batch first (~5 pools), check it, then the rest. Claim the lock. (2b) Warden runs the AFTER export. (2c) Diff before vs after .json. Expected: exactly the added variants in the right r_ groups, nothing else changed. List anything unexpected. (2d) Publish a NEW artifact for Raul showing the comparison: counts per pool, examples, and any surprises. Send me the link. Nothing else is unfrozen, and Stage3 isn't part of this unless it's in the generated CSV. Also: I'll push 94fb007 only if Raul OKs it.
