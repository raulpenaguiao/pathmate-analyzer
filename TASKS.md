# Tasks

The original task list, kept in the user's own wording and grouped the way
they grouped it. Status updated as work lands. For the dependency-ordered
game plan and full detail on each item, see `README.md`'s "Roadmap: five
workstreams" section — this file is the checklist, that's the writeup.

## ▶ Raul's decisions + today's priorities (2026-09-25)

**Standing rule: no writes to the live pathmate tool** until Raul sets up
a new test workbench coaching (and an export of it). Until then, the
current coaching is used only for testing tools. The live-write queue is
dropped: Mason's spirometry Yes/No fix and Loom's Stage3 write.

Due today:
- [ ] **Clean export**, with a log that has zero errors (Warden, **top
      priority**).
- [ ] **r_ steps 0-3 rerun** (Loom): export .json → r_ table → LLM
      requests → run the prompt. Step 4 (apply) is **test only**. Output:
      the CSV for Raul's advisor. Needs Raul's API key.
- [ ] **r_ tool explainer artifact** for the advisor (Herald, with facts
      from Loom): what the tool creates, the CSV columns, current status,
      and the ro-RO duplicate flag.
- [ ] **Chat test with Raul** on a locally running portal (Smith). This
      unblocks workstream 5. **Ready:** the demo portal is at
      http://localhost:8010 (throwaway `DATA_DIR`, 0925 export attached);
      Smith re-ran the walks there with 0 errors.
- [x] **Commit round + push.** Everyone committed; Loom pushed `b35d0a1`,
      and Kart pushed the rest. `main` = origin as of 09-25 ~10:15.

Also queued:
- [ ] **One Question at a Time**: a detailed flow walk-through plus
      implementation steps, with the scope questions inside it for Raul
      (Herald owns the artifact, Mason supplies the design; tighter
      Raul↔Mason loop).
- [ ] **ro-RO duplicate wording**: it's in the **existing v01 content**,
      not LLM output. "within reach" and "nearby" are both "Este
      spirometrul la îndemână?", and "handy" is near-identical (md-020
      #011/#014/#016). Flag it for the advisor, and add a no-duplicates
      check to the expand prompt and output (Loom).
