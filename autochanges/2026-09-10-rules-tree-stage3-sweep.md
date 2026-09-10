# 2026-09-10 — live PMCP Rules-tab sweep (Stage-3 capture)

**Coaching:** "ALEX v01 zum Ausprobieren" (sandbox — not production, per the
user).
**Driving:** both. The user started the CDP Chromium
(`--remote-debugging-port=9222`, Playwright's bundled Chromium), logged in,
and navigated to the coaching's **Rules** tab. Claude drove
`tools/coaching-bundle-export/probe_rules_tree.py` over CDP and iterated on
it against the live page.
**Goal:** resolve the open Stage-3 schema questions and capture, for every
message/dialog-sending rule, its send-hour, not-answered timeout, target
micro dialog / message group, and DOES / DOES-NOT-answer routing.

## What was navigated

1. Coachings → "ALEX v01 zum Ausprobieren" → Edit → Rules tab (the `.v-tree`
   with the four `Execution on …` roots).
2. Full tree expansion — 122 nodes across DAILY BASIS, PERIODIC BASIS,
   UNEXPECTED MESSAGE (empty), USER INTENTION.
3. "Edit rule:" modal opened for each of the 25 `message-icon-small.png`
   rules, read via `probe_rules_tree.py` phase 3, then dismissed with the
   modal's "Close" button.
4. Several read-only diagnostic scripts against the same page while working
   out the Vaadin-tree expand gesture (no modals, no writes).

## Writes

- **~40 no-op "Edit rule:" re-saves**, all on this sandbox coaching. Break-
  down: a 4-rule validation run, a 6-rule validation run, a failed 25-rule
  run (bailed before opening anything — view had drifted off the Rules tab),
  and the full 25-rule run. Each modal was opened to read and dismissed with
  "Close", which — as recorded on 2026-09-09 — fires "The rule has been
  updated." with zero fields touched. Confirmed-harmless same-value re-saves
  on this sandbox; **not** safe to assume elsewhere.
- Claude clicked the top-nav **"Rules"** tab once via Playwright to restore
  the tree view after it drifted to the coaching's Information page (a
  read-only navigation click, no state change).
- **Monitoring:** left as the user had it. Body text during the session
  showed the toggle reading "on" at least once; the Rules-tab work did not
  depend on it either way. Still deactivated-or-not per the user's
  standing 2026-09-09 call — revisit before using this coaching for
  anything monitoring-dependent.

## Findings — resolves the Stage-3 open questions

Full data: `tools/coaching-bundle-export/rules_stage3_ALEX_v01.json` (25
rules). Human writeup: `docs/rules_stage3_ALEX_v01.md`.

- **"Edit rule:" modal schema, confirmed across all three non-empty
  sections:** Comment · Rule[x] / operator / Comparison term[y] · Store-
  result-var · **4 TRUE-result action checkboxes** (`Send message` /
  `Start micro dialog` / `Mark case as solved (unexpected message) and stop
  the current rule execution run` / `Stop current rule execution run and
  finish coaching for this participant`) · `Message group to send messages
  from` · `Micro dialog to start` · `Hour to send message (24h, 0 =
  immediately)` · `Minutes after sending until message is handled as not
  answered` · tabs `Rules if participant DOES answer` / `DOES NOT answer`
  (each a nested `.v-tree`).
- **Both action paths exist and are used.** 24 of 25 senders use
  `Start micro dialog`; one ("🌬️ Send regular pushed reminder for spirometry
  measurement (temp. disabled)") uses `Send message` + a **message group**
  (`Test (expects NO answer)`) instead of a micro dialog. Same timing field
  set on both paths.
- **`Hour to send message` is a `$variable`, not a literal clock.** Every
  scheduled sender points it at a variable — user-preference vars
  (`$userSetDesiredSpirometryTime`,
  `$userSetDesiredFirstDoseOfControllerMedicationInhalationTime`,
  `$userSetTimeOfTheDayForACQ`, …) or reschedule new-time vars
  (`$myFirstMedication_newTimeForFirstMedication`, `$newTimeForACQ`,
  `$spiroMesTimeDelay`, …). The literal "00:00" widget next to it is unset.
  Event-driven senders (debug dialog, `START`, sensor-data updates,
  `dataEdited`) leave the hour empty.
- **`Minutes … not answered` default is 4h** (`0 days, 4 hours, 0 minutes`)
  on every dialog-starting sender; the one `Send message` rule uses 19 min.
- **None of the 25 senders set "Mark case as solved… and stop" or
  "Stop… and finish coaching".** So senders don't self-terminate the run —
  the "execution stops once a rule solves the issue" behaviour is driven by
  the *condition* rules above them, not the sender leaves.
- **DOES / DOES-NOT-answer routing is rarely used.** Only the disabled
  pushed-reminder rule has any (`Go to spirometry micro-dialog` in both
  branches). The other 24 senders have both subtrees empty.
- **Row-icon set mapped:** `rule-icon-small.png` = a condition/calculation
  rule; `message-icon-small.png` = a message/dialog sender (the Stage-3
  payload); the four section roots have their own icons
  (`calendar` / `watch` / `bubble` / `signs`).
- **UNEXPECTED MESSAGE is genuinely empty.** DAILY BASIS is *not* empty (an
  earlier probe run wrongly concluded it was) — it holds most of the
  reminder senders. PERIODIC BASIS holds the guard tree + the six
  `$…_userRequestedNewTime` reschedule handlers. USER INTENTION holds
  intent routing (`go` / `coach` / `language` / personal-data-edited).

## Tooling — Vaadin `.v-tree` mechanics learned (now baked into probe_rules_tree.py)

- Expand state is the `aria-expanded="true|false"` attribute, **not** a
  `v-tree-node-expanded` class. Absent `aria-expanded` means leaf *or*
  never-opened parent — indistinguishable until you try.
- Children are pre-rendered but hidden; `.v-tree-node` COUNT never changes on
  expand. Progress signal is caption **visibility** (`rect.width > 0`).
- The expand gesture: click the caption **at x≈20** (near the text — the
  box centre of a short caption is dead space Vaadin ignores), wait ~600ms
  for the selection round-trip, **then ArrowRight**. A shorter wait or an
  immediate ArrowRight silently no-ops.
- Opening a node can lazy-load new children, shifting every later sibling
  index — so the probe re-dumps the tree after every single expansion and
  matches nodes by `(depth, caption)` identity.
- The "Edit rule:" modal is `v-window … v-readonly`; filterselect display
  values are only in the live `.value` DOM property, never the HTML
  attribute — read them via `page.evaluate`, not a static-HTML parse.

## Session hygiene notes

- The Rules-tab view **drifted back to the coaching's Information page**
  between two runs with no obvious trigger (idle re-render, or the previous
  run's final interactions). A run that starts with "no `.v-tree` on
  screen" just needs the "Rules" tab re-clicked — the session itself was
  still valid. `probe_rules_tree.py` now prints that instruction on this
  condition and exits before opening any modal.
- Confirmed again: `page.reload()` is never the fix — re-click the in-app
  tab.
