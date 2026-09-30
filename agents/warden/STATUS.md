# Warden — status

_Updated 2026-09-30 13:30._

## Now
- **Export at a fixed window size (Raul, 09-30): done, in testing.** The exporter no
  longer resizes the window. Menus collapsed into the menubar's `►` are opened
  through it; it opens on hover, not click (b431973, 97893b0). Raul's alex-sandbox
  test at 1400x1000: 90/90 dialogs and 14/14 jump targets, much faster.
- That test exposed a **silent failure in phase 4**: 0/6 sender rules read, yet
  `ok = True`. There were two causes, both fixed:
  1. `--update-baseline` compared the run with itself.
  2. Failed senders were only printed.
  Now the check runs first, the baseline is only updated from a passing run, a
  missing sender fails the run, and a failed sender takes a snapshot (ef8f83a, 3a88447).
  The phase 4 failure itself didn't reproduce in a read-only probe at the same size;
  the suspect is a dying session. Next: Raul reruns his test.
- **Loom is on hold** for the browser until Raul signs off on that test.

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
