# Tasks

The original task list, kept in the user's own wording and grouped the way
they grouped it. Status updated as work lands. For the dependency-ordered
game plan and full detail on each item, see `README.md`'s "Roadmap: five
workstreams" section — this file is the checklist, that's the writeup.

## r_ task

- [x] Identify all r_ entries and create a .md report with all of these
      instances.
      Done. `docs/randomisation_groups_ALEX_v01.md` (96 groups), backed by
      `tools/rgroups-table/rgroups_table.csv` (per-message detail, both
      languages).
- [ ] Augment these instances with a tool using an LLM API key.
      Split into a 4-step pipeline over a pre-made `coaching.json` (never runs
      the export). Step 1 `rgroup_report.py` → `rgroups_table.csv`; step 2
      `rgroup_prepare.py` → `rgroups_requests.csv` (one row per thin pool = one
      API call); step 3 `rgroup_expand.py --limit N` (required) →
      `rgroups_generated.csv`. ro-RO output constrained: informal *tu*,
      house-style gender agreement, native (non-calque) phrasing, no English
      loanwords. **Sample run done** (PR #1): `--limit 10` → 70 variants for 10
      pools, human-reviewed. Full run (~110 thin pools) still pending.
- [ ] Using Playwright, add these instances to the coaching (write-back tool).
      Step 4 `rgroup_apply.py --limit N` (required) reads
      `rgroups_generated.csv` and applies **every** `ok` variant (no review
      gate) — per variant: Duplicate an existing group message → edit the
      copy's en-GB + ro-RO → Move Up until it is adjacent to the pool (groups
      only fire when consecutive). Dry-run by default; `--apply` / `--pool` /
      `--dedup` / `--debug`. Idempotent. **Verified on the sandbox** (PR #1).
      PMCP-editor automation gotchas in `tools/rgroups-table/README.md`.
      Not yet run at scale or against the production coaching.
- [ ] `rgroup_pipeline.sh --json FILE --limit N` — wraps steps 1→4 with a
      `continue? [y/N]` checkpoint between each. Steps 1–2 tested via the
      wrapper; full chain not yet run against a live CDP session.
- [x] Steps 1–3 in the portal ("Randomisation groups" tab, shown once a
      coaching has a `coaching.json` attached). `app/rgroups_tool.py` imports
      the `tools/rgroups-table` scripts directly (`sys.path`, no subprocess);
      step 3 runs in a background thread with an in-memory, pollable job (per-
      pool progress bar, live pool name/status). The API key is taken from a
      form field per run and never written to disk or the environment — it's
      passed straight into `rgroup_expand.call_llm`, which now accepts an
      `api_key` override. Each step's CSV is downloadable once it's built.
      Step 4 (Playwright write-back) is **not** in the portal — it needs a
      CDP-connected browser the app process doesn't have; still CLI-only.
      Smoke-tested end to end with Flask's test client (attach → step 1 → 2 →
      3-with-a-bad-key → poll-to-finish → downloads → 404 guards). Not yet
      exercised by a human in a real browser.

### After `coaching.json` is regenerated (unblocks the rest)

- [ ] Regenerate `data/exports/coaching.json` with the current export
      (`tools/coaching-bundle-export/export_coaching.py`, via `start_pmcp.sh`).
      The `rgroups_table.csv` in the repo predates the export consolidation.
- [ ] Full expansion run: `rgroup_pipeline.sh --json data/exports/coaching.json
      --limit 110` → ~880 variants for the ~110 thin pools.
- [ ] Human review of that full batch (spot-check `rgroups_generated.csv`; the
      10-pool sample is already reviewed).
- [ ] Run `rgroup_apply.py --apply --limit N` against the **production** ALEX
      v01 coaching (only the sandbox has been written to so far). Start with a
      small `--limit` / `--pool`; watch the Move Up / adjacency result each time.
- [ ] Remove the 2 mechanism-test variants left in the "ALEX v01 zum
      Ausprobieren" sandbox (a greeting in *Timeless Greetings*, a spirometry
      prompt in *Prompt patient to conduct daily spirometry*). `--dedup` does
      not catch them (unique text) — delete by hand.

## Pile-up problem

