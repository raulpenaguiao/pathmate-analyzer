# In flight: docs/pileup/ restructure (Raul approved 2026-09-25)

Pages: README, problem, priority, interruptions, reminder-pattern, rollout, and categories/ with 9 pages (health literacy sits inside education). Old spec + findings move to archive/, with a pointer stub left at each old path (code and autochanges reference those paths).

Design choices made while writing interruptions.md (flag these to Raul):
- Global `$openDialogName` + `$openDialogRank` markers; restart = the firing rule re-fires; the resume line lives at the dialog's opening decision point.
- The grace window still ends the *reminder nag*; end of day/week is only the restart cutoff. This is my default, Raul never answered it explicitly.
- A stale open marker after an unanswered timeout needs a reset path. It's unverified whether the "does not answer" rules or a time-based fallback can provide one.

Unverified, needs a Warden slot: the message-level "clears current dialog cascade" flag on an interrupter, and the does-not-answer rules.

Order after the docs: rollout plan (Phase 3/4.1 retrofit), then Phase 4.2 sleep-prep build.

## Side task (2026-09-25)
Spirometry v02 rows 3–4 have one-line answer options (Smith's find, confirmed in the 093313 export). Asked Warden for a slot; waiting. Fix = set_bilingual_field with `Yes:1\nNo:0` / `Da:1\nNu:0`, verify with a fresh re-nav, log in autochanges.

Progress: README, problem, priority, interruptions written. Next: reminder-pattern, rollout, categories/*, archive moves plus stubs.

Fix script ready (scratchpad fix_spiro_answer_options.py, dry run by default). Waiting on Warden to lift the HOLD.
