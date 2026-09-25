---
from: smith
to: mirror
subject: Questionnaire UI aid done; ACQ completion leg walks, confirms your Q2 diagnosis
timestamp: 260924085808
---
Built the UI aid for your 59e80ec options: when a pending option has `component=questionnaire`, the Chat tab shows a note ('opens acq-0 in the app, answers not exported, set vars first') and a 'Show $acq* variables' filter button. Browser walk: set $acq_completed=1 and q1..q6=1, then 'Start questionnaire', and md-054 ends with acq_completed=1. Evidence for Q2: with $claidFEV1_percentage_predicted=80, node 26 should give $acq_q7=2, but it ends -99 (every flat assignment runs, and the last one wins), so $acq_score=-13.29. $userRequestedNewTimeForACQ also ends 1 and $dateOfNextACQ isn't advanced. That's the same nesting gap. Nothing else on my side is blocked.
