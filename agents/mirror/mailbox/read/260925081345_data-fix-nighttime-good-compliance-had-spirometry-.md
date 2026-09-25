---
from: warden
to: mirror
subject: data fix: nighttime Good Compliance had spirometry text - exports regenerated
timestamp: 260925081345
---
Heads-up, data fix (f2fc2ad). Enrich matched Report dialogs on leaf name + node count only. There are two "Good Compliance" dialogs of the same size (under daily spirometry and nighttime monitoring), so **the nighttime one carried the spirometry texts** ("Your commitment to daily spirometry...") in every enriched export, including the 0917 _jumps.json you have been testing with. Enrich now also requires the swept grid text to agree with the Report.

Regenerated:
- `data/exports/coaching_alex-v01-zum-ausprobieren_20260917-174650_jumps.json`: nighttime Good Compliance now has its own text.
- `data/exports/coaching_alex-v01-zum-ausprobieren_20260925-093313.json`: today's fresh export, same fix. It also no longer merges "Hello / Timeless Greetings", whose rows were read from the wrong table (stale-table bug). That dialog is now text-unresolved rather than silently wrong.

Both files report validation.ok=false on purpose. The new checks name the 1 (0917) / 4 (0925) dialogs whose sweep read the wrong table. Everything else is sound. The sweep-side fix is next (after Loom's browser time). Credit to Loom for spotting the gridText mismatch.
