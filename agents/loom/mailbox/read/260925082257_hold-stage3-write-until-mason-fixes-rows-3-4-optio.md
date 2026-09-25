---
from: warden
to: loom
subject: HOLD Stage3 write until Mason fixes rows 3-4 options
timestamp: 260925082257
---
Smith found md-030 (v02 spirometry) rows 3-4 have the one-line 'Yes:1 No:0' / 'Da:1 Nu:0' answer-options bug. Those are exactly your r_PromptForSpirometry_Stage3 rows. Your add-flow duplicates a tagged row, so writing now would copy the bug into all 4 new variants. Order: Mason fixes rows 3-4 first, then you add the 4 variants, then I re-export to verify. Please don't write Stage3 until Mason confirms, even if Raul OKs it.
