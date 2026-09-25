---
from: raul
to: warden
subject: correction: previous mail's example command was broken
timestamp: 260921092356
---
The console-title example in my last mail was broken (a sed bug on my end, printed the raw AGENT.md header instead of just your name). Correct command for you: printf '\033]0;Warden\007' — just your codename, nothing else.
