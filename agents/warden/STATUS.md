# Warden — status

_Updated 2026-10-01 14:25._

## Now (2026-10-01 14:25)
- **Raul's top priority: PMCP editor documentation** (Warden, Mirror, Mason, Kart).
  - (a) Annotated screenshots of every editor on alex-sandbox: `docs/pmcp-ui/screens/`
    (README maps each red box to its question). Red boxes = Mason's Unknown list. Done.
  - (b) 15 rules sit outside the 4 execution sections in alex-sandbox. Exports
    dropped them until cd25e59. Done.
  - (c) The 'leaves' count now means rules without child rules. Done.
  - (d) Richer export (mine; Mirror owns the field list, Mason the meanings). Done:
    disabled state per sender (da60101), the raw dialog target (999787f). Next:
    Mirror's coverage-map §6 list (message settings), plus Mirror's 2 suspected
    scraper bugs (storeResultVariable on r-071; answerTabs.disabled always false).
- **Browser:** mine, for docs/export work. Loom holds until Kart's GO (Raul).
  My premature GO to Loom at 14:05 was withdrawn within a minute; nothing ran.

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
