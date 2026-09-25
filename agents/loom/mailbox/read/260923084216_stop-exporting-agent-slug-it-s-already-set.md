---
from: raul
to: loom
subject: stop exporting AGENT_SLUG - it's already set
timestamp: 260923084216
---
RULES.md had a mistake: it told you to `export AGENT_SLUG=<slug>` every session. That's stale - wake.sh already sets it at launch, it's inherited automatically, you never need to export it yourself. Please stop - each attempt isn't on the permission allow-list, so it was popping a confirmation prompt for Raul every time, repeatedly, across all of you. Fixed in RULES.md just now (Tools section) and a permission rule added as a backstop, but don't rely on the backstop - just don't export it. If `echo $AGENT_SLUG` is ever genuinely empty, that's a real bug, PushNotification the manager instead of self-fixing it with export.
