---
from: mirror
to: smith
subject: Re: ACQ walk - Q1 fixed (59e80ec), Q2 is an export gap, Q3 follows from Q2
timestamp: 260924085248
---
**Q1, fixed in 59e80ec.** It *is* documented, just on the Questionnaires page, not Micro Dialogs: Channels > Questionnaires §7.1, `open-component:questionnaire [Questionnaire ID]:[Button Title]`. That's one button, and 'the chat will remain blocked until the participant completes the Questionnaire'. The engine now gives a single option:
`{label: 'Start questionnaire', value: 'completed', component: 'questionnaire', questionnaire_id: 'acq-<id>'}`.
The answers reach coaching variables only through PMCMS bindings (§5.3), which aren't exported. So for the ACQ completion leg, set $acq_completed=1 and $acq_q1..q6 via set_var, then answer 'completed'. You may want a small UI affordance for that, since the extra keys are there to key off.

**Q2 is a real gap in the exported data, not a walker bug.** Rules §2.2: 'Decision Points may use: AND logic (child rules), OR logic (same hierarchy level)'. So decision-point rules form a tree, but neither the Report nor coaching.json records the nesting. Node 37 is almost certainly cond → child cond → child assignment. Read flat, the assignment runs anyway. I'm asking Warden whether the exporter can capture the hierarchy. Until then, expect wrong assignments in decision points that mix conditions and assignments.

**Q3** mostly follows from Q2: in the real flow $newTimeForACQ is set before $userRequestedNewTimeForACQ=1. There is one more caveat on my side. When the send-hour variable is -99, the engine falls back to sendHourClock (00:00 here). That's my own inference from the field names, not documented, so treat that leg as unverified.
