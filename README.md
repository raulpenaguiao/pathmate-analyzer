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

Not yet built: **rule-level** send-delay/not-answered-timeout capture,
answer→child routing capture (bundle "Stage 3"), importing the bundle into
the analyzer's own model (bundle "Stage 4"), and rule-order-aware pile-up
logic in the simulator.

**Correction (live exploration, 2026-09-09):** PMCP has **no explicit
message-priority or tier field anywhere**. Confirmed by opening the live
"Edit micro dialog message:" and "Edit rule:" modals on the sandbox
"ALEX v01 zum Ausprobieren" coaching. Interruption/pile-up behaviour is
*emergent*, from two real mechanisms: (1) **rule execution order** — the
Rules tab runs top-to-bottom/down-the-tree, skips a rule's children if it
doesn't match, and **stops entirely once a rule "solves the issue"**; (2)
each dialog-starting rule's own **"Hour to send message"** delay and
**"Minutes after sending until message is handled as not answered"**
timeout, plus separate **"Rules if participant DOES/DOES NOT answer"**
subtrees. `ALEX_v02_simulator_scope.md`'s P0–P3 tier model is *our*
abstraction over this, not a PMCP concept — see the "Not yet captured"
section of `tools/coaching-bundle-export/DESIGN.md` for the full writeup.
This reframes workstreams 2 and 3 below (their descriptions are updated
accordingly).

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
| 2 | **ALEX pile-up first steps** | Not started — blocked on #3 for real rule order/timeout data; can start qualitatively now from the Rules tab's actual semantics (see correction above) | `alex-pileup-analysis` |
| 3 | **Exhaustive machine-readable export** | Partial — Stage 1+2 done (`coaching.bundle.v2.json`); Stage 3 (rule-level send-delay/not-answered-timeout, answer→child routing) not started, needs per-rule "Edit rule:" modals, not per-message ones (`tools/coaching-bundle-export/probe_node_editor.py` is the groundwork; confirmed live it opens both) | `bundle-export-stage3` |
| 4 | **In-platform faithful chat simulator** | Not started (Stage 4) — `coaching_model.py` needs `parse_bundle()`, `coaching_sim.py` needs r_group random-pick collapsing + branch routing + rule-order/timeout-aware interruption, wired into the existing Chat tab | `bundle-sim-integration` |
| 5 | **Markov-chain patient simulation over time** | Not started — design already exists in `ALEX_v02_simulator_scope.md` (10 patient archetypes, 1000 seeded runs, invariant checks for starvation/engagement-lock/double-fire); needs #4's engine as its substrate | `patient-markov-simulation` |

### Workstream detail

**1 — `r_` entries report.** Done. `docs/randomisation_groups_ALEX_v01.md`
lists all 96 groups with message/dialog counts; full per-message text and
trigger conditions are in `tools/rgroups-table/rgroups_table.csv`. Re-run
`tools/coaching-bundle-export/` + `tools/rgroups-table/build_table.py` against
the live portal for a coaching other than ALEX v01, or after ALEX v01 changes.

**2 — Pile-up problem in ALEX "zum Ausprobieren".** The pile-up problem (a
message pushing out one that was mid-flow) is real, but not governed by a
tier system PMCP tracks — `ALEX_v02_simulator_scope.md`'s P0–P3 model was our
own abstraction, written before we could see the live Rules tab. What
actually governs it, confirmed live: **rule execution order** within each of
the DAILY BASIS / PERIODIC BASIS / UNEXPECTED MESSAGE / USER INTENTION trees
(top-to-bottom, non-matching branches skipped, **execution stops the instant
a rule "solves the issue"**), plus each dialog-starting rule's own send-delay
and not-answered-timeout. A first qualitative pass can be done today by
reading the live Rules tab's actual tree order and timeouts for the
spirometry/medication/ACQ/education rules (the ones most likely to collide);
a rigorous pass needs workstream 3's Stage 3 data pulled in bulk rather than
read by hand. Deliverable: a findings doc naming specific rules to reorder,
re-delay, or guard with an extra "already showing something else" condition.

**3 — Finish the machine-readable export.** `coaching.bundle.v2.json`
already has node order, type, comment, channel, randomisation group, and
(where enriched) full text and decision branches — enough to reconstruct
*content*, not enough to reconstruct *timing behaviour*. Stage 3 closes that
gap, but on the **rule** level, not the message level (confirmed live —
see the correction above): scrape, per dialog-starting rule, the send **hour**,
the **not-answered timeout**, and the **DOES-answer / DOES-NOT-answer**
subtrees, from each rule's "Edit rule:" modal (not the message's "Edit micro
dialog message:" modal, which has no timing fields at all).
`probe_node_editor.py` already opens both modal types live; it needs
extending to walk the Rules tab tree (not just Micro Dialogs) and to parse
these specific fields out of the form. This is the direct prerequisite for a
*faithful* (not just content-accurate) simulation, so it's the one workstream
worth finishing before deep investment in 2, 4, or 5.

**4 — Simulate a chat in the analyzer itself.** The Chat tab and tick-based
`Simulator` already exist, but they run against `coaching_model.py`'s
Report-HTML parse (dialogs launched manually, no randomisation, no
interruption logic) — not the bundle. Stage 4 (sketched in
`tools/coaching-bundle-export/DESIGN.md`): `parse_bundle()` to load
`coaching.bundle.v2.json` into the existing `CoachingModel`/`MicroDialog`/`Node`
dataclasses (extended with `uid`, `randomisation_group`, `order`, and
rule-level `send_hour`/`not_answered_timeout_minutes`); `Simulator` gains
r_group collapsing (one random pick per run, like the real engine),
scraped-branch routing, and interruption modeled as "rule order + timeout"
per workstream 2's corrected understanding — not a tier lookup. Variable
tracking and clock-advancing already work in the existing simulator — this
workstream extends fidelity, not the basic interaction model.

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

