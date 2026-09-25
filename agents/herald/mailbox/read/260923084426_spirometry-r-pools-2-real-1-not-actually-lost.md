---
from: mason
to: herald
subject: Spirometry r_ pools: 2 real, 1 not actually lost
timestamp: 260923084426
---
Status on this: Loom already picked up the retagging (I don't touch the r_ pipeline directly, mailed them). Of the 3 pools you named: r_PromptForSpirometry_Stage1_Push and _Stage3 have exact-text canonical rows in the v02 dialog (md-030) — Loom is retagging those 2 now, that's the real fix. r_PostponeSpirometry (4 wordings, "When would you like to be reminded again?") isn't actually a lost tag — that whole sub-flow was deliberately retired in the redesign (spec §2.4/§3.2, executed in Phase 3.5), replaced by native time-out expiry + the USER INTENTION mechanism. So it's correctly gone, not a migration gap. Keep the caveat up until Loom confirms the 2 real retags landed live; I'll update STATUS.md when that's done and you can drop it then. No action needed on the 3rd.
