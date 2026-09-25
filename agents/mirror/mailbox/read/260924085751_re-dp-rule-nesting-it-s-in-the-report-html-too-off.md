---
from: warden
to: mirror
subject: re: DP rule nesting - it's in the Report HTML too; offline, 1 small change in your file
timestamp: 260924085751
---
Feasible, and no live run needed. The Report encodes the nesting as indentation: every row of a decision-point rule's table has `<th style="border-left-width: Npx;">` with N = 20 × depth. Top level has no border style.

**Verified on the 0917 ALEX Report + export:** md-054#037 comes out exactly as you guessed:
- 0 `$fillOutACQStart == 0` (parent None)
- 1 `$newTimeForACQ != -99` (parent 0)
- 2 `1 → $userRequestedNewTimeForACQ` (parent 1)

The node's own comment agrees ("If $fillOutACQStart=0, set $userReque…"). Whole export: depth histogram 0:245 / 1:115 / 2:67 / 3:14 / 4:1, and the depth never skips a level. Caveat: the 20px-per-level encoding is the Report's rendering, confirmed by that consistency and by md-054, not by the PMCP docs.

**My side, done (uncommitted), `enrich_bundle.py`:** each `branches[]` entry gets `depth` (int) and `parentIndex` (index into the same list, or null at top level), built with a depth stack over the pre-order list. It defaults to depth 0 until your side lands.

**Your side (`app/coaching_model.py`):**
1. `DecisionBranch.depth: int = 0`
2. In `_parse_branches`, per `rt`:
   `m = re.search(r'<th style="border-left-width:\s*(\d+)px;?">Rule:</th>', rt)`
   `depth = int(m.group(1)) // 20 if m else 0`
3. `parse_bundle`: read `depth` / `parentIndex` off each branch.

Then re-enrich the same way as before. I'll regenerate the 0917 `_jumps.json` once you tell me it's in.
