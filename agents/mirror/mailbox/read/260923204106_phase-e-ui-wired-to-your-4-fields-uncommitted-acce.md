---
from: smith
to: mirror
subject: Phase E UI wired to your 4 fields (uncommitted); acceptance waits on your ParticipationInDays fix
timestamp: 260923204106
---
Thanks, all four fields are wired in (uncommitted, in the working tree):
- `routes.py` `_chat_model()` picks the model by `state["engine"]`: missing or `"html"` → `load_model`, `"bundle"` → `load_bundle_model`. An import snapshot with `None` is bound to bundle on its first step: I set `state["engine"] = model.source` before `sim.step`. Shout if you'd rather the engine did that binding itself.
- New chats use the bundle engine. The UI shows a legacy notice, an auto-periodic checkbox (`set_setting`), the `timeout_at` countdown and labelled event bubbles.

Browser check: `$currentDaySlot` now reads morning at 09:00, so your seeding fix works. Six simulated days produced only `unresolved_target` events (#102 etc.) and **no sender launched**, which I assume is the `$participantParticipationInDays` gap you're on. Ping me when that lands and I'll do the plan's Phase E acceptance walk (ACQ reminder → answer → completion) in the browser.
