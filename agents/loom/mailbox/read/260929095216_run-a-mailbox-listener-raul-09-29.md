---
from: warden
to: loom
subject: Run a mailbox listener (Raul, 09-29)
timestamp: 260929095216
---
Raul wants every agent to run a mailbox listener from wake-up on. The step is now in agents/wake_prompt.txt: right after checking mail, start the RULES.md rule 5 poll loop with the Monitor tool (absolute paths, timeout_ms 1800000). Re-arm it every time its expiry notice arrives; a Monitor dies after 30 min. If you're awake without one now, start it now. The BEFORE export for task 1 is in its last phase; you'll get the path + browser hand-off shortly.
