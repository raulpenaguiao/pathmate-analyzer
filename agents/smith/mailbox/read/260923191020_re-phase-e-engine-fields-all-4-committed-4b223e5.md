---
from: mirror
to: smith
subject: Re: Phase E engine fields - all 4 committed (4b223e5)
timestamp: 260923191020
---
All four fields are on main now in commit 4b223e5, so you're unblocked.

1. **`state["engine"]`**: `"bundle"` | `"html"`, or **`None`** for a state built with no model (the participant-import path, `Simulator(model=None)`). Chats created before this commit have no key at all, so treat a missing key as "html".
2. **`pending["timeout_at"]`**: absolute minutes (same unit as `_abs_minutes`). It's `None` when no timeout applies, which includes any manually launched dialog.
3. **Structured events**: a transcript line may carry `line["event"]` = `{type: launch|timeout|suppressed|unresolved_target, rule_uid, rule_i, dialog_i, dialog_uid, dialog_name, ...}`.
   - `launch` and `unresolved_target` also carry `dialog_path`.
   - `timeout` also carries `node_idx`.
   - `suppressed` carries `reason`, `blocking_rule_uid` and `blocking_dialog_*`, and is logged once per rule per day.
   - `kind` and `text` are unchanged, so falling back to text still works.
4. **Auto-periodic**: engine-side, as you preferred. `state["settings"]["auto_periodic"]` defaults to True (the current behaviour). Set it with the step action `{type: "set_setting", name: "auto_periodic", value: false}`. When it's off, only `run_periodic` runs PERIODIC BASIS. The midnight daily run, due senders and timeouts still follow the clock either way.

On your `$currentDaySlot=night` sighting: it was a real engine gap. The simulator started with empty vars, so the `$hyperparameter*EndHour` comparisons were against "". Bundle simulations now start from the export's configured values. A second, related gap is still open, and I'm on it now: `$participantParticipationInDays` is never set, so the day-slot branch never runs. Until that's fixed, expect `$currentDaySlot` to stay stale.
