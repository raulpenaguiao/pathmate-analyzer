# 2026-09-11 — ALEX v02 redesign, Phase 2 (prune dead/pile-up-mechanism dialogs)

**Coaching:** "ALEX v01 zum Ausprobieren" (sandbox — not production, per the
user).
**Driving:** Claude, over the user's CDP session (browser restarted once
mid-session after being closed; user re-opened and confirmed before
resuming — see below).
**Goal:** Phase 2 of `TASKS.md`'s "ALEX v02 redesign" section — delete the
3 pile-up-mechanism dialogs and the 17 P4 dev/test dialogs named in
`docs/ALEX_v02_redesign_spec.md` §2.4/§5/Appendix A.

## What was done

Built `tools/coaching-bundle-export/prune_dialogs.py` (dry-run by default,
`--apply --limit N` to write, `--only NAME` for a single target, calls
`_pmcp_safety.assert_expected_coaching()` first). Ran it in two waves:

**Wave 1 (15 top-level targets, via the confirmed `Delete Dialog` button):**
both `Transition message...` dialogs, `Clearing microdialogs of the day
related to spirometry`, `Attic`, `⚙️ Controls`, `☑️ Testing`, `Testing of
gamification concept` (I & II), `Testing infocards`, `Testing Media
Objects`, `Testing questionnaires`, `Testing of streak concept`, `Testing
REDCap data`, `🐞 Testing sensor data retrieval`, `🐞 Testing time line of
scheduled periodic events`. One controlled single-target test first
(`🐞 Testing time line...`), verified gone via a fresh dry-run, then the
remaining 14 in one `--apply --limit 14` batch (ran long enough to move to
background — exit 0, all succeeded per the tool's own post-delete
re-check).

**Correction discovered mid-wave-1:** deleting a folder dialog does **not**
cascade-delete its children — it deletes the folder node and **promotes its
children to the level above**. `Attic` and `⚙️ Controls` were assumed to
carry their contents down with them; instead 6 children resurfaced as new
top-level items: `Morning greetings + inquire about sleep` (Attic's archived
duplicate of the live sleep-check dialog — see the earlier Romanian-review
session in this same conversation, which had already flagged this exact
folder as dev/archived), `System` (Attic's empty folder), `Test dialog for
debugging`, `Andreas Test`, `Test Andreas` (all Attic's), and — importantly
— **`📄 dataEdited`**, real P3 content (the `personal-data-edited` intent
handler, per spec Appendix A #87), nested under `Controls`. This was
**correctly left alone**, not deleted.

**Wave 2 (5 follow-up targets, the dead ones among those promoted
children):** `Test dialog for debugging`, `Andreas Test`, `Test Andreas`,
`System`, `Morning greetings + inquire about sleep`. All 5 confirmed
deleted (one, `Test Andreas`, needed a retry — its first delete attempt's
post-check reported "NOT FOUND" as if it had vanished on its own, but a
fresh top-level scan showed it was still present; re-running `--only "Test
Andreas" --apply --limit 1` deleted it for real). Final dry-run over both
target lists: all 20 originally-identified dead items confirmed gone,
`📄 dataEdited` confirmed still present.

**Net result:** coaching went from 107 to ~87 top-level-reachable micro
dialogs area (exact remaining dialog count not re-swept via the full
export — a fresh `export_coaching.sh` run would give the authoritative
number if needed later). 30 top-level menu items remain.

## Writes

19 real "Delete Dialog" actions (confirmed via each dialog's own
"Are you sure?" popup, clicked OK/affirmative every time — never Cancel).
No message/rule content was touched. `📄 dataEdited` was explicitly
preserved.

## Session hygiene notes

- **The CDP browser was closed and had to be reopened mid-session** (plain
  `curl` to `:9222` refused, no Chromium process for it in `ps aux` — this
  was a full close, not the ~10-minute idle/login timeout documented
  elsewhere). The user reopened it and confirmed before any further action;
  `_pmcp_safety.assert_expected_coaching()` re-verified the correct coaching
  was open before resuming writes.
- **The Micro Dialogs menubar's item list can under-report right after a
  wide resize** — a fixed ~1.2s wait after `Browser.setWindowBounds` isn't
  always enough for the Vaadin MenuBar's layout recompute to finish;
  `prune_dialogs.py`'s `top_level_items()` now polls (up to 6× at 500ms)
  until it sees at least 40 items rather than trusting one read. Without
  this, most targets falsely reported `NOT FOUND` on the very first
  dry-run of the session (cold-browser layout recompute was slower than
  usual, plausibly a one-off).
- **A delete's own post-check can also be a false negative once** — same
  class of transient timing issue as above, not a structural problem;
  confirmed by re-checking and retrying (`Test Andreas`). Treat one
  unexpected `NOT FOUND`/`ERROR` result as "verify with a fresh dry-run
  before concluding it actually failed," not as ground truth on the first
  read.
- **This session's Bash tool calls to `prune_dialogs.py` were repeatedly
  blocked by Claude Code's "auto mode classifier"**, including for
  dry-runs with no live writes at all. Retrying the identical command
  didn't help; it was resolved only by the user approving the specific
  tool-use prompt. Worth knowing for future sessions: a script whose name
  reads as bulk-deletion (this one, or the equivalent future
  `rule_apply.py`) may need the user's live approval per call, or a
  standing `autoMode.allow` / `permissions.allow` rule added to
  `.claude/settings.local.json` if this becomes frequent friction (offered
  this session; user preferred per-call approval for now).
