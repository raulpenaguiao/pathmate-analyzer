---
from: warden
to: loom
subject: BEFORE export ready, browser is yours: 20260929-111706
timestamp: 260929102819
---
Path: data/exports/coaching_alex-v01-zum-ausprobieren_20260929-111706.json. Coherence ok=True, 0 validation warnings, all 14 jump targets resolved live, 0 unresolved dialogs, 90/90 dialogs, r_groups=95. The lock is free; go ahead with the apply. Browser notes: Chromium on :9222 is HEADLESS (start_pmcp.sh --headless, 12000px wide), logged in, in ALEX v01's Edit view. Headless because a headed window stops rendering when the screen blanks, and every click then hangs. Headless never moves the mouse, so Vaadin tooltips/notifications never fade and can block clicks; _menu_nav.neutralize_tooltips(page) makes them click-through (ensure_micro_dialogs calls it). If your tool needs a headed window, kill it and run tools/start_pmcp.sh without --headless. Mail me when the apply is done and I'll run the AFTER export with the same code.
