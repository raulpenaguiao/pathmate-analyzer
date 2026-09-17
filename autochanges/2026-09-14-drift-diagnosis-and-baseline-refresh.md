# Diagnosing the coherence-check drift + regenerating the baseline

2026-09-14. User uploaded a fresh export
(`data/exports/coaching_alex-v01-zum-ausprobieren_20260914-094837.json`,
self-run via `start_pmcp.sh` + `export_coaching.sh`) to the portal and
asked why every coherence-check metric showed drift against
`coherence_baseline.json`:

```
microDialogs: 65 vs baseline 83 (down 22%)
nodesTotal: 1049 vs baseline 1177
messageNodes: 830 vs baseline 919
decisionNodes: 219 vs baseline 258
randomisationGroups: 95 vs baseline 102
ruleTreeNodes: 125 vs baseline 117
sendingRules: 21 vs baseline 25
```

Also provided a matching fresh Report HTML export,
`~/Downloads/Coaching_ALEX_v01_zum_Ausprobieren.html`, which made a rigorous
cross-check possible instead of guessing.

## Diagnosis

**Primary cause: the baseline (2026-09-10) predates almost the entire
engagement.** Phase 2 (`autochanges/2026-09-11-alex-v02-phase2-prune.md`,
2026-09-11) deliberately deleted 20 dead/test/dev Micro Dialogs
(`Testing questionnaires`, `Testing infocards`, `Attic`, `⚙️ Controls`,
etc. — "coaching went from 107 to ~87 top-level-reachable"), and Phase 3
deleted 20 old rules while adding new spirometry ones (net +8 rule nodes)
and consolidated some senders (net -4, `sendingRules: 25→21`). Every
flagged number is consistent with this already-completed, already-
documented work — comparing against a pre-project snapshot, not evidence
of anything going wrong.

Verified this wasn't scrape noise: diffed yesterday's export
(`coaching_ALEX_v01_phase3.7b-variables-verify_20260912-182148.json`)
against today's fresh one — identical 65 leaf dialogs, byte-for-byte same
names, zero difference either direction.

**Secondary, separate finding: the `microDialogs` metric itself undercounts
by definition.** Cross-checked all 20 dialogs the coherence check reported
as "missing" against the fresh Report HTML: every single one's node count
matched exactly (e.g. `Prompt patient to conduct daily spirometry` = 51 in
both, `Compassionate feedback when patient is not doing so great` = 7 in
both). Nothing is actually missing — these are PMCP menu items that are
simultaneously a container (has its own submenu, so `isFolder: true` in the
sweep) AND carry their own real message content. `_metrics()`'s
`microDialogs = sum(1 for m in bundle["microDialogs"] if not
m.get("isFolder"))` silently excludes all of them, even the ones with
content. This is a pre-existing metric-definition gap in
`export_coaching.py`, not something this pass introduced — flagged for the
user to decide on (redefine as "dialogs with nodeCount > 0"?) but not
changed this pass, since the user's ask was specifically the baseline
refresh.

## Action taken: regenerated `coherence_baseline.json`

Ran `export_coaching.write_baseline()` directly against the two files
already on disk (no live browser touched — both files were already
verified-correct). New baseline:

```
microDialogs: 65, nodesTotal: 1049, messageNodes: 830, decisionNodes: 219,
randomisationGroups: 95, ruleTreeNodes: 125, sendingRules: 21,
variablesTotal: 334
```

## A real bug found while sanity-checking the auto-generated
`acceptedPerDialogDeltas`

`write_baseline()` computed a NEW accepted delta:
`"Prompt patient to conduct daily spirometry / Quit spirometry dialog
after successful spirometry procedure": [51, 7]` (sweep says 51, HTML says
7). A "quit dialog" swept as 51 rows looked implausible on its face — 51
also exactly matches the row count of the PARENT dialog (`Prompt patient
to conduct daily spirometry`), which was the previously-open grid right
before navigating into this child.

Inspected the actual node content rather than trusting the number:
real, distinct message content (6 farewell-message variants in
`r_GoodByeAfterSuccessfullyCarryingOutSpirometryMeasurement`, a couple of
decision points, 4 "To be shown if $mySpiro_readinessForSpirometry..."
variants) runs from row 0 to row 14 — **15 real rows**. Rows 15 through 50
(36 rows) all have completely empty comment/type/text/randomisation-group
fields — clearly not real content, a scrape artifact.

Likely mechanism: `_menu_nav.py`'s `sweep_table()` estimates the table's
`total` row count from `GRAB_JS`'s `Math.round(scrollHeight / rowHeight)`
(there's no authoritative PMCP-provided row count to read directly). If
the `.v-table-body-wrapper`'s `scrollHeight` hasn't been recomputed for the
new (much smaller) dialog's content by the time the very first grab runs —
`wait_round_trip()` only waits for the loading indicator to clear plus a
fixed 400ms settle, with no explicit check that the scroll geometry itself
has caught up — the estimate inherits the PREVIOUS (parent) dialog's
larger height, over-estimating `total` and then filling the excess with
blank ghost rows nothing ever populates. This is the same *class* of
virtualization/stale-DOM-state issue already found and fixed twice this
engagement (the Variables-tab sweep's undercounting, the rule-tree
`close_windows()`/`open_rule_modal()` flakiness) — a new instance, not a
new pattern.

**Deliberately NOT accepted into the baseline.** Wrote the baseline without
this one delta (removed it by hand after the auto-generation, added a
`note2` field explaining why) so the coherence check keeps flagging this
specific dialog on every future run until the underlying `sweep_table()`
race is actually fixed — accepting a known-bogus number would have
defeated the point of the check. Logged as an open TASKS.md item; needs a
live-browser session to repro/fix (try an extra settle or an explicit
re-grab after the first scroll step; check whether other dialogs
navigated-into-from-a-much-larger-sibling show the same symptom).

## Not done this pass

- The `microDialogs` metric redefinition (count by content, not by
  folder/leaf classification) — flagged to the user, left as their call.
- The `sweep_table()` stale-scrollHeight bug itself — diagnosed, not fixed;
  needs the live browser.
- The portal's Raw-tab JSON display issue the user separately mentioned —
  not investigated this pass.