- Owners set by Raul:
  - workstream 5 → **Mirror**, blocked until Raul has tested the chat
  - "what info to collect" → **Mirror**. **First pass done 09-25**:
    `docs/participant_data_collection.md`.
    - PMCP already timestamps every variable write, so collecting data
      means writing variables at the right moment.
    - Biggest gap: all 18 senders time out, but none has a "does not
      answer" branch, so ignored prompts leave no trace.
    - Also ranked: response latency, deferral counts, 31 unstored
      answers, which variant was shown, and engagement stages.
    - It maps each gap to the workstream 5 patient-model field it
      would let us estimate.
    - **4 open questions for Raul** in the doc, including privacy limits
      and who builds it (probably Mason, since it's live content).
  - questionnaire `multiSubmit` → **Warden**, blocked until we have
    access to the real ALEX coaching

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
      3-with-a-bad-key → poll-to-finish → downloads → 404 guards).
      **Browser QA done 2026-09-23 (Smith):** steps 1-2 run in headless
      Chromium on a throwaway instance, with zero console or HTTP errors.
      Step 3 (the LLM call) was only checked for gating, because a real
      run needs Raul and an API key, so that part is still open.

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
- [ ] **Re-tag the 2 r_ pools the v02 rebuild dropped (added 2026-09-23).**
      Owner: **Loom** (found by Mason in Phase 3.4). In the dialog *Prompt
      patient to conduct daily spirometry / Prompt patient to conduct daily
      spirometry (v02)*, `r_PromptForSpirometry_Stage1_Push` and `_Stage3`
      lost their live `r_` tags when the dialog was rebuilt. (`r_PostponeSpirometry` was
      retired on purpose in Phase 3.5, so it doesn't need re-tagging.)
      - [x] `r_PromptForSpirometry_Stage1_Push` — re-tagged and checked
            live (Loom).
      - [ ] `r_PromptForSpirometry_Stage3` — **2 of 6 wordings live and
            verified (2026-09-25)**, checked from Warden's fresh export
            `..._20260925-093313.json`: rows 3-4 are "handy" and "within
            reach", with no duplicates. Loom fixed the duplicate-check bug
            (it matched on the first 18 characters of en-GB, so sibling
            wordings collided) with an exact match, tested offline.
            **Needs Raul's OK** to add the last 4 ("close by", "with you",
            "access to", "nearby"). This comes after Mason's spirometry
            Yes/No fix in Warden's browser queue. **Content flag for
            Raul:** "within reach" and "nearby" have identical ro-RO text.
            History: partly written, live state unverified (2026-09-24
            ~13:40). The session drops were a
            plain expiry, not a lock. The run did two things:
            - tagged the canonical row
            - added "Is your spirometer within reach?"
            The rest of its output contradicts itself. The duplicate check
            probably matched on the identical ro-RO text, and one variant
            reported "popup never opened". Loom writes nothing more until
            the rows are read back, either live or from Warden's fresh
            export. Loom will then propose a fix to Raul. **Needs Raul**:
            he rejected Loom's live read-only check, so the check has to
            come from somewhere else. Loom also fixed two
            `rgroup_apply.py` bugs: the widen order and `PMCP_WIDE`.
      - Downstream: once Stage3 is live, Herald removes the "1 pool
        untagged" caveat from the *One Question at a Time* artifact (v4).

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
      - [x] **2a — done 2026-09-14.** Findings doc:
            `docs/pileup_findings_ALEX_v01.md`. Done as a data-driven read of
            a fresh `export_coaching.sh` capture (a faithful machine reading
            of the same live tree) rather than eyeballing the UI by hand,
            using Stage 4 Phase 0's now-structured rule expressions.
      - [x] **2b — done 2026-09-14, same doc.** Cross-checked tree order,
            gate chains, and timeouts across all 21 sending rules. Headline
            finding: only the already-redesigned spirometry rule (r-113,
            this session's Phase 3) guards against pile-up at all — it
            checks `$participantOpenQuestions==0` before firing; none of
            the 8 other DAILY-BASIS reminder senders (medication ×3,
            sleep-prep, ACQ, educational content, weekly incentive,
            poor-compliance feedback) have any equivalent guard, and DAILY
            BASIS evaluates every sibling regardless of earlier results (no
            sender sets the stop-the-run checkbox) — so any participant
            whose preference times/due-dates line up is structurally
            exposed to the exact pile-up pattern Phase 3 just fixed for
            spirometry. Directly informs Phase 4's scope (also flags 2
            senders — weekly incentive, poor-compliance feedback — not in
            the current 4.1-4.6 breakdown). Separately found what looks
            like a real existing bug, unrelated to pile-up: the dose-2
            medication reminder (`r-063`) is nested as a Rules-tree CHILD
            of the dose-3 reminder (`r-062`), so (AND semantics) dose 2
            can only ever fire for a participant who's also set a dose-3
            time — likely an accidental mis-drop in v01, not a design
            choice. No live edits made this pass (diagnostic only, per
            2a/2b's own scope); both findings feed Phase 4.1's medication
            redesign.

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
      - [x] **3.1 — Test the "clears dialog cascade" checkbox** — done
            2026-09-11, see
            `autochanges/2026-09-11-alex-v02-phase3.1-cascade-checkbox.md`.
            Mechanical round-trip confirmed: toggled on `👋 Hello` row 1 (a
            safe, non-reminder message), saved, reopened, persisted; reverted
            cleanly. **Correction to Phase 0's assumption**: all the cascade/
            behavior checkboxes sit directly in the outer message-editor form
            once "Show additional settings" is expanded — no nested sub-
            editor needed, at least for a plain (non-answer-expecting)
            message row. Two sibling checkboxes (`answer can be cancelled`,
            `blocks the micro dialog`) were disabled on this row, likely
            gated on "expects to be answered" — **re-check that gating on an
            actual decision-point row in 3.4**, don't assume it carries over.
            Runtime semantics (does it really delete-not-reactivate on
            interrupt) still can't be verified without a live participant
            run — not pursued further; the docs site didn't surface
            corroborating language on the 4 pages checked.
      - [x] **3.2 — Rewrite the DAILY BASIS reset rule** for spirometry —
            done 2026-09-11, see
            `autochanges/2026-09-11-alex-v02-phase3.2-daily-basis-spirometry.md`.
            12 new rules added to the existing "🔄 Reset variables" block:
            simple `$spiroReminderStage`/`$spiroReminderEngaged` → 0 resets,
            a 4-gate cascade computing "end of the slot containing
            `$spiroMesTime`" into `$spiroWindowEnd` (same technique as the
            day-slot rule, keyed on `$spiroMesTime` instead of
            `$systemHourOfDay`), and a final min-clip gate applying
            `$spiroMesTime + $hyperparameterSpiroGraceMinutes/60`.
            `$spiroMesDone`'s existing reset needed no change. **Correction**:
            `Duplicate` appends to the end of the parent's full children
            list, not "immediately after the source" as the day-slot log
            implied (that session's source rows always happened to already
            be last). The `New`-nesting bug is frequent — 4 of 5 nesting
            attempts here landed as a stray top-level section on the first
            try. Division syntax (`/60`) in a Rule[x] expression is accepted
            and persists, unconfirmed whether it *evaluates* correctly
            (no live participant run available).
      - [x] **3.3 — Rewrite the PERIODIC BASIS firing rule** for spirometry —
            done 2026-09-11, see
            `autochanges/2026-09-11-alex-v02-phase3.3-periodic-firing-rule.md`.
            A 5-level AND-gate chain (`$spiroMesDone==0` → `$timeDecimal>=
            $spiroMesTime` → `$timeDecimal<$spiroWindowEnd` →
            `$spiroReminderStage==0` → `$participantOpenQuestions==0`) with
            two condition-free children under the innermost gate: the sender
            (Start micro dialog = the spirometry reminder, Hour to send
            message = `$spiroMesTime`, 4h default timeout unchanged) and
            `$spiroReminderStage=1`. **Read PMCP's own documentation before
            building this one** (per explicit user instruction) — confirmed
            nesting=AND/siblings=OR, division-in-expressions, and found the
            real system variables `$participantOpenQuestions` /
            `$participantOpenDialogCascades` (the latter corroborates 3.1's
            cascade-checkbox finding: a "cascade" is PMCP's own dialog
            return-stack). Used `$participantOpenQuestions==0` as a stricter-
            than-spec but safe approximation of "no dialog open with
            effective tier ≥ P1" (no tier-aware system variable exists).
            Spec's second IF-block (window-expiry) is deliberately **not**
            a separate rule — deferred to 3.4's message-level timeout
            configuration, per the spec's own text and Phase 1's fixed-
            preset-only limitation. Session expired mid-task (Vaadin
            timeout, unrelated to the write tooling) — no work lost, all
            already-committed rules confirmed intact after re-auth.
      - [x] **3.4 — Rebuild the spirometry micro dialog** — done
            2026-09-12, see
            `autochanges/2026-09-12-alex-v02-phase3.4-dialog-rebuild-complete.md`.
            Built as a **new** dialog "Prompt patient to conduct daily
            spirometry (v02)" (nested under the original — `New Dialog`
            always nests under whatever's selected) rather than editing the
            37-row original in place, since its decision-point branching
            wasn't safe to trace and prune blind. 10 rows total, matching
            spec §3.3 almost 1:1. Original 37-row dialog confirmed untouched
            throughout. Found several **general Micro Dialogs mechanics**
            (not spirometry-specific, will matter for Phase 4): bilingual
            text needs the language-tab switcher, not a combined string;
            cascade-clear is mutually exclusive with both "ONLY a push
            notification" and "expects to be answered" (only a message's
            *entry point* can carry cascade-clear); a decision-point rule's
            editor is a separate stacked window with 3 jump-target fields
            (message-level, other-dialog-level, cascade-level); the outer
            decision-point form has 3 "Edit" buttons and only the 3rd opens
            the selected node's own rule (the other 2 are unrelated fields);
            `New` is unreliable for nesting here too (same as the Rules tab)
            — `Duplicate` is reliable for siblings. Two Vaadin session
            expirations happened mid-task; no work was lost either time
            (`.env` has no login credentials — this project's workflow is,
            and always has been, manual login only, not a bug).
      - [x] **3.5 — Decommission the old spirometry bookkeeping** — done
            2026-09-12, see
            `autochanges/2026-09-12-alex-v02-phase3.5-3.6-cutover-and-sweep.md`.
            Deleted 20 rules total: the old PERIODIC "postponed reminder"
            chain (5, cascade-deleted from its root), an already-inert
            Attic-gated duplicate of that chain (3, used as the safe canary
            to confirm Rules-tab delete cascades rather than promotes —
            opposite of the Micro-Dialogs dialog-delete behavior from Phase
            2), the old **DAILY BASIS** primary sender (`🌬️ Send regular
            reminder for spirometry measurement` — not previously
            identified; this, not the PERIODIC retry chain, was v01's actual
            daily trigger) plus its inert test-content sibling (2), the old
            "ask if still want reminded" reschedule chain (3, cascaded), and
            the 6 retired-variable resets (7 rows, one variable had a
            pre-existing duplicate reset). Then repointed 3.3's sender
            rule's `Micro dialog to start` from the original dialog to the
            new one — listed as a **path** in the picker since the new
            dialog is nested under the original (`"...spirometry > ...
            spirometry (v02)"`), found via the same pagination search used
            elsewhere. `sendHourVariable`/actions/timeout confirmed
            untouched by the edit.
      - [x] **3.6 — Sanity sweep** — done 2026-09-12, same log as 3.5. 129
            total rule nodes (149 → 129, exact match for 20 deletions), zero
            stray top-level nodes, zero remaining references to any retired
            variable name, original 37-row dialog confirmed still 37 rows,
            new dialog confirmed still 10 rows, 0 open modals.
      - [x] **3.7 — Export verification** — done 2026-09-12, took 4 attempts
            (runs 1-3 crashed on pre-existing Vaadin "element is not enabled"
            flakiness in `_rules_nav.py`'s `close_windows()` and
            `open_rule_modal()`, neither of which had retry protection —
            both fixed this phase, see autochanges log). Run 4 succeeded:
            `data/exports/coaching_ALEX_v01_phase3-verify_20260912-133202.json`,
            run time 8m 58s (dialogs 456s, rules 83s). Confirmed in the
            output: `$currentDaySlot` and `$spiroReminderEngaged` present via
            `$name` references; `$currentDaySlot` rule nested correctly under
            `PERIODIC BASIS` with all 4 day-slot branches; the
            `Fire spirometry reminder (P2 time-out question, ALEX v02 spec
            3.2/3.3)` sending rule captured; the new dialog `Prompt patient
            to conduct daily spirometry (v02)` present with 10 nodes under
            the right folder. Coherence check flagged drift vs. baseline
            (microDialogs/nodes/rules counts) — expected, since the baseline
            predates this session's edits and the known per-run popup-hover
            scrape gaps (documented pre-existing flakiness, not a regression).
      - [ ] **3.8 — Interrupt Contract retrofit (added 2026-09-21).** 3.1-3.7
            shipped spirometry's guard as a flat "wait for everything" gate
            (`participantOpenQuestions==0` only). The Interrupt Contract
            (https://claude.ai/code/artifact/08cda0cf-aa0d-4b21-9441-a178bd7b61b2)
            has since replaced that with a ranked ladder — spirometry is
            rank 4 (lowest of the insistent tier, ~180min grace, existing
            default) and needs the `activeDialogRank`-aware interrupt gate,
            not just the soft check it has today. Owner: **Mason** (already
            briefed on the Interrupt Contract in his starter mail).
            **Update 2026-09-23:** under the spec §2.0 ladder, spirometry is
            now **rank 1**. The interrupt model is also moving to
            restart-with-resume-line plus expiry. Expect this item to be
            rescoped once Mason's spec rewrite lands.
- [ ] **Phase 4 — propagate the pattern.** Spec §4-5, each mirrors 3.2-3.4's
      pattern for a different feature.
      **Design-level order (Mason, 2026-09-25, `docs/pileup/rollout.md`;
      the spec now lives in `docs/pileup/`, and the old spec path is a
      stub pointing there):**
      0. three platform tests
      1. spirometry/medication interrupt retrofit (3.8 / 4.1.8)
      2. sleep-prep, including the smartwatch battery prompt (4.2)
      3. ACQ + compliance coaching (4.3 + the new compliance item)
      4. ranks 3–6: sleep quality, education/health literacy,
         gamification, misc (4.4, 4.5 + new items)
      5. a full check, including a starvation test (Phase 5)
      The 4.x numbering below is kept for history. Follow the order above.
      Whether ranks 3–6 are in scope for v02 still needs Raul.
      - [ ] **4.1 — Medication reminders ×3 doses** (parametrized
            variables/rules/dialog). Spec §4. Recon done 2026-09-14 (no
            live writes yet): each dose today is a plain `start_micro_dialog`
            sender (`r-058`/`r-062`/`r-063`) with an empty own condition
            beyond the timing gate, no `doesAnswerRules`/`doesNotAnswerRules`
            at the rule level — all escalation/retry logic lives inside
            each dose's own 39-row dialog (`Prompt patient to take Nth dose
            of controller medication`), same shape spirometry had
            pre-redesign. `$hyperparameterMedicationGraceMinutes` doesn't
            exist yet. Reuses Phase 3's day-slot infrastructure
            (`$currentDaySlot` etc.) directly — that was built shared, not
            spirometry-specific. Breakdown, mirroring 3.1-3.7:
            - [x] **4.1.1 — Variables** — done 2026-09-14. All 13 created and
                  value-verified live (347 total = 334 + 13):
                  `$hyperparameterMedicationGraceMinutes=180`, and per dose
                  `i∈{1,2,3}`: `$myMedication_windowEnd_i=0`,
                  `$myMedication_done_i=0`, `$myMedication_reminderStage_i=0`,
                  `$myMedication_engaged_i=0`, all `=0`. Reused existing
                  `$userSetDesired{First,Second,Third}DoseOf...Time` as
                  `doseTime_i` — not recreated. Hit and recovered from a
                  real incident along the way: `create_variables.py`'s
                  `create_one()` had zero retry protection on its clicks
                  (unlike the already-hardened `_rules_nav.py` helpers) and
                  crashed mid-run on the same "element is not enabled"
                  Vaadin flakiness class documented repeatedly this
                  project, leaving a stray "Enter name for variable:" popup
                  open. Recovering from that popup (a direct JS `.click()`
                  on Cancel, bypassing Playwright's actionability wait)
                  **desynced the Vaadin client/server session** — the DOM
                  looked completely normal afterward but the Variables
                  table's server round-trip silently stopped completing
                  (`.v-loading-indicator` stuck visible forever, content
                  frozen regardless of scroll position, no error shown) —
                  a new variant of the already-documented "session looks
                  fine but RPCs are dropped" pattern. A full browser
                  restart (kill the CDP Chrome process, rerun
                  `start_pmcp.sh`) was needed to clear it — a same-process
                  page reload alone logged the session out instead of
                  fixing it. Hardened `create_one()`'s clicks with the same
                  retry pattern as `_rules_nav.py` (`_click_retry()`); the
                  retried run then completed cleanly with no crash. Also
                  swapped `create_variables.py`'s own `all_variable_names()`
                  from its original jump-to-bottom sweep (confirmed buggy
                  2026-09-12) to the fixed incremental one in
                  `_variables_nav.py`, and moved `create_one()`'s
                  post-create confirmation from a full ~2min re-sweep to a
                  fast targeted `scroll_table_to_row()` check (the former
                  would have made a 13-variable run take ~26 minutes just
                  in confirmation steps).
            - [x] **4.1.2 — DAILY BASIS reset rule(s)** — done 2026-09-15,
                  all 3 doses. Per dose: `done_i`/`reminderStage_i`/
                  `engaged_i` reset to 0; `windowEnd_i` computed via the
                  same boundary-cascade + min-clip pattern as 3.2
                  (4 day-slot boundary gates + 1 min-clip gate, each with a
                  nested assignment child), reusing the shared day-slot
                  hyperparameters unchanged. 13 rules/dose × 3 = 39 new
                  rules, all built via `Duplicate` off spirometry's
                  equivalents (top-level siblings) + `New` (nested
                  children), then field-edited. **Verified byte-for-byte
                  correct for every one of the 39 rules** (exact caption
                  match, not just structural spot-checks) — final rule-tree
                  node count 164 = 125 (before) + 39 (new), exact match, no
                  strays anywhere.

                  Ran into and resolved several real platform/tooling
                  issues along the way (all fixed in `_rules_nav.py`,
                  reusable for 4.1.3+ and every later Phase-4 area):
                  - **Confirmed `Duplicate` copies only the single row, not
                    nested children** — building a gate's own child always
                    needs a separate `New`.
                  - **Coaching edit-lock**: killing the browser mid-session
                    without clicking "Back to List" left the coaching
                    locked server-side, blocking re-entry entirely for a
                    period (no force-unlock control found; it did clear on
                    its own after a wait). Documented in
                    `pmcp-portal-and-randomisation-groups.md` memory —
                    likely the real explanation for this *and* the previous
                    day's "session looks fine but every round-trip silently
                    stops completing" incidents.
                  - **Found and fixed the real cause of that "hardened
                    click still hangs" pattern in `_rules_nav.py` itself**:
                    `_open_field_popup`/`_fill_and_ok` (used by every
                    `set_rule_*` field setter) had never had retry
                    protection, unlike `close_windows`/`open_rule_modal` —
                    now hardened with the same `_click_retry` pattern.
                  - **New platform mechanic found: the comparison/assign
                    OPERATOR is a separate control from Rule[x]/Term[y]** —
                    a directly-clickable `.v-filterselect` in the outer
                    form, not one of the 4 Edit-button popups. An
                    EXISTING rule (e.g. one made via `Duplicate`) already
                    has the right operator and never needs it touched; a
                    brand-new rule (via `New`) starts on PMCP's own default
                    (`"calculated value equals"`, confirmed live) and must
                    have it set explicitly, or the rule silently means
                    something else (`--- calculated value equals ---`, no
                    real comparison). Added `_rules_nav.py::set_rule_
                    operator()`, which also found and works around a real
                    flakiness: the click can report success while the
                    selection silently doesn't take — confirmed this
                    happened on effectively every nested-child creation
                    this session (all 10 boundary/min-clip children across
                    doses 2-3 needed the built-in retry-and-verify to
                    self-correct); the helper now always re-reads the
                    dropdown's displayed text after selecting and retries
                    once if it doesn't match.
                  - One exact duplicate child (two identical "evening
                    boundary" rows under dose 1's evening gate, from an
                    earlier recovery step creating a second copy) found
                    only by the final byte-for-byte verification pass and
                    deleted — a good reminder that verifying by depth/
                    structure alone isn't enough; always verify content
                    too and always re-check the final state fresh rather
                    than trusting an in-progress step's own "success"
                    report.

                  Full session narrative:
                  `autochanges/2026-09-15-phase4.1.2-medication-daily-reset.md`.
            - [x] **4.1.3 — PERIODIC BASIS firing rule(s)** — done
                  2026-09-16, all 3 doses. Per dose, gate chain mirrors 3.3
                  exactly **plus the guard 2a/2b found missing everywhere
                  except spirometry**: `done_i==0` AND
                  `timeDecimal>=doseTime_i` AND `timeDecimal<windowEnd_i`
                  AND `reminderStage_i==0` AND
                  **`participantOpenQuestions==0`** → fire (start the
                  dose's existing micro dialog, `notAnsweredTimeoutMinutes`
                  = 240), set `reminderStage_i=1`. 7 rules/dose × 3 = 21
                  rules, gates built via `New` chained one inside the next
                  (Gate 1 only via `Duplicate` off spirometry's own Gate 1,
                  the sole step `Duplicate` can help with). **Verified
                  byte-for-byte correct for all 3 doses' full chains**
                  (exact gate captions, sender `actions`/
                  `microDialogPath`/`sendHourVariable`/
                  `notAnsweredTimeoutMinutes`, leaf caption) via
                  `final_verify_all_periodic.py`-style re-reads, not just
                  structural spot-checks.

                  Spanned two sessions and several real incidents, all
                  fixed in `_rules_nav.py`/process (reusable for 4.1.4+):
                  - **Confirmed `_rules_nav.py::set_rule_hour_variable()`
                    was fundamentally broken** (matched the wrong DOM
                    target, always returned `False`) — rewrote it to match
                    the proven filterselect pattern used for the operator
                    and micro-dialog pickers, and found it ALSO needed
                    pagination (334 variables, 10/page) like the micro-
                    dialog picker (which lists every dialog/folder,
                    "A > B" path strings, also paginated). Added
                    `set_rule_micro_dialog()` for the latter.
                  - Hit the same "clicks don't register anywhere" failure
                    class twice more this phase. The first time (session
                    end), it did **not** clear via two automated restarts,
                    only via the user manually opening a brand-new browser
                    window — automated restarts reusing the same throwaway
                    Chrome profile/relaunch mechanism were not equivalent.
                    The second time (session resume), automated restarts
                    also failed at first — **root cause found this time**:
                    repeated `start_pmcp.sh` invocations against an
                    already-listening CDP browser open a **second PMCP tab
                    in the same browser** instead of reusing/replacing the
                    first one, and the two logged-in tabs fight over the
                    server's apparent single-session-per-account state,
                    producing exactly this symptom (plus spurious
                    logouts and coaching-lock churn) even in a freshly
                    launched browser. Fix: check `len(context.pages)` and
                    close every extra tab before doing anything else. Worth
                    hardening `start_pmcp.sh`/nav helpers to always enforce
                    a single tab going forward.
                  - **Coaching edit-lock recurred multiple times** (see
                    4.1.2 and `pmcp-portal-and-randomisation-groups.md`) —
                    every kill of the CDP browser without "Back to List"
                    first (forced during the above incidents) re-locked
                    the coaching under the automation account
                    (`alex-dev-2` from `.env` — not a mystery third party).
                    Clear time was inconsistent, from ~2 minutes up to the
                    ~15-20 minutes seen in the earlier incident; no
                    force-unlock control exists, so waiting it out (with a
                    polling loop) is the only option.
                  - A stuck "Edit comment:" popup left over from a
                    mid-edit browser kill produced **one stray, blank-
                    comment duplicate of dose 3's Gate 2** (right field
                    values, no comment — so it didn't match the cleanup
                    helper's comment-substring search and survived
                    silently as an extra sibling) — found only by the
                    final byte-for-byte verification pass and deleted.
                    Same lesson as 4.1.2: always re-verify final state
                    fresh rather than trusting an in-progress step's own
                    "success" report.
                  - A fresh page load starts the Rules tree **collapsed**;
                    every build script now calls `expand_all()` right
                    after `ensure_rules_tree()` instead of assuming
                    whatever expand state a previous long-lived session
                    left behind.

                  Full session narrative:
                  `autochanges/2026-09-16-phase4.1.3-medication-periodic-firing.md`.
            - [x] **4.1.4 — Rebuild each dose's dialog** — done
                  2026-09-16, all 3 doses. (~5 items per spec:
                  reminder (idle) → "did you take it?" (sets `engaged_i=1`)
                  → confirmation (resets `engaged_i=0`, sets `done_i=1`) →
                  thanks / timeout fallback). 3 separate dialogs (build dose
                  1 first as the template, like 3.4 did for spirometry).
                  Dose 1's template dialog built and byte-for-byte
                  verified; doses 2-3 built via `Duplicate Dialog` +
                  per-dose field edits (`_1`→`_2`/`_3` throughout),
                  each independently byte-for-byte verified via a
                  genuine fresh re-navigation (see below for why that
                  distinction matters on this tab). New
                  dialog "Prompt patient to take first dose of controller
                  medication (v02)", nested under the original (`New
                  Dialog` always nests, confirmed again). 8 rows (fewer
                  than spirometry's 10 since spec explicitly drops the
                  CLAID handoff/retry-loop for medication): reminder
                  (push+cascade-clear, reused v01 wording) → Yes/No
                  question (new `$myMedication_confirmAnswer_1` reply
                  variable, `-99` no-reply sentinel, mirroring
                  `$mySpiro_spirometerWithinReach`'s exact pattern since
                  no existing v01 variable fit a direct self-report
                  question) → decision point (`!= -99` gate branch +
                  unconditional `engaged_1=1` assign branch) → decision
                  point (single branch, `==1` condition, jumps to the
                  Thanks/No-problem messages by TRUE/FALSE) → Thanks
                  message → decision point (`done_1=1` branch +
                  `engaged_1=0`+stop branch) → No-problem message →
                  decision point (`engaged_1=0`+stop branch). Original
                  39-row dialog confirmed untouched throughout (byte- and
                  row-count-verified after every work session this phase).

                  Found several new Micro Dialogs platform mechanics this
                  phase (on top of 3.4's, all apply to doses 2-3 too):
                  - **Row selection needs cell index 0** (the TYPE icon
                    cell) — cell index 1 (COMMENT) immediately
                    *deselects* the row instead of selecting it, a new
                    trap not covered by 3.4's notes.
                  - **The row-toolbar "Edit" button is a different
                    element from the dialog's own 4 field-level "Edit"
                    buttons** (Comment/Identifier/Variable Prefix/
                    Assigned Units) — a `.first` grab silently opens the
                    *dialog's* comment editor instead of the *row's*, with
                    no error. Find it by position (below the `.v-table`)
                    instead.
                  - **A decision point's branches are a FLAT sibling list,
                    not a nested tree** (confirmed via the JSON export's
                    raw `branches` array), despite using `.v-tree` DOM
                    markup for the list. Each branch is either a pure
                    condition gate or an unconditional assignment
                    (`Rule[x]="1"`/`"0"`, operator="calculate value but
                    result is always true", Store-result-variable=target)
                    — the same two leaf shapes as the Rules tab.
                  - **Navigating into a dialog nested under a folder needs
                    a HOVER on the parent row to reveal the Vaadin
                    MenuBar submenu, not a click** — clicking the parent
                    navigates straight into the parent's own dialog
                    instead of revealing children. A `.first.click()` on
                    the child dialog's own text otherwise silently
                    lands the write on the WRONG dialog (confirmed live:
                    lost 20+ minutes to a stray message row built inside
                    the folder's own row list before finding this).
                  - **A decision point branch's own Comment field can leak
                    into the PARENT decision point's top-level Comment
                    field** — confirmed reproducible twice: setting a
                    fresh branch's comment via its "Create rule:" popup
                    sometimes silently also (or instead) overwrites the
                    enclosing decision point's own comment, and the
                    branch's own comment then reads back unset. No
                    reliable trigger condition found; the fix is
                    mechanical, not preventive: after closing a branch,
                    always re-check the decision point's own top-level
                    comment before closing it too, and re-set it if it
                    was clobbered.
                  - **A brand-new branch can silently fail to persist at
                    all**, even though every field read back correct
                    immediately after building it (found twice, both
                    times on the *second* branch added to a decision
                    point) — only caught by leaving the dialog entirely
                    and navigating back in fresh. **Always do a genuine
                    fresh re-navigation (not just re-reading the
                    in-memory DOM) as the final verification step for any
                    decision point with more than one branch** — an
                    in-session re-read is not sufficient proof of a
                    server-side commit here.
                  - Every "Create rule:"/"Edit rule:" popup opened from
                    inside a decision point is a further-stacked
                    `.v-window` on top of the decision point's own window
                    (matches 3.4's finding) — `_rules_nav.set_rule_
                    operator()`'s `.v-window.first` targeting hangs here;
                    needed a `.last`-targeting variant. Also confirmed
                    this specific filterselect's `innerText` reads back
                    **empty even on a fully successful selection**
                    (screenshot-verified) — unlike the Rules tab's own
                    operator filterselect, so don't treat an empty
                    read-back as failure here.
                  - Read-after-write checks on this tab are noticeably
                    slower/racier than the Rules tab's — a `.v-window`
                    count or row count read immediately after a
                    navigation click can catch a stale/partial state that
                    resolves correctly half a second later. Add a longer
                    settle wait before trusting a "not found"/wrong-count
                    result as real.

                  **`Duplicate Dialog` confirmed to deep-copy all 8 rows
                  correctly** — used it to create "Prompt patient to take
                  second/third dose of controller medication (v02)" as
                  full copies of dose 1's dialog (via `Duplicate Dialog`
                  + `Rename Dialog`; the two are indistinguishable by name
                  until renamed, needed a throwaway Identifier-field
                  marker to tell which list entry was the fresh copy).
                  Both then field-edited (`_1`→`_2`/`_3` throughout: row1
                  result var, row2 condition+assignment, row3 condition,
                  row5/row7 assignment targets) and independently
                  verified via a genuine fresh re-navigation — all field
                  edits landed correctly on the first attempt for both
                  doses (no repeat of dose 1's branch-persistence issue
                  this time), and both doses' row3 jump targets
                  (message-level, set automatically by `Duplicate
                  Dialog` since it copies internal references, not by
                  name) were re-confirmed still correctly pointing at
                  each dose's own Thanks/No-problem messages after the
                  comment edits. Dose 1's dialog and both original 39-row
                  v01 dialogs confirmed unaffected throughout.
            - [x] **4.1.5 — Decommission old bookkeeping** — done
                  2026-09-17. Repointed the 3 new PERIODIC senders (built
                  in 4.1.3) at their new `(v02)` dialogs (built in 4.1.4)
                  — each `Micro dialog to start` field updated via
                  `set_rule_micro_dialog()`, independently re-verified by
                  reopening each rule and reading its filterselect value
                  fresh (the helper's own internal verification reported
                  `False` for all 3 due to the same innerText-unreliable
                  pattern documented elsewhere on this control, but every
                  independent re-check confirmed the change had actually
                  landed). Then deleted 8 obsolete rules, confirmed clean
                  via a genuine fresh re-navigation afterward:
                  - **3 old "ask if still want reminded" reschedule
                    chains** (`Check whether $my{First,Second,Third}
                    Medication_userRequestedNewTime=1`, each cascading
                    away its own reset + "Rescheduled reminder..." leaf,
                    9 nodes total) — the pre-redesign equivalent of the
                    mechanism spec 3.2 explicitly replaces with "the
                    existing USER INTENTION mechanism... updates the time
                    variable directly", already removed for spirometry in
                    3.5. Not explicitly named in this task's original
                    text but the same principle applies 1:1 to
                    medication's 3 per-dose copies — found via a broad
                    "dose" caption search while confirming the sender/
                    variable cleanup below, and removed to match.
                  - **The 2 old pre-4.1.3 PERIODIC senders** ("Send
                    regular reminder for first/third of the day
                    controller medication inhalation") — deleting the
                    "third dose" one cascaded away dose 2's sender too
                    (it was the mis-nested child, exactly the 2a/2b bug),
                    so this single delete both retired the old firing
                    mechanism and resolved the mis-nesting in one action
                    — confirmed via the pre-delete parent/child dump that
                    dose 2's old sender had no other function beyond
                    firing its own now-superseded reminder.
                  - **3 old bookkeeping-variable resets** — 2 duplicate
                    `Reset $medicationNumberOfRegularRemindersIssued to
                    0` rules (a pre-existing v01 duplicate-bug, unrelated
                    to this redesign, cleaned up as a side effect of
                    retiring the variable) + 1
                    `Reset $myMedication_NumberOfInhalationsOfTheDayCompleted
                    to 0`.

                  Final state confirmed via fresh re-navigation: zero
                  remaining references anywhere in the Rules tree to any
                  of the 6 retired identifiers above, all 3 new PERIODIC
                  senders still present and correctly pointed at their
                  `(v02)` dialogs, node count 171 (185 after 4.1.3 minus
                  the 15 nodes removed here — one off due to a counting
                  quirk in root-vs-subtree totals, not a discrepancy in
                  actual content). This bulk-delete needed the user's
                  explicit go-ahead in chat plus a `/permissions` grant —
                  the auto-mode classifier blocks multi-rule Rules-tab
                  deletions even after verbal confirmation.
            - [x] **4.1.6 — Sanity sweep** (mirror 3.6) — done 2026-09-17.
                  9 legitimate top-level root nodes confirmed, no strays
                  (onboarding-check, daily-basis-marker, day-start-delay,
                  daily-rules-gate + 4 USER INTENTION branches + the
                  `$today` setter). Zero remaining references anywhere to
                  any of the 6 identifiers retired in 4.1.5. All 3
                  original 39-row v01 dialogs confirmed still intact (37
                  rows visible per dialog, matching the known
                  virtualization gap). All 3 new `(v02)` dialogs confirmed
                  still exactly 8 rows each. 0 open modals.
            - [x] **4.1.7 — Export verification** (mirror 3.7) — done
                  2026-09-17, took 3 attempts (runs 1-2 failed before
                  even starting the sweep — a leftover "Edit rule:" modal
                  from earlier repointing work was blocking the whole
                  page with a modality curtain, closing it let run 3
                  through). Run 3:
                  `data/exports/coaching_alex-v01-zum-ausprobieren_phase4.1-verify.json`,
                  run time 6m 31s. Rules and Variables sections both swept
                  cleanly and are the ones that matter for this phase's
                  own content — confirmed in the output: 171 rule-tree
                  nodes (exact match to the live count from 4.1.6), all 3
                  new PERIODIC senders present (`Fire medication dose
                  {1,2,3} reminder...`), **zero** remaining references
                  anywhere to any of the 6 retired 4.1.5 identifiers, and
                  all 16 variables added this phase present (13 from
                  4.1.1 + the 3 `confirmAnswer_i` from 4.1.4).

                  The Micro Dialogs sweep itself hit a **pre-existing,
                  unrelated tool bug** in `_menu_nav.py::open_folder_path`
                  — past roughly the 20th of 90 menu targets it started
                  raising `RuntimeError("top '...' not found")` for
                  almost everything remaining (including all 3 new
                  medication `(v02)` dialogs and the 3 original 39-row
                  ones), driving the coherence check's ~70% node-count
                  "drift" — not a regression, just this run's share of
                  the tool's own known scrape gaps (same category
                  documented in 3.7's log). Root cause not fully chased
                  down (worth a dedicated look before the next phase
                  leans on this export for dialog-content verification)
                  but plausibly a window-width reset partway through the
                  sweep collapsing the widened menubar back under a `►`
                  overflow. Not a blocker here since this phase's dialog
                  content was already independently verified byte-for-
                  byte via live DOM checks (fresh re-navigations, not
                  just in-session reads) in 4.1.4 and 4.1.6, which this
                  export's own successful Rules/Variables data
                  corroborates rather than needing to duplicate.
            - [ ] **4.1.8 — Interrupt Contract retrofit (added 2026-09-21).**
                  4.1.1-4.1.7 shipped all 3 medication doses under the same
                  old flat gate as spirometry's pre-3.8 state
                  (`participantOpenQuestions==0` only, no rank awareness).
                  The Interrupt Contract ranks medication 3 (~120min grace,
                  proposed default, not yet confirmed by the manager) —
                  needs the same `activeDialogRank` retrofit as 3.8, for all
                  3 doses. Owner: **Mason**. **Update 2026-09-23:** under the
                  spec §2.0 ladder, medication is now **rank 1**, alongside
                  spirometry and nighttime monitoring. The interrupt model
                  is also changing from delete to restart-with-resume-line
                  plus expiry (Decision 1, under Hierarchy). Mason expects
                  3.8 and this item to be rescoped once his spec rewrite
                  lands.
      - [ ] **4.2 — Sleep-prep / nighttime monitoring.**
      - [ ] **4.3 — ACQ administration** (**rank 2** in the spec §2.0
            ladder, set 2026-09-23; it was "P1" under the old tiers). It
            creates reminders, which is the dual-mode exception in spec
            2.2a.
      - [ ] **4.4 — Educational-content nudges** (**rank 4**; was "P1").
            It creates reminders. Its stub dialog is empty and has to be
            built first.
      - [ ] **4.5 — Health-literacy prompt** (was "P2"; now **rank 4**,
            grouped with education, per Mason 2026-09-25).
      - [ ] **Categories with no Phase 4 item yet (found 2026-09-23 by
            Mason, when the §2.0 ladder was set).** Owner: **Mason**
            (redesign scope). None of these has been phased yet:
            - compliance coaching (**rank 2**). Its only rule starts an
              empty dialog, so it has no working trigger.
            - sleep quality inquiry (**rank 3**). No working trigger.
            - gamification (**rank 5**). It fires with no guard.
            - misc: FAQ, air quality, clinic visits (**rank 6**). No
              working trigger.
            Where there's no working trigger, the job is to **build a
            rule**, not just add a guard. Source: spec §2.0. **Scope
            growth**: this adds up to 4 new phase-sized items, so Raul
            should confirm which of them are in scope for v02.
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

## Further tasks

Captured 2026-09-18 in the Progress Tree from a live variable audit plus one
outstanding item from Simone's email; pushed here 2026-09-21 per the
manager's mail. Owners assigned where the fit is clear; two items flagged
below still need a manager decision before anyone picks them up.

- [ ] **Dead-variable cleanup.** Owner: **Mason** (touches variables in his
      own Phase 4.2-4.6 territory — sleep-prep outcomes, education,
      compliance feedback — so natural to fold in as he rebuilds those
      dialogs rather than as a separate pass; confirm with Kart if that
      doesn't hold once he's in the detail). Set somewhere, never read back
      anywhere in the whole coaching — candidates for deletion, or in a
      few cases for finally wiring up logic that looks like it was meant to
      consult them:
      - `$needMedicalHelp` — check this one first.
      - `$needForCatharsis`, `$needGeneralAssistance` — same pattern,
        likely the same well-being check-in flow (`Offer assistance`/
        `Coaching` dialogs).
      - `$displayOfSpirometryOutcomes`,
        `$displayOfNighttimeMonitoringOutcomes` — look like flags meant
        to gate an outcomes/feedback dialog that never actually checks them.
      - `$newTimeForHealthLiteracyQuiz`,
        `$newTimeForDisplayingOutcomeOfSpirometry`,
        `$newTimeForDisplayingOutcomeOfSleepMonitoring`,
        `$timeToSendSleepMonitoringDialog` — same reschedule-flag shape
        as the already-documented ACQ/education reschedule flags, but never
        read back.
      - `$needSupportMaterialOnCompliance`,
        `$needSupportMaterialOnMedicationAdherence`,
        `$needSupportMaterialOnHowAshtmaControllerMedicationWorks` —
        consistent with the compliance-feedback stubs already documented in
        `ALEX_v01_design_spec.md` §11; the "send support material" logic
        that should check these doesn't seem to exist.
      - `$coach` — captures `$participantIntentionContent` once, never
        read again; possibly intentional metadata capture, not a bug.
      - `$participantTimeZone` — hardcoded to the literal string
        `Europe/Bucharest`, never derived from the participant's actual
        locale, never referenced by any time-of-day math elsewhere.
        **Flag for the v02 redesign specifically**: if `$systemHourOfDay`
        and friends run on server time rather than participant-local time,
        the day-slot/window design (spec §2.3) needs to confirm it's
        computing against the right timezone before it ships.
      - `$readinessForSpirometry` — set to 99, never read; the live one
        actually in use is `$mySpiro_readinessForSpirometry`.
- [ ] **Rename `$userSetBedTime` / `$userSetBedtime` for clarity.** Owner:
      **Mason** (bedtime is sleep-prep territory, Phase 4.2). Two variables
      one capitalization apart, easy to confuse mid-edit. Proposed:
      `userSetBedTime` → *stated bed time* (what the participant typed),
      `userSetBedtime` → *our implied bed time* (what the coaching
      actually computes/uses).
- [ ] **Hierarchy — refine The Interrupt Contract's priority ladder with
      real scheduling constraints, not just rank order.** Owner: **Mason**
      — already flagged in his own starter mail as needing a manager
      conversation before Phase 4.2 locks in the ranked-ladder rebuild. The
      three proposed grace values (60/90/120 min) in the Interrupt Contract
      are placeholders, not confirmed numbers — get sign-off before
      they're built into live rules, not after. See also the 2026-09-21
      3.8/4.1.8 follow-up items above/below — spirometry and medication
      both shipped as fully soft and need to move onto the ladder too.
      - [x] **Decision 1 (Raul, 2026-09-23): an interrupted dialog has an
            expiry, not a restart cap.** It can be restarted, with a resume
            line, until it expires. Spirometry and medication expire at end
            of day. Educational content and gamification expire at end of
            week. Recorded in Mason's STATUS.md; the spec hasn't been
            rewritten yet.
      - [ ] Still open with Raul (Mason is waiting on these before any
            spec rewrite): (a) the scope question; (b) which expiry bucket
            sleep-prep, low-compliance feedback and ACQ go in; (c) whether
            end of day *replaces* the grace-minute windows
            (`$spiroWindowEnd`, `$myMedication_windowEnd_i`) or only sets
            the resume cutoff. The answer to (c) decides whether the
            60/90/120 min grace sign-off below is still needed. Note that
            "end of week" for educational content conflicts with the
            "reprompt after 1 day" line below; reconcile them when (b) is
            settled.
      - [ ] Top-3 (spirometry, medication, night-time monitoring) only
            interruptible by end of day — nothing below them in the
            ladder can pre-empt them at all; only the day boundary
            (midnight) can close them out, not a lower-priority reminder
            waiting its turn.
      - [ ] Sequence spirometry before medication, or ≥5h after — plan
            the day intelligently rather than just by rank; if that's not
            achievable, surface a pop-up saying medication isn't advised
            right now because spirometry is coming up in a couple of hours.
      - [ ] ACQ and educational content persist over days, reprompt after 1
            day — neither is top-priority, but both should survive being
            deprioritized for a day rather than being dropped.
- [ ] **What info to collect — open design question, no owner yet.** We
      should be collecting a lot more into structured variables to actually
      know what's going on with a participant over time, not just enough to
      fire the next reminder. Needs a first pass at what's actually useful
      to capture before it's anyone's task to build. **Flagging for the
      manager per Kart's scope** (challenge unclear tasks rather than guess
      an owner): this isn't scoped enough yet to assign — no stated goal
      beyond "collect more" — and it plausibly feeds workstream 5's
      Markov-chain patient simulation (Mirror's Stage-4 engine is its
      eventual consumer), which may want to shape the scoping before this
      is handed to anyone.
- [ ] **Set questionnaire `multiSubmit` to false — no clear owner yet.**
      Should restrict a participant to a single submission per
      questionnaire. Documented somewhere already per Simone's email, but
      not actually implemented — needs to be found and set. **Flagging
      for the manager**: this is a PMCP questionnaire-config setting, not
      clearly inside any current agent's declared scope (not the r_
      pipeline, not the Rules/Dialogs/Variables tabs the redesign touches,
      not the Flask portal) — needs a decision on who picks it up, and
      whether it needs Warden's navigation tooling to find/set via
      automation or is just a one-off manual portal click.
- [ ] **Which model backs the read-only analysis tabs (Rules/Dialogs/
      Variables/Statistics) — added 2026-09-23, Smith's own call.** Found
      while scoping a portal visual-nav feature: `coaching_view` never
      calls `parse_bundle()`, so these tabs are 100% HTML-sourced today
      regardless of a bundle being attached — some data (e.g.
      `Rule.micro_dialog_path`, rule→dialog routing) only ever exists via
      the bundle path and isn't in the HTML export at all. Switching would
      surface that, but `parse_bundle`-derived models have empty
      `message_groups` (the known Stage-3 gap,
      `test_message_groups_are_empty_stage3_gap`) — a real regression to
      the Rules tab's "Message Groups" section for every bundle-attached
      coaching today, not a pure addition. **Confirmed 2026-09-23 (Mirror)
      this is unrelated to Stage 4's own Phase A-F** — Chat's
      `load_bundle_model()` is a separate entry point Mirror built on
      purpose to avoid exactly this fork; nothing about Phases A-F needs
      the analysis tabs on bundle data. So this is purely Smith's own
      tradeoff to make (or defer indefinitely), not a cross-agent blocker —
      options: fix the Message Groups gap first, accept it and switch
      anyway, or leave HTML as the source of truth for these tabs for good.

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

- [x] **Add a Variables-tab sweep to `export_coaching.py`** — done 2026-09-12
      (ALEX v02 Phase 3.7 follow-up). Previously neither the export tool nor
      the analyzer's own "Variables" tab read PMCP's actual Variables tab —
      both only inferred variable existence from `$name` references inside
      captured rule/dialog text, so a variable that exists but isn't
      referenced anywhere yet (a real risk right after a variable-creation
      pass, before the rules that use it are built) was invisible, and even
      a referenced variable's current value was never captured. New module
      `tools/coaching-bundle-export/_variables_nav.py`, wired in as phase 2
      (dialogs=1, variables=2, enrich=3, rules=4, coherence=5; new
      `--no-variables` flag). Found and fixed a real sweep-correctness bug
      along the way: a jump-straight-to-bottom scroll sweep of the
      virtualized/paginated Variables table looked converged (stable
      scrollHeight + row count) but silently captured only ~84 of the
      coaching's actual 334 variables (~25%) — including missing
      `$currentDaySlot`/`$spiroReminderEngaged`/etc. entirely. Fixed with an
      incremental per-viewport scroll instead of one big jump: 334/334,
      reproducibly. Verified live:
      `data/exports/coaching_ALEX_v01_phase3.7b-variables-verify_20260912-182148.json`
      has all 334 variables with full metadata (value/privacy/access/auto-
      sync/multilingual/sensitive-data columns), confirmed `$currentDaySlot`
      = `"morning"` and `$spiroReminderEngaged` = `"0"`. Run time 11m 25s
      (dialogs 451s, variables 113s, rules 122s). Along the way also
      hardened `_rules_nav.py::close_windows()` again — the "element is not
      enabled" Vaadin flakiness fixed in 3.7 recurred and this time
      exhausted all 4 retries; it no longer raises on that, falling back to
      Escape + a wider outer retry (6→10) instead, only failing loud if a
      modal is genuinely still stuck after every attempt. See autochanges
      log for full detail.

- [x] **Portal Raw tab didn't display the attached `coaching.json`** — done
      2026-09-14. Root cause: the Raw tab's iframe/download link only ever
      pointed at `coaching_raw` (the HTML file) — there was never a route
      or template element for the bundle at all, so attaching a
      `coaching.json` had literally no effect on that tab. Added
      `GET /coachings/<id>/bundle/raw` (serves the file with
      `application/json`) and `GET /coachings/<id>/bundle/download`
      (`app/routes.py`); the Raw tab now shows a small "HTML export /
      coaching.json" toggle (only when a bundle is attached — no bundle,
      no change from before) switching between two iframes/download links,
      wired in `app/static/coaching_tabs.js` following the existing
      tab-activation pattern, styled in `app/static/style.css`. Verified
      live against a spare portal instance (a second `wsgi.py` on :8001,
      to avoid touching the user's own running :8000 instance mid-test):
      view page renders the toggle, `bundle/raw` returns real JSON with the
      right content-type, `bundle/download` serves it as `coaching.json`.
      48/48 tests still pass.

- [x] **Regenerate `coherence_baseline.json`** — done 2026-09-14, from the
      user's fresh `data/exports/coaching_alex-v01-zum-ausprobieren_20260914-094837.json`
      + `~/Downloads/Coaching_ALEX_v01_zum_Ausprobieren.html`. The old
      baseline (2026-09-10) predated Phase 2's dialog prune (2026-09-11) and
      all of Phase 3, so every metric was flagged as "drift" against a
      pre-project snapshot — none of it was real data loss; cross-checked
      the 20 supposedly-"missing" dialogs against the fresh HTML export and
      every one's node count matched exactly (they're `isFolder: true`
      container dialogs that also carry real content — the `microDialogs`
      metric excludes them by definition, a separate pre-existing quirk, not
      a bug in this pass). New baseline also carries `variablesTotal: 334`.

- [x] **`sweep_table()` over-read bug — fixed 2026-09-14.** Original
      hypothesis (stale `scrollHeight` carried over from the immediately-
      preceding, much-larger PARENT dialog) turned out to be **wrong**: the
      real target list shows the dialog immediately BEFORE `"...Quit
      spirometry dialog after successful spirometry procedure"` in the
      actual sweep order is `"Medical Feedback lung function"` (only 6
      rows, not the 51-row parent), and a live isolated repro of
      parent→child (including a full `sweep_table()` scroll-through of the
      parent first, to faithfully match the real sequence) did NOT
      reproduce the bug — resolved cleanly to `total=7` every time,
      matching the HTML export. Cross-checking against **yesterday's**
      export (`...phase3.7b-variables-verify_20260912-182148.json`) showed
      the SAME dialog, SAME index, SAME preceding items, correctly swept as
      7 rows that day — so this is a genuine **intermittent** Vaadin timing
      race (present in 1 of 2 otherwise-identical runs), not a
      deterministic trigger tied to dialog size or order. Given it isn't
      reliably reproducible on demand, fixed the SYMPTOM instead of the
      unconfirmed root cause: `sweep_table()` (`_menu_nav.py`) now trims any
      TRAILING run of fully-blank captured rows (`_trim_trailing_blanks()`)
      before returning `total` — a genuine PMCP row always has content in
      at least one column, so a wholly-blank row is never real. Verified
      against the actual bad data from today's export (51 → 15, exactly the
      36 blank rows removed) and against 3 normal dialogs (no trailing
      blanks → untouched, no regression). Live re-sweep of the same dialog
      right now: `total=7`, matching HTML. `coherence_baseline.json`'s
      `note2`/excluded-delta note is now stale and can be removed on the
      next `--update-baseline` run (left as-is for now — harmless, and
      documents the investigation).

