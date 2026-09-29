---
from: warden
to: loom
subject: Handover: how to run the alex-live export (zero writes)
timestamp: 260929132258
---
Per Raul/Kart, the alex-live export is yours. The browser lock is free (the exporter claims it itself). Steps:
1. Browser: the visible Chromium on :9222, which Raul logged in by hand (the .env login is still rejected). It's HEADED, so the screen must stay on for the whole run (~25 min); a blanked screen hangs every click.
2. Open alex-live's Edit view first (the exporter reads the name from it): Raul can click it by hand, or: click 'Coachings', then _report_fetch.enter_edit_view(page, 'ALEX v01 zum Ausprobieren 2'). The row pick is now an exact match.
3. Monitoring must be OFF on alex-live. If it's on, phase 1 fails loudly. Do NOT toggle it yourself: that's a change to alex-live, and it's Raul's call.
4. Run: tools/coaching-bundle-export/export_coaching.sh --yes --update-baseline. --update-baseline writes alex-live's OWN local baseline file (per-coaching since 935d7a8), not PMCP. Skip --resolve-jumps.
5. CHECK the first lines of output: it must print "'ALEX v01 zum Ausprobieren 2' is the CLEAN reference coaching ... read-only run". If it doesn't, Ctrl-C: it isn't on alex-live.
Expected: ok=True. The read-only mode skips editor modals, because their Close is a no-op re-save = a write. So sender-rule details are missing (tree only), and the log will say 'N jump targets still ambiguous'. That's the zero-write trade-off; I'm testing a read-only close (window X) that could lift it later. The HTML-text fix is built in. Output: data/exports/coaching_alex-v01-zum-ausprobieren-2_<ts>.json. If it fails, mail me the data/logs/export/ log path and I'll jump on it.
