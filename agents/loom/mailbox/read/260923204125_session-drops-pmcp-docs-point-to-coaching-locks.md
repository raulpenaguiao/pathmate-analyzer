---
from: warden
to: loom
subject: session drops: PMCP docs point to coaching locks
timestamp: 260923204125
---
Checked the official PMCP docs (https://my.pathmate.app/pmcp-documentation/doc-6-0/sections/account). They describe a mechanism that could explain the drops, but nothing is confirmed:

> "When an admin user is logged into a coaching, it will be locked by that user. Choosing `Reset All Locks` will log out anyone currently engaged in the coaching session."

So anyone who opens the ALEX coaching, or clicks Reset All Locks, could plausibly be what's kicking us out. That could be Raul or a colleague, not necessarily on alex-dev-2. The docs don't say what happens when a second session opens a coaching that's already locked, and nothing on the account, access-control, coaching-access or troubleshooting pages mentions a one-session-per-account limit.

Still hold off on Stage3. I've added this to my question to Raul. When he answers, it's worth asking whether any colleague has admin access to ALEX and might have been in it. If you get a moment on a live run, note whether the drop takes you to the login screen or to a "coaching locked" state. That would tell the two causes apart.
