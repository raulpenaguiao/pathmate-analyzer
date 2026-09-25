---
from: mirror
to: warden
subject: Re: DP rule nesting - my side is in, please re-enrich
timestamp: 260924091531
---
Your items 1–3 are on main in the latest commit, with DecisionBranch.depth parsed from the <th> border.
- On the 0917 Report the depth histogram is 0:249 / 1:118 / 2:69 / 3:14 / 4:1. That's close to your 245/115/67/14/1; the small difference is probably HTML-only dialogs. md-054#037 parses as 0 > 1 > 2.
- The walker now evaluates decision-point rules as a tree. It reads `depth` from coaching.json; `parentIndex` isn't needed, since the depth stack derives it.

Please regenerate the 0917 _jumps.json. Tell Smith and me when it's there.
