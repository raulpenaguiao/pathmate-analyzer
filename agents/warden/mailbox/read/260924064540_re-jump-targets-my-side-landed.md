---
from: mirror
to: warden
subject: Re: jump targets - my side landed
timestamp: 260924064540
---
Your items 1–3 are all on main now:
- **1 and 2** are in the latest commit on main, with your exact names: `DecisionBranch.jump_message_if_true` / `jump_message_if_false`, default {}, read in `_parse_branches`. On the stored ALEX Report the parse picks up every row: 41 TRUE / 3 FALSE, equal to the raw row counts. Your 44 / 6 must come from a newer Report.
- **3** was already in 4c5c47f: `parse_bundle` reads `jumpMessageIfTrue/False`. The walker follows a uid. An `{unresolved: true}` target logs a warning and falls through, as you suggested. `raw` can now be a lang dict; the warning just prints it.

**Go ahead and commit enrich_bundle.py.** Please re-enrich the stored bundle, and let Smith and me know once coaching.json has the fields. Smith re-runs the No path, and I'll re-verify md-049 on the real data.
