# Stage 4 — bundle-driven stateless chat engine — plan

Self-contained brief for picking this up cold. Workstream 4 of the five in
`README.md` ("In-platform faithful chat simulator"). Depends on Stage 3
(`coaching.json` export), which is done and on `main`.

---

## 1. Goal & what's already decided

Replace the current HTML-parse-driven simulator with one driven **only** by
`coaching.json` (the single-file export from
`tools/coaching-bundle-export/export_coaching.py`). The Report HTML is a
side-channel double-check (the coherence canary in that exporter) — it must
**never** drive the chat.

The engine is a **pure function** — no hidden state, deterministic,
serializable:

```
advance(coaching, state, to_time)  -> (state', events[])   # clock moves / "advance clock" button
answer(coaching, state, value)     -> (state', events[])   # user replies to the open question
```

`state` — the complete, serializable snapshot ("recreate the chat from a
variable dump + a clock"):

| field | meaning |
| --- | --- |
| `vars` | every participant variable — **this is where PMCP's real state lives** (all the `$…Done` / `$…ReminderStage` / `$…Active` / `$dateOfNext…` bookkeeping the coaching authors maintain) |
| `clock` | current time, integer minutes from an epoch |
| `pending` | `null`, or the ONE open question: `{dialogUid, nodeIdx, sentAt, doesNotAnswerRules?}` |
| `seed` | int, fixed at init — makes r_-group random picks reproducible |

`transcript` is **not** state. It is the accumulation of `events[]` the
engine returns each call; replay `advance` over the same inputs → identical
transcript.

**Decisions (with rationale):**

- **`coaching.json` is the only chat input.** HTML stays for the coherence
  check and the Statistics/Rules/Raw tabs. Per the user: "the chat cannot be
  driven by the html so that is not an option."
- **Upload menu is unchanged** (HTML only). A coaching can have a
  `coaching.json` *added* to it after creation; the Chat tab and all Stage-4
  features are hidden/disabled until it is attached.
- **Rule expressions are parsed in the exporter**, not at load time. The
  `ruleTree` entries in `coaching.json` today are just captions like
  `"🕖 Delayed day start at 3 AM: $systemHourOfDay calculated value is bigger
  than 3"`. `export_coaching.py` must parse each into structured fields
  (`{lhs, operator, rhs}` / `→` assignment / `unsupported` for JS) so
  `coaching.json` is fully machine-readable and `parse_bundle` just loads it.
- **One dialog / one open question at a time** (PMCP's model).
- **Interruption:** a sender rule that fires while `pending` is set is
  **skipped that tick** (PMCP won't overwrite an open question; and from the
  Stage-3 findings no sender rule sets a stop/solve checkbox). Emergent from
  rule order + timeout — there is no priority/tier field (see the
  "priority-field correction" in `README.md`).
- **Not the real PMCP engine.** JS-snippet rules, regex, multilingual-array
  lookups stay `unsupported` and are skipped with a transcript note, exactly
  as the current simulator does. The value-add is: auto rule→dialog
  launching, r_-group collapsing, the not-answered timeout, and
  rule-order-driven interruption.

---

## 2. Current code inventory

| file | what it is | HTML-bound? |
| --- | --- | --- |
| `app/coaching_model.py` | `parse_model(html_bytes) -> CoachingModel`. Dataclasses: `Rule` (`context`, `depth`, `raw_expr`, `comment`, `writes_var`, `sends_message`, `stops_intervention`, `is_js_snippet`, `supported`), `Node` (`type`, `comment`, `channel`, `writes_var`, `text_by_lang`, `answer_type`, `answer_options_by_lang`, `command_by_lang`, `media_file`, `trigger_exprs`, `branches`, `jump_msg_*`), `DecisionBranch`, `MicroDialog` (`i`, `name`, `nodes`), `MessageGroup`, `CoachingModel` (`rules`, `micro_dialogs`, `message_groups`, `variables`, `languages`). `load_model(coaching_id)` reads the stored file, caches per (id, mtime). | **yes** — `parse_model` only |
| `app/coaching_sim.py` | `Simulator(model, lang)`. `parse_expr` / `eval_expr` — the ~8-operator declarative mini-language (`_CMP_OPS`, `_ASSIGN_*`, `_DATE_*`). `initial_state()`, `step(state, action)` for actions `reset` / `set_var` / `tick` / `run_periodic` / `launch_dialog` / `launch_group` / `answer`. `_run_context` walks `model.rules` filtered by `context`, depth-stack for nesting, does assignments, logs "rule sends a message" **but does not launch the dialog** (the link isn't in the HTML). `_advance` walks a dialog's `nodes` in order; `_run_decision` handles branch jump/cascade/stop. State today: `{clock, vars, open_dialog, pending, transcript}`. | uses `CoachingModel` — engine is model-shape-bound, not HTML-bound directly |
| `app/routes.py` | `GET /coachings/<id>/sim/init` → `Simulator(model).initial_state()` + dialog/group lists. `POST /coachings/<id>/sim/step` → `Simulator(model, lang).step(state, action)`. Both `load_model(id)`. | via `load_model` |
| `app/templates/coaching_view.html` | 6-tab view incl. Chat. Chat tab drives `sim/init` / `sim/step`, buttons for tick / advance-to-slot / run-periodic / launch-dialog / answer. | — |
| `app/storage.py` | `save_coaching(name, tag, filename, file_bytes)`, `coaching_file_path(id)`, patient-model storage. Coachings are `.html` on disk keyed by id. | — |
| `tools/coaching-bundle-export/export_coaching.py` | produces `coaching.json` = `{coaching, microDialogs, nodes, rules{sections, ruleTree, sendingRules}, validation}`. `_rules_nav.build_rule_tree()` builds `ruleTree` (captions only, no parsed exprs yet). `_rules_nav.parse_rule_fields()` already parses the sender modals into `sendingRules` (`primaryAction`, `microDialogPath`, `messageGroup`, `sendHourVariable`, `notAnsweredTimeoutMinutes`, `doesAnswerRules`, `doesNotAnswerRules`). | it's the producer |

Reference data on disk:
- **`data/exports/coaching.json`** — ALEX v01, first live unified export
  (2026-09-10). `microDialogs` + `nodes` (+ enrich `textByLang`/`branches`) +
  `rules{sections, ruleTree, sendingRules}` + `validation` + `run`. One
  dialog ("Adherence barriers dialog / Medication") is present with an
  `error` field and no nodes (a transient sweep timeout) — re-run to get a
  clean one. `coaching.name` may be `null` on this file (predates name
  capture).
- `tools/coaching-bundle-export/rules_stage3_ALEX_v01.json` — ALEX v01 rules
  reference: `ruleTree` (captions) + `sendingRules` (25, fully parsed).
- `tools/coaching-bundle-export/coherence_baseline.json` — known-good counts.

---

## 3. Input & how to start

Use **`data/exports/coaching.json`** directly — it exists now. Re-run
`tools/coaching-bundle-export/export_coaching.sh --report <Report.html>`
(via `tools/start_pmcp.sh`) for a fresh/clean one (also populates
`coaching.name`).

If that file is ever unusable, a synthetic stand-in can be stitched from
`tools/coaching-bundle-export/rules_stage3_ALEX_v01.json`'s `rules` block +
whatever `microDialogs`/`nodes` you have — but the real export is the
reference now.

**First real target:** ALEX v01 — it's the only coaching with full Stage-3
data and a baseline. The engine must stay coaching-agnostic (no ALEX
hardcoding); a smaller coaching can be added later once its `.json` is
exported. (`data/waterbot.html` / `data/smallchange.html` are the only other
coachings on disk, and they have no `.json` and may not be PMCP exports.)

---

## 4. Phased plan

Additive throughout — the HTML `parse_model` path and the current Chat tab
keep working until phase E swaps the wiring.

### Phase 0 — exporter: parse rule expressions  *(no live browser needed)*
- In `tools/coaching-bundle-export/_rules_nav.py`, extend `build_rule_tree()`
  (or add a `parse_rule_caption(caption) -> dict`) to split each caption into
  `comment` + a structured expr: `{kind: "cmp", lhs, op, rhs}` /
  `{kind: "assign", lhs, target, result}` / `{kind: "unsupported", raw}`.
  Reuse the operator phrase list from `app/coaching_sim.py` (`_CMP_OPS`,
  `_ASSIGN_TRUE/FALSE`, `_DATE_*`) — keep them in sync or move to a shared
  module.
- Add the parsed fields to each `ruleTree` node.
- Regenerate `tools/coaching-bundle-export/rules_stage3_ALEX_v01.json` and
  bump `coherence_baseline.json` if counts move.
- **Acceptance:** every `ruleTree` node has a `kind`; `unsupported` only for
  JS snippets / regex; spot-check 10 against the HTML rules parser output.

### Phase A — `parse_bundle()` + dataclass fields  *(synthetic json ok)*
- `app/coaching_model.py`: `parse_bundle(data: dict) -> CoachingModel`.
  Group `data["nodes"]` by `microDialogUid`, sort by `order`, build
  `MicroDialog.nodes`. Map `branches` (same shape). Build `Rule` list from
  `data["rules"]["ruleTree"]` (+ `sendingRules` joined by `uid`).
- Additive optional fields:
  - `Node`: `uid`, `randomisation_group`, `order`
  - `Rule`: `uid`, `kind` (`condition`/`sender`), `parent_uid`,
    `micro_dialog_path`, `send_hour_variable`,
    `not_answered_timeout_minutes`, `does_answer_rules`,
    `does_not_answer_rules`, structured `expr`
  - `MicroDialog`: `uid`
- `load_model()`: dispatch on the stored file — `.json` → `parse_bundle`,
  `.html` → `parse_model`.
- **Acceptance:** `parse_bundle(synthetic)` yields a `CoachingModel` the
  existing `Simulator` can `initial_state()` on without error; dialog/rule
  counts match the JSON.

### Phase B — randomisation-group collapsing
- In the dialog walker, a run of consecutive message nodes sharing a
  non-empty `randomisation_group` (within one dialog) → pick **one**,
  seeded from `state["seed"]` (+ dialog uid + a call counter), skip the
  rest. Emit one coach message.
- **Acceptance:** same `seed` → same picks across runs; different seed →
  different picks; a dialog with no r_ groups is unchanged.

### Phase C — rule → dialog launching + not-answered timeout
- `_run_context` (renamed/rebuilt around `ruleTree` order): when a
  `kind=="sender"` rule's condition chain is truthy, resolve
  `micro_dialog_path` (the `" > "`-joined path) to a `MicroDialog` and launch
  it — walk to the first question (set `state["pending"]` with
  `sentAt=clock`) or to completion.
- Each `advance`: if `pending` and `clock > pending["sentAt"] +
  not_answered_timeout_minutes` → emit "handled as not answered", run that
  rule's `does_not_answer_rules` subtree, clear `pending`.
- Resolve first (read the `ruleTree`): is DAILY BASIS gated by the
  "🕖 Delayed day start at 3 AM" rule, or a separate 00:00 pass? Is
  `send_hour_variable` already enforced by a parent condition
  (`$systemHour … equals $userSetTimeForX`), making the field
  display-only? (Best guess: yes.)
- **Acceptance:** advancing the clock over a due ACQ/medication window
  produces the right dialog automatically; letting it sit past the timeout
  fires the DOES-NOT-answer branch.

### Phase D — interruption
- A sender that would fire while `state["pending"]` is set → **skip**, log
  `"(rule X suppressed: a question is already open)"`.
- This is a modelling choice, not verified PMCP behaviour — flag it as an
  explicit assumption directly in this doc (or in a committed doc reachable
  from here), not in `ALEX_v02_simulator_scope.md` — that file is
  gitignored (local-only, stale) and won't exist on a fresh clone.
- **Acceptance:** two senders due in the same tick → only the first opens;
  the second fires on a later tick once the first is answered/expired.

### Phase E — Chat tab wiring
- `sim/init` / `sim/step` keep their shapes. `Simulator` (or a new
  `ChatEngine`) uses `parse_bundle` output. Add an "auto-run periodic"
  toggle; surface "rule X launched dialog Y", a timeout countdown, and
  not-answered events. Keep manual `launch_dialog` as an escape hatch.
- Gate the Chat tab on the coaching having a `.json` attached.
- **Acceptance:** click through a full ACQ reminder → answer → completion in
  the browser, matching a hand-trace of the rules.

### Phase F — patient-model hook  *(design only in this workstream)*
- Refactor `answer` so a headless `PatientModel.respond(pending, clock) ->
  value | None | "later"` can drive the engine without HTTP. This is the
  seam workstream 5 (Markov patient simulation) plugs into — `§4–7 of
  ALEX_v02_simulator_scope.md` had the fuller spec for this, but that file
  is gitignored/stale and may not be present; don't block on finding it,
  treat this bullet as the seam's actual spec if it's missing.

---

## 5. Open questions to settle by reading data (not blocking)

- **RESOLVED 2026-09-23 (Mirror, before Phase C, against the real ALEX v01
  export)** — DAILY BASIS trigger: it's its own separately-scheduled pass
  (matches the Simulator's existing crossed-midnight model), not literally
  invoked by the "3 AM delayed day start" rule. That rule is the *first*
  rule under `PERIODIC BASIS`, gating a `"🚀 Only perform if daily rules
  have NOT been already performed"` branch - a same-day catch-up path for
  when the app missed its midnight run, not the day's primary trigger.
  `PERIODIC BASIS`'s sibling branch (`"...have been already performed"`)
  holds the section's normal per-tick sender checks. Phase C does not need
  to change how DAILY vs PERIODIC get invoked.
- **RESOLVED, and the plan's guess was WRONG** — `send_hour_variable` is
  **not** redundant with the condition chain: checked all 18 real
  `sendingRules`' full ancestor chains in `ruleTree` (`parentUid` walk) -
  **none** contain a `$systemHour`/`$systemDecimalMinuteOfHour` comparison
  anywhere. A sender's condition chain being truthy only means the message
  is *due* (content-wise, e.g. `$today text value equals $dateOfNextACQ`);
  the configured hour (`send_hour_variable`, falling back to
  `send_hour_clock` when unset - all 5 checked `send_hour_variable`s
  default to the coaching's `-99`/"unset" sentinel) is a genuinely separate
  gate the engine must enforce itself. Consequence for Phase C: a
  `PERIODIC BASIS` sender (7 of 18) whose condition stays truthy across
  many ticks needs its own due-hour + once-per-day dedup logic, or it
  would auto-relaunch its dialog on every single periodic tick.
  Implemented as `_sender_due()` / `state["_sender_last_fired"]` in
  `coaching_sim.py`.
- **Also found, not previously flagged**: none of the 18 real
  `sendingRules` have any `doesAnswerRules`/`doesNotAnswerRules` populated
  - the not-answered-timeout → run-the-handler-subtree half of Phase C has
  no real data to verify shape against. Implemented defensively: the
  timeout fires, `pending` clears, and a *non-empty* `does_not_answer_rules`
  is logged (names/counts) rather than evaluated as executable rules -
  evaluating against a guessed, unverified schema was judged riskier than
  a clearly-flagged gap. Revisit once a coaching with real
  `doesAnswerRules`/`doesNotAnswerRules` data is exported.
- **`microDialogPath` shape, found while resolving the above**: a list of
  folder-tree breadcrumb segments (e.g. `["Prompt patient to take
  controller medication", "...first dose", "...first dose (v02)"]`, or
  `['']` when PMCP never resolved a target at all) - only the **last**
  non-empty segment is the actual target dialog's name; resolve it the
  same way `DecisionBranch.jump_dialog`/`cascade_dialog` already are
  (match against `MicroDialog.name`), not the whole path.
- **`send_hour_variable` holds a decimal hour, not "HH:MM"** (e.g.
  `$userSetBedtime-0.17` → `21.83` = 21:50). Only `sendHourClock` /
  `sendHourLiteral` are "HH:MM" strings. `_sender_due()` tries a float
  first and falls back to an HH:MM parse.
- **System hour variable names were wrong (pre-existing bug, fixed in
  Phase C)**: the real ALEX v01 rules read `$systemHourOfDay` and
  `$systemDecimalMinuteOfHour` (a fraction of an hour); there are zero
  occurrences of `$systemHour`/`$systemMinute`, which is all the
  simulator used to set. Every hour-gated rule, including "Delayed day
  start at 3 AM", was always false. Both naming conventions are now set.
  This likely matters beyond Phase C (Stage 3 / exporter reviewers).
- **The coaching owns `$today`, so the engine can't rely on it**: ALEX v01
  r-000 rebuilds it as `$systemDayOfMonth.$systemMonth.$systemYear`
  (unpadded, e.g. `3.1.2026`), then r-001 applies `$today{#d}`. The
  engine doesn't interpret the `{#d}` suffix (3 occurrences in the
  export, no documentation found), so `$today` ends up as the literal
  `3.1.2026{#d}`. That broke Phase C's once-per-day key (fixed: senders
  now key on `clock["day"]`), and it probably also breaks the coaching's
  own `$today` comparisons (r-010/r-014 date diffs, r-097/r-098
  `text value equals`). **Open**: what `{#d}` does in PMCP. Don't guess;
  it needs a doc reference or a live precedent.
- Coverage of `_CMP_OPS` vs operators actually appearing in `ruleTree`
  captions → tally distinct operator phrases in
  `rules_stage3_ALEX_v01.json`.
- Decision-point-internal quick-reply routing (a `DecisionBranch` that routes
  on the *user's answer* to a question inside the same dialog) — the
  Stage-3 findings flagged this as still-open. Check `branches` on decision
  nodes that follow a question node.

---

## 6. Reference material

- `README.md` → "Roadmap: five workstreams", "priority-field correction",
  "Navigating the live PMCP portal".
- `tools/coaching-bundle-export/DESIGN.md` → export schema, "Stage 3 …
  CAPTURED", "Analyzer import (Stage 4)".
- `tools/coaching-bundle-export/WORKFLOW.md` → how to produce `coaching.json`.
- `docs/rules_stage3_ALEX_v01.md` + `tools/coaching-bundle-export/rules_stage3_ALEX_v01.json`
  → the 25 sending rules with timing/routing, and the rule tree.
- `ALEX_v02_simulator_scope.md` → the fuller (tier-model) design this is a
  reframing of; §4–7 are the workstream-5 patient/Markov spec. **Stale,
  gitignored, local-only** — don't expect it to exist on a fresh clone;
  it's listed here for historical context only, nothing in this plan
  should require reading it to proceed.
- `autochanges/2026-09-10-rules-tree-stage3-sweep.md` → Stage-3 session log
  and the Vaadin/portal gotchas.
- Auto-memory: `coaching-analysis-rework`, `pathmate-analyzer-roadmap`,
  `pmcp-portal-and-randomisation-groups`.
