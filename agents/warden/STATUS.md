# Warden — status

_Updated 2026-10-01 14:25._

## Now (2026-10-02 11:40)
- **Exporter test PASSED:** `data/exports/coaching_alex-v01-zum-ausprobieren_20261002-111732.json`
  (alex-sandbox). ok=True, 0 dialog errors, 14/14 jumps, 21/21 senders. New per-sender
  fields (actionBoxes, answerTabs, disabledFields, microDialogToStartRaw), and the 15 loose
  rules are included. Sent to Kart, Mirror (coverage) and Mason (meanings).
- Fixed on the way: top-level menu clicks after a dropdown (045481e; it cost Welcome+Hello).
- Lesson: run login + open + export as ONE command. Separate steps let the session time
  out (the 10-02 morning failures; NOT Loom, apologised).
- Next: the per-message settings (coverage-map §6 items 1-5) as an opt-in phase; it
  needs every message editor opened (Close = a no-op re-save).

## Coachings (RULES.md, Raul 09-29)
alex-live = "ALEX v01 zum Ausprobieren 2" (never changed; a full export needs a
human's `--allow-noop-resaves`); alex-sandbox = "ALEX v01 zum Ausprobieren"
(pile-up target); sandbox = "Minimal Coaching for Development 2 for Raul".

## Latest exports
- alex-live: `coaching_alex-v01-zum-ausprobieren-2_20260929-162548.json` (ok; 4/26
  jump targets ambiguous). Loom has it.
- alex-sandbox: `coaching_alex-v01-zum-ausprobieren_20260929-111706.json` (the BEFORE
  snapshot for task 2).

## Next
1. Raul's rerun of the test, then hand the browser to Loom (task 2 apply on alex-sandbox).
2. Phase 3b: resolve "no jump set", command-message targets, and paged dropdowns.
3. Queued live-read fields: Smith's `$weekdays` (full multilingual values) and Mirror's
   `clearsCascade` (batched).
4. multiSubmit (read-only).

## Notes
- The `.env` PMCP login works again (confirmed 2026-09-30). The 09-29 rejection was temporary.
- Runs pause when the screen sleeps (they beep and wait for Enter) and are wrapped in
  systemd-inhibit.