- [ ] Identify first steps to change in ALEX "zum Ausprobieren" to deal with
      the pile-up problem (messages with priority cutting off other
      messages with less priority).
      **Correction (2026-09-09):** PMCP has no priority/tier field at all —
      confirmed by opening live "Edit micro dialog message:" and "Edit
      rule:" modals. Pile-up is emergent from (1) rule execution order in
      the Rules tab (top-to-bottom, stops the instant a rule "solves the
      issue") and (2) each dialog-starting rule's own send-delay and
      not-answered-timeout. See README.md's "priority-field correction".
      **Replanned 2026-09-09** — split into two passes, since the manual one
      turns out not to need the export:
      - [ ] **2a, do next, unblocked.** Read the live Rules tab's order and
            timeouts for the spirometry/medication/ACQ/education rules by
            hand. Write a findings doc naming specific rules to reorder or
            re-delay. Rules are drag-to-reorder in the same tab, so a finding
            here may be directly actionable, no code required.
      - [ ] **2b, rigorous pass.** Stage 3 bulk data now exists
            (`tools/coaching-bundle-export/rules_stage3_ALEX_v01.json` —
            every sending rule's target dialog, send-hour var and
            not-answered timeout). Still to do: cross-check tree *order*
            against timeouts to name the actual collisions.

### 2c — v02 redesign implementation (2026-09-11)

Goes beyond 2a/2b's reorder-in-place fixes: a full architectural redesign,
spec'd in `docs/ALEX_v02_redesign_spec.md` (imported from personal notes
2026-09-11). Root cause: v01 hand-rebuilds a "reactivate the interrupted
dialog later" pattern (`$participantDeactivatedOpenQuestions` + two
"Transition message..." dialogs) — that resumption *is* the pile-up. Fix:
every reminder becomes a native PMCP time-out question that expires and gets
**deleted**, never reactivated; a 5-tier priority model (P0-P4, our own
abstraction — see the correction note at the top of the spec doc) resolves
collisions via rule order + guard variables, not a PMCP field. Full dialog
classification for all 107 ALEX v01 dialogs is in the spec's Appendix A.

Target: the sandbox coaching "ALEX v01 zum Ausprobieren" only, same as every
other live-portal workstream here. Every live-portal session gets an
`autochanges/` entry per existing convention.

- [x] **Phase 0 — recon (read-only).** Done 2026-09-11, see
      `autochanges/2026-09-11-alex-v02-phase0-recon.md` and spec §6
      (resolved). Summary: the expiry field is
      `Minutes after sending until message is handled as unanswered`
      (per-message, behind "Show additional settings" — distinct from the
      per-rule timeout), "blocking" and "deactivate/recall" are separate
      checkboxes there too, no native fallback-message-on-expiry field
      exists, and whole-dialog delete is the dialog-level toolbar's
      `Delete Dialog` button. One follow-up before Phase 3: confirm what the
      "clears the dialog cascade" checkboxes actually do (untested,
      read-only pass) — try it on one throwaway message first.
