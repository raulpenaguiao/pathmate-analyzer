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
| Editor `.v-table` sweep (`_menu_nav` + `export_coaching.py`) | node type, order, comment, channel, answer type, result var, **randomisation group**, all flags, accurate counts (1177 nodes / 107 dialogs, matches the metadata sidecar) | full text (grid truncates with `…`), branch conditions, answer routing, delay/priority |
| Report HTML (`app/coaching_model.py`) | full per-language text, decision branches, trigger expressions, answer options | randomisation groups, node ids, correct counts for ~5 dialogs |
| Editor detail modal (per node) | everything, incl. delay/priority, answer→route | slow: ~1200 modal opens + nested sub-editors |

## Pipeline (built)

One script, one run, one file: **`export_coaching.py OUT.json --report REPORT.html`**
(wrapper `export_coaching.sh` adds the Monitoring pause). Phases:

1. **Micro Dialogs** — widen the window to defeat the menubar's `►` overflow,
   DFS the menu (folders included), round-trip-aware positional sweep of each
   dialog's `.v-table` (`_menu_nav.all_targets` / `sweep_table`).
   → `microDialogs`, `nodes` (uids, order, grid columns, r_ group).
2. **Enrich** — `enrich_bundle.enrich_dict()` joins the Report-HTML model on
   `(micro-dialog leaf name, node order)`, only where a Report dialog matches
   by name AND node count. Attaches `textByLang`, `branches`, `triggerExprs`,
   `answerOptionsByLang`. (92/107 dialogs, 0 unresolved on ALEX v01.)
3. **Rules** — `_rules_nav`: expand the `.v-tree`, `build_rule_tree()`, and
   for every `message-icon` sender open its "Edit rule:" modal and
   `parse_rule_fields()`. → `rules` (`sections`, `ruleTree`, `sendingRules`).
4. **Coherence check** — `coherence_check()` compares the sweep to the Report
   HTML and to `coherence_baseline.json` (dialog / node / rule / r_-group
   counts, per-dialog deltas). Writes `validation`; the script exits non-zero
   if the sweep collapsed or drifted — a canary for PMCP UI changes.
   `--update-baseline` rewrites the baseline from a run you trust.

Downstream: **`../rgroups-table/rgroup_report.py`** reads the export's `nodes` →
`rgroups_table.csv` (one row per `r_*` message); `rgroup_prepare.py` →
`rgroup_expand.py --limit N` tops up thin pools with an LLM; `rgroup_apply.py
--limit N` writes them back to the live editor.

## Result (ALEX v01, 2026-09-03)

107 micro dialogs, **1177 nodes** (919 Message, 258 Decision Point — "events"
and commands are Decision Point / flagged Message rows, there is no separate
type). **96 distinct `r_` randomisation groups** (the earlier count of 63 was
from a sweep that truncated tall dialogs). 127 randomisation pools, 110 of them
with < 10 distinct variants.

## Export schema

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

## Stage 3 — rule-level timing & routing — CAPTURED 2026-09-10

**Status: done for ALEX v01.** `probe_rules_tree.py` walked the live Rules
`.v-tree` (122 nodes) and opened the "Edit rule:" modal for every one of the
25 message/dialog-sending rules (`message-icon-small.png` rows). Outputs:
`rules_stage3_ALEX_v01.json` (this dir) and `../../docs/rules_stage3_ALEX_v01.md`.
Session log: `../../autochanges/2026-09-10-rules-tree-stage3-sweep.md`.

Open questions from 2026-09-09, now answered:

- **Both rule actions exist and are used.** 24/25 senders `Start micro
  dialog`; one uses `Send message` + a **message group** (`Test (expects NO
  answer)`). Same timing field set on both.
- **`Hour to send message` is a `$variable`**, never a literal clock —
  user-preference time vars or reschedule new-time vars; empty ⇒ immediate.
  The scheduling decision itself is in the rule's *condition chain*, not
  this field.
- **`Minutes … not answered` default = 4h** on every dialog sender (19 min
  on the one message sender).
- **Field set is identical across DAILY BASIS / PERIODIC BASIS / USER
  INTENTION.** UNEXPECTED MESSAGE is empty.
- **The 4 TRUE-result action checkboxes** are: `Send message`,
  `Start micro dialog`, `Mark case as solved (unexpected message) and stop
  the current rule execution run`, `Stop current rule execution run and
  finish coaching for this participant`. **No sender sets the two
  stop/solve boxes** — the run-stopping behaviour is on the condition rules
  above them.