- [x] **Auto-fetch the Report HTML inside `export_coaching`** — done
      2026-09-14. New phase 0 (`_report_fetch.py`) clicks "Report" on the
      Coachings list and grabs the result — no more manual save +
      `--report FILE`. The tricky part: clicking "Report" does **not**
      navigate or open a popup (confirmed live — `context.expect_page()`
      times out, `context.pages` never grows); it triggers a native Chrome
      **file download**, invisible to normal Playwright page/popup
      tracking. Needed `Page.setDownloadBehavior` +
      `Browser.setDownloadBehavior` via CDP pointed at a directory this
      script controls, before the click. `--report FILE` still works
      (skips the fetch); `--no-report` skips it entirely. Verified live
      end-to-end: fetched file matched the reference file's exact byte
      size (1,215,736 bytes), and a full export run successfully used the
      auto-fetched HTML for phase 3 enrich (`"enriched 72 dialogs, 15
      empty, 0 unresolved (of 87)"`) with no manual step at all.

- [x] **`export_coaching.sh` also builds the r_ report/tables** — done
      2026-09-14. New `--with-rgroups` flag: after a successful export,
      runs `tools/rgroups-table/rgroup_report.py OUT.json --md` against
      the run's own output (parses JSON, no browser) — one run now gives
      `coaching.json` *and* an up-to-date `rgroups_table.csv` +
      `rgroups_report.md`, without the rest of `rgroup_pipeline.sh` (LLM
      expansion / write-back). Implemented as a flag on the `.sh` wrapper
      (not `.py`) since it's pure post-processing orchestration — parses
      the export's own `wrote <path>` log line rather than needing the
      python side to expose it, and skips with a clear warning (not a
      crash) if that line can't be found.

