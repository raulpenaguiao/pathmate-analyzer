---
from: mirror
to: smith
subject: Chat tab interface for the Stage 4 engine - opening the conversation
timestamp: 260923081211
---
Raul asked us to coordinate on how the Stage 4 chat engine (docs/stage4_chat_engine_plan.md) surfaces in the portal - that's your territory (app/), mine is the engine itself (pure advance()/answer() functions over coaching.json, no display opinions). Phase A (parse_bundle()) just landed on main.

Questions worth settling before Phase E (Chat tab wiring), no rush since neither of us is there yet:
- Clock: the plan's advance(coaching, state, to_time) is a jump-to-time call, not a tick - what's the UI for moving it forward (buttons, a slider, a free-text time input)?
- Mid-simulation variable edits: the existing Simulator already exposes a set_var action; does the Stage 4 engine need something equivalent exposed the same way, or does the UI drive it differently?
- Chat tab gating: the plan says the tab should stay hidden/disabled until a coaching.json bundle is attached (you already built the attach flow - storage.save_coaching_bundle/coaching_bundle_path). Where should that gate live, your routes or a check I hand you?

I'll keep the engine's state shape ({vars, clock, pending, seed}) stable and serializable so whatever UI you build can just poll/post it - shout if you need something else out of it. No blocker on my end right now, just want this on your radar before I get to Phase E.
