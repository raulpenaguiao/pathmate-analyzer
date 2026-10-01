# Warden — status

_Updated 2026-09-30 13:30._

## Now (2026-10-01 11:45)
- **Task 2 BEFORE export of alex-sandbox: done.**
  `data/exports/coaching_alex-v01-zum-ausprobieren_20261001-112433.json`. ok=True,
  90/90 targets, 18/18 senders, 13/14 jumps. Loom + Kart have it.
- **Browser order:** Mason's urgent capped ~30 min read-only slot on sandbox
  (rule-modal options, Raul) -> Loom's alex-sandbox apply -> my AFTER export.
- Fixed today: bar menus open by hover first (65697d8; headless lost 2 folders before).
  The mail listener is now `agents/waitmail.sh` (Raul 10-01).
- Herald's PathMate-email claims checked: claims 2 and 4 are done; the exact
  captions come from Mason's live look.

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
