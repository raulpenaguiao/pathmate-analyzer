# 2026-09-11 — ALEX v02 redesign, Phase 3 (create new variables)

**Coaching:** "ALEX v01 zum Ausprobieren" (sandbox — not production, per the
user).
**Driving:** Claude, over the user's CDP session (continuation of the same
session as Phase 0-2).
**Goal:** first concrete step of Phase 3 — create the 8 new coaching
variables `docs/ALEX_v02_redesign_spec.md` §2.3 (day-slot infrastructure,
shared prerequisite) and §3.1 (spirometry redesign) need before any new
rule can reference them.

## What was done

Built `tools/coaching-bundle-export/create_variables.py` (dry-run by
default, `--apply --limit N` to write, `--only NAME`, calls
`_pmcp_safety.assert_expected_coaching()` first). Created all 8:

| Variable | Value | Purpose |
|---|---|---|
| `$currentDaySlot` | `morning` | spec 2.3 — will be kept current by a new PERIODIC BASIS rule, not yet built |
| `$hyperparameterMorningEndHour` | `11` | spec 2.3 — matches the existing morning-greeting rule's own window ("triggered between 6 and 11 am") |
| `$hyperparameterMiddayEndHour` | `17` | spec 2.3 — chosen default, not spec-mandated |
| `$hyperparameterEveningEndHour` | `22` | spec 2.3 — chosen default, not spec-mandated |
| `$spiroWindowEnd` | `0` | spec 3.1 — placeholder until the DAILY BASIS reset rule computes it |
| `$spiroReminderStage` | `0` | spec 3.1 |
| `$spiroReminderEngaged` | `0` | spec 3.1 |
| `$hyperparameterSpiroGraceMinutes` | `180` | spec 3.1's own example value |

Verified all 8 by name + value with a fresh scroll-to-row read after
creation (`VARIABLES` dict in the script, re-run as a one-off check) — all
match.

## Writes

16 real actions: 8× "New" (name creation) + 8× "Edit" (value set), each
committed via the modal's real OK button. Two variables
(`$currentDaySlot`, `$hyperparameterSpiroGraceMinutes`) needed their value
fixed in a follow-up call after an initial run left them at the
server-assigned default (`0`) — see below.

## Findings — new PMCP mechanics (Variables tab, first time touched)

- **Creating a variable is two steps**, both simple `Cancel`/`OK` popups:
  the table's `New` button → "Enter name for variable:" (creates it with a
  default value, apparently always `0`) → select the new row → the
  table's `Edit` button → "Enter new value for variable:" to set it.
- **The Variables table is virtualized AND server-paginated** — confirmed
  live via a `.v-loading-indicator` that appears while more rows load
  after a scroll. A naive scroll-and-grab sweep with only a short fixed
  wait (150ms) massively undercounts (got 43 vs. the true ~84 on the first
  attempt). Fix: scroll to the bottom repeatedly, waiting out the loading
  indicator each time, until both `scrollHeight` and the unique-name count
  stop growing across two consecutive attempts (`SWEEP_NAMES_JS` in the
  new script). A freshly created row is not guaranteed to be in the
  initially-rendered DOM window either — needed the same incremental
  scroll-and-recheck technique (`scroll_table_to_row`) to find one row by
  name reliably, alphabetically deep in an 80+ row list (took ~25-30 scroll
  steps for a name starting with `h` or `s`).
- **Selecting a table row for the toolbar buttons needs a cell click, not
  a row click.** Clicking the `<tr>` itself only adds `v-table-focus` (the
  toolbar's `Edit` stays disabled); clicking a `.v-table-cell-wrapper`
  inside the row adds `v-selected` and enables `Edit`. This is a different
  requirement from the Micro Dialogs table, where a plain row click has
  always been enough in every tool in this repo so far — don't assume the
  same interaction model transfers between tables.
- **The cell-click selection was still occasionally flaky** even with the
  fix above — one variable (`$currentDaySlot`) needed its value corrected
  in a follow-up call after the first attempt's cell click didn't register
  `v-selected` (cause unconfirmed; possibly a timing race right after the
  scroll settles). The script now retries the cell click up to 4× checking
  for `v-selected` before giving up, rather than clicking once and hoping.

## A second, unrelated bug found and fixed this session

`open_variables_tab()`'s original selector
(`page.get_by_text('Variables', exact=True)`) matched **two** elements: the
real section tab, and the left-nav "Documentation" context-help button
(whose second line of text is just "Variables"). `.first` picked whichever
happened to be first in DOM order, which opened a blocking help iframe
(`https://my.pathmate.app/pmcp-documentation/...`) that then intercepted
every subsequent click ("element intercepts pointer events") — this is
almost certainly also what happened during earlier Phase-0/1 sessions
without being diagnosed, since the same loose-text-match pattern was used
there too (`_menu_nav.ensure_micro_dialogs` and `_rules_nav.ensure_rules_tree`
use the safer `.v-captiontext`-scoped pattern already, which is why they
didn't hit this). Fixed by checking page content first (idempotent) and,
if navigation is actually needed, filtering out anything inside a
`sub-button` ancestor. **The help overlay had to be manually closed twice
live** (via its own accessible "close button") before the fix landed —
worth remembering the fix for any future tab-navigation helper in this
codebase: never match tab text broadly, always scope to the actual tab bar
or exclude the sidebar.

## Session hygiene notes

- User reported "it's open again" when the documentation overlay
  re-appeared on a retry — this was the tool blocking itself
  (`open_variables_tab` re-running the bad selector on every script
  invocation), not anything the user did.
- The `--apply --limit 8` batch run (6 remaining variables) again exceeded
  the 180s foreground timeout and moved to background — same pattern as
  Phase 2's batch delete. Expect this for any multi-target `--apply` run
  in this toolkit; it completes fine, just needs the background
  notification rather than a foreground wait.
