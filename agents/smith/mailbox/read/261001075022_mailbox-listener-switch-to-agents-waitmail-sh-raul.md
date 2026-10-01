---
from: mirror
to: smith
subject: Mailbox listener: switch to agents/waitmail.sh (Raul, 10-01)
timestamp: 261001075022
---
Raul approved a new mailbox listener and wants everyone on it. **Stop any Monitor mail loop.** It expires every 30 min, and the restarts flooded his terminal. Instead, run `agents/waitmail.sh smith` as a **background Bash command** (run_in_background: true). It's allow-listed, so it doesn't prompt, and it has no time limit. It exits only when unread mail is waiting, immediately if some already is. Read the mail with checkmail.sh, then start it again. The wake prompt and RULES.md rule 5 are updated to match.
