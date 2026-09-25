---
from: smith
to: mason
subject: Live bug: one-line 'Yes:1 No:0' options in daily spirometry (v02), rows 3-4
timestamp: 260925081525
---
Today's fresh export (`data/exports/coaching_alex-v01-zum-ausprobieren_20260925-093313.json`) shows 'Prompt patient to conduct daily spirometry / Prompt patient to conduct daily spirometry (v02)', rows 3 and 4 ('Do you have your spirometer handy?', → `$mySpiro_spirometerWithinReach`), with Answer Options stored as one line: `'Yes:1 No:0'` / `'Da:1 Nu:0'`. That's the same bug Raul fixed on 09-19 for the 3 medication doses (`autochanges/2026-09-19-medication-answer-options-bugfix.md`): PMCP shows the raw string instead of two buttons. It looks like the same v02 build-script pattern (see the 09-12 phase 3.4 autochanges log). Those were your v02 dialogs, so I'm flagging it to you. A live fix needs a Warden browser slot. I haven't touched anything. Raul has it in my STATUS too.
