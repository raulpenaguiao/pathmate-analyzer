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
| `rgroups_table.csv` | one row per message that carries an `r_*` group (full text, both languages, context) |
| `rgroups_summary.csv` | one row per `r_*` group (totals, pool sizes, whether it still needs top-up) |
| `build_table.py` | (re)generates the two CSVs from a `coaching.bundle.v2.json` |
| `expand_rgroups.py` | asks Claude or ChatGPT for extra variants for every thin pool → `rgroups_table.expanded.csv` |
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
| `nodeUid` | stable id from `coaching.bundle.v2.json` (`md-###`#`###`) |
| `type` | `message` / `decision` |
| `comment` | the node's editor comment |
| `resultVariable` | `$var` the node writes, if any |
| `answerType` | e.g. `expects NO answer` |
| `channel` | delivery channel |
| `containsRules` | rule/branch count on the node |
| `isCommand` | `yes` if it's a command message (not shown to the user) |
| `triggerExprs` | conditions under which this specific variant fires (` ; ` joined) |
| `en-GB`, `ro-RO` | the full message text |

## Rebuild the tables

```bash
.venv/bin/python tools/rgroups-table/build_table.py
# or point at a specific bundle:
.venv/bin/python tools/rgroups-table/build_table.py path/to/coaching.bundle.v2.json
# change the "healthy pool" size (default 10):
TARGET=12 .venv/bin/python tools/rgroups-table/build_table.py
```

Default input is `../../data/rgroups/coaching.bundle.v2.json` (produced by
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

## Has it been tested?

- `build_table.py` — yes, produced the committed `rgroups_table.csv` /
  `rgroups_summary.csv` from the real bundle.
- `expand_rgroups.py` — the `--dry-run` path is tested end-to-end (110 pools,
  1340-row skeleton CSV, prompts written). The live API calls are standard
  `urllib` POSTs to the documented Anthropic / OpenAI endpoints and were **not**
  run here (no key). Do a `--dry-run` then `--limit 2` first.

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
