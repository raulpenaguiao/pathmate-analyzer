# pathmate-analyzer
A web browser analyser that allows for an upload of html based pathmate exports, and creates simple statistics, saves different versions of exports and models different patient interaction types, allowing for a quick analysis of interaction types.

## Status (2026-09-09)

Built and on `main`:

- **Tabbed coaching view** (`app/templates/coaching_view.html`) — Statistics /
  Rules / Micro Dialogs / Variables / **Chat (simulator)** / Raw, backed by
  `app/coaching_model.py` (parses the PMCP "Report" HTML export) and
  `app/coaching_sim.py` (a 1-minute-tick interpreter for the declarative rule
  mini-language; JS-snippet/regex rules are parsed but skipped at run time —
  see `ALEX_v02_simulator_scope.md` for the scope boundary).
- **Coaching bundle exporter** (`tools/coaching-bundle-export/`) — browser
  automation (Playwright over CDP, no LLM) that sweeps the live PMCP Vaadin
  editor, which is the *only* place the per-message **Randomisation Group**
  lives (the Report HTML export omits it entirely). `--enrich` joins the
  Report HTML back in for full per-language text and decision branches.
  Reference run (ALEX v01, 2026-09-03): 107 micro dialogs, 1177 nodes, 96
  distinct `r_` groups, 92/107 dialogs text-enriched, 255/258 decision
  branches resolved. See `tools/coaching-bundle-export/DESIGN.md`.
- **Randomisation-group tables** (`tools/rgroups-table/`) — turns the bundle
  into `rgroups_table.csv` (one row per `r_`-tagged message) and
  `rgroups_summary.csv` (per-group pool sizes), plus an LLM top-up tool for
  thin pools (`expand_rgroups.py`).
- `docs/randomisation_groups_ALEX_v01.md` — the committed **`r_` groups
  report** (see Workstream 1 below).

Not yet built: message **delay/priority** capture, answer→child routing
capture (bundle "Stage 3"), importing the bundle into the analyzer's own
model (bundle "Stage 4"), and any tier/priority-aware pile-up logic in the
simulator.

## Roadmap: five workstreams

Five open tasks, reordered here by dependency rather than the order they were
raised in. **Workstream 3 (finish the export) is the pivot everything else
leans on** — the pile-up analysis needs real priority data, and the in-app
simulator + patient simulation both need routing/delay data, so both wait on
it for full fidelity even though they can start in parallel on what already
exists.

```
1. r_ report        [done]
3. Finish export ────────► 2. Pile-up first steps  (needs priority data)
   (Stage 3: delay/            │
   priority/routing)           │
        │                      │
        ▼                      ▼
4. In-app faithful simulator (Stage 4) ────► 5. Markov patient simulation
   (bundle → CoachingModel → Chat tab)         (batch runs, invariant checks)
```

| # | Workstream | Status | Branch |
|---|---|---|---|
| 1 | **`r_` entries report** | Done — `docs/randomisation_groups_ALEX_v01.md`, backed by `tools/rgroups-table/rgroups_table.csv` | merged to `main` |
| 2 | **ALEX pile-up first steps** | Not started — blocked on #3 for real priority data; can start qualitatively now from `ALEX_v02_simulator_scope.md`'s tier model | `alex-pileup-analysis` |
| 3 | **Exhaustive machine-readable export** | Partial — Stage 1+2 done (`coaching.bundle.v2.json`); Stage 3 (delay/priority/"Low Priority" placeholder, answer→child routing) not started, needs the per-node detail modal (`tools/coaching-bundle-export/probe_node_editor.py` is the groundwork) | `bundle-export-stage3` |
| 4 | **In-platform faithful chat simulator** | Not started (Stage 4) — `coaching_model.py` needs `parse_bundle()`, `coaching_sim.py` needs r_group random-pick collapsing + branch routing + delay/priority-aware interruption, wired into the existing Chat tab | `bundle-sim-integration` |
| 5 | **Markov-chain patient simulation over time** | Not started — design already exists in `ALEX_v02_simulator_scope.md` (10 patient archetypes, 1000 seeded runs, invariant checks for starvation/engagement-lock/double-fire); needs #4's engine as its substrate | `patient-markov-simulation` |

