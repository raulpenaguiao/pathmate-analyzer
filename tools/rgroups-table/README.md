# rgroups-table

The **randomisation-group tables** for a PMCP coaching, plus a tool to grow the
thin ones with an LLM.

Background: inside a micro dialog, all messages that share an `r_<Name>`
randomisation group are merged and one is picked at random each run. The unit
that actually matters is a **pool** = one `(r_ group, micro dialog)` pair — the
same group name can appear in several micro dialogs and those are independent
pools that happen to share a name.

## Files

| File | Role |
| --- | --- |
| `build_table.py` | `coaching.json` → `rgroups_table.csv` (one row per `r_*` message) + `rgroups_summary.csv` (one row per group) |
| `report.py` | `coaching.json` → `rgroups_report.md` — the one-table-per-group summary (the committed-deliverable view, see `docs/randomisation_groups_*`). Parses the JSON, no browser. |
| `expand_rgroups.py` | asks Claude or ChatGPT for extra variants for every thin pool → `rgroups_table.expanded.csv` |
| `render_review_report.py` | `rgroups_table.expanded.csv` → `rgroups_review.md` (per-pool review with checkboxes) |
| `rgroups_pipeline.sh` | the whole chain: (bundle →) build_table → report → expand → review |
| `apply_approved.py` | write ticked `rgroups_review.md` proposals back into the live coaching (Playwright) |
| `expand_prompts.txt` | the exact prompt sent per pool (written on every run, incl. `--dry-run`) |

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

## Full pipeline (one command)

`rgroups_pipeline.sh` runs the whole chain — coaching JSON → tables → LLM top-up →
review report — from a single entry point. **Preferred:** hand it a ready-made
JSON and it never touches the portal:

```bash
BUNDLE=data/exports/coaching.json tools/rgroups-table/rgroups_pipeline.sh
```

