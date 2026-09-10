# pathmate-analyzer

A web tool for analysing PMCP coaching exports. Upload an HTML export, get statistics, saved versions, and patient-interaction models.

## TL;DR

- `TASKS.md` is the checklist, in the user's own task wording. This file is the writeup — read both.
- Five open workstreams are tracked below, each on its own branch. Workstream 1 (the `r_` groups report) is done.
- Everything else waits on **Stage 3 of the coaching exporter**: pulling rule-level timing data out of the live PMCP editor.
- **Big correction today (2026-09-09):** PMCP has no priority/tier field anywhere. Pile-up behaviour comes from rule execution order and per-rule timeouts, not a P0–P3 system. Our earlier `ALEX_v02_simulator_scope.md` design assumed a tier system that doesn't exist. See "Status" below.
- If you're going to touch the live PMCP portal, read "Navigating the live PMCP portal" first. It has real gotchas that will otherwise cost you time.

## Status (2026-09-09)

Built and on `main`:

- **Tabbed coaching view** (`app/templates/coaching_view.html`). Tabs: Statistics, Rules, Micro Dialogs, Variables, Chat (simulator), Raw. Backed by `app/coaching_model.py` (parses the PMCP "Report" HTML export) and `app/coaching_sim.py` (a 1-minute-tick interpreter for the declarative rule mini-language). JS-snippet and regex rules are parsed but skipped at run time. See `ALEX_v02_simulator_scope.md` for that scope boundary.
- **Coaching bundle exporter** (`tools/coaching-bundle-export/`). Browser automation over CDP (Playwright, no LLM) that sweeps the live PMCP Vaadin editor. This is the only place the per-message **Randomisation Group** lives — the Report HTML export omits it entirely. `--enrich` joins the Report HTML back in for full per-language text and decision branches. Reference run (ALEX v01, 2026-09-03): 107 micro dialogs, 1177 nodes, 96 distinct `r_` groups, 92/107 dialogs text-enriched, 255/258 decision branches resolved. Details in `tools/coaching-bundle-export/DESIGN.md`.
- **Randomisation-group tables** (`tools/rgroups-table/`). Turns the bundle into `rgroups_table.csv` (one row per `r_`-tagged message) and `rgroups_summary.csv` (per-group pool sizes). `expand_rgroups.py` tops up thin pools with an LLM; `render_review_report.py` turns that into a per-pool markdown report for human review.
- `docs/randomisation_groups_ALEX_v01.md` — the committed **`r_` groups report**. See Workstream 1 below.

Not yet built: rule-level send-delay/timeout capture, answer→child routing capture (bundle "Stage 3"), importing the bundle into the analyzer's own model (bundle "Stage 4"), and rule-order-aware pile-up logic in the simulator.

### The priority-field correction

We opened the live "Edit micro dialog message:" and "Edit rule:" modals on the sandbox coaching "ALEX v01 zum Ausprobieren". Neither has a priority or tier field. There is no such field anywhere in PMCP.

Interruption and pile-up behaviour is emergent, from two real mechanisms:

1. **Rule execution order.** The Rules tab runs top-to-bottom, down the tree. A rule's children are skipped if it doesn't match. Execution stops entirely once a rule "solves the issue."
2. **Per-rule timing.** Each dialog-starting rule has its own "Hour to send message" delay and "Minutes after sending until message is handled as not answered" timeout, plus separate "Rules if participant DOES / DOES NOT answer" subtrees.

`ALEX_v02_simulator_scope.md`'s P0–P3 tier model was our own abstraction, invented before we could see the live Rules tab. It isn't a PMCP concept. Full writeup: the "Not yet captured" section of `tools/coaching-bundle-export/DESIGN.md`. This reframes workstreams 2 and 3 below.

## Roadmap: five workstreams

Reordered here by dependency, not by the order they were raised.

**Replanned 2026-09-09.** We originally thought workstream 3 (finish the export) had to happen before workstream 2 (pile-up analysis) could start at all. That's wrong. Since pile-up is just rule order + per-rule timeout — both fully visible today in the live Rules tab, and rules are literally drag-to-reorder in that UI ("Rules can be moved with the mouse!", per the tab's own Info panel) — a first, useful pass at workstream 2 needs no export at all. So workstream 2 is split: **2a** (read the live Rules tab by hand, write findings) is unblocked and is the next concrete step. **2b** (a rigorous pass covering every reminder rule, cross-checked in bulk) still waits on workstream 3.

```
1. r_ report        [done]

2a. Pile-up: manual first pass  [unblocked, do next]
        │
        ▼
3. Finish export (Stage 3: rule delay/timeout/routing)
        │
        ├──────────────► 2b. Pile-up: rigorous pass (bulk data)
        │
        ▼
4. In-app faithful simulator (Stage 4) ────► 5. Markov patient simulation
   (bundle → CoachingModel → Chat tab)         (batch runs, invariant checks)
```

