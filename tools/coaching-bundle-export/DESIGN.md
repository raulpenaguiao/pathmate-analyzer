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

**Correction from live exploration (2026-09-09, via `probe_node_editor.py`
against the live "ALEX v01 zum Ausprobieren" sandbox coaching):** PMCP has
**no explicit message-level "priority" field at all** — "message priority"
below was a wrong guess. What actually exists:

- The **"Edit micro dialog message:" modal** (per node) has: Comment, text
  (with placeholders), media, message key, **randomisation group** (already
  captured), "is command" / "expects answer" checkboxes, answer type +
  options, result-variable, no-reply-value. No priority, no delay. The
  earlier "Low Priority" hit in a probe dump wasn't a field — it was one
  node's literal **Comment text** (a human-authored placeholder-message
  label), i.e. content, not a schema field.
- **Send delay and interruption timing live on the *rule* that starts a
  micro dialog** (Rules tab → e.g. PERIODIC BASIS → nested conditions → a
  leaf with "Start micro dialog if rule result is TRUE"), not on the message.
  The **"Edit rule:" modal** has: which micro dialog to start, **"Hour to
  send message (24h hours, 0 = immediately)"**, **"Minutes after sending
  until message is handled as not answered"** (the real expiry/timeout - a
  slider, common presets 1/5/10/30/60 min, up to multi-hour), and two nested
  rule-subtrees: **"Rules if participant DOES answer"** / **"...DOES NOT
  answer"** — this is the actual answer→routing mechanism.
- **There is no interruption/tier attribute anywhere.** The Rules tab's own
  "Info" panel states the real semantics: rules execute **top-to-bottom,
  down the tree**; a non-matching rule's children are skipped; **execution
  stops the moment a rule "solves the issue" or stops the whole coaching**.
  So pile-up/interruption behaviour is *emergent* from (a) the order rules
  are listed under DAILY BASIS / PERIODIC BASIS / UNEXPECTED MESSAGE / USER
  INTENTION, and (b) each rule's own send-delay + not-answered timeout — not
  from a P0–P3-style tag PMCP tracks anywhere. `ALEX_v02_simulator_scope.md`'s
  tier model (P0–P3) is **our abstraction over this**, not a PMCP concept;
  workstream 2's pile-up analysis needs to read rule *order and timeouts* in
  the live Rules tree, not look for a priority column that doesn't exist.
- Confirmed live: the rule → micro-dialog trigger link (which memory flagged
  as "only weakly present" in the Report HTML) **is** fully present in the
  live editor's Rules tab, on every "Start micro dialog" leaf — it's a
  scraping gap, not a missing-from-PMCP gap.
- Still open: answer **quick-reply → child routing** for decision points
  specifically (Report has option text, not the target — the DOES-answer
  rule-subtree above is presumably where this lives for rule-triggered
  dialogs; decision points inside a micro dialog may route differently and
  need their own probe), the 3 decision points with no parsed branch (likely
  JS-only), media/survey references beyond the file name.
- Practical hazard found live: some node-editor modals' dismiss button reads
  "Close" and is a pure cancel (message editor); on the **rule editor it
  actually commits** ("The rule has been updated" toast fires even with no
  edits made). Harmless on this sandbox coaching (not production, all writes
  logged) but any Stage-3 scraper must not click a modal's dismiss button
  assuming it's read-only — check for a real Cancel/Escape path, or accept
  that opening an "Edit rule:" modal writes a no-op save.

## Analyzer import (Stage 4 — not started)

`app/coaching_model.py` gains `parse_bundle(json)` → existing
`CoachingModel`/`MicroDialog`/`Node` dataclasses, extended with `uid`,
`randomisation_group`, `order`, and **rule-level** `send_hour`/`not_answered_timeout_minutes`
(sourced from the Rules tree, not the message). `app/coaching_sim.py` gains:
collapse a run of same-`r_group` siblings into one random pick; follow
scraped branch routes; honour rule delays/timeouts; and — since there's no
PMCP-native priority field — implement interruption purely as "rule order +
timeout", matching what the live Rules tab actually does, rather than a
tier system.
