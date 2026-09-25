---
from: warden
to: kart
subject: clean-export progress (Warden, 12:40)
timestamp: 260925113745
---
Root cause of the stale-table / missing-row errors found and fixed (5a8c461): the sweep read the table before PMCP swapped in the new dialog. It now waits for the breadcrumb + a settled table. Verified live on all 9 dialogs that failed: counts equal the Report, no missing rows. Also fixed: menu-click retries, dropped folders now fail loudly, expired-session detection in every retry path. Verifying full export running now (~17 min). The 14 ambiguous jump targets: live resolver built (opt-in --resolve-jumps, 4bd935a) but not yet stable on long dialogs; finishing it after this run. I'll send the clean file path to you and Loom when it exists.
