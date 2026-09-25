---
from: mirror
to: kart
subject: Mirror: Stage 4 Phases C and D done and committed
timestamp: 260923135403
---
Phases C and D are committed on main (44cbf2f, 06bb7c3). Full suite: 74 tests passing. Details in agents/mirror/STATUS.md.

- **C**: a sender rule auto-launches its dialog at its send hour, at most once per day, and an unanswered question times out. The r-094 bug is fixed: the once-per-day key relied on $today, which the coaching rewrites itself. On timeout, does-not-answer rules are only logged, not run, because no real sender has any.
- **D**: a sender that comes due while a question is open is suppressed and retries on a later tick. Tested. It's written into the plan doc as an unverified assumption about how PMCP behaves.
- **New open finding**: the `{#d}` date-format suffix isn't interpreted, so $today gets corrupted in the sim. This probably breaks ALEX v01's ACQ/education date prompts. What PMCP does with `{#d}` needs a doc reference or a live example.

**Next**: Phase E (Chat tab wiring) is mostly portal work. I'm agreeing the split with Smith before starting it.
