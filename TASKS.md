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
      Tool built (`tools/rgroups-table/expand_rgroups.py`) and dry-run
      tested (110 pools, 882-variant skeleton), but never run for real — no
      `ANTHROPIC_API_KEY`/`OPENAI_API_KEY` set in this environment yet.
      `render_review_report.py` turns its output into a per-pool markdown
      report with checkboxes, for double-checking before anything is used.
      **Needs:** an API key (e.g. in `.env`, gitignored) to actually run it.
- [ ] Using Playwright, add these instances to the coaching (write-back tool).
      Not started. Deliberately deferred until there's a real
      human-approved batch from the step above to design against, and until
      a read-only discovery pass on the node/message *creation* flow (not
      just editing) has been done. This writes to a live coaching, so it
      must default to a human clicking the actual save action — see the
      modal-safety notes in README.md's hurdles section.

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
      Stage 3 captured live 2026-09-10: `tools/coaching-bundle-export/
      probe_rules_tree.py` walks the Rules `.v-tree` and reads every
      sending rule's "Edit rule:" modal. All the 2026-09-09 open schema
      questions are answered (both action paths; send-hour is a `$variable`;
      4h default timeout; identical field set across sections; the 4
      TRUE-result action checkboxes; DOES/DOES-NOT routing). Data:
      `tools/coaching-bundle-export/rules_stage3_ALEX_v01.json`, writeup
      `docs/rules_stage3_ALEX_v01.md`, DESIGN.md "Stage 3 … CAPTURED".
      Remaining: fold this into `coaching.bundle` (a Stage-3 pass of the
      export script) and handle decision-point-internal quick-reply routing.
- [x] Run the export once.
      Rules-tree Stage-3 sweep run against ALEX v01 (122 tree nodes, all
      25 message-sending rules, ~40 no-op re-saves logged). Production
      exporter `export_rules.py` built (shares `_rules_nav.py` with
      `probe_rules_tree.py`): emits `coaching.rules.json` and, with
      `--merge`, `coaching.bundle.v3.json` (v2 bundle + a `rules` key with
      `sections` / `ruleTree` / `sendingRules`). The committed reference
      output `tools/coaching-bundle-export/rules_stage3_ALEX_v01.json` was
      re-derived offline through that same code path from the sweep dumps;
      a fresh `export_rules.py --merge` run reproduces it. Next: a live
      `--merge` run to actually produce `coaching.bundle.v3.json`, then
      Stage 4 (`parse_bundle` in the analyzer).

## Simulate chat (depends on structure of export)

- [ ] Use the export to simulate a chat with the user in the
      pathmate-analyzer web platform, in a specific tab.
      Not started (Stage 4). A Chat tab and tick-based `Simulator` already
      exist, but run off the old Report-HTML parse, not the bundle.
- [ ] Allow tracking and changing variables on the go, and advancing the
      clock.
      Already works in the *existing* (pre-bundle) simulator. Needs
      porting/extending once Stage 4 switches it to bundle-driven content.
- [ ] Interface the chat simulation with patient models using Markov chains,
      and log every Playwright-driven change or exploratory session to a
      folder called `autochanges/`, as markdown files.
      Not started (patient/Markov modeling — design exists in
      `ALEX_v02_simulator_scope.md` §4–7, reframed in README.md's roadmap).
      The `autochanges/` folder itself is set up as of this session — see
      `autochanges/README.md` for the log format, and
      `autochanges/2026-09-09-live-exploration.md` for the first entry
      (today's live PMCP exploration, including the accidental-but-harmless
      rule re-save).
