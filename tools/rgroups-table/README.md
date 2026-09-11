# rgroups-table

The **randomisation-group tables** for a PMCP coaching, plus a tool to grow the
thin ones with an LLM.

Background: inside a micro dialog, all messages that share an `r_<Name>`
randomisation group are merged and one is picked at random each run. The unit
that actually matters is a **pool** = one `(r_ group, micro dialog)` pair — the
same group name can appear in several micro dialogs and those are independent
pools that happen to share a name.

## Files

Four steps, each a standalone script (`.py` + a thin `.sh` wrapper), plus one
interactive wrapper. All read a **pre-made `coaching.json`** — none of them
runs the coaching export (that's costly; produce the JSON separately with
`tools/coaching-bundle-export/export_coaching.sh`).

| Step | Script | In → Out |
| --- | --- | --- |
| 1 | `rgroup_report.py` | `coaching.json` → `rgroups_table.csv` (one row per `r_*` message; `--md` also writes the `docs/randomisation_groups_*` summary) |
| 2 | `rgroup_prepare.py` | `rgroups_table.csv` → `rgroups_requests.csv` — one row per **thin pool** = one LLM call to make. No prompt text. |
| 3 | `rgroup_expand.py` | `rgroups_requests.csv` + an API key + **`--limit N`** → `rgroups_generated.csv` (one row per generated variant) + `expand_prompts.txt` |
| 4 | `rgroup_apply.py` | `rgroups_generated.csv` + **`--limit N`** → adds every `ok` variant to the live PMCP editor over CDP (dry-run by default; `--apply` writes) |
| — | `rgroup_pipeline.sh` | runs 1→4 with a `continue? [y/N]` checkpoint between each. Requires `--json FILE` and `--limit N`. |

There is no review gate — step 4 applies everything step 3 generated, bounded by
`--limit`. `rgroups_table.csv` is committed (the deliverable);
`rgroups_requests.csv` / `rgroups_generated.csv` / `expand_prompts.txt` are
git-ignored intermediates.

## `rgroups_table.csv` columns