- [ ] **Later: a UI-structure self-check that fails loudly on drift** (per
      the user, 2026-09-12). Every navigation/write helper in this project
      (`_menu_nav.py`, `_rules_nav.py`, and the message/decision-point
      helpers built in Phase 3.4) assumes a specific DOM shape **by
      position** — "the 3rd Edit button opens the selected rule", "this
      form has exactly N filterselects in this order", "New nests a child /
      Duplicate creates a sibling". None of these assumptions are verified
      before acting on them today. When PMCP's DOM doesn't match, the
      failure mode ranges from a generic Playwright timeout to something
      worse: a **wrong but successful** action (this session hit both —
      editing the decision point's own comment instead of the selected
      rule, by clicking `.first` instead of the 3rd "Edit"; a rule landing
      at the wrong tree depth with no error at all) that can only be caught
      by manual re-verification after the fact.
      Idea: add a lightweight assertion layer — before acting on a
      structural assumption, assert it explicitly (e.g. "exactly 8 Edit
      buttons expected, found N", "filterselect[2] should show a dialog
      path or be disabled") and raise a clear, **named** error identifying
      *which* assumption broke, instead of proceeding on stale positional
      indices or surfacing a generic timeout. Rationale: Pathmate is far
      more likely to change UI layout/labels/ordering than to change PMCP's
      underlying data model (rule tree, decision points, variables,
      dialog/message structure) — so write the code's assumptions about
      that **stable architecture** explicitly, and treat any UI-shape
      mismatch as a loud, specific, adapt-the-workflow signal rather than a
      silent wrong click or a from-scratch debugging session. Would also
      double as living documentation of what each helper actually assumes.

      **Fresh concrete example (2026-09-14), same failure class**: found
      live while verifying the auto-fetch/rgroups changes above.
      `_rules_nav.py::click_expander()` catches ANY exception from
      `select_node()`/the ArrowRight expand gesture and returns `False` —
      which `expand_all()` then unconditionally records as "this is a
      leaf" (`leaves += 1`), permanently excluding that node (and
      everything under it) from the tree for the rest of the run. Hit a
      bad flakiness patch this session where dozens of expand attempts
      timed out in a row (cause not identified — possibly session
      degradation from a long CDP-attached session with heavy use
      earlier that day); the run silently "succeeded" with only 58 of the
      coaching's ~125 real rules captured (46%) and all 8 sender modals
      then failing too (stale tree indices). **Only caught because the
      coherence check compares against a baseline** (`ruleTreeNodes: 58
      now vs baseline 125 (down 54%)`, `sendingRules: 0 now vs baseline 21
      (down 100%)`, exit code 1) — without that safety net this would have
      silently written a badly truncated `coaching.json` with exit code 0.
      This is exactly the "wrong but successful, no error" pattern the
      idea above targets, and a good minimal FIRST application if this
      item gets picked up: `click_expander` should distinguish "confirmed
      not expandable" from "timed out, unknown" and retry/report the
      latter distinctly rather than silently counting it as a leaf.

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