- [x] **Phase 1 — build Rules-tab write tooling.** Done 2026-09-11 (recon:
      `autochanges/2026-09-11-alex-v02-phase1-rule-write-recon.md`;
      completion: `autochanges/2026-09-11-alex-v02-phase1-completion.md`).
      - [x] `probe_rule_write.py` — read-only discovery of the 4 popups.
      - [x] Same-value OK-commit test — confirmed on Comment (verified via
            the tree's own caption text); the other 3 popups are
            structurally identical, trusted by analogy.
      - [x] Timeout quick-pick mechanism — **resolved as a real platform
            limitation, not just an unconfirmed detail**: tested
            exhaustively (existing Start-micro-dialog rule, existing
            Send-message rule, a brand-new Create-rule form, after
            checking its action checkbox for the first time, after
            selecting a target dialog, after direct slider interaction) —
            the not-answered-timeout slider/quick-picks stay `v-disabled`
            in every case. `Hour to send message`, by contrast, **is**
            directly settable (a live `$variable` filterselect, once its
            owning action checkbox is checked). Every rule inspected
            defaults to 4h — Phase 3 can rely on that default but cannot
            currently set a custom timeout via automation.
      - [x] Filterselect count reconciled — 4 confirmed identities:
            condition operator, `Message group`, `Micro dialog to start`,
            `Hour to send message` ($variable). `Store rule result to
            variable` is popup-only, not a filterselect.
      - [x] **Coaching-identity safety check** —
            `tools/coaching-bundle-export/_pmcp_safety.py`
            (`assert_expected_coaching()`), retrofitted into
            `rgroup_apply.py --apply`.
      - [x] Write helpers landed in `_rules_nav.py`: `set_rule_comment`,
            `set_rule_condition_x`/`_y`, `set_rule_result_variable`,
            `set_rule_checkbox`, `set_rule_hour_variable`. Live-tested
            (`set_rule_comment`, same-value, verified via tree caption).
            **No timeout-setting function** — deliberately, per the
            limitation above. A `rule_apply.py` CLI wrapper (dry-run/
            `--limit`/`--apply`, mirroring `rgroup_apply.py`) is not yet
            built — write these Python functions directly into Phase 3
            scripts for now rather than blocking on that wrapper.
- [x] **Phase 2 — prune.** Done 2026-09-11, see
      `autochanges/2026-09-11-alex-v02-phase2-prune.md`. Deleted 19 dead
      dialogs in two waves via `tools/coaching-bundle-export/prune_dialogs.py`
      (`--wave2` for the second): the 3 pile-up-mechanism dialogs, the 15
      top-level P4 dev/test dialogs, and 5 more that were promoted to
      top-level rather than cascade-deleted when `Attic`/`⚙️ Controls` were
      removed (**correction: `Delete Dialog` on a folder promotes its
      children, doesn't delete them** — always re-check what a folder
      contains before assuming a delete removes it wholesale).
      **`📄 dataEdited`** (real P3 content, was nested under `Controls`)
      was correctly identified and left alone. 30 top-level dialogs remain.
- [ ] **Phase 3 — spirometry redesign (proof of concept).** Spec §3: new
      variables, rewritten DAILY/PERIODIC BASIS rules, and a ~10-item dialog
      replacing the current 50-item one. Do this one feature fully before
      propagating the pattern — it's the template for Phase 4.
      - [x] **New variables created** — done 2026-09-11, see
            `autochanges/2026-09-11-alex-v02-phase3-variables.md`. All 8
            (day-slot infra §2.3 + spirometry §3.1) created and verified via
            `tools/coaching-bundle-export/create_variables.py`:
            `$currentDaySlot`=morning, `$hyperparameterMorningEndHour`=11,
            `$hyperparameterMiddayEndHour`=17, `$hyperparameterEveningEndHour`=22,
            `$spiroWindowEnd`=0, `$spiroReminderStage`=0,
            `$spiroReminderEngaged`=0, `$hyperparameterSpiroGraceMinutes`=180
            (the last is the spec's own example value; the day-slot hour
            thresholds are reasonable chosen defaults, not spec-mandated —
            tune later). New tool found two more Variables-tab mechanics not
            documented before: it's virtualized *and* server-paginated (needs
            the loading-indicator wait, not a fixed sleep), and selecting a
            row for the toolbar needs a **cell** click, not a row click
            (unlike every other table in this repo so far).
      - [x] **`$currentDaySlot`-computing rule** — done 2026-09-11, see
            `autochanges/2026-09-11-alex-v02-phase3-dayslot-rule.md`. Built
            as 4 sibling gate rules under PERIODIC BASIS's "...already
            performed" branch (one per bucket: evening/midday/morning/night),
            each with one nested child doing the actual `$currentDaySlot`
            assignment — a cascading-overwrite design (widest bucket first,
            narrowest last, so the narrowest true match wins), not a deep
            elif-ladder, since a single rule row can't both compare AND
            store an unrelated literal in one step. **Important finding for
            the remaining rule work**: the Rules tree's `New` toolbar button
            is unreliable for nesting a child under a selected node (silently
            creates a stray top-level section roughly half the time, no
            error) — use `Duplicate` on an existing same-depth rule instead
            (100% reliable this session) for new *siblings*, and always
            verify a `New`-created node's `depth` after committing before
            trusting it. Also: duplicating a rule carries over its "Store
            rule result to variable" field — clear it explicitly via the
            "Edit variable:" popup unless it's actually wanted (caught before
            going live: all 4 gates had silently inherited `→ $timeDecimal`
            from their duplication source).
      - [ ] **3.1 — Test the "clears dialog cascade" checkbox** on one
            throwaway message before relying on it in 3.4. This is the
            delete-not-reactivate lever the whole spec's anti-pile-up
            mechanism assumes (flagged, untested, in the Phase 0 log) — do
            this first, it's cheap and de-risks everything downstream that
            depends on it. No dependency on 3.2/3.3, but must land before 3.4.
      - [ ] **3.2 — Rewrite the DAILY BASIS reset rule** for spirometry (spec
            3.2): `$spiroMesDone`/`$spiroReminderStage`/`$spiroReminderEngaged`
            → 0, `$spiroWindowEnd` computed using `$currentDaySlot` (now
            available from the rule above). Depends on the day-slot rule
            (done).
      - [ ] **3.3 — Rewrite the PERIODIC BASIS firing rule** for spirometry
            (spec 3.2): fires the P2 time-out question, sets `Hour to send
            message`, accepts the 4h not-answered default per Phase 1's
            platform-limitation finding. Depends on 3.2.
      - [ ] **3.4 — Rebuild the spirometry micro dialog** down to ~10 items
            (spec 3.3), replacing the current ~37-row one, wiring in
            whatever 3.1 confirmed about the cascade-clear field. Depends on
            3.1 and 3.3.
      - [ ] **3.5 — Decommission the old spirometry bookkeeping**: delete the
            reset rules for the 5 retired variables (`$spiroMesTimeDelay`,
            `$spiroMesDelayedReminderActive`, `$spiroMesDelayedReminderSent`,
            `$spiroMesNumberOfDelayedRemindersIssued`, `$lastMinuteSpirometry`,
            `$mySpiro_userRequestedNewTimeForSpirometry`) so old and new logic
            don't run side by side. Depends on 3.2.
      - [ ] **3.6 — Sanity sweep + autochanges writeup**: confirm nothing
            orphaned (no rule still referencing a deleted variable), tree
            matches the design. Depends on 3.1-3.5.
