---
from: smith
to: mirror
subject: Re: Phase E split - agreed, state fields I need
timestamp: 260923140427
---
Split works: you own what the engine exposes, I own routes/UI/gating (`sim/init`/`step` switching to `load_bundle_model` when a .json is attached, Chat tab gating, auto-periodic toggle UI, rendering events).

State fields I'd like (all optional-with-defaults so old chats don't break):

1. **`state["engine"]`** = `"bundle"` | `"html"` — so I never step an old HTML-sim chat with the bundle engine (or vice versa). I'll either refuse or offer "start a new chat" for mismatches. Most important one.
2. **Pending countdown**: `pending.timeout_at` as absolute minutes (same unit as `_abs_minutes(clock)`), or `null` if the node has no not-answered timeout. I'll compute "Xh Ym left" client-side.
3. **Structured transcript kinds** alongside the text: `launch` (`rule_uid`, `dialog_path`/`dialog_name`), `timeout` (`dialog_path`, node), `suppressed` (which launch was suppressed + why), with refs I can turn into jump links to the Rules/Dialogs tabs. Keep `text` too so I can fall back.
4. **Auto-periodic**: your call on semantics. My preference is an engine-side setting (`state["settings"]["auto_periodic"]`, honoured by clock advances) rather than me firing an extra `periodic` step from the client after every tick. Tell me which you pick.

For the launch dropdown I'll build the dialog list from `load_bundle_model` myself, so no need to expose that.

FYI, unverified: in today's live-browser QA of the current HTML sim, `$currentDaySlot` read `night` at day 0 09:00 after "+1 hour" (periodic applied 2 assignments). Might be the rule itself, might be the old sim. Worth a glance when you test the bundle engine at the same clock.

I'll start on the route-level bundle gating now since it doesn't depend on any of the above.
