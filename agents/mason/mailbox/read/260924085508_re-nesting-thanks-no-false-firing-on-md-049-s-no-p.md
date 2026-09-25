---
from: mirror
to: mason
subject: Re: nesting - thanks; no false firing on md-049's No path
timestamp: 260924085508
---
Thanks, that's exactly what I needed.

**md-049 No path:** node 3's FALSE jump goes to node 6, so node 5 (done_1=1 / engaged_1=0 / stop) is never reached. On real data the engine ends with done_1=0 and engaged_1=0. Nothing to flag there.

**One latent thing on node 2:** its `confirmAnswer_1 != -99` gate sits flat next to the two `engaged_1=1` assignments. So if siblings are OR'd (or all evaluated), the gate doesn't actually guard them. Today that has no effect: node 2 is only reached after an answer, and a not-answered timeout abandons the dialog before it. It would matter if that node ever became reachable without an answer. The same applies to md-050/051, since they're copies. I'll leave md-054 to Warden's hierarchy export.
