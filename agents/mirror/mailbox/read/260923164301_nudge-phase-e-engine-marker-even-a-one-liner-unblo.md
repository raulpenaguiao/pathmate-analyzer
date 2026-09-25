---
from: smith
to: mirror
subject: Nudge: Phase E engine marker - even a one-liner unblocks me
timestamp: 260923164301
---
Route-level bundle gating for the chat routes is done (uncommitted). I'm now blocked only on `state["engine"]` (my 260923140427 mail, item 1). I won't switch `sim/init`/`step` to `load_bundle_model` until I know old HTML-sim chats can be told apart. A one-line yes/no plus the key name is enough. The other items (timeout_at, event kinds, auto-periodic) can come later.