Any JSON meeting the [Bundle JSON contract](#bundle-json-contract) works — in
particular the output of the project-wide coaching export
(`../coaching-bundle-export/export_coaching.py`). Without `BUNDLE`, step 1 runs
that export itself, which needs the browser from `tools/start_pmcp.sh` and the
coaching's "Report" HTML export on disk:

```bash
tools/rgroups-table/rgroups_pipeline.sh /path/to/Report_export.html
```

Steps: obtain JSON → `build_table.py` → `report.py` → `expand_rgroups.py` →
`render_review_report.py`. (`SKIP_EXPAND=1` stops after `report.py`.)

Knobs (env vars): `BUNDLE` (ready-made JSON; skips step 1), `PMCP_CDP`
(default `http://127.0.0.1:9222`), `TARGET` (healthy-pool size, default 10),
`EXPAND_ARGS` (e.g. `--limit 10`, `--dry-run`, `--provider chatgpt`),
`SKIP_EXPORT=1` (reuse the existing `data/exports/coaching.json`),
`SKIP_EXPAND=1` (stop after the tables), `PYTHON` (interpreter; default
`.venv/bin/python`). `ANTHROPIC_API_KEY` is read from a git-ignored `.env` at
the repo root.

The individual steps below can still be run on their own.

## Bundle JSON contract

`build_table.py` is the only step that reads the JSON, and it reads a small,
stable subset of the coaching export (`../coaching-bundle-export/export_coaching.py`).
Any source that provides these fields can drive the pipeline via `BUNDLE=`:

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

## Rebuild the tables

```bash
.venv/bin/python tools/rgroups-table/build_table.py
# or point at a specific bundle:
.venv/bin/python tools/rgroups-table/build_table.py path/to/coaching.json
# change the "healthy pool" size (default 10):
TARGET=12 .venv/bin/python tools/rgroups-table/build_table.py
```

Default input is `../../data/exports/coaching.json` (produced by
`../coaching-bundle-export/`).

Reference run: **96 `r_` groups, 458 messages, 127 pools; 83 groups have at
least one pool below 10 variants.**

## Grow the thin pools with an LLM

`expand_rgroups.py` reads `rgroups_table.csv`, and for every pool with
`poolVariants < TARGET` asks an LLM for the missing variants. The prompt tells
the model to keep the **same meaning** (fully interchangeable), **about the same
length**, **natural sparing emoji**, tone **appropriate for ages 10–19**, keep
the `$participantName` mix, and return **both en-GB and ro-RO** — with the ro-RO
using the **informal/colloquial "tu"** (never the formal `dumneavoastră`).

```bash
# 1. see what would be sent, no API calls, no key needed
.venv/bin/python tools/rgroups-table/expand_rgroups.py --dry-run
#    -> writes expand_prompts.txt and a rgroups_table.expanded.csv skeleton

# 2. generate for real — pick ONE:
ANTHROPIC_API_KEY=sk-ant-...  .venv/bin/python tools/rgroups-table/expand_rgroups.py
OPENAI_API_KEY=sk-...         .venv/bin/python tools/rgroups-table/expand_rgroups.py --provider chatgpt

# 3. try a couple of pools first
ANTHROPIC_API_KEY=sk-ant-... .venv/bin/python tools/rgroups-table/expand_rgroups.py --limit 3
```

Provider auto-detects from whichever key env var is set; `--provider claude` /
`--provider chatgpt` forces it. Model overrides: `ANTHROPIC_MODEL` (default
`claude-sonnet-5`), `OPENAI_MODEL` (default `gpt-4o`). `TARGET` sets the goal
size (default 10).

**Output** `rgroups_table.expanded.csv`: every existing row (`kind=existing`)
plus the new ones (`kind=generated`, or `kind=TO_GENERATE` if a call failed).
Re-run to retry the failures.

No third-party packages — the HTTP calls are plain `urllib`.

## Write approved variants into the portal

`apply_approved.py` reads the ticked (`- [x]`) proposals in `rgroups_review.md`,
joins them to `rgroups_table.expanded.csv` for each pool's micro dialog / folder
/ `r_` group, and adds each one to the **live PMCP editor** over CDP.

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
PMCP_CDP=http://127.0.0.1:9222 .venv/bin/python tools/rgroups-table/apply_approved.py           # DRY RUN: plan only
PMCP_CDP=... .venv/bin/python tools/rgroups-table/apply_approved.py --apply --limit 1 --pool 'r_X @ Micro Dialog'
PMCP_CDP=... .venv/bin/python tools/rgroups-table/apply_approved.py --dedup --apply --pool 'r_X @ Micro Dialog'  # remove exact-dup rows from a failed run
```

Default is a **dry run** (navigate + print the plan, no writes). `--apply`
writes; `--limit N` caps it; `--pool` restricts to one pool; `--debug` dumps
per-step state; `--dedup` deletes rows whose text exactly copies an earlier
sibling in the same group. Idempotent: a variant already in the pool is
skipped; one present but not adjacent is only repositioned.

## PMCP editor automation — pitfalls

Hard-won lessons from `apply_approved.py` / the `probe_*` spikes. The PMCP
editor is Vaadin 7; these bite anything that drives it:

- **A confirm popup blocks everything behind it.** Delete (and some other
  actions) open an "Are you sure?" `.v-window` with `Cancel` / `OK`. You **must
  wait for it** (`page.wait_for_selector('.v-window')`) and click its
  affirmative button before doing anything else — if you read/scroll the table
  underneath while it is open, the click lands on the curtain, the popup stays,
  and the action never happens (it looks like "delete did nothing").
  `apply_approved.py`'s `confirm()` waits, then clicks any button whose caption
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

- `build_table.py` — yes, produced the committed `rgroups_table.csv` /
  `rgroups_summary.csv` from the real bundle.
- `expand_rgroups.py` — `--dry-run` tested end-to-end (110 pools, 1340-row
  skeleton CSV, prompts written); the live Anthropic path verified with
  `--limit 3` and `--limit 10` (70 real variants, ro-RO informal `tu` + gender
  house-style checks passed). A full unlimited run has not been done yet.
- `rgroups_pipeline.sh` — the three post-scrape steps it chains are individually
  tested (above); the wrapper's control flow is `bash -n` clean but has not been
  run start-to-finish against a live CDP session.
- `apply_approved.py` — `--apply` verified on the **sandbox** ("ALEX v01 zum
  Ausprobieren"): added a variant to a small pool (*Timeless Greetings*) and to
  a 51-row multi-group dialog (*Prompt patient to conduct daily spirometry*,
  Move Up climbed the new row 44 places to sit adjacent to its pool);
  idempotent re-run skips; `--dedup` removes strays. Not yet run at scale or
  against the production coaching.

## Known hiccups

- **`rgroups_table.csv not found`** — run `build_table.py` first.
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