- **DOES / DOES-NOT-answer subtrees**: empty on 24/25.
- **Row icons**: `rule-icon-small.png` = condition/calc rule;
  `message-icon-small.png` = sender.

Still open: quick-reply → child routing for decision points *inside* a micro
dialog (distinct from the rule-level DOES/DOES-NOT subtree); media/survey
refs beyond the file name.

### Original notes (kept for context)

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
- **Open, unresolved as of 2026-09-09 (resolve before finalizing the Stage 3
  schema):**
  - The "Edit rule:" form has **two independent action checkboxes**: "Send
    message if rule result is TRUE" and "Start micro dialog if rule result is
    TRUE." Only the micro-dialog path was sampled. Unknown whether the
    single-message path has the same delay/timeout fields, and whether it
    matters for pile-up the same way.
  - **"Message group to send messages from"** — a field on the rule form,
    blank/disabled in the one sample taken. May be a second dispatch layer
    alongside "micro dialog." Needs a sample where it's actually set.
  - **Only one rule was sampled**, under PERIODIC BASIS. Unconfirmed whether
    UNEXPECTED MESSAGE / USER INTENTION rules carry the same field set, and
    whether decision-point answer routing *inside* a micro dialog matches the
    rule-level DOES/DOES-NOT-answer mechanism seen at the top level.
  - **The Rules tab (`.v-tree`) is a structurally different Vaadin widget**
    from the Micro Dialogs picker (`.v-menubar`) that `_menu_nav.py` walks.
    Stage 3's bulk scraper needs its own tree-walker, not an extension of the
    existing menu navigation.
  - The rule tree renders **different icons per row** (message-send vs
    calculation-only vs "BEISPIEL"/example rules, at least). These probably
    encode action type and could drive automated classification — worth
    mapping the icon set before writing the bulk scraper.
- Practical hazard found live: some node-editor modals' dismiss button reads
  "Close" and is a pure cancel (message editor); on the **rule editor it
  actually commits** ("The rule has been updated" toast fires even with no
  edits made). Harmless on this sandbox coaching (not production, all writes
  logged) but any Stage-3 scraper must not click a modal's dismiss button
  assuming it's read-only — check for a real Cancel/Escape path, or accept
  that opening an "Edit rule:" modal writes a no-op save.

## Analyzer import (Stage 4 — not started)

Input is the single `export_coaching.py` output (`coaching` / `microDialogs` /
`nodes` / `rules` / `validation`):

```jsonc
"rules": {
  "sections": ["DAILY BASIS", "PERIODIC BASIS", "USER INTENTION"],
  "ruleTree": [ { "uid": "r-000", "section", "depth", "order", "parentUid",
                  "kind": "condition|sender", "icon", "caption" } ],
  "sendingRules": [ { "uid", "section", "parentChain": [],
    "primaryAction": "start_micro_dialog|send_message", "actions": [],
    "microDialogToStart", "microDialogPath": [], "messageGroup",
    "sendHourVariable", "sendHourLiteral",
    "notAnsweredTimeoutMinutes", "notAnsweredTimeoutText",
    "storeResultVariable", "doesAnswerRules": [], "doesNotAnswerRules": [] } ]
}
```

`app/coaching_model.py` gains `parse_bundle(json)` → existing
`CoachingModel`/`MicroDialog`/`Node` dataclasses, extended with `uid`,
`randomisation_group`, `order`; plus a `Rule` list carrying `section`,
`parent_uid`, `kind`, and — for senders — `micro_dialog_path`,
`send_hour_variable`, `not_answered_timeout_minutes`. `app/coaching_sim.py`
gains: collapse a run of same-`r_group` siblings into one random pick; follow
scraped branch routes; walk the `ruleTree` top-to-bottom honouring each
sender's timeout; and — since there's no PMCP-native priority field —
implement interruption purely as "rule order + timeout", matching what the
live Rules tab actually does, rather than a tier system.

The `sendHourVariable` binds the fire time to a `$variable`; the *whether*
(does this rule fire today) is in the condition chain above the sender, which
`ruleTree` captions carry verbatim and the Report-HTML rules parser
(`app/coaching_model.py::_parse_rules`) already turns into expressions — the
Stage-4 join is `ruleTree.caption` ⇄ Report-HTML rule by `(section, order)`.
