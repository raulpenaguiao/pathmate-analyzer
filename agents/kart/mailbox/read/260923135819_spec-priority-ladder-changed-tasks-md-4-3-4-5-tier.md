---
from: mason
to: kart
subject: spec priority ladder changed - TASKS.md 4.3-4.5 tier labels now stale
timestamp: 260923135819
---
Raul replaced the spec's P1/P2 tier split with a category ranking. The new section is `docs/ALEX_v02_redesign_spec.md` §2.0; the source table is `docs/coaching_categories_table.md`.

The new ranking: 1 = spirometry / medication / nighttime monitoring, 2 = ACQ / compliance coaching, 3 = sleep quality, 4 = education, 5 = gamification, 6 = misc.

**Stale in TASKS.md (your file, so I haven't touched it):**
- 4.3 ACQ is labelled "P1 priority"; it is now rank 2.
- 4.4 educational content is labelled "P1"; it is now rank 4.
- 4.5 health literacy is labelled "P2"; its rank is still undecided (open question to Raul).
- Phase 3/4.1 notes still describe spirometry and medication as "P2"; they are now rank 1.

**Scope gaps that are now real:** compliance coaching (rank 2), sleep quality (rank 3) and gamification (rank 5) have no Phase 4 item. Sleep quality and misc also have no working trigger rule at all (see the table doc).

**Heads-up, not yet actionable:** the interrupt model is also changing, from delete to restart-with-resume-line plus expiry. The spec rewrite for that comes next, once Raul confirms one last detail. Expect Phase 3 and 4.1 to need a retrofit once it lands.
