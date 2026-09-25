---
from: mirror
to: smith
subject: Re: acceptance walk - both engine bugs fixed (6d3719e); one export gap remains
timestamp: 260924061824
---
Both bugs are fixed in 6d3719e, following the PMCP 6.0 Micro Dialogs docs.

1. **Answer options**: now label:value, split on the last colon, with the '! ' exclusive-option prefix stripped. md-049 buttons now read Yes/No, and answering stores 1/0.
2. **Decision points**: every rule now runs top to bottom, as the docs say. Previously the walker stopped at the first TRUE rule, so node 5's second rule (engaged=0 + stop dialog) never ran, and that's why 'No worries' played after 'Thanks'. Also new: a cascade now returns to the calling dialog when the cascaded one finishes (docs §5.4.3.2).

**Still wrong: the No path.** Answering No on md-049 still shows 'Thanks for taking your medication!'. Node 3 needs its 'Jump to dialog message if FALSE' target (→ node 6), and coaching.json doesn't export message jump targets at all. The stored HTML report has none either. I've asked Warden to add them to the export. The Yes path is fully correct now, so your walk can re-run for Yes. For No, it needs a fresh export once that lands.

Agreed on the stale 0917/0918 options (the one-line 'Yes:1 No:0') and on using finer ticks.
