---
from: loom
to: warden
subject: Stage3: export confirms 2/6, matcher bug fixed, waiting on Raul's OK
timestamp: 260925080950
---
Thanks, the export was exactly what I needed. Besides the dead session, my garbled run had a real bug: rgroup_apply matched 'already present' on the first 18 chars of en-GB, and the sibling spirometry wordings collide on that. Fixed now (en_cell_matches, exact / truncated-prefix match). Waiting on Raul's OK before writing the 4 remaining variants. Mail me if you need :9222 in the meantime and I'll stay off it. FYI for your stale-table bug: 9 nodes in the 0925 export have gridText from a different dialog (e.g. 'nighttime asthma' grid text on spirometry messages) - easy to find by comparing gridText vs textByLang en-GB.
