# Mirror — status

## Last 24h summary (for Raul, 2026-09-25)
**Stage 4 chat engine: Phases A–F all done.** Phase E acceptance walks pass
in the browser (Smith). Phase F is the engine-only seam (Kart's call).
All 98 tests pass; everything is committed (`98e19f0` … `87e5e11`).

What changed in the engine (all against the PMCP 6.0 docs unless noted):
- Fresh sims start from the export's configured variable values. `{#d}`
  date format is implemented. `$systemMinuteOfHour`, `$systemDayInWeek`
  and `$participantOpenQuestions` are now set.
- `$participantParticipationInDays` follows **your chosen assumption**:
  the day index, which still reads the previous day during the 00:00
  daily run.
- Dialog walker:
  - answer options are `label:value` (they were inverted)
  - decision rules evaluate as a tree (child = AND)
  - per-rule jump-to-message targets
  - cascades return to the calling dialog
  - `open-component:questionnaire` is one blocking button
- Portal support: engine tag, `timeout_at`, structured events,
  auto-periodic toggle, `model_fingerprint` (Smith refuses stale chats),
  and `dialog_menu_path` (your "uids are positional" rule).
- Phase F: `app/patient_sim.py`. It has a `PatientModel` protocol and a
  headless `run()`, with no behaviour from stored patient models.

**Data update (08:15):** Warden's fresh export
`data/exports/..._20260925-093313.json` works in the engine without
patching: the options fix is in, and the medication Yes/No paths are
correct. (It flags 4 wrongly-swept dialogs on purpose.)

**Open problems / decisions for you:**
1. **Workstream 5 has no owner.** How patient-model fields (adherence %,
   response time, sleep window) become answers is undecided. That's the
   only Stage 4 follow-up left.
2. **Unverified assumptions to confirm** (docs or live precedent):
   - `$participantParticipationInDays` timing
   - a sender suppressed while a question is open retries later (Phase D)
   - the send-hour fallback to `sendHourClock` when the variable is -99
   - `leaveDecisionPoint` is unknown, so it's ignored with a warning
3. **Data gaps the engine can't fix:**
   - 14/49 jump targets are unresolvable from the Report (they need a
     live pass)
   - questionnaire → variable bindings aren't exported (the user sets
     `$acq_*` by hand)
   - `$participantDeactivatedOpenQuestions` is undocumented and unset
   - 4 senders have empty target dialogs (content)
4. **The v02 medication dialogs were authored flat** (Mason). A gate
   next to its assignments doesn't guard them. It's latent today, but
   it's worth knowing for new content.
5. **Waiting on your yes**: delete `docs/coaching_categories_table.md`?
   All 6 agents say yes. It's untracked, so the delete can't be undone.
6. **Uncommitted, not mine:** Smith's Phase E portal files
   (`app/routes.py`, JS/CSS/templates). The Phase E acceptance evidence
   depends on them. Also my `RULES.md` PMCP-docs section, which is mixed
   with other uncommitted edits to that file.

