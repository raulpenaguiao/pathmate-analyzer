---
from: raul
to: warden
subject: behavior change: auto-resume on wake, Kart owns git pull
timestamp: 260923132515
---
Two changes, now baked into wake_prompt.txt for future restarts, but applying now too since you're already running:

1. From now on, don't sit idle just because your inbox is empty. If your own STATUS.md/context already has a clear next step that isn't waiting on someone else's answer, resume it yourself - no need to wait for a go-ahead. (Still wait if you're genuinely blocked on a decision from someone else, same as before - that hasn't changed.)
2. Kart now owns keeping the shared repo checkout synced: git pull first thing on every wake, before anything else. Nobody else needs to pull themselves. (Kart: please run git pull now as a one-time catch-up, and flag the manager if it hits conflicts rather than forcing anything.)

Full wording in agents/RULES.md rule 4b and agents/wake_prompt.txt if you want the exact text.