| # | Workstream | Status | Branch |
|---|---|---|---|
| 1 | **`r_` entries report** | Done. `docs/randomisation_groups_ALEX_v01.md`, backed by `tools/rgroups-table/rgroups_table.csv`. | merged to `main` |
| 2a | **ALEX pile-up — manual first pass** | Not started, **unblocked, do next**. Read the live Rules tab's actual order/timeouts for the reminder rules. | `alex-pileup-analysis` |
| 2b | **ALEX pile-up — rigorous pass** | Not started. Needs #3's bulk data instead of hand-reading. | `alex-pileup-analysis` |
| 3 | **Exhaustive machine-readable export** | Stage 1+2 done (`coaching.bundle.v2.json`). Stage 3 **captured** (2026-09-10): `tools/coaching-bundle-export/probe_rules_tree.py` walked the live Rules `.v-tree` and every sending rule's "Edit rule:" modal → `rules_stage3_ALEX_v01.json` + `docs/rules_stage3_ALEX_v01.md`. All 2026-09-09 schema questions answered. Remaining: a non-probe `export_rules.py` that writes into the bundle, plus decision-point-internal quick-reply routing. | `bundle-export-stage3` |
| 4 | **In-platform faithful chat simulator** | Not started (Stage 4). `coaching_model.py` needs `parse_bundle()`. `coaching_sim.py` needs r_group random-pick collapsing, branch routing, and rule-order/timeout-aware interruption. Wire into the existing Chat tab. | `bundle-sim-integration` |
| 5 | **Markov-chain patient simulation over time** | Not started. Design exists in `ALEX_v02_simulator_scope.md`: 10 patient archetypes, 1000 seeded runs, invariant checks for starvation/engagement-lock/double-fire. Needs #4's engine as its substrate. | `patient-markov-simulation` |

### Workstream detail

**1 — `r_` entries report.** Done. `docs/randomisation_groups_ALEX_v01.md` lists all 96 groups with message/dialog counts. Full per-message text and trigger conditions are in `tools/rgroups-table/rgroups_table.csv`. To refresh: re-run `tools/coaching-bundle-export/` then `tools/rgroups-table/build_table.py` against the live portal.

**2 — Pile-up problem in ALEX "zum Ausprobieren".** The pile-up problem is real: a message can push out one that was mid-flow. But it isn't governed by a tier system PMCP tracks. What actually governs it, confirmed live:

- Rule execution order within each of the DAILY BASIS / PERIODIC BASIS / UNEXPECTED MESSAGE / USER INTENTION trees. Top-to-bottom. Non-matching branches are skipped. Execution stops the instant a rule "solves the issue."
- Each dialog-starting rule's own send-delay and not-answered timeout.

**2a — manual first pass, do next, no export needed.** Read the live Rules tab's actual tree order and timeouts for the spirometry/medication/ACQ/education rules — those are the ones most likely to collide. Deliverable: a findings doc naming specific rules to reorder, re-delay, or guard with an extra "already showing something else" condition. The fix mechanism is drag-and-drop in the same tab — the Rules tab's Info panel says outright "Rules can be moved with the mouse!" — so a finding here can plausibly be applied by hand in the same sitting, no code required.

**2b — rigorous pass.** Needs workstream 3's data pulled in bulk instead of read by hand: every reminder-generating rule's order and timeout, cross-checked systematically rather than sampled.

**3 — Finish the machine-readable export.** `coaching.bundle.v2.json` already has node order, type, comment, channel, randomisation group, and (where enriched) full text and decision branches — enough for *content*, not *timing behaviour*. Stage 3 closes that gap on the **rule** level. **Captured live 2026-09-10** by `tools/coaching-bundle-export/probe_rules_tree.py`, which walks the Rules `.v-tree` (a different Vaadin widget from the Micro Dialogs `.v-menubar`, so its own tree-walker) and opens the "Edit rule:" modal for every one of the 25 message/dialog-sending rules. Findings — `docs/rules_stage3_ALEX_v01.md`, data — `tools/coaching-bundle-export/rules_stage3_ALEX_v01.json`, session log — `autochanges/2026-09-10-rules-tree-stage3-sweep.md`:

