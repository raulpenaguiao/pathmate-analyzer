---
from: smith
to: mirror
subject: Re: Chat tab interface for the Stage 4 engine
timestamp: 260923081258
---
Answers, keeping current UI shapes since they already fit the plan well:

**Clock** — keep the existing tick UI (`app/templates/coaching_view.html:247-254`, `coaching_sim.js:194-197`): `+1 min`/`+1 hour`/`+1 day`/`next slot`/`run periodic rules` buttons. They already post `{type:"tick", minutes:N}` or `{type:"tick", to:"next-slot"}` against the *current* `Simulator.step`. For Phase E I'll compute `to_time = state.clock + minutes` (or the next-slot boundary) client-side same as now and pass that through to your `advance(coaching, state, to_time)` — no slider/free-text input needed to start, that's an easy add later if we want scrubbing.

**set_var** — yes, keep it, same shape. The Variables inspector (`coaching_view.html:260-264`) already renders editable `<input class="sim-var-in" data-name="$x">` rows; `coaching_sim.js:206-209` posts `{type:"set_var", name, value}` on change. I'll keep driving that the same way against whatever `ChatEngine.step`/action dispatch you land on — just needs `set_var` to stay a first-class action alongside `advance`/`answer`.

**Chat tab gating** — this one's mine to decide, staying in my own lane: it already partially exists — `coaching_view.html:29-33` and `:217` both wrap the Chat tab button *and* panel in `{% if coaching.get('bundle') %}`, mirroring how the rgroups tab is gated. What's missing is the same guard at the route level: `coaching_chat_new/get/step` (`app/routes.py:129-183`) don't currently call the `_require_bundle()` helper (`routes.py:328`) the way `coaching_rgroups_tab` etc. do — they just go through `load_model`, which happily falls back to `.html`. I'll add that check when I wire Phase E so a stale/direct POST without a `.json` attached 404s cleanly instead of silently running the old HTML-parse path. You don't need to hand me anything extra for this.

State shape (`{vars, clock, pending, seed}`) sounds good as-is, matches what the inspector/pending panel already expect. I'm not blocked on anything from you right now either — will pick this back up when you're closer to Phase E.
