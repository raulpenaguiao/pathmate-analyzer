# Stage 4 Phase 0 — exporter parses rule expressions

2026-09-13/14, offline (no live PMCP browser touched — the user was
concurrently running a live export + portal upload test, so this session
picked up a piece of work that doesn't need the shared browser resource:
`docs/stage4_chat_engine_plan.md` Phase 0, explicitly marked "no live
browser needed").

## Goal

`coaching.json`'s `ruleTree` entries were just captions — e.g. `"🕖 Delayed
day start at 3 AM: $systemHourOfDay calculated value is bigger than 3"` —
with no structured `{lhs, operator, rhs}` fields. Stage 4's chat engine
needs those parsed at export time (per the plan: "Rule expressions are
parsed in the exporter, not at load time"), reusing the operator-phrase
list that already exists in `app/coaching_sim.py`'s `parse_expr()`.

## What changed

- **New `app/rule_grammar.py`** — the shared home for PMCP's fixed
  declarative-rule phrases (`CMP_OPS`, `ASSIGN_TRUE`, `ASSIGN_FALSE`,
  `DATE_DIFF`, `DATE_ADD`, `ARROW`) and `parse_expr()`, moved verbatim out
  of `app/coaching_sim.py`. No Flask/app-package runtime dependency beyond
  being importable as `app.rule_grammar`, so a standalone script can use it
  the same way `enrich_bundle.py` already imports `app.coaching_model`
  (`sys.path.insert(0, repo_root)`).
- **New `parse_rule_caption(caption)`** in the same module — the actual
  Phase-0 capability. The HTML export already hands `app.coaching_model`
  comment and expression as two separate fields (separate table columns),
  so `coaching_sim.parse_expr()` never had to deal with a comment prefix.
  The **live Rules-tree caption is different**: it's the single rendered
  string `"<comment>: <expr>"` (comment optional), so Phase 0's real job
  was finding the comment/expression boundary, not re-parsing the
  expression grammar itself. Approach: find the earliest occurrence of any
  known operator phrase in the caption, then the LAST `": "` before that
  point is the comment/expression boundary (last, not first, so a comment
  that happens to contain its own colon doesn't break the split); hand the
  remainder to the existing `parse_expr()` unchanged. No caption with a
  matched phrase needed a fallback — see verification below.
- **`app/coaching_sim.py`** now imports the phrase constants and
  `parse_expr` from `app.rule_grammar` instead of defining its own copies;
  `eval_expr` (which does variable substitution/evaluation — simulator-
  specific, not grammar) is unchanged and stays local. Existing imports
  (`from app.coaching_sim import parse_expr, eval_expr`, used by
  `tests/test_coaching_sim.py`) keep working unmodified — this is a pure
  internal refactor, not a public API change.
- **`tools/coaching-bundle-export/_rules_nav.py::build_rule_tree()`** now
  adds an `expr` field to every `ruleTree` node via a new
  `_parse_rule_caption()` wrapper (imports `app.rule_grammar` the same
  `sys.path`-insert way `enrich_bundle.py` does). Deliberately a nested
  `expr` field, not flattened into the node dict — the node already has its
  own unrelated `kind` (`sender`/`condition`/`other`), which would collide
  with `parse_expr`'s `kind` (`cmp`/`assign`/`date_diff`/`date_add`/
  `unsupported`).

## Verification (offline — no live browser)

1. `.venv/bin/python -m unittest discover -s tests -q` — 48/48 still pass
   both before touching `coaching_sim.py` (baseline) and after (regression
   check on the refactor).
2. Ran `parse_rule_caption()` against every one of the 125 real `ruleTree`
   captions in the latest live export
   (`data/exports/coaching_ALEX_v01_phase3.7b-variables-verify_20260912-182148.json`):
   every node got a `kind` (60 `assign`, 57 `cmp`, 4 `unsupported`, 2
   `date_diff`, 2 `date_add`); the 4 `unsupported` ones are exactly the
   genuine JS-snippet rules (spirometry-week-counting helpers, the CLAID
   crash-check snippet, the sensor-data-surveillance snippet) — nothing
   else misclassified as unsupported, and no false structured parse of a
   JS snippet. Matches the plan's acceptance criterion exactly.
3. Spot-checked 15 rules (seeded random sample) against the **HTML**
   parser's already-separated `Rule.comment` + `Rule.raw_expr` fields, via
   `tests/fixtures/coaching_ALEX_v01.html` (`parse_model()`): reconstructed
   each as a combined `"comment: raw_expr"` string, ran it through the new
   `parse_rule_caption()`, and confirmed the extracted `comment` matches
   the HTML parser's own `Rule.comment` exactly. 15/15 correct, including
   the one JS-snippet rule in the sample (correctly `unsupported`, comment
   not recoverable for that case — an accepted, documented limitation, not
   a bug: there's no safe way to locate the comment boundary in free-form
   JS text without a recognised operator phrase to anchor on).

## Deliberately not done this session

- **Regenerating `rules_stage3_ALEX_v01.json` and bumping
  `coherence_baseline.json`** (both explicitly called for in the plan) need
  a fresh live export run. Skipped for now because the user was
  concurrently driving the same PMCP CDP browser (`tools/start_pmcp.sh`) to
  test the Variables-tab export upload — running a second live sweep at the
  same time would have raced against that session on the same browser tab.
  Do this on the next live `export_coaching.sh` run.
- Phase A (`parse_bundle()` in `app/coaching_model.py`, `load_model()`
  dispatch on `.json` vs `.html`) is the natural next step and is explicitly
  callable with a synthetic/offline JSON per the plan — not started this
  session, left for a deliberate next pass rather than folded in here.