- Both action paths are real: 24/25 `Start micro dialog`, 1 `Send message` (+ a message group). Same timing fields on both.
- `Hour to send message` is always a **`$variable`** (user-preference time, or a reschedule new-time var), not a literal — the actual scheduling decision is in the rule's condition chain.
- `Minutes … not answered` default is **4h** on every dialog sender (19 min on the one message sender).
- Field set is identical across DAILY BASIS / PERIODIC BASIS / USER INTENTION; UNEXPECTED MESSAGE is empty.
- The four TRUE-result action checkboxes include `Mark case as solved … and stop the rule run` and `Stop the rule run and finish coaching` — **no sender sets either**, so senders never cut the run; the guard rules above them do.

Remaining: a non-probe `export_rules.py` that emits straight into `coaching.bundle` rather than the `spike/` dumps, and quick-reply → child routing for decision points *inside* a micro dialog (distinct from the rule-level DOES/DOES-NOT subtree). This is the prerequisite for a faithful simulation (4) and the rigorous pile-up pass (2b).

**4 — Simulate a chat in the analyzer itself.** The Chat tab and tick-based `Simulator` already exist. But they run against `coaching_model.py`'s Report-HTML parse: dialogs launched manually, no randomisation, no interruption logic, and no bundle data. Stage 4 (sketched in `tools/coaching-bundle-export/DESIGN.md`):

- `parse_bundle()` loads `coaching.bundle.v2.json` into the existing `CoachingModel`/`MicroDialog`/`Node` dataclasses, extended with `uid`, `randomisation_group`, `order`, and rule-level `send_hour`/`not_answered_timeout_minutes`.
- `Simulator` gains r_group collapsing (one random pick per run, like the real engine), scraped-branch routing, and interruption modeled as "rule order + timeout" — not a tier lookup.

Variable tracking and clock-advancing already work in the existing simulator. This workstream extends fidelity, not the basic interaction model.

**5 — Markov-chain patient simulation over a period.** `ALEX_v02_simulator_scope.md` §4–7 already specs this: 10 patient archetypes as parameterized stochastic processes (response latency, completion-after-engagement rate, per-reminder adherence, time-of-day availability, reschedule acceptance). Run 10×100 seeded times over a 14-day simulated horizon. Check against invariants: starvation, engagement-lock duration, flag-leak, double-fire, window-overrun, delivery-rate. Needs workstream 4's engine as its substrate, so it runs the real bundle-driven content rather than a synthetic rule model. Estimated ~1 focused week per the existing effort table in that doc.

### Open questions from today's exploration

Things the live probing surfaced but didn't answer. Worth resolving before Stage 3's scraper schema is considered final — otherwise it'll need a second pass.

- **A rule can send a single message directly, or start a whole micro dialog.** The "Edit rule:" form has two independent checkboxes: "Send message if rule result is TRUE" and "Start micro dialog if rule result is TRUE." We only exercised the micro-dialog path on our one sample. Does the single-message path have the same delay/timeout fields? Does it matter for pile-up the same way?
- **"Message group to send messages from"** is a field on the rule form we saw but didn't investigate — blank/disabled in our sample. It hints at a possible second dispatch layer alongside "micro dialog." Needs a sample where it's actually set.
- **Only one rule was sampled.** We don't know if "Start micro dialog" rules under UNEXPECTED MESSAGE or USER INTENTION carry the same fields as the PERIODIC BASIS one we opened, or whether answer routing for a decision point *inside* a micro dialog works the same way as the rule-level DOES/DOES-NOT-answer subtree we saw at the top level.
- **The Rules tab is a different Vaadin widget** (`.v-tree`, expand/collapse triangles) from the Micro Dialogs picker (`.v-menubar`). Stage 3's scraper needs its own tree-walker — it can't just extend `tools/coaching-bundle-export/_menu_nav.py`.
- **The rule tree shows different icons per row** (a chat-bubble-ish icon on message-sending rules, a gear on calculation-only ones, a warning triangle on rules commented "BEISPIEL"/example, others unidentified). These likely encode the action type and could drive an automated parser — worth mapping the icon set before writing the bulk scraper.

## Branches

No workstream branches exist right now — four were created ahead of time and then deleted (2026-09-09) since they sat empty. Create a branch from `main` when a workstream actually starts, not before:

- `alex-pileup-analysis` — workstream 2
- `bundle-export-stage3` — workstream 3
- `bundle-sim-integration` — workstream 4
- `patient-markov-simulation` — workstream 5

`main` stays the deploy branch: `tools/release_frontend.sh` tags `main`'s HEAD for the `release_frontend` GitHub Actions workflow. Merge a workstream back to `main` when it's ready to ship.

## Navigating the live PMCP portal (hurdles)

Workstreams 2–4 all eventually need hands-on time in the live PMCP Vaadin editor (`https://cp22.pathmate.cloud/PMCP/admin`), by a person or by a CDP script driving a shared browser. It's an old-school server-rendered app with non-obvious client state. The same hurdles bite every time. Notes so far:

