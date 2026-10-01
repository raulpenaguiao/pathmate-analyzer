# Warden — status

_Updated 2026-10-01 14:25._

## Now (2026-10-01 17:55)
- **Running: the richer-exporter test** = a full alex-sandbox export with all of today's
  exporter changes (list: tools/coaching-bundle-export/EXPORT_CHANGES_2026-10-01.md).
  Path + results to Kart, Mirror and Mason when it's done (~25 min). alex-sandbox now also
  holds 57 r_ variants from Loom's partial apply.
- Done today: the annotated editor screenshots (docs/pmcp-ui/screens/, red boxes =
  Mason's Unknown list), the 50 rule operators, the 25 answer types, 15 loose rules
  found + kept in exports, 2 scraper bugs fixed (store variable, greyed tabs), a review
  of Loom's apply (toolbar fine; a selection check was added, c945781).
- Delay 17:13-17:50: the PMCP session expired and the auto-login couldn't type into
  the form (nothing submitted); a fresh browser fixed it.
- Loom is on the back burner (Raul). No GO from me; only Kart/Raul give one.

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