## Done
- **Phase A** (`app/coaching_model.py`): `parse_bundle(data: dict) -> CoachingModel`,
  the `coaching.json` counterpart to the HTML `parse_model()`. Additive only -
  `load_model()`/`parse_model()` untouched, every other tab keeps reading HTML.
  New entry point for the chat engine: `load_bundle_model(coaching_id)`, reads
  via `storage.coaching_bundle_path()` (Smith's attach mechanism), separate
  cache from the HTML loader.
  - Verified against the real ALEX v01 export: 171/171 rules, 90/90 dialogs,
    699/699 nodes placed, 18/18 sender rules joined via `sendingRules` uid.
    Gotcha: an `isFolder` dialog can still carry its own nodes directly (a
    "quit if debug mode" decision point sitting above its children) - filtering
    those out on the first pass silently dropped 184 nodes. Fixed: every
    `microDialogs` entry becomes a `MicroDialog`, folder or not.
  - `Rule.raw_expr` is rebuilt bare (comment-free) from the exporter's
    structured `expr` field so it stays directly evaluable by
    `coaching_sim.eval_expr` unchanged - no changes needed to `coaching_sim.py`
    or `rule_grammar.py` for this phase.
  - Known gap, not blocking: `coaching.json` doesn't export message groups or
    a stop-intervention flag yet - `CoachingModel.message_groups` is always
    `[]` and `Rule.stops_intervention` always `False` on the bundle path.
  - Tests: `tests/test_coaching_model_bundle.py` +
    `tests/fixtures/coaching_bundle_sample.json` (synthetic, small). Full
    suite (60 tests) green. Committed on main.

- **Phase B** (`app/coaching_sim.py`): a run of consecutive message nodes
  sharing a non-empty `randomisation_group` now collapses to one seeded pick
  in `_advance()`. New `state["seed"]` (fixed per sim, `initial_state(seed=)`)
  feeds a stable sha256-based pick (not `hash()` - that's
  `PYTHONHASHSEED`-randomized, not reproducible across runs) so replaying the
  same actions with the same seed reproduces the same picks. New
  `state["_rgroup_calls"]` counts resolutions per (dialog, group) so a
  relaunch of the same dialog (e.g. a daily reminder) can land on a
  different variant instead of repeating itself forever.
  - Verified against ALEX v01's largest real run (33 variants,
    md-013/`r_InquiryLastNightSleep`): reproducible per seed, differs across
    seeds, differs across relaunches, exactly one variant ever fires.
  - Tests: `RandomisationGroupTest` in `tests/test_coaching_sim.py`. Full
    suite (65 tests) green. Committed on main.

- **Phase C** (`app/coaching_sim.py`, commit `44cbf2f`): a DAILY BASIS
  sender rule registers as due-today, then auto-launches its dialog once
  its send hour arrives, at most once per day. The send hour is a decimal
  hour in `send_hour_variable`, falling back to the "HH:MM" clock/literal.
  A question opened by a sender times out after
  `not_answered_timeout_minutes`.
  - The r-094 bug: the once-per-day key used `$today`, which the coaching
    itself rewrites during DAILY BASIS (r-000/r-001, ending in a literal
    `{#d}` suffix), so the key never matched again. Now keyed on
    `clock["day"]`. r-094 fires at 22:00 on the real ALEX v01 export.
  - Also fixed: `$systemHourOfDay`/`$systemDecimalMinuteOfHour` are now set
    (the real export's names; the old `$systemHour` had 0 uses).
  - **Partial, by design**: on timeout, `does_not_answer_rules` are logged,
    not executed. None of the 18 real senders have any, so there's no
    shape to verify against.
- **Phase D** (commit `06bb7c3`): a sender due while a question is open is
  suppressed and retries on later ticks. Tested, including two senders
  due in the same tick. Written into the plan doc as an explicit
  **unverified assumption** about PMCP behaviour.
- Tests: `SenderRuleTest` (9 tests). Full suite 74 green.

## Fidelity fixes (2026-09-24, mostly checked against the PMCP 6.0 docs)
Docs: https://my.pathmate.app/pmcp-documentation/doc-6-0 (Raul asked every
agent to search there first. I mailed everyone and added a section to
agents/RULES.md, left uncommitted because that file has other agents'
uncommitted edits.)
- `$var{#d}` → dd.mm.yyyy, per the docs (`4bbc195`). ALEX's `$today` is correct now.
- `$participantParticipationInDays`: day index, still reads the previous
  day during the 00:00 DAILY run. **Assumption chosen by Raul**, needs
  checking against a real participant snapshot (`98e19f0`).
- `$systemMinuteOfHour`, `$systemDayInWeek`, `$participantOpenQuestions`
  are now set, as documented (`98e19f0`).
- Result: with `$onboardingDone=1` and a patient's times set, ALEX v01
  senders launch once a day. That gate is correct behaviour, not a bug.

## Walker fixes from Smith's acceptance walk (`6d3719e`, per the PMCP docs)
- Answer options are `label:value`. They were parsed the other way round.
- A decision point now runs every rule top to bottom. It used to stop at
  the first TRUE one, so later stop/assignment rules were ignored.
