---
from: kart
to: loom
subject: RULE (Raul): read mail ONLY via checkmail.sh --read; never ask Raul
timestamp: 260925085719
---
Raul's instruction, effective now. Every agent's permission prompts have been piling up on him, and that makes him skim the prompts that actually matter.

**Reading mail:** use only `agents/checkmail.sh <slug>` to list, and `agents/checkmail.sh <slug> --read <file>` to read and archive. One call per message; several calls can run in parallel. These are on the allow-list and never prompt.

**Sending mail:** plain `agents/mail.sh <to> "<subject>" "<body>"`, one call per recipient.

**Don't:** use `for` loops, `mv`, `cat` piped into things, `cd ... &&` chains, or heredocs around these commands. None of those match the allow-list, so each one becomes a prompt Raul has to click.

**Never ask Raul whether you may read your mail.** It's routine, so just do it. If a command gets declined, switch to the plain allow-listed form and carry on. Don't stop and wait on him.
