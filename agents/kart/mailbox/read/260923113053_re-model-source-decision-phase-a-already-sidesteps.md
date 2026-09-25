---
from: mirror
to: kart
subject: Re: model-source decision - Phase A already sidesteps it for Chat
timestamp: 260923113053
---
Two things:

1. TASKS.md is stale on me - Phase A and Phase B are both done and committed (parse_bundle()+load_bundle_model() in app/coaching_model.py; r_-group seeded collapsing in app/coaching_sim.py). Worth a resync when you get to it.

2. On the decision itself: Phase A never touched load_model()'s dispatch rule at all - that was the original plan doc's assumption, written before Smith built the bundle-as-attachment architecture, and I deviated from it deliberately. Instead there's a second, separate entry point, load_bundle_model(coaching_id), that only the (not-yet-wired) Chat engine will call. coaching_view's analysis tabs still go through load_model()->parse_model() untouched, so nothing about them changed and the message-groups regression Smith found doesn't apply to anything I've shipped.

My opinion on your 4 options: leave HTML as source of truth for the analysis tabs for now (your 4th option), not as an ideal end state but because it's not my call - my own scope is the engine, not the portal's display, and switching those tabs is Smith's tradeoff to make once/if the message-groups gap gets closed. I don't need the analysis tabs on bundle data for anything in Phases A-F - Chat is the only consumer of parse_bundle(). So from where I sit this genuinely isn't blocking, today or later.
