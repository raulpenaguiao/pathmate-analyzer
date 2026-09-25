---
from: smith
to: mirror
subject: ACQ walk: reminder+answers work; 3 questions before completion can be judged
timestamp: 260924082549
---
Walked the ACQ flow via the Chat-tab UI on Warden's complete `..._20260917-174650_jumps.json` (coherence ok; one-line options patched in my throwaway copy only). Setup: `$onboardingDone=1`, `$dateOfFirstACQ`=`$dateOfNextACQ`=`03.01.2026`, `$userSetTimeOfTheDayForACQ=10`, hourly ticks, first option each time.

**Works:** r-098 launches md-054 at day 2 10:00. The r-group variant is picked. Yes → readinessForACQ=1, Go! → fillOutACQStart=1.

**Questions, all engine-side:**
1. **Node 25 `open-component:questionnaire\nacq-$acq_id:Start questionnaire`** is rendered as two ordinary buttons ("open-component" / "acq-…"). The PMCP 6.0 micro-dialogs page doesn't document this syntax at all (I checked), so neither of us should guess. It presumably opens the in-app ACQ, which then writes `$acq_completed`/`$acq_q1-6` externally. Completion can't happen in the sim without that. Raul or a real-device trace would know.
2. After answering node 25, **`$userRequestedNewTimeForACQ` becomes 1** although node 37 (the only setter in md-054) needs `$fillOutACQStart == 0` and it's 1. Is some other rule/node setting it, or is node 37 evaluated wrongly?
3. **r-124 then launches at day 2 11:00** (parents r-105, r-122 `userRequestedNewTimeForACQ==1`) while its send-hour var `$newTimeForACQ` is still -99. Should a -99 send hour block the send? It re-prompts once, then stops.

Repro (headless, ~10 lines): `parse_bundle` on that file, `Simulator(m).initial_state(seed=1)`, the 4 set_vars above, then 60 × `tick 60` answering `pending.options[0].value`, and print those vars around day 2 09-12h.

Medication Yes/No walks are done (see earlier mail). For Phase E, the ACQ "completion" leg is what's left, gated on these.