## Navigating the live PMCP portal (hurdles)

Workstreams 2–4 all eventually need hands-on time in the live PMCP Vaadin
editor (`https://cp22.pathmate.cloud/PMCP/admin`), by a person or by a CDP
script driving a shared browser. It's an old-school server-rendered app with
non-obvious client state, so the same hurdles bite every time. Notes so far:

- **You always land on the Home/Welcome page after login**, never inside a
  coaching. Click **"Coachings"** in the left nav first — there is no
  shortcut/deep link into a specific coaching.
- **Select the coaching row, then click "Edit"** — the row-select and the
  "Edit" button are two separate clicks; clicking the row alone only shows the
  read-only toolbar (Report / Validate / Results / …). For this repo's
  reference coaching that's **"ALEX v01 zum Ausprobieren"**.
- **Deactivate Monitoring before touching Micro Dialogs — confirmed hard
  requirement, not just habit.** Inside Edit → "Basic Settings and Modules"
  there's a "Monitoring is active! Click to deactivate." toggle. Confirmed
  live 2026-09-09: the Micro Dialogs *tab* renders fine either way, but the
  dialog-picker MenuBar's popups reliably fail ("popup 1 for '…' never
  opened") while Monitoring is active, and work immediately once it's
  deactivated — same window, same navigation, only variable changed. This
  changes live coaching state, so an assistant should never click it
  unattended — a human should do it by hand (on this repo's sandbox
  coaching, "ALEX v01 zum Ausprobieren", that's low-stakes and logged; a
  different, real coaching may not be). Turn it back on when the session is
  done unless told otherwise.
- **Widen the browser window a lot (~9000–12000px) before touching the Micro
  Dialogs menu.** The dialog-picker is a Vaadin `MenuBar`; past a handful of
  items it collapses into a `►` overflow submenu that will **not** open under
  scripted/automated input (mouse-hit-testing on it is unreliable). At
  ~9000px+ every top-level item renders inline instead and the `►` never
  appears. Resize the *real* window via the CDP `Browser.setWindowBounds` call
  — `Emulation.setDeviceMetricsOverride` (viewport-only emulation) desyncs
  mouse hit-testing on a headed browser instead of fixing this.
- **A Vaadin MenuBar top item opens its popup on click, not hover, from a
  closed state** (hover only switches between menus that are already open).
  Ad-hoc clicks (e.g. Playwright `get_by_text(...).click()`) can select/
  highlight a top item without actually opening its dropdown, leaving the menu
  in a state the automated tooling doesn't expect. If a folder that reliably
  opens through the automation (`tools/coaching-bundle-export/_menu_nav.py`)
  suddenly reports **"popup 1 for '…' never opened"**, first suspect leftover
  state from a manual click and re-navigate cleanly from "Coachings" — do
  *not* just retry in place.
- **Never call a plain page reload to "reset" the view.** Confirmed live
  2026-09-09: `page.reload()` drops the Vaadin SPA straight back to the
  username/password/TOTP login screen, even though the underlying session
  cookie may still be valid — the app's client-side state (not just auth) is
  what a reload destroys. If you need a clean slate, re-navigate via the
  in-app "Coachings" link, don't reload the page.
- **The PMCP session expires quickly when idle — closer to ~10 minutes than
  the ~1–2h originally assumed** (per the user, 2026-09-09). Symptom: "popup
  N for '…' never opened" / hover timeouts on *every* folder, not just one.
  Fix: reload (accepting the forced re-login) and re-navigate from
  "Coachings" by hand, then rerun the automation. Practical consequence: keep
  gaps between live-portal actions short during a session, and expect to
  need a fresh login if you pause to write up findings for more than a few
  minutes.
- **One folder failing while the rest succeed** is a different, intermittent
  MenuBar quirk unrelated to session expiry — just rerun, or ignore it if
  that folder is an empty grouper (its children are usually still reachable
  directly).
- **A modal left open by a crashed/interrupted script blocks *all* further
  MenuBar clicks**, producing the exact same "popup 1 for '…' never opened"
  symptom as session expiry or the width issue — it's a third, easy-to-miss
  cause. Confirmed live 2026-09-09: a script that threw mid-loop (on an
  unrelated `page.screenshot` timeout) left a `.v-window` open; nothing else
  was wrong, but every subsequent menu click failed until that window was
  explicitly closed. If navigation suddenly stops working after a script
  errored out, check `document.querySelectorAll('.v-window').length` (or
  just screenshot) before assuming session expiry or re-widening the window.
- **A node-editor modal's dismiss button is not consistently labeled, and
  not consistently safe.** The "Edit micro dialog message:" modal's button
  reads **"Close"** and is a pure cancel. The "Edit rule:" modal's button
  *also* reads "Close" but **commits the form** — it fires a "The rule has
  been updated." toast even with zero fields touched. A few modals instead
  use "Exit". Never assume a modal's dismiss button is read-only from its
  label alone; on a sandbox coaching a same-value re-save is harmless
  (confirmed with the user), but treat it as a real write on anything else.
- `.md-menu` and `.v-menubar` select the **same element** in this app (not
  ancestor/descendant) — don't assume nesting when reading selectors in the
  tooling.
- **The Rules tab has no explicit priority/tier/interrupt field anywhere** —
  confirmed by opening live "Edit rule:" modals and grepping their full HTML.
  See the Status section's correction above; don't go looking for a priority
  column, it isn't there.

See also `tools/coaching-bundle-export/README.md`'s "Known hiccups" section,
which overlaps with this list but is scoped to the export script specifically.
