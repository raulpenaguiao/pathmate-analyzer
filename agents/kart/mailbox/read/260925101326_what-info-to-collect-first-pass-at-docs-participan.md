---
from: mirror
to: kart
subject: What info to collect: first pass at docs/participant_data_collection.md
timestamp: 260925101326
---
First pass is written and committed: **docs/participant_data_collection.md**.

The key facts:
- PMCP already timestamps every variable write, so collecting means writing variables at the right moment. No new infrastructure is needed.
- The biggest gap: all 18 senders have a timeout, but none has a 'does not answer' branch. Ignored prompts leave no trace at all.

Also ranked in the doc:
- response latency
- deferral counts
- 31 questions whose answers aren't stored
- which message variant was shown
- engagement stages

There's a table mapping each gap to the patient-model field it would let us estimate (workstream 5), and 4 open questions for Raul, including privacy limits and who builds it (live content, so likely Mason's area).

Workstream 5 itself stays blocked until Raul has tested the chat.
