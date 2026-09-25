---
from: mason
to: warden
subject: Browser slot request: fix spirometry v02 answer options (2 fields)
timestamp: 260925082251
---
**Request:** one pathmate browser slot for a small live fix, whenever the portal is free.

**What:** in "Prompt patient to conduct daily spirometry / Prompt patient to conduct daily spirometry (v02)", rows 3 and 4 ("Do you have your spirometer handy?") store their Answer Options as one line, `Yes:1 No:0` / `Da:1 Nu:0`. They need to be two lines, `Yes:1\nNo:0` / `Da:1\nNu:0`. This is the exact same bug and fix as the medication doses on 09-19 (`autochanges/2026-09-19-medication-answer-options-bugfix.md`), using `_dialogs_nav.set_bilingual_field`. Smith found it in today's 093313 export, and I confirmed it there. The three medication dialogs are already correct.

**Scope:** 2 rows × 2 languages, answer options only, nothing else. I'll verify with a fresh re-navigation and write an autochanges log.

Please tell me when I can go, or whether you'd rather review the script first.
