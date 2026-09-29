# Warden — status

_Updated 2026-09-29 16:55._

## Now
- **Raul is running the alex-live export himself** (headed :9222, full program with
  `--allow-noop-resaves`). His 16:25 run is healthy and in phase 4. Phase 3b resolved
  22 of 26 jump targets. When the JSON is written I'll mail Kart + Loom the path
  (for Loom's r_ CSVs).
- The 4 earlier runs (15:29 onwards) died: the screen went to sleep, and the headed
  12000px-wide window showed black with sporadic frames. The Reports from those
  runs are leftovers.

## Coachings (RULES.md, Raul 09-29)
alex-live = "ALEX v01 zum Ausprobieren 2" (never changed); alex-sandbox =
"ALEX v01 zum Ausprobieren" (pile-up target); sandbox = "Minimal Coaching for
Development 2 for Raul". The write guard refuses alex-live. Picking a coaching row
is an exact match (the alex-sandbox name is a prefix of alex-live's).

## Done today (all committed)
- The BEFORE export of alex-sandbox: `coaching_alex-v01-zum-ausprobieren_20260929-111706.json`.
- Jump-target reading went from 4/14 to 14/14. Tooltips and notifications are
  click-through. Headless mode.
- `start_pmcp.sh` without `--headless` gives Raul a visible window on demand.
- The export can run the full program on alex-live, but only with a human's
  `--allow-noop-resaves`. Baselines are per-coaching.
- A render guard pauses the run when the screen sleeps, asks for Enter / a
  re-login, and resumes in place. The run is wrapped in systemd-inhibit.
- Menu telemetry proved the flaky dropdowns are rendering starvation, not a menu bug.

## Next
1. Hand the alex-live JSON to Loom + Kart.
2. Root fix for the black window: keep the real window screen-sized and emulate the
   12000px viewport (CDP device metrics). Test on sandbox.
3. Phase 3b: resolve "no jump set", command-message targets, and paged dropdowns.
4. Queued live-read fields: Smith's `$weekdays` (full multilingual values) and Mirror's
   `clearsCascade` (batched).
5. multiSubmit (unblocked now that the real coaching is available; read-only).

## Blocked / open, not mine
- The `.env` PMCP login has been rejected since ~13:10; Raul logs in by hand. Fixing it
  would allow unattended headless runs again.
