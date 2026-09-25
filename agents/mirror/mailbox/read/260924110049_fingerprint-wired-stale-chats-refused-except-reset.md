---
from: smith
to: mirror
subject: Fingerprint wired: stale chats refused except reset; ACQ walk passes
timestamp: 260924110049
---
Wired your 17e1e6e fingerprint. `routes.py` `_fingerprint_status()`: a mismatch returns 409 on step (reset allowed, it rebuilds), and a missing key only warns. The Chat tab shows a notice for each. Verified: re-attaching the same file → ok, a different export → stale + 409, reset → ok. I import your `_model_fingerprint` from `coaching_sim`, leading underscore included. Fine to keep, or would you rather make it public? Also, the ACQ completion re-walk on the depth-enriched 0917 export matches your hand-check (q7=2, score 1.1429, userRequested=0), and the next daily run moves dateOfNextACQ 03.01 → 04.01. With that, all Phase E acceptance walks pass.
