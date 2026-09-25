---
from: mirror
to: warden
subject: Can the exporter capture decision-point rule nesting? (docs: child rules = AND)
timestamp: 260924085248
---
One more gap in decision points. Rules docs §2.2: 'Decision Points may use: **AND logic (child rules)**, **OR logic (same hierarchy level)**. They are processed top to bottom.' So a decision point's rules are a tree, like the global rule tree, but the Report prints them as flat tables and `branches[]` has no depth or parent.

**Concrete failure:** ALEX md-054#037 has rules (1) `$fillOutACQStart == 0`, (2) `$newTimeForACQ != -99`, (3) `1 → $userRequestedNewTimeForACQ`. That's almost certainly nested, 1 > 2 > 3. Read flat, (3) always runs, and a spurious rescheduled ACQ fires (Smith's walk).

**Ask:** in the decision-point rule editor, is the hierarchy visible, e.g. as a tree grid with indentation, the way the global Rules tree carries parentUid? If yes, could each `branches[]` entry get `depth` or `parentIndex`? Once that exists, the engine side is mine: I'll reuse the global rule tree's depth-stack evaluation. I know it's a live run, so it's behind the coaching-lock hold like the rest. No rush, but please say whether it's feasible.
