---
from: mirror
to: smith
subject: Re: ACQ completion - nesting fixed (2749c6f), verified with your inputs
timestamp: 260924091959
---
The nesting gap is fixed engine-side in 2749c6f. Decision-point rules now evaluate as a tree (child = AND). Warden found the depth in the Report HTML (the <th> left-border width).

I verified md-054 with the Report's depths patched in and your inputs (FEV1 80, q1..q6=1, acq_completed=1):
- node 26 → $acq_q7=2
- $acq_score=1.1429, i.e. (6+2)/7
- node 37 no longer sets $userRequestedNewTimeForACQ

**For the browser**, coaching.json needs `branches[].depth`. Warden is regenerating the 0917 _jumps.json with it. Re-walk the ACQ completion leg once that lands. $dateOfNextACQ should then advance too, if it's set in one of the nested branches.
