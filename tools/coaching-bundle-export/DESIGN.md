# Coaching exporter — design & status

Goal: a self-contained file that captures enough of a PMCP coaching's micro
dialogs to **reproduce the chat behaviour** in the pathmate-analyzer simulator —
not just the randomisation groups.

## Why the Report HTML export isn't enough

`Coaching_*.html` is a PMCP "Report" export. It has full per-language text and
decision branches (already parsed by `app/coaching_model.py`), but **no
Randomisation Group column**, no node ids, and its node model miscounts a few
dialogs (decision sub-structure, duplicate dialog names). The Randomisation Group
only exists in the live Vaadin editor.

## Data sources

| Source | Gives | Misses |
| --- | --- | --- |
| Editor `.v-table` sweep (`export_bundle.py`) | node type, order, comment, channel, answer type, result var, **randomisation group**, all flags, accurate counts (1177 nodes / 107 dialogs, matches the metadata sidecar) | full text (grid truncates with `…`), branch conditions, answer routing, delay/priority |
| Report HTML (`app/coaching_model.py`) | full per-language text, decision branches, trigger expressions, answer options | randomisation groups, node ids, correct counts for ~5 dialogs |
| Editor detail modal (per node) | everything, incl. delay/priority, answer→route | slow: ~1200 modal opens + nested sub-editors |

## Pipeline (built)

1. **`export_bundle.py`** — CDP-attach to a hand-logged-in Chromium, widen the
   window to defeat the menubar's `►` overflow, DFS the menu (folders included),
   select each micro dialog, round-trip-aware positional sweep of its table.
   → `coaching.bundle.json` (uids, order, grid columns, r_ group).
2. **`enrich_bundle.py`** (`export_bundle.py --enrich REPORT.html`) — join the
   bundle with the Report-HTML model on `(micro-dialog leaf name, node order)`,
   only where a Report dialog matches by name AND node count. Attaches
   `textByLang`, `branches`, `triggerExprs`, `answerOptionsByLang`.
   → `coaching.bundle.v2.json` — 92/107 dialogs enriched (15 empty folders),
   0 unresolved; 255/258 decision points have branch data.
3. **`../rgroups-table/build_table.py`** — `coaching.bundle.v2.json` →
   `rgroups_table.csv` / `rgroups_summary.csv` (one row per r_ message / per
   group; pool = `(group, micro dialog)`).
4. **`../rgroups-table/expand_rgroups.py`** — every pool with < N distinct
   variants → Claude or ChatGPT for the rest (same meaning, ~same length, emoji,
   age-appropriate for 10-19; both en-GB and ro-RO) → `rgroups_table.expanded.csv`.

## Result (ALEX v01, 2026-09-03)

107 micro dialogs, **1177 nodes** (919 Message, 258 Decision Point — "events"
and commands are Decision Point / flagged Message rows, there is no separate
type). **96 distinct `r_` randomisation groups** (the earlier count of 63 was
from a sweep that truncated tall dialogs). 127 randomisation pools, 110 of them
with < 10 distinct variants.

## `coaching.bundle.json` schema

```jsonc
{
  "coaching":     { "name", "languages": ["en-GB","ro-RO"], "scrapedAt", "stage" },
  "microDialogs": [ { "uid": "md-000", "name", "folderPath": [], "isFolder",
                      "nodeCount", "nodeUids": [], "missingRows": [],
                      "textResolved": true } ],
  "nodes": [ {
    "uid": "md-000#003", "microDialogUid": "md-000", "order": 3,
    "type": "message|decision", "rawType": "Message|DECISION POINT",
    "comment", "gridText",                 // gridText is the truncated cell
    "channel", "answerType", "resultVariable", "randomisationGroup",
    "flags": { "commandMessage", "containsMedia", "containsSurvey", "containsRules" },
    // added by enrich_bundle.py:
    "textByLang": { "en-GB": "", "ro-RO": "" },
    "answerOptionsByLang": {}, "commandByLang": {}, "triggerExprs": [], "mediaFile": "",
    "branches": [ { "condition", "comment", "writesVar", "stopMicroDialog",
                    "leaveDecisionPoint", "jumpDialog", "cascadeDialog", "supported" } ]
  } ]
}
```

## Not yet captured (Stage 3 — needs the detail modals)

- send **delay** / message **priority** / the "Low Priority" placeholder row semantics
- answer **quick-reply → child routing** (Report has option text, not the target)
- the 3 decision points with no parsed branch (likely JS-only)
- media/survey references beyond the file name

## Analyzer import (Stage 4 — not started)

`app/coaching_model.py` gains `parse_bundle(json)` → existing
`CoachingModel`/`MicroDialog`/`Node` dataclasses, extended with `uid`,
`randomisation_group`, `order`, `delay`. `app/coaching_sim.py` gains: collapse a
run of same-`r_group` siblings into one random pick; follow scraped branch
routes; honour delays.
