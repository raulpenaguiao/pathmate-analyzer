---
from: raul
to: mirror
subject: console title + context hygiene
timestamp: 260921092334
---
RULES.md just got two new protocol rules (10 and 11) — go read the current file, don't rely on this summary:

1. Rename your console tab to your codename now: `printf '\033]0;<Codename>\007'` (e.g. for you: `printf '\033]0;# Mirror (mirror)\007'`). Future wakes via wake.sh do this automatically — this is a one-time catch-up since you're already running.
2. You may be cut off with as little as ~10 minutes' notice. Keep agents/mirror/context/ and STATUS.md continuously current as you work, not as a last-minute dump — and keep context/ itself pruned, not a growing pile.
