---
from: kart
to: loom
subject: Task 2 is GO: apply Raul's CSV to alex-SANDBOX, resilient to missing groups
timestamp: 261001083857
---
Kart here. Raul made the CSV himself: /home/raul/projects/rgroups_generated_260930163339.csv (804 variant rows, one level ABOVE the repo). Copy it into data/rgroups/ under the same name and pin it with --csv. TARGET: alex-sandbox ('ALEX v01 zum Ausprobieren') ONLY, never alex-live. RESILIENCE (Raul's requirement): some r_ groups/pools in this CSV may not exist in alex-sandbox. For each one, apply must print a clear error (group, dialog, why) and MOVE ON, not abort. Add that before the live run and test it offline, then do a dry-run that lists the missing groups up front and mail me the count. Order: Warden takes a fresh BEFORE export of alex-sandbox, then hands you the lock, then your apply, then Warden's AFTER export, then your diff + the new comparison artifact for Raul (per pool: added / skipped-missing / skipped-duplicate; anything that changed but shouldn't have). No API use anywhere in this.
