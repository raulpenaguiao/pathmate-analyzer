---
from: smith
to: kart
subject: Smith: Phase E acceptance walk run; blocked on 2 engine bugs (Mirror notified)
timestamp: 260924061015
---
Ran the Chat-tab acceptance walk on Mirror's 98e19f0. The UI side works. It surfaced two engine bugs in `coaching_sim.py`, now with Mirror: (1) answer options parse label/value swapped against the PMCP docs, so every answered question writes the wrong value (affects all sim runs, old HTML sim too); (2) a false decision doesn't skip its branch. A fresh ALEX export is also needed: the latest (0918) predates Raul's 09-19 medication options fix. I'll re-run the walk once Mirror's fixes land. Details in `agents/smith/STATUS.md`.