- **You always land on the Home/Welcome page after login**, never inside a coaching. Click "Coachings" in the left nav first. There's no shortcut into a specific coaching.
- **Select the coaching row, then click "Edit."** These are two separate clicks. Clicking the row alone only shows the read-only toolbar (Report / Validate / Results / …). This repo's reference coaching is "ALEX v01 zum Ausprobieren".
- **Deactivate Monitoring before touching Micro Dialogs. Confirmed hard requirement, not just habit.** Inside Edit → "Basic Settings and Modules" there's a "Monitoring is active! Click to deactivate." toggle. Confirmed live: the Micro Dialogs tab renders fine either way, but the dialog-picker MenuBar's popups reliably fail ("popup 1 for '…' never opened") while Monitoring is active. They work immediately once it's deactivated — same window, same navigation, only that one thing changed. This changes live coaching state, so an assistant should never click it unattended. A human should do it by hand. On this repo's sandbox coaching that's low-stakes and logged; a different, real coaching may not be. Turn it back on when the session is done unless told otherwise.
- **Widen the browser window a lot (~9000–12000px) before touching the Micro Dialogs menu.** The dialog-picker is a Vaadin `MenuBar`. Past a handful of items it collapses into a `►` overflow submenu that will not open under scripted input — mouse-hit-testing on it is unreliable. At ~9000px+ every top-level item renders inline instead and the `►` never appears. Resize the real window via the CDP `Browser.setWindowBounds` call. `Emulation.setDeviceMetricsOverride` (viewport-only emulation) desyncs mouse hit-testing on a headed browser instead of fixing this — don't use it.
- **A Vaadin MenuBar top item opens its popup on click, not hover, from a closed state.** Hover only switches between menus that are already open. An ad-hoc click (e.g. Playwright `get_by_text(...).click()`) can highlight a top item without opening its dropdown, leaving the menu in a state the automated tooling doesn't expect. If a folder that normally opens fine through `tools/coaching-bundle-export/_menu_nav.py` suddenly reports "popup 1 for '…' never opened", suspect leftover state from a manual click first. Re-navigate cleanly from "Coachings" — don't just retry in place.
- **Never call a plain page reload to "reset" the view.** Confirmed live: `page.reload()` drops the Vaadin SPA straight back to the username/password/TOTP login screen, even though the underlying session cookie may still be valid. The app's client-side state — not just auth — is what a reload destroys. Need a clean slate? Re-navigate via the in-app "Coachings" link. Don't reload the page.
- **The PMCP session expires quickly when idle — closer to ~10 minutes than the ~1–2h originally assumed** (per the user). Symptom: "popup N for '…' never opened" on every folder, not just one. Fix: reload (accepting the forced re-login), re-navigate from "Coachings" by hand, then rerun the automation. Practical consequence: keep gaps between live-portal actions short. Expect to need a fresh login if you pause to write up findings for more than a few minutes.
- **One folder failing while the rest succeed** is a different, intermittent MenuBar quirk unrelated to session expiry. Just rerun. Or ignore it if that folder is an empty grouper — its children are usually still reachable directly.
- **A modal left open by a crashed script blocks all further MenuBar clicks.** Same symptom as session expiry or the width issue — a third, easy-to-miss cause. Confirmed live: a script that threw mid-loop (on an unrelated `page.screenshot` timeout) left a `.v-window` open. Nothing else was wrong, but every subsequent menu click failed until that window was explicitly closed. If navigation suddenly stops working right after a script errored out, check `document.querySelectorAll('.v-window').length` (or just screenshot) before assuming session expiry or re-widening the window.
- **A node-editor modal's dismiss button is not consistently labeled, and not consistently safe.** The "Edit micro dialog message:" modal's button reads "Close" and is a pure cancel. The "Edit rule:" modal's button also reads "Close" but commits the form — it fires a "The rule has been updated." toast even with zero fields touched. A few modals use "Exit" instead. Never assume a modal's dismiss button is read-only from its label alone. On a sandbox coaching a same-value re-save is harmless. Treat it as a real write on anything else.
- `.md-menu` and `.v-menubar` select the same element in this app, not ancestor/descendant. Don't assume nesting when reading selectors in the tooling.
- **The Rules tab has no explicit priority/tier/interrupt field anywhere.** Confirmed by opening live "Edit rule:" modals and grepping their full HTML. See "The priority-field correction" above. Don't go looking for a priority column — it isn't there.

See also `tools/coaching-bundle-export/README.md`'s "Known hiccups" section. It overlaps with this list but is scoped to the export script specifically.

Every live-portal session (exploration or write) gets a dated log entry in `autochanges/` — see `autochanges/README.md` for the format. That's the raw log; this section is the maintained summary of what it taught us.