### Workstream detail

**1 — `r_` entries report.** Done. `docs/randomisation_groups_ALEX_v01.md`
lists all 96 groups with message/dialog counts; full per-message text and
trigger conditions are in `tools/rgroups-table/rgroups_table.csv`. Re-run
`tools/coaching-bundle-export/` + `tools/rgroups-table/build_table.py` against
the live portal for a coaching other than ALEX v01, or after ALEX v01 changes.

**2 — Pile-up problem in ALEX "zum Ausprobieren".** The pile-up problem (a
high-priority message pushing out a lower-priority one that was mid-flow) is
exactly what `ALEX_v02_simulator_scope.md` was written to stress-test — tiers
P0–P3, the interruption rule ("strictly-higher tier interrupts and deletes the
open dialog; same-or-lower waits"), and the engagement-lock edge case. That
document is a simulator *design*, not yet an analysis of the live coaching. A
first pass can be done today by walking the `r_` groups/micro dialogs already
exported (workstream 1) against the known tier assignments; a rigorous pass
needs each message's actual priority/delay, which only exists in the
per-node detail modal and is workstream 3's Stage 3. Deliverable: a findings
doc naming specific micro dialogs/messages to retier, delay, or exempt from
interruption.

**3 — Finish the machine-readable export.** `coaching.bundle.v2.json`
already has node order, type, comment, channel, randomisation group, and
(where enriched) full text and decision branches — enough to reconstruct
*content*, not enough to reconstruct *timing/priority behaviour*. Stage 3
closes that gap: scrape send delay, message priority, the "Low Priority"
placeholder row's semantics, and answer-option → child-node routing from each
node's detail modal (~1200 modal opens; `probe_node_editor.py` is the
reconnaissance script for this). This is the direct prerequisite for a
*faithful* (not just content-accurate) simulation, so it's the one workstream
worth finishing before deep investment in 2, 4, or 5.

**4 — Simulate a chat in the analyzer itself.** The Chat tab and tick-based
`Simulator` already exist, but they run against `coaching_model.py`'s
Report-HTML parse (dialogs launched manually, no randomisation, no tier
logic) — not the bundle. Stage 4 (sketched in
`tools/coaching-bundle-export/DESIGN.md`): `parse_bundle()` to load
`coaching.bundle.v2.json` into the existing `CoachingModel`/`MicroDialog`/`Node`
dataclasses (extended with `uid`, `randomisation_group`, `order`, `delay`);
`Simulator` gains r_group collapsing (one random pick per run, like the real
engine), scraped-branch routing, and delay/priority handling built from
workstream 2's tier logic. Variable tracking and clock-advancing already work
in the existing simulator — this workstream extends fidelity, not the basic
interaction model.

**5 — Markov-chain patient simulation over a period.** `ALEX_v02_simulator_scope.md`
§4–7 already specs this: 10 patient archetypes as parameterized stochastic
processes (response latency, completion-after-engagement rate, per-reminder
adherence, time-of-day availability, reschedule acceptance — each a Markov/
stochastic model of patient behaviour), run 10×100 seeded times over a
14-day simulated horizon, checked against invariants (starvation, engagement-
lock duration, flag-leak, double-fire, window-overrun, delivery-rate). Needs
workstream 4's engine as its substrate, so it runs the real bundle-driven
content rather than a synthetic rule model. Estimated ~1 focused week per the
existing effort table in that doc.

## Branches

- `alex-pileup-analysis` — workstream 2
- `bundle-export-stage3` — workstream 3
- `bundle-sim-integration` — workstream 4
- `patient-markov-simulation` — workstream 5

Each branches from `main` at the commit that added this roadmap. `main` stays
the deploy branch (`release_frontend.sh` tags `main`'s HEAD for the
`release_frontend` GitHub Actions workflow); merge a workstream back to `main`
when it's ready to ship.