- [x] **Surface the export/coaching.json coherence check in the portal**
      — done 2026-09-23 (Smith, portal-side only — not a live PMCP
      session, no autochanges/ entry). The phase-4 coherence check built
      into `export_coaching.py` (sweep vs Report HTML vs
      `coherence_baseline.json`) was already computed and stored
      (`app/storage.py`'s `_bundle_summary` → `coherenceOk`/
      `coherenceWarnings`) but only ever rendered once, buried in the
      Statistics tab — invisible unless you went looking. Added a loud
      page-level banner (any tab, not just Statistics) when an attached
      `coaching.json`'s coherence check failed, linking to the existing
      Statistics-tab detail, plus a "⚠ export/JSON mismatch" badge next
      to the coaching's name on the `/coachings` list so drift is visible
      without opening the coaching at all. Template/CSS/JS surfacing only,
      no new backend logic. Verified: full suite still green (60/60,
      untouched by this change) plus a throwaway Flask test-client smoke
      check (banner+badge fire on `coherenceOk:false`, silent on
      `coherenceOk:true` and on no-bundle coachings). **Uncommitted in the
      working tree** as of this entry — see Smith's own STATUS.md for
      the file-level detail.

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

- [x] **To start:** need one real `coaching.json` from a live
      `export_coaching.sh` run (the blocker). **Unblocked 2026-09-12** — several
      live exports now on disk in `data/exports/` (Phase 3.7 + the Variables-
      tab follow-up), including a 334-variable one.
