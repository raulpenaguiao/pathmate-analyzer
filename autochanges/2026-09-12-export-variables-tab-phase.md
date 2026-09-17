# Add a Variables-tab sweep to `export_coaching.py`

2026-09-12, follow-up to ALEX v02 Phase 3.7. User request: the export
tool's only way of surfacing a variable was inferring it from a `$name`
reference inside captured rule/dialog text — never reading PMCP's actual
Variables tab, which is the authoritative list. Asked to fix this now,
live against the sandbox.

## What changed

- New module `tools/coaching-bundle-export/_variables_nav.py`:
  `open_variables_tab()` (lifted from `create_variables.py`, same mechanics
  confirmed live 2026-09-11) + `sweep_variables()`, returning one dict per
  variable with columns `Variable Name`, `Variable Value`, `Privacy
  Setting`, `Access Setting`, `Auto Sync`, `Multilingual Array Variable`,
  `Sensitive Data` (confirmed live 2026-09-12).
- Wired into `export_coaching.py` as a new phase 2, between Micro Dialogs
  (1) and the Report-HTML enrich step. Renumbered enrich→3, rules→4,
  coherence→5. New `--no-variables` flag (also implied by `--dialogs-only`
  / `--rules-only`). `bundle["variables"]`, `_metrics()`'s
  `variablesTotal`, and the final summary line all updated.
- `export_coaching.sh`'s help comment updated to list `--no-variables`.

## The sweep-correctness bug found along the way

The obvious technique — jump `scrollTop` straight to `scrollHeight`, wait
out `.v-loading-indicator`, repeat until both scrollHeight and the seen-row
count stop growing across two iterations (this is what
`create_variables.py`'s original `all_variable_names()` already did, and
matches the pattern used for the Micro Dialogs node sweep) — looked fully
converged on the live Variables tab: stable height, stable count, no
error. It had actually captured only 84-85 of the coaching's real 334
variables (~25%). Confirmed by targeted scroll-search: `$currentDaySlot`,
`$spiroReminderEngaged`, `$spiroWindowEnd`,
`$hyperparameterSpiroGraceMinutes` (this session's own Phase 3.1 variables)
were all present in the live table but silently absent from the big-jump
sweep's result — exactly the content this new phase exists to catch.

Root cause: PMCP's `.v-table` here is virtualized AND server-paginated. A
big scroll jump lets the virtualizer skip rendering whole windows of rows
in between old and new scroll position; those rows never enter the DOM at
all, so a listener grabbing only currently-rendered `<tr>`s never sees
them — and the final scrollHeight/count both still land on a stable value,
so the usual "stable = done" check gives false confidence. There is no
`missingRows`-style signal here the way there is for the Micro Dialogs
sweep; the gap is completely silent.

Fix: scroll in increments of ~1 viewport height
(`scroller.clientHeight`), waiting out the loading indicator after each
step, concluding "done" only after 3 consecutive steps land at the
scroller's bottom. Reproducibly 334/334 across multiple runs (~110-115s on
its own). Documented as a general PMCP-platform finding (not specific to
Variables — likely true of any virtualized `.v-table`) in persistent
memory (`pmcp-portal-and-randomisation-groups.md`), per the standing
instruction to capture general platform behavior, not just feature-
specific notes.

## `close_windows()` flakiness recurrence

The first live full-export attempt this session (before this fix) hit the
exact same "element is not enabled" Vaadin quirk in
`_rules_nav.py::close_windows()` that Phase 3.7 had already fixed with a
4-attempt retry (`autochanges/2026-09-12-alex-v02-phase3.7-*`) — except
this time the stuck spell outlasted all 4 retries (4×8s) too, and the
function still `raise`d, crashing the export mid-rules-sweep (variables
phase itself had already succeeded, 334/334, before this crash).

Hardened further: a click that's still "not enabled" after 4 retries no
longer raises — it falls back to `Escape` and lets the *outer* loop
(widened 6→10) re-examine and retry the close, instead of crashing the
caller. Only raises (fails loud) if a `.v-window` is genuinely still open
after every outer attempt, so a truly stuck modal is never silently
swallowed. The very next full run hit this exact stuck spell again and
recovered via the new fallback with no crash (logged inline: `! close_
windows: 'Close' stuck 'not enabled' past 4x8s — Escape + outer retry`),
completing with 21/21 sender rules captured (24 no-op re-saves, one extra
from the recovery).

## Verified live

`data/exports/coaching_ALEX_v01_phase3.7b-variables-verify_20260912-182148.json`:
- 334 variables, full metadata per row.
- `$currentDaySlot` = `"morning"`, `$spiroReminderEngaged` = `"0"` (both
  Access Setting `internal`, Privacy `private` — same shape as every other
  hand-created variable this session).
- Run time: 11m 25s total (dialogs 451s, variables 113s, rules 122s).
- Coherence check still flags drift vs. `coherence_baseline.json` (dated
  2026-09-10, predates this session's Phase 3 rule/dialog rebuild) —
  expected, not a regression; same situation already noted in the Phase
  3.7 log. Baseline was not regenerated as part of this change (a
  `--update-baseline` run is a separate decision, not bundled into this
  fix).
