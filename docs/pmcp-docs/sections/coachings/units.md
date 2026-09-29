# Units

Source: https://my.pathmate.app/pmcp-documentation/doc-6-0/sections/coachings/units · "Last updated: February 2026" · fetched 2026-09-29 · near-verbatim extract

"Units are a higher-level organisational concept that exists independently of Micro Dialogues." They are thematic modules (e.g. 🩸 bloodPressure) that are "created once and can then be assigned to multiple Micro Dialogues". Their main purpose is **controlled resets of user progress**.

- **Assigning:** every micro dialogue has an **Assigned Units** metadata field (multi-select), on parent or sub-dialogues. "Assigning a Unit does not change the dialog flow."
- **Variable Prefix:** set in the dialogue metadata, e.g. `bloodPressureGoal1_`. Then `$systolicValue` is stored as `$bloodPressureGoal1_systolicValue`. This prevents collisions and makes "Resetting a Unit can safely reset all related variables".
- **Local vs global variables:** local variables are created in a dialogue, usually prefixed and bound to a unit, and reset with it. Global variables "are not automatically reset when a Unit is reset".
- **Resetting:** a decision point setting, **"Assigned units to reset if TRUE"**, with a dropdown of units. When its condition is TRUE, "All local variables associated with selected Units clear or reset" and the affected dialogues "behave as if the user encounters them for the first time". Resets are "conditional and intentional, rather than automatic".
- **Reset values:** no default → empty; with a default → the default is restored.
- **History is kept:** "Historical values are not deleted; all previous values remain available for analytics and evaluation; resets only affect the active coaching state, not stored data history."
- **Use units when** a topic may be revisited or restarted, several dialogues form one module, or progress should reset without side effects. Skip them only for strictly linear, never-repeated content.

**Relevance (ours):**
- *Pile-up:* a unit reset is a documented way to wipe a dialogue family's state in one step (e.g. a daily or weekly expiry reset of `$X_started`/`$X_resumeMode`). This only works if those variables are prefixed locals. The docs don't say whether a unit reset touches open or deactivated *questions*, only variables.
- *Participant data:* resets keep the variable history, so counters can be reset without losing data.
