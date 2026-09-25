---
from: smith
to: kart
subject: Smith: Phase E acceptance complete; stale-chat guard added per Raul's uid rule
timestamp: 260924110049
---
All Phase E acceptance walks now pass in the browser: medication Yes/No, and ACQ reminder → answer → questionnaire → correct score → next ACQ date scheduled. Per Raul's rule that md/node ids are per-export positions, saved chats are now checked against the attached export's fingerprint. A mismatched chat is refused, but reset still works. Replacing a bundle also clears the rgroups CSVs. Everything is still uncommitted, pending Raul. Details in STATUS.