- [x] **Phase 0** — exporter parses `ruleTree` captions → structured exprs.
      Done 2026-09-13/14 (offline, no live browser needed — see autochanges
      log). New shared module `app/rule_grammar.py` (`parse_expr`, phrase
      constants, and the new `parse_rule_caption()` for the Rules-tree's
      combined "comment: expr" captions) — `app/coaching_sim.py` refactored
      to import from it instead of duplicating the phrase list, per the
      plan's own instruction to keep them in sync. `_rules_nav.py::
      build_rule_tree()` now adds an `expr` field to every `ruleTree` node.
      **Acceptance confirmed** against the live 2026-09-12 export: all 125
      real `ruleTree` nodes get a `kind`; exactly the 4 genuine JS-snippet
      rules land as `unsupported`, nothing else does; 15 rules spot-checked
      against the HTML parser's `Rule.comment`/`raw_expr` fields (via
      `tests/fixtures/coaching_ALEX_v01.html`), 15/15 correct. **Not done
      yet** (needs the live browser, deferred to avoid clashing with a
      concurrent live session): regenerating
      `tools/coaching-bundle-export/rules_stage3_ALEX_v01.json` and bumping
      `coherence_baseline.json` — do this on the next live export run.
- [x] **Phase A** — done, commit `695b490` ("Stage 4 Phase A: parse_bundle()
      - coaching.json -> CoachingModel"). **Correction to this item's own
      original wording, per Mirror 2026-09-23**: deviated from the plan
      doc's assumption on purpose — `load_model()`'s own dispatch (HTML vs
      bundle) was never touched, and still isn't; `parse_bundle()` is
      reachable only through a new, separate entry point,
      `load_bundle_model(coaching_id)`, that only the (not-yet-wired) Chat
      engine calls. `coaching_view`'s read-only analysis tabs
      (Rules/Dialogs/Variables/Statistics) still go through
      `load_model()`→`parse_model()` untouched — nothing about them
      changed by this phase. See "Which model backs the analysis tabs" in
      Further tasks above for the separate, non-blocking question Smith
      raised about *those* tabs — it doesn't touch Phase A/B-F at all.
- [x] **Phase B** — done, commit `31d92ea` ("Stage 4 Phase B:
      randomisation-group collapsing in the dialog walker"), seeded per
      plan.
- [x] **Phase C** — sender rule → auto-launch its `microDialogPath`;
      not-answered timeout → run `doesNotAnswerRules`. Done, commit
      `44cbf2f` (2026-09-23). A sender fires at most once per day. The
      sleep-monitoring sender bug is fixed: the once-per-day key used
      `$today`, which the coaching rewrites itself. `doesNotAnswerRules` are only logged on
      timeout, not run, because no real sender has any.
- [x] **Phase D** — interruption (skip a sender while `pending` is set).
      Done, commit `06bb7c3`. A sender that comes due while a question is
      open is suppressed and retries on a later tick. This is an
      **unverified assumption** about PMCP's behaviour, recorded as one in
      `docs/stage4_chat_engine_plan.md`. 74 tests pass.
- [x] **`{#d}` date-format suffix (found 2026-09-23, Mirror).** Done,
      commit `4bbc195`: implemented as the documented `dd.mm.yyyy`
      modifier, per the PMCP 6.0 docs.
- [x] **Phase E** — Chat tab wired to `parse_bundle`; gate on `.json`
      present; surface rule→dialog, timeout countdown, not-answered events.
      **Done 2026-09-24.** The browser acceptance walks pass on the
      jump-enriched 0917 ALEX export and match hand-traces:
      - medication v02 dialog, Yes and No paths
      - ACQ reminder → answers → questionnaire → correct score → the
        next daily run advancing `$dateOfNextACQ`
      Engine side (Mirror) is committed, `4b223e5` → `efc238a`. Engine
      fixes made along the way, all checked against the PMCP 6.0 docs:
      - answer options are label:value
      - decision rules run as a tree (child = AND)
      - per-rule jump-to-message targets
      - cascades return to the calling dialog
      - questionnaire buttons
      - `$participantParticipationInDays` and 3 system variables are
        simulated
      - sims start from the export's variable defaults
      Portal side (Smith) is **uncommitted, waiting on Raul's
      go-ahead**. It includes the stale-chat guard: a saved chat is
      refused if it doesn't match the attached export's model
      fingerprint.
      - [ ] Verify the assumed semantics of
            `$participantParticipationInDays` (Raul chose them) against a
            real participant snapshot. Flagged in the plan doc.
      - [ ] Re-walk on a **fresh, complete ALEX export**. The 0918 export
            fails its own coherence check and predates the 09-19
            medication-options fix. Warden's fresh export is **queued**
            for the browser right after Loom's Stage3 run. Until then,
            Raul says the 0917 export is fine for testing.
- [x] **Jump-to-message targets in the export (Warden, 2026-09-24).**
      They were already in the Report HTML, just unparsed.
      `enrich_bundle.py` resolves 22 of the 36 on ALEX v01; the other 14
      are ambiguous from the text alone and are listed as candidates.
      Exporter commit `0686367`; more exporter and enrich changes are
      still in the working tree, waiting on Raul's go-ahead.
      - [ ] Optional: a small live pass to settle the 14 ambiguous
            targets. It fits into Warden's browser time.
- [x] **Phase F (design only)** — `PatientModel.respond()` seam for
      workstream 5. **Done, commit `87e5e11`** (`app/patient_sim.py`, 98
      tests pass). **Decided 2026-09-24 (Kart, delegated by Raul):**
      Mirror builds the **engine-only seam now**:
      - a `PatientModel` protocol
      - a headless `run(model, patient, days)` loop
      - one always-answers test patient
      It has no behavioural logic. How stored patient-model fields turn
      into answers stays open for workstream 5's owner, which is still
      unassigned.

- [ ] Allow tracking and changing variables on the go, and advancing the
      clock. — Already works in the current simulator (`set_var` / `tick` /
      `advance-to-slot` actions); carries over once the engine is
      bundle-driven.
- [ ] Interface the chat simulation with patient models using Markov chains
      (workstream 5). Design in `ALEX_v02_simulator_scope.md` §4–7. Needs
      Stage 4's engine + the phase-F hook as its substrate. `autochanges/` is
      set up (`autochanges/README.md` for the format). **No owner assigned
      in any agent's `AGENT.md` yet.** Surfaced concretely 2026-09-23:
      Smith found the existing Patient Models CRUD (adherence %,
      response-time, sleep window — already built, currently disconnected
      from the Chat tab) is explicitly in Smith's own scope to *wire in*,
      but the behavioral model it needs (how does e.g.
      `adherence_spirometry_pct` actually decide whether/when a simulated
      patient answers a given question?) is workstream 5's own open design
      question, not an implementation detail — right call not to invent
      it solo. Needs a manager decision on who owns workstream 5's
      behavioural design. Phase F's engine-only seam is going ahead
      without it (2026-09-24), but nothing behavioural can be built on
      top until there's an owner.
