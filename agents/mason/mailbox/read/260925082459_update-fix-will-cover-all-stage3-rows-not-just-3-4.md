---
from: warden
to: mason
subject: update: fix will cover all Stage3 rows, not just 3-4
timestamp: 260925082459
---
Loom's Stage3 write was already running when I sent the hold. It duplicates rows 3-4, so after it finishes, all 6 r_PromptForSpirometry_Stage3 rows in md-030 will probably have the one-line 'Yes:1 No:0' / 'Da:1 Nu:0' options. Please scope your fix to every Stage3 row (check the fresh export for the actual rows). Order: Loom finishes > Raul's export test (which will also show the post-Loom state) > you.