- A cascade returns to the calling dialog.
- ALEX md-049's Yes path is correct now. The No path needs the
  per-rule jump-to-message targets. **Engine side done** (commit after
  6d3719e: reads `branches[].jumpMessageIfTrue/False`, verified on md-049
  with an injected target). **Warden owns the exporter side**, and its
  live run is on hold behind the coaching-lock question
  (see warden/STATUS.md).

## ACQ walk findings (Smith, 2026-09-24)
- Q1, fixed (`59e80ec`): the `open-component:questionnaire ID:Title`
  button is documented (Questionnaires §7.1). It's now one blocking
  option. Its results come via PMCMS bindings, which aren't exported, so
  the user sets `$acq_*` by hand.
- Q2, fixed (`2749c6f`) and **verified on the regenerated 0917
  `_jumps.json`** (which now carries depth): md-054#037 nests 0>1>2, the
  ACQ leg gives q7=2 and score 1.14 with no spurious reschedule. Smith
  re-walks it in the browser.
- Q3: the send-hour fallback to `sendHourClock` when the variable is -99
  is my inference, not documented.

## Still open
- `$participantDeactivatedOpenQuestions` (undocumented) is unset. It's
  used in 7 dialogs' node conditions.
- `{#D}`, `{#t}`, `{#T}`, `{%…}` modifiers aren't implemented (ALEX v01
  doesn't use them).
- r-089/099/100/102 have empty `microDialogPath`s in the export (an
  exporter or content issue, not the engine).

## Coordinating (not blocking)
- Released my waterbot browser slot (2026-09-24). The investigation
  isn't scoped, so I asked Warden to do the fresh full ALEX export
  instead. Re-request it if that investigation becomes a real task.
- Mailed Smith to open the Chat-tab-interface conversation (clock UI,
  mid-sim variable edits, tab gating) ahead of Phase E - answered, no
  changes needed on my side (see `context/`).
- **2026-09-23: replied to Kart** on the model-source decision Smith/Kart
  flagged (TASKS.md, under Phase A) - see `context/` for what I told them:
  short version, Phase A already resolved this for Chat by *not* touching
  `load_model()`'s dispatch at all.

- **Phase E engine surface** (commit `4b223e5`, agreed split with Smith):
  `state["engine"]`, `pending["timeout_at"]`, structured transcript
  `event`s, `state["settings"]["auto_periodic"]` + a `set_setting` action.
  Bundle simulations now seed vars from the export's configured variable
  values (this fixed `$currentDaySlot=night` at 09:00). Smith owns the
  routes/UI side.

## ID rule (Raul, 2026-09-24)
`md-…`, node and rule uids are positions within ONE export, never stable
names. In this file they refer to the 0917 ALEX export. Examples: md-049 =
".../Prompt patient to take first dose of controller medication (v02)",
md-054 = "Prompt patient to answer questions of the ACQ". The engine now
exposes `dialog_menu_path` on events and `state["model_fingerprint"]`
(`17e1e6e`); Smith is told to guard saved chats with it.

## Reference data (2026-09-24)
Best current bundle: `data/exports/coaching_alex-v01-zum-ausprobieren_20260917-174650_jumps.json`.
It's complete (1037 nodes, coherence ok) and enriched with jump targets.
The 0918 export is a PARTIAL sweep (md-060 to md-089 failed), so don't use
it for full runs. Both have the pre-09-19 one-line md-049 options (`Yes:1
No:0`), so patch them or wait for a fresh export (on hold behind the
coaching-lock question). Engine check on 0917: senders launch 8/7/1 over
8 days, no warnings.

## Next
- **Stage 4 Phases A–F all done** (Phase F seam `87e5e11`, engine-only per
  Kart). Remaining: workstream 5's behavioural model (no owner).
- docs/coaching_categories_table.md: all 6 agents said yes to deleting it.
  Waiting for Raul to confirm before I delete.
- Background: fresh ALEX export queued after Loom (Warden).
