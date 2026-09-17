#!/usr/bin/env bash
# Thin wrapper around export_coaching.py: one manual pause for the Monitoring
# toggle, then run the single-file export. See WORKFLOW.md.
#
# Usage:  ./export_coaching.sh [options] [output.json]
#   output.json defaults to data/exports/coaching_<slug>_<YYYYMMDD-HHMMSS>.json
#   passes every option straight through to export_coaching.py:
#     --report FILE      use this Report-HTML export instead of auto-fetching
#     --no-report        skip the Report HTML entirely (no auto-fetch)
#     --dialogs-only     Micro Dialogs sweep only (no live writes)
#     --rules-only       Rules sweep only
#     --no-modals        rules tree skeleton only, no "Edit rule:" modals
#     --no-variables     skip the Variables-tab sweep (~2 min on its own)
#     --update-baseline  rewrite coherence_baseline.json from this run
#   plus:
#     --yes / -y         don't pause for the Monitoring step
#     --cdp URL          CDP endpoint (default http://127.0.0.1:9222)
#     --with-rgroups     also run tools/rgroups-table/rgroup_report.py
#                        (--md) against this run's own output — one run
#                        gives coaching.json AND an up-to-date
#                        rgroups_table.csv + rgroups_report.md, no browser
#                        involved for that second step (parses the JSON).
#                        Skipped with a warning if the export's own output
#                        path can't be found in its log (e.g. it crashed
#                        before writing anything).
#
# Prereq: tools/start_pmcp.sh (launches Chromium + logs in).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
PY="$REPO/.venv/bin/python"; [ -x "$PY" ] || PY="python3"

CDP="http://127.0.0.1:9222"
ASSUME_YES=0
WITH_RGROUPS=0
PASS=()
for a in "$@"; do
  case "$a" in
    --yes|-y)       ASSUME_YES=1 ;;
    --with-rgroups) WITH_RGROUPS=1 ;;
    --cdp)          CDP="__next__" ;;
    *)              if [ "$CDP" = "__next__" ]; then CDP="$a"; else PASS+=("$a"); fi ;;
  esac
done

if ! curl -sf "${CDP}/json/version" >/dev/null 2>&1; then
  echo "No CDP browser at ${CDP}. Run  tools/start_pmcp.sh  first." >&2
  exit 1
fi
export PMCP_CDP="$CDP"

if [ "$ASSUME_YES" -eq 0 ]; then
  printf '\n============================================================\n'
  printf '  ACTION NEEDED IN THE BROWSER:\n'
  printf '  Open your coaching -> Edit -> Basic Settings and Modules ->\n'
  printf '  Monitoring: click to DEACTIVATE.  (Never touched by the script.)\n'
  printf '============================================================\n'
  printf '  Press Enter when done (Ctrl-C to abort)... '
  read -r _
fi

if [ "$WITH_RGROUPS" -eq 0 ]; then
  exec "$PY" "$HERE/export_coaching.py" "${PASS[@]}"
fi

OUT_LOG="$(mktemp)"
trap 'rm -f "$OUT_LOG"' EXIT
set +e
"$PY" "$HERE/export_coaching.py" "${PASS[@]}" | tee "$OUT_LOG"
RC=${PIPESTATUS[0]}
set -e

OUT_JSON="$(grep -m1 '^wrote ' "$OUT_LOG" | sed 's/^wrote //')"
if [ -n "$OUT_JSON" ] && [ -f "$REPO/$OUT_JSON" -o -f "$OUT_JSON" ]; then
  [ -f "$OUT_JSON" ] || OUT_JSON="$REPO/$OUT_JSON"
  printf '\n--- rgroups report (--with-rgroups) ---\n'
  "$PY" "$REPO/tools/rgroups-table/rgroup_report.py" "$OUT_JSON" --md || true
else
  echo "! --with-rgroups: could not find the export's output path in its log — skipping" >&2
fi
exit "$RC"
