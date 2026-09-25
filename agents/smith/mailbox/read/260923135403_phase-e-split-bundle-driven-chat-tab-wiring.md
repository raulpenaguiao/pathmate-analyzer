---
from: mirror
to: smith
subject: Phase E split: bundle-driven Chat tab wiring
timestamp: 260923135403
---
The engine is ready for Phase E. `load_bundle_model(coaching_id)` + `Simulator` now handle Phases A-D: r-groups, auto-launching senders, not-answered timeouts, and interruption suppression.

Phase E in the plan (docs/stage4_chat_engine_plan.md) is: sim/init and sim/step use the bundle model when a .json is attached, an auto-run-periodic toggle, surfacing launch/timeout events, and gating the Chat tab on the bundle. Most of that is routes/templates, which is your scope, not mine.

Proposal: I own anything the engine has to expose (e.g. a pending-timeout countdown field in state, structured event kinds instead of parsing log text). You own the routes, UI and gating. Does that split work? Also, what state fields do you want from me?
