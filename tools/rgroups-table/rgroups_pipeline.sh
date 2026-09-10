#!/usr/bin/env bash
# The r_ randomisation-group pipeline, end to end (rename of rebuild_all.sh):
#
#   1. obtain a bundle JSON  (BUNDLE=... , or reuse , or live scrape)
#   2. build_table.py                     -> rgroups_table.csv + rgroups_summary.csv
#   3. expand_rgroups.py                  -> rgroups_table.expanded.csv + expand_prompts.txt
#   4. render_review_report.py            -> rgroups_review.md
#
# Step 1 preferred path: pass BUNDLE=/path/to/coaching.json - any JSON meeting
# the contract in README.md ("Bundle JSON contract"). The project-wide coaching
# export (tools/coaching-bundle-export/export_coaching.py) produces exactly
# this. Without BUNDLE, step 1 runs that export itself (needs the browser from
# tools/start_pmcp.sh and the coaching's Report-HTML export on disk).
#
# Usage:
#   BUNDLE=/path/to/coaching.json tools/rgroups-table/rgroups_pipeline.sh
#   tools/rgroups-table/rgroups_pipeline.sh /path/to/Report_export.html   # run the export
#
# Env / knobs:
#   BUNDLE        ready-made coaching JSON; skips step 1 entirely (the forward path)
#   REPORT_HTML   Report HTML export path (or pass as $1). Needed only to run the export.
#   PMCP_CDP      CDP endpoint of the logged-in Chromium   (default http://127.0.0.1:9222)
#   PMCP_WIDE     window width px to defeat the menu overflow (forwarded to the export)
#   PYTHON        interpreter to use (default: <repo>/.venv/bin/python, else python3)
#   TARGET        healthy-pool size, forwarded to build_table.py + expand_rgroups.py (default 10)
#   EXPAND_ARGS   extra args for expand_rgroups.py, e.g. "--limit 10" or "--dry-run"
#   SKIP_EXPORT=1 reuse the existing data/exports/coaching.json (skip step 1)
#   SKIP_EXPAND=1 stop after build_table.py (no API calls, no report)
#
# ANTHROPIC_API_KEY is read from <repo>/.env (git-ignored) or the environment.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
EXPORT_DIR="$REPO/tools/coaching-bundle-export"
DATA_DIR="$REPO/data/exports"
DEFAULT_BUNDLE="$DATA_DIR/coaching.json"

REPORT_HTML="${REPORT_HTML:-${1:-}}"
EXPAND_ARGS="${EXPAND_ARGS:-}"
# BUNDLE: consume a ready-made bundle JSON and skip the scrape entirely. This is
# the forward path - once the project-wide Playwright coaching export exists,
# point BUNDLE at its output and step 1 below is never used. Contract for what
# the JSON must contain: README.md "Bundle JSON contract".
BUNDLE="${BUNDLE:-}"

if [ -n "${PYTHON:-}" ]; then
  :
elif [ -x "$REPO/.venv/bin/python" ]; then
  PYTHON="$REPO/.venv/bin/python"
else
  PYTHON="python3"
fi

# .env -> environment (ANTHROPIC_API_KEY etc.); never fatal if absent
if [ -f "$REPO/.env" ]; then
  set -a; . "$REPO/.env"; set +a
fi

step() { printf '\n\033[1m=== %s ===\033[0m\n' "$*"; }

# --- step 1: obtain a coaching JSON --------------------------------------
# Prefer a ready-made bundle (BUNDLE=...); else reuse the last export
# (SKIP_EXPORT=1); else run the project-wide coaching export.
if [ -n "$BUNDLE" ]; then
  step "1/4 bundle  (using pre-supplied BUNDLE, no export)"
  [ -f "$BUNDLE" ] || { echo "BUNDLE not found: $BUNDLE" >&2; exit 1; }
elif [ "${SKIP_EXPORT:-}" = "1" ]; then
  BUNDLE="$DEFAULT_BUNDLE"
  step "1/4 bundle  (SKIP_EXPORT=1, reusing $BUNDLE)"
  [ -f "$BUNDLE" ] || { echo "SKIP_EXPORT set but $BUNDLE is missing" >&2; exit 1; }
else
  BUNDLE="$DEFAULT_BUNDLE"
  [ -n "$REPORT_HTML" ] || { echo "REPORT_HTML not set (pass the Report HTML export path as \$1, or set BUNDLE=/path/to/coaching.json)" >&2; exit 1; }
  [ -f "$REPORT_HTML" ] || { echo "Report HTML not found: $REPORT_HTML" >&2; exit 1; }
  step "1/4 export_coaching.sh --report  (needs tools/start_pmcp.sh browser)"
  mkdir -p "$DATA_DIR"
  ${PMCP_WIDE:+PMCP_WIDE="$PMCP_WIDE"} \
    "$EXPORT_DIR/export_coaching.sh" --yes --cdp "${PMCP_CDP:-http://127.0.0.1:9222}" \
      --report "$REPORT_HTML" "$BUNDLE"
  [ -f "$BUNDLE" ] || { echo "export finished but $BUNDLE was not produced" >&2; exit 1; }
fi

# --- step 2: bundle -> tables + r_ groups report -------------------------
step "2/5 build_table.py"
TARGET="${TARGET:-10}" "$PYTHON" "$HERE/build_table.py" "$BUNDLE"

step "3/5 report.py  (r_ groups summary, from $BUNDLE)"
"$PYTHON" "$HERE/report.py" "$BUNDLE"

if [ "${SKIP_EXPAND:-}" = "1" ]; then
  step "4-5/5 expand + review  (SKIPPED, SKIP_EXPAND=1)"
  echo "tables + report rebuilt; stop here."
  echo "report:  $HERE/rgroups_report.md"
  exit 0
fi

# --- step 4: top up thin pools with the LLM -----------------------------
step "4/5 expand_rgroups.py $EXPAND_ARGS"
case " $EXPAND_ARGS " in
  *" --dry-run "*) : ;;
  *) [ -n "${ANTHROPIC_API_KEY:-}" ] || { echo "ANTHROPIC_API_KEY not set (put it in $REPO/.env)" >&2; exit 1; } ;;
esac
# shellcheck disable=SC2086
TARGET="${TARGET:-10}" "$PYTHON" "$HERE/expand_rgroups.py" $EXPAND_ARGS

# --- step 5: render the human review report ---------------------------
step "5/5 render_review_report.py"
"$PYTHON" "$HERE/render_review_report.py"

step "done"
echo "report:  $HERE/rgroups_report.md"
echo "review:  $HERE/rgroups_review.md"
