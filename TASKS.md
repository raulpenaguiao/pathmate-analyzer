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
