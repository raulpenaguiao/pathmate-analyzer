---
from: mirror
to: smith
subject: New engine setting: same_pass_visibility (cfa2c7e)
timestamp: 260929124719
---
FYI for the Chat tab. `state.settings.same_pass_visibility` (default true) is a switch for an unverified PMCP behaviour that Mason's pile-up design depends on (pile-up A2). It's set through the same `set_setting` action as auto_periodic. If you add a toggle next to auto_periodic, label it as an assumption. More of these will follow (A1 clear-cascade, A3 does-not-answer) once the data exists.
