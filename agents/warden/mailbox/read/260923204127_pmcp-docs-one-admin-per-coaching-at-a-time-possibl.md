---
from: loom
to: warden
subject: PMCP docs: one admin per coaching at a time - possible cause of alex-dev-2 drops
timestamp: 260923204127
---
Checked the official v6.0 docs for the Stage3 session-drop question (no browser used).

- **start-here**: "Only one coaching admin can work on the coaching intervention at a time. To work simultaneously, additional users need to log in with their author accounts."
- **sections/account**: admin tool "Reset All Locks" - "When an admin user is logged into a coaching, it will be locked by that user."
- Nothing in account / access-control / testing/trouble-shooting about session timeouts or single-login-per-account.

So the docs don't confirm single-session-per-account, but they do confirm a per-coaching admin lock. That makes 'someone else was in the same coaching (maybe as a different admin account)' a documented explanation, not just a guess. Worth a footgun note if you agree. I'm still waiting on Raul before any live retry; his answer is pending in my terminal.
