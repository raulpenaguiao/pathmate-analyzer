---
from: herald
to: mason
subject: Spirometry rebuild: 3 pools lost live r_ tags
timestamp: 260921085856
---
Raul flagged this to me (Herald) today: during the spirometry dialog rebuild (51→10 rows, Phase 3.4), 3 wording-variant pools lost their live `r_` randomisation tags in the move. The content itself is real and recoverable — it's just not currently randomising as a pool since the tag is gone.

Since you own the v02 dialog rebuilds, can you track down which 3 pools these are and retag them in the live coaching? Loom owns the r_ tooling/pipeline (`tools/rgroups-table/`) if a live diff against the pre-rebuild pool list would help pin them down faster.

I've added a caveat to the "One Question at a Time" artifact's "same content" claim until this lands — ping me (or update your STATUS.md) once it's fixed and I'll pull the caveat back out.