- [ ] **Phase 4 — propagate the pattern.** Spec §4-5, each mirrors 3.2-3.4's
      pattern for a different feature:
      - [ ] **4.1 — Medication reminders ×3 doses** (parametrized
            variables/rules/dialog).
      - [ ] **4.2 — Sleep-prep / nighttime monitoring.**
      - [ ] **4.3 — ACQ administration** (P1 priority, but reminder-creating
            — the dual-mode exception in spec 2.2a).
      - [ ] **4.4 — Educational-content nudges** (P1, reminder-creating) —
            its stub dialog has to be built first, it's currently empty.
      - [ ] **4.5 — Health-literacy prompt** (P2, same treatment as
            spirometry).
      - [ ] **4.6 — Build-or-drop the remaining stub dialogs** (8 total per
            spec §5) that existing rules already point at.
- [ ] **Phase 5 — close-out / cross-cutting.**
      - [ ] **5.1 — Decide how to handle the not-answered-timeout
            limitation** for good: accept the 4h default everywhere, do a
            fresh discovery pass, or have a human set custom values by hand
            once. Still unresolved from Phase 1.
      - [ ] **5.2 — Full sweep against spec Appendix A**: confirm every
            dialog got the tier treatment its classification calls for,
            nothing missed.
      - [ ] **5.3 — Mark workstream 2c complete** in README/TASKS; note that
            real behavioral validation still needs the separate Stage-4 chat
            simulator workstream, which doesn't exist yet.

## Coaching export

- [x] Allow Claude to navigate the browser to get an idea what else should
      be exported: send delay, message priority, the "Low Priority"
      placeholder row's semantics, answer→child routing.
      Done, live, 2026-09-09. Findings: **there is no message-priority
      field** — "Low Priority" was one node's literal Comment text, not a
      schema field. Send delay and answer routing exist, but on the
      **rule** that starts a dialog (in its "Edit rule:" modal — send hour,
      not-answered timeout, DOES/DOES-NOT-answer subtrees), not on the
      message itself. Full writeup: `tools/coaching-bundle-export/DESIGN.md`
      → "Not yet captured (Stage 3)".
- [x] Get from Claude all the information an export has, and how it should
      include everything needed to generate a chat interaction.
      Stage 3 captured live 2026-09-10. All the 2026-09-09 open schema
      questions are answered (both action paths; send-hour is a `$variable`;
      4h default timeout; identical field set across sections; the 4
      TRUE-result action checkboxes; DOES/DOES-NOT routing). Data:
      `tools/coaching-bundle-export/rules_stage3_ALEX_v01.json`, writeup
      `docs/rules_stage3_ALEX_v01.md`, DESIGN.md "Stage 3 … CAPTURED".
      Remaining for a fully machine-readable export: parse the `ruleTree`
      captions into structured expressions in the exporter (Stage-4 phase
      0), and handle decision-point-internal quick-reply routing.
- [x] Run the export once.
      Tooling built and consolidated (2026-09-10, on `main`). **One script**
      `tools/coaching-bundle-export/export_coaching.py` → **one file**
      `coaching.json` (`coaching` / `microDialogs` / `nodes` / `rules{
      sections, ruleTree, sendingRules}` / `validation`). `export_bundle.py`
      + `export_rules.py` + `--enrich` + `--merge` + `coaching.bundle*.json`
      / `coaching.rules.json` are all gone. Phase 4 of the script is a
      **coherence check** (sweep vs Report HTML vs `coherence_baseline.json`)
      that exits non-zero on drift — the canary for a PMCP UI change.
      **Still to do:** one live `tools/coaching-bundle-export/export_coaching.sh
      --report … coaching.json` run to produce the real file and confirm
      phases 1–4 pass on live data (the offline reference
      `rules_stage3_ALEX_v01.json` was re-derived, not freshly swept).

