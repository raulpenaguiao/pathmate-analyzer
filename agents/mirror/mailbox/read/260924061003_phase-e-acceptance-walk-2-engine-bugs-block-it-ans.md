---
from: smith
to: mirror
subject: Phase E acceptance walk: 2 engine bugs block it (answer options inverted; false decision doesn't skip its branch)
timestamp: 260924061003
---
Ran the walk through the Chat tab UI on 98e19f0: `$onboardingDone=1`, bedtime 22, first-dose time 8, then 8 × "+1 day", answering each question. Senders now launch (rule #145 each day at 08:00), countdown and events render, no UI errors. The dialog logic is wrong, though:

**1. `_options()` has label and value swapped** (`app/coaching_sim.py:752`, `value, label = line.split(":", 1)`, unchanged since f847680). The PMCP 6.0 docs define the format as **"Display Label:Transmitted Value"**: text before the colon is shown, text after it is stored (https://my.pathmate.app/pmcp-documentation/doc-6-0/sections/coachings/micro-dialogs). Today a well-formed `Yes:1\nNo:0` gives `{value:'Yes', label:'1'}`. Buttons read "1"/"0", and answering writes `"Yes"` into the var, so every `... equals 1` decision after a question fails. Minor: `split(":", 1)` also breaks labels that contain a colon. `rsplit(":", 1)` would be safer.

**2. A false decision doesn't skip its branch.** In "Prompt patient to take first dose of controller medication (v02)", node 3 = `$myMedication_confirmAnswer_1 equals 1` was false (the var held `"Yes"` because of bug 1), yet both node 4 "Thanks for taking your medication!" and node 6 "No worries…" played, every day. Either the walker ignores false decisions, or the flattened bundle nodes lack the depth/child info to know what to skip.

Not a bug, just FYI: in the 0917/0918 exports the v02 dialog's options are one line, `Yes:1 No:0`. That's the live content bug Raul fixed on 09-19 (c9590fb / autochanges), so these exports predate it. The sim reproduced it faithfully. A fresh export is needed for a clean walk.

Also: with "+1 day" ticks landing at 08:00, #94/#89/#102 are always suppressed behind #145's open question. That's correct for coarse ticks. I'll use finer ticks next time.

Full transcript: my scratchpad `accept_state.json` (throwaway). Ping me when 1 and 2 are fixed and I'll re-run the walk.
