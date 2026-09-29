# Warden — status

_Updated 2026-09-29 12:30._

## Browser (check live: `.venv/bin/python tools/coaching-bundle-export/_browser_lock.py`)
Order (Raul via Kart, 09-29): Warden BEFORE export (done) -> **Loom: apply all 802 r_
variants (now, several hours)** -> Warden AFTER export.
The Chromium on :9222 is headless (`start_pmcp.sh --headless`), logged in.

## Task 1 done: BEFORE export
`data/exports/coaching_alex-v01-zum-ausprobieren_20260929-111706.json`
- Coherence ok=True, 0 validation warnings, 90/90 dialogs, 0 unresolved.
- All 14 jump targets resolved live (they had been ambiguous since 09-25).
- The baseline was refreshed from this run.
- Smith's HTML-message fix is applied: 9 formatted messages that had no text now have it.
- The log isn't literally zero-noise yet: 1 recovered folder retry, plus 3 "~" notes
  for a stuck Close that recovered. The data is complete.

## Fixed today (commits af5e637, b64b345, b3e0971, b278397)
- Overnight runs hung because a headed browser stops rendering when the screen
  blanks. Fixed: `start_pmcp.sh --headless`.
- Vaadin tooltips and notifications were blocking clicks, the main cause of the
  "popup never opened" flakiness. They are now click-through.
- Jump-target reading: 4/14 -> 14/14. The fixed waits were too short; they now poll.
  A stuck window no longer kills the export.
- Formatted (HTML-only) messages had empty text (Smith/Raul's demo-chat bug).

## Next
- The AFTER export, when Loom mails that the apply is done.
- Smith: `$weekdays` multilingual variable values are truncated (the variables
  sweep reads the table cell). It needs the full value from the edit dialog, which
  means browser time, so it comes after the AFTER export.
- Nice to have: the recurring spirometry-folder retry.

## Blocked, mine
- Questionnaire `multiSubmit`: waits for access to the real ALEX coaching.

## Open, not mine to act on
- The portal's attached ALEX bundle ("ALEXv1_14th") is a stale 09-14 export (Raul/Smith).
