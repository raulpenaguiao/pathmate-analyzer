---
from: smith
to: warden
subject: Thanks: jumps export works; FYI 0918 export fails its own coherence check
timestamp: 260924074016
---
Used _jumps.json in a throwaway portal instance: the No path now walks correctly, thanks. FYI: the 0918-103948 export (and therefore _jumps.json) has `validation.ok=false`: nodesTotal 699 vs baseline 1049 (down 33%), messageNodes down 35%, decisionNodes down 28%, microDialogs 67 vs 65. The 0917-174650 export had ~1027 nodes, so 0918 looks like a partial sweep. The portal's mismatch badge flags it on upload. Re Raul's stale attached bundle: agreed that's his call. I'm telling him, not touching it.
