# autochanges

An audit trail for actions taken against the **live PMCP portal** (not this
repo) via Playwright — by Claude, driving a shared CDP-attached browser.
Distinct from git history: git tracks changes to this repo's files, this
folder tracks changes to (or exploration of) the external coaching system,
which git can't see.

One markdown file per session, named `YYYY-MM-DD-short-slug.md`. Write one
even for a read-only exploration session — "nothing was changed, here's what
was looked at" is still useful log content, and it's often hard to be
certain nothing changed (see the 2026-09-09 entry for why).

## What to put in an entry

- **Date, coaching, who was driving** (the user, Claude, or both — most
  sessions are both, with the user doing anything that writes live state).
- **What was navigated / looked at.**
- **Any write action**, even a suspected or accidental one — what triggered
  it, what the UI said (e.g. a toast message), whether it was confirmed
  harmless, and by whom.
- **Anything learned** that changes how future sessions should approach the
  portal (new gotchas belong here *and* in root `README.md`'s "Navigating
  the live PMCP portal" section — this file is the raw log, that section is
  the maintained summary).

## Why this matters

The live coaching editor has no per-field diff/undo visible to us, several
modals commit on "Close" rather than cancel (see root README's hurdles
section), and sessions expire in ~10 minutes — so it's easy to lose track of
what actually got written during an exploration session. This folder is the
record.