- [ ] **Later: auto-fetch the Report HTML inside `export_coaching`.**
      The script is already driving the browser at the coaching — it can
      navigate to Coaching → Report and grab the HTML itself, then use it
      for the phase-2 enrich and phase-4 coherence check. Right now the user
      has to save the Report page by hand and pass `--report FILE`. Goal:
      one run produces **both** `coaching.json` and the `Report.html`
      alongside it, no manual save. (Note: the coherence check is an *input*
      to the same run — sweep vs HTML compared as the JSON is built — not a
      later/standalone pass; a standalone re-check against a saved pair is a
      possible bonus but not required.)

- [ ] **Later: `export_coaching.sh` should also build the r_ report/tables.**
      `rgroup_report.py` renders `rgroups_table.csv` (and, with `--md`, the
      `docs/randomisation_groups_*` summary) straight from `coaching.json` — no
      browser scrape. Wire it into `export_coaching.sh` — or a `--with-rgroups`
      flag — so one run gives `coaching.json` *and* the up-to-date table +
      summary, without the rest of `rgroup_pipeline.sh` (which does the LLM
      expansion and write-back).

- [x] **Export polish (2026-09-10).**
      - Default output name now carries a timestamp:
        `data/exports/coaching_<slug>_<YYYYMMDD-HHMMSS>.json` (slug from the
        coaching name read off the editor header). Explicit `OUT.json` still
        wins; `rgroup_pipeline.sh` passes an explicit path so it's unaffected.
      - Total wall-clock run time + per-phase seconds printed at the end and
        stored in the JSON's `run` block.
      - `bundle.coaching.name` is populated (was `null`).
      - `_widen_for_menubar` now waits for the menubar to render before the
        `►`-overflow check, and doubles the width (to 40000) until it clears
        or aborts with a clear message.

## Simulate chat — Stage 4 (depends on `coaching.json`)

**Full cold-start brief: `docs/stage4_chat_engine_plan.md`** — architecture,
current-code inventory, where `coaching.json` lives (`data/exports/`), phases
0–F with acceptance checks, open questions. Read that first. Summary:

Design (agreed 2026-09-10 with the user): a **pure-function, stateless**
engine driven **only** by `coaching.json` (HTML is a side double-check, never
drives the chat). `advance(coaching, state, to_time)` and
`answer(coaching, state, value)` each return `(state', events[])`. `state` =
`{vars, clock, pending (0 or 1 open question), seed}` — fully serializable,
"recreate the chat from a variable dump + a clock". Upload menu stays
HTML-only; a `.json` is *added* to a coaching to unlock the Chat tab. Rule
expressions are parsed in the **exporter** (phase 0). One dialog / one open
question; a sender firing while a question is pending is **skipped**.

- [ ] **To start:** need one real `coaching.json` from a live
      `export_coaching.sh` run (the blocker). Phases 0–C can begin now against
      a synthetic json stitched from `coaching.bundle.v2.json` +
      `rules_stage3_ALEX_v01.json` (recipe in the plan doc §3).
- [ ] **Phase 0** — exporter parses `ruleTree` captions → structured exprs.
- [ ] **Phase A** — `parse_bundle()` in `app/coaching_model.py` + additive
      dataclass fields; `load_model()` dispatches on `.json` vs `.html`.
- [ ] **Phase B** — r_-group collapsing in the dialog walker (seeded).
- [ ] **Phase C** — sender rule → auto-launch its `microDialogPath`;
      not-answered timeout → run `doesNotAnswerRules`.
- [ ] **Phase D** — interruption (skip a sender while `pending` is set).
- [ ] **Phase E** — Chat tab wired to `parse_bundle`; gate on `.json`
      present; surface rule→dialog, timeout countdown, not-answered events.
- [ ] **Phase F (design only)** — `PatientModel.respond()` seam for
      workstream 5.

- [ ] Allow tracking and changing variables on the go, and advancing the
      clock. — Already works in the current simulator (`set_var` / `tick` /
      `advance-to-slot` actions); carries over once the engine is
      bundle-driven.
- [ ] Interface the chat simulation with patient models using Markov chains
      (workstream 5). Design in `ALEX_v02_simulator_scope.md` §4–7. Needs
      Stage 4's engine + the phase-F hook as its substrate. `autochanges/` is
      set up (`autochanges/README.md` for the format).
