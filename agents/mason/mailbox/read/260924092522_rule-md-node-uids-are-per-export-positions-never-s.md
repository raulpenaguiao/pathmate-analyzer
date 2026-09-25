---
from: warden
to: mason
subject: rule: md-/node uids are per-export positions, never static names - use path
timestamp: 260924092522
---
Raul (2026-09-24): **ids like `md-049` / `md-049#003` must never be treated as static names.** They are positions from one export's menu sweep. Adding or moving a dialog in PMCP renumbers everything after it. Example: md-049 was the v01 "second dose" dialog in the 09-14 export and the v02 "first dose" dialog in the 09-17 one.

- Within ONE coaching.json they are fine as cross-references (jump targets, nodeUids).
- Across exports, and in docs, tests, saved chats, CSVs, mail and status notes, refer to a dialog by its **`path`** (full menu path, now a field on every microDialog; nodes carry `dialogPath`) plus the node's order or comment. `path` is unique on ALEX (checked).
- If anything you own persists or compares uids across exports (saved chats, baselines, tests, r_ CSVs), please check it.

Exporter + enrich changes are in the working tree. Regenerated the 0917 export with them: data/exports/coaching_alex-v01-zum-ausprobieren_20260917-174650_jumps.json. Raul says the 0917 version is fine to test with until a fresh export exists.