| column | meaning |
| --- | --- |
| `randomisationGroup` | the `r_*` name |
| `pool` | `<group> @ <micro dialog>` — the real randomisation unit |
| `groupTotalMessages` | messages with this group across the whole coaching |
| `groupMicroDialogs` | how many micro dialogs this group appears in |
| `poolVariants` | **distinct** non-empty en-GB texts in *this* pool (the number top-up cares about) |
| `microDialog` | leaf name of the micro dialog |
| `folderPath` | its folder path in the editor menu |
| `order` | node position within the micro dialog |
| `nodeUid` | stable id from the coaching export (`md-###`#`###`) |
| `type` | `message` / `decision` |
| `comment` | the node's editor comment |
| `resultVariable` | `$var` the node writes, if any |
| `answerType` | e.g. `expects NO answer` |
| `channel` | delivery channel |
| `containsRules` | rule/branch count on the node |
| `isCommand` | `yes` if it's a command message (not shown to the user) |
| `triggerExprs` | conditions under which this specific variant fires (` ; ` joined) |
| `en-GB`, `ro-RO` | the full message text |

## Full pipeline (one interactive run)

`rgroup_pipeline.sh` runs steps 1→4 with a `continue? [y/N]` checkpoint between
each ("here's the output, next is X, continue?"). It **never runs the coaching
export** — you pass a ready-made `coaching.json`.

```bash
tools/rgroups-table/rgroup_pipeline.sh --json data/exports/coaching.json --limit 10
```

| flag | meaning |
| --- | --- |
| `--json FILE` | **required** — a `coaching.json` from `export_coaching.sh` |
| `--limit N` | **required** — caps API calls in step 3 and variants applied in step 4 |
| `--yes` / `-y` | don't pause at the checkpoints |
| `--apply` | let step 4 actually write (default: step 4 is a dry run) |
| `--stop-after N` | stop after step N (1..4) |

`ANTHROPIC_API_KEY` / `OPENAI_API_KEY` (step 3) and any model overrides are read
from a git-ignored `.env` at the repo root, or the environment. Step 4 needs a
Chromium logged in to PMCP on the coaching's Micro Dialogs view, from
`tools/start_pmcp.sh`. `TARGET` (healthy-pool size, default 10) is honoured by
every step.

The four steps can each be run on their own — `.py` directly, or the matching
thin `.sh` wrapper (`rgroup_report.sh`, `rgroup_prepare.sh`, `rgroup_expand.sh`,
`rgroup_apply.sh`), which just resolves the venv and sources `.env`.

Steps 1–3 are also available from the portal — the "Randomisation groups" tab
on a coaching that has a `coaching.json` attached (`app/rgroups_tool.py` /
`app/templates/_tab_rgroups.html` / `app/static/rgroups_tool.js`). It calls
these same functions in-process (no subprocess), runs step 3 in a background
thread with a pollable progress bar, and lets you download each step's CSV.
The API key is a per-run form field, never persisted. Step 4 stays CLI-only —
the portal process has no CDP-connected browser.

## Bundle JSON contract

`rgroup_report.py` is the only step that reads the JSON, and it reads a small,
stable subset of the coaching export (`../coaching-bundle-export/export_coaching.py`).
Any source that provides these fields can drive the pipeline (pass it as
`rgroup_report.py path/to/coaching.json`, or `rgroup_pipeline.sh --json …`):

```jsonc
{
  "microDialogs": [
    { "uid": "md-000",          // referenced by nodes[].microDialogUid
      "name": "Morning greetings",   // micro-dialog leaf name -> the "pool" label
      "folderPath": ["Greetings"] }  // list<str>, joined with " / "
  ],
  "nodes": [
    {
      "randomisationGroup": "r_MorningGreetings",  // only nodes matching /^r_/ are kept
      "microDialogUid": "md-000",
      "order": 3,
      "uid": "md-000#003",
      "type": "message",
      "comment": "",
      "resultVariable": "",
      "answerType": "expects NO answer",
      "channel": "",
      "flags": { "containsRules": 0, "commandMessage": false },
      "triggerExprs": [],                 // list<str>, " ; " joined
      "textByLang": { "en-GB": "Hi!", "ro-RO": "Salut!" }  // "[not set]" = untranslated
    }
  ]
}
```

Nothing else in the export (`branches`, `answerOptionsByLang`, `rawType`,
media, `rules`, `validation`) is used here. If the export ever renames these
fields, a ~20-line adapter to this shape is enough — no scraper of our own.

## Step 1 — `rgroup_report.py` → `rgroups_table.csv`

```bash
.venv/bin/python tools/rgroups-table/rgroup_report.py
# or point at a specific bundle:
.venv/bin/python tools/rgroups-table/rgroup_report.py path/to/coaching.json
# also write the per-group markdown summary (the docs/ deliverable view):
.venv/bin/python tools/rgroups-table/rgroup_report.py --md docs/randomisation_groups_ALEX_v01.md
# change the "healthy pool" size (default 10):
TARGET=12 .venv/bin/python tools/rgroups-table/rgroup_report.py
```

Default input is `../../data/exports/coaching.json`. One row per `r_*` message;
columns are the table above. Reference run: **96 `r_` groups, 460 messages,
126 pools (110 thin, < 10 variants)**.

## Step 2 — `rgroup_prepare.py` → `rgroups_requests.csv`

Reads `rgroups_table.csv`, emits **one row per thin pool** — the manifest of
LLM calls step 3 will make. No prompt text. Pools already at `TARGET` are
dropped; `needVariants = TARGET - haveVariants`. Existing variants are carried
across (`existing_enGB` / `existing_roRO`, newline-joined inside the cell) so
step 3 builds the prompt without re-reading the bundle.

```bash
.venv/bin/python tools/rgroups-table/rgroup_prepare.py
# -> 110 thin pools -> rgroups_requests.csv  (110 API calls, 880 variants to generate)
```

## Step 3 — `rgroup_expand.py --limit N` → `rgroups_generated.csv`

For the **first `--limit N`** request rows, build the prompt, call the LLM, and
write one row per generated variant. `--limit` is **required** — the number of
API calls is always an explicit, bounded choice. The prompt keeps the **same
meaning** (fully interchangeable), **about the same length**, **sparing emoji**,
tone for **ages 10–19**, the `$participantName` mix, and returns **both en-GB
and ro-RO** — ro-RO in the **informal "tu"** (never `dumneavoastră`), native
(non-calque) phrasing, no English loanwords, comma-below diacritics.

```bash
# prompts only, no key, no calls:
.venv/bin/python tools/rgroups-table/rgroup_expand.py --limit 10 --dry-run
# for real — pick ONE key:
ANTHROPIC_API_KEY=sk-ant-... .venv/bin/python tools/rgroups-table/rgroup_expand.py --limit 10
OPENAI_API_KEY=sk-...        .venv/bin/python tools/rgroups-table/rgroup_expand.py --limit 10 --provider chatgpt
```

Provider auto-detects from whichever key env var is set; `--provider claude` /
`--provider chatgpt` forces it. Model overrides: `ANTHROPIC_MODEL` (default
`claude-sonnet-5`), `OPENAI_MODEL` (default `gpt-4o`). Output rows carry a
`status` (`ok` / `failed: …` / `dry-run`); re-run with a higher `--limit` to
cover more pools. `expand(requests, provider, limit, …, progress=…)` is the
importable API the portal calls (progress callback fires per pool). No
third-party packages — the HTTP calls are plain `urllib`.

## Step 4 — `rgroup_apply.py --limit N` → live PMCP editor

Reads `rgroups_generated.csv` and adds **every** `ok` variant (non-empty en-GB)
to the live editor over CDP. No review gate — step 4 applies everything step 3
generated. `--limit N` is **required** and caps the number of variants added.

Recipe per variant (this is how you add to an `r_` group by hand too — a
randomisation group only fires when its messages are **consecutive**):

1. select an existing message already in that `r_` group
2. **Duplicate** (the node button, *not* "Duplicate Dialog") → a copy is
   appended at the **bottom of the dialog**, keeping the group
3. select the copy → **Edit** → the **Edit** by "text (with placeholders):" →
   `English (GB)` tab, replace the textarea → `Romanian (RO)` tab, replace it →
   **OK** → **Close**
4. **Move Up** the copy until the row above it is in the same group

```bash
# needs a Chromium logged in to PMCP on the coaching's Micro Dialogs view (CDP)
PMCP_CDP=http://127.0.0.1:9222 .venv/bin/python tools/rgroups-table/rgroup_apply.py --limit 5             # DRY RUN: plan only
PMCP_CDP=... .venv/bin/python tools/rgroups-table/rgroup_apply.py --apply --limit 1 --pool 'r_X @ Micro Dialog'
PMCP_CDP=... .venv/bin/python tools/rgroups-table/rgroup_apply.py --dedup --apply --limit 20 --pool 'r_X @ Micro Dialog'  # remove exact-dup rows from a failed run
```

`--limit N` is **required**. Default is a **dry run** (navigate + print the
plan, no writes); `--apply` writes; `--pool` restricts to one pool; `--debug`
dumps per-step state; `--dedup` deletes rows whose text exactly copies an
earlier sibling in the same group. Idempotent: a variant already in the pool is
skipped; one present but not adjacent is only repositioned.

## PMCP editor automation — pitfalls

Hard-won lessons from `rgroup_apply.py` / the `probe_*` spikes. The PMCP
editor is Vaadin 7; these bite anything that drives it:

- **A confirm popup blocks everything behind it.** Delete (and some other
  actions) open an "Are you sure?" `.v-window` with `Cancel` / `OK`. You **must
  wait for it** (`page.wait_for_selector('.v-window')`) and click its
  affirmative button before doing anything else — if you read/scroll the table
  underneath while it is open, the click lands on the curtain, the popup stays,
  and the action never happens (it looks like "delete did nothing").
  `rgroup_apply.py`'s `confirm()` waits, then clicks any button whose caption
  is not a known "cancel" word (locale-safe).
- **Never let a scroll-collect loop run unbounded.** The `.v-table` body is
  virtualized, so reading all rows means scrolling top→bottom and accumulating.
  Always cap the `while (scrollTop + clientHeight < scrollHeight) { … }` loop
  with a guard counter (`guard++ < 2000`) — a layout hiccup where `scrollHeight`
  keeps growing, or a mis-read `scrollTop`, otherwise spins forever.
- **The table is virtualized — work in *logical* row indices, never DOM order.**
  Only on-screen `<tr>`s exist. Derive a row's index from its pixel position:
  `round((tr.top − scroller.top + scroller.scrollTop) / rowHeight)`. The
  `v-table-row-<n>` class is a widget id that keeps incrementing, **not** a row
  number — keying rows by it gives hundreds of phantom rows. Get the true row
  count from `round(scrollHeight / rowHeight)`.
- **Grid cells truncate long text** (`en-GB: Hey $participa…`). Match rows on a
  short prefix (~18 chars), not the full string, or you will never find your
  own row after adding it.
- **Clicking an already-selected row toggles the selection OFF.** After
  Duplicate, PMCP already selects the new row — click it again and the node
  toolbar greys out. Check the current selection before clicking.
- **Toolbar buttons enable on a server round-trip after a row is selected.**
  `Edit` / `Duplicate` / `Move Up` render disabled first; poll until enabled.
- **The node toolbar sits *below* the table** (`New Message`, `New Decision
  Point`, `New Event`, `Edit`, `Duplicate`, `Move Up/Down`, `Delete`), separate
  from the per-row `Edit` buttons in the far-right action column and from the
  dialog-level row (`New Dialog`, `Duplicate Dialog`, …). Distinguish by x
  position and exact caption.
- **The message editor is a property sheet.** "Edit micro dialog message:" shows
  each field (Comment, text, media, message key, **Randomisation group**, answer
  options, …) read-only with its own `Edit` button opening a nested sub-editor.
  There is **no Save** — only `Close`; the sub-editors commit on their own `OK`.
  The text sub-editor ("Edit text (with placeholders):") has `English (GB)` /
  `Romanian (RO)` toggle buttons over one `textarea`, plus `Cancel` / `OK`.
- **Session expiry is silent** (~1–2 h) — the old page still renders but clicks
  are rejected server-side. Re-login and re-navigate.

## Has it been tested?

- `rgroup_report.py` — yes, produced the committed `rgroups_table.csv` from the
  real bundle (96 groups, 460 messages, 126 pools).
- `rgroup_prepare.py` — yes, `rgroups_table.csv` → `rgroups_requests.csv`
  (110 thin pools, 880 variants to generate).
- `rgroup_expand.py` — `--limit N --dry-run` tested end-to-end (prompts written,
  skeleton `rgroups_generated.csv`); the live Anthropic path verified earlier
  with `--limit 3` / `--limit 10` (70 real variants, ro-RO informal `tu` +
  gender house-style checks passed). A full run has not been done yet.
- `rgroup_apply.py` — `build_plan` reads `rgroups_generated.csv`; tested that
  `--limit` is required and that only `ok` rows with text enter the plan.
- `rgroup_pipeline.sh` — steps 1–2 run start-to-finish via the wrapper
  (`--stop-after 2`); `--help` and the missing-`--limit` guard work. Steps 3–4
  are individually tested (above); the full chain has not been run against a
  live CDP session.
- `rgroup_apply.py` — `--apply` verified on the **sandbox** ("ALEX v01 zum
  Ausprobieren"): added a variant to a small pool (*Timeless Greetings*) and to
  a 51-row multi-group dialog (*Prompt patient to conduct daily spirometry*,
  Move Up climbed the new row 44 places to sit adjacent to its pool);
  idempotent re-run skips; `--dedup` removes strays. Not yet run at scale or
  against the production coaching.

## Known hiccups

- **`rgroups_table.csv not found`** — run `rgroup_report.py` first.
- **`set ANTHROPIC_API_KEY or OPENAI_API_KEY`** — export one, or use `--dry-run`.
- **A pool's `en-GB` is `[not set]`** — that variant was never translated in
  PMCP; it's skipped when counting `poolVariants` and not shown to the model.
- **Model returns prose / fenced code instead of a bare JSON array** — the
  script strips a ```` ```json ```` fence; if a provider wraps it differently the
  row stays `TO_GENERATE` and the raw error prints. Lower the batch by raising
  `TARGET` slowly, or switch provider.
- **Rate limits / timeouts** — there's a 1 s pause between pools; for 110 pools
  budget a few minutes. Failed pools stay `TO_GENERATE`; just re-run.
- **`groupTotalMessages` vs `poolVariants`** — top-up is driven by
  `poolVariants` (distinct texts in one pool), not the group total. A group with
  30 messages spread over 3 pools of 10 needs no top-up; a group with 3 messages
  in 1 pool needs 7.
