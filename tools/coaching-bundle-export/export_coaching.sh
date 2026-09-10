#!/usr/bin/env bash
# Thin wrapper around export_coaching.py: one manual pause for the Monitoring
# toggle, then run the single-file export. See WORKFLOW.md.
#
# Usage:  ./export_coaching.sh [options] [output.json]
#   output.json defaults to data/rgroups/coaching_<slug>_<YYYYMMDD-HHMMSS>.json
#   passes every option straight through to export_coaching.py:
#     --report FILE      enrich from the coaching's Report-HTML export
#     --dialogs-only     Micro Dialogs sweep only (no live writes)
#     --rules-only       Rules sweep only
#     --no-modals        rules tree skeleton only, no "Edit rule:" modals
#     --update-baseline  rewrite coherence_baseline.json from this run
#   plus:
#     --yes / -y         don't pause for the Monitoring step
#     --cdp URL          CDP endpoint (default http://127.0.0.1:9222)
#
# Prereq: tools/start_pmcp.sh (launches Chromium + logs in).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
PY="$REPO/.venv/bin/python"; [ -x "$PY" ] || PY="python3"

CDP="http://127.0.0.1:9222"
ASSUME_YES=0
PASS=()
for a in "$@"; do
  case "$a" in
    --yes|-y) ASSUME_YES=1 ;;
    --cdp)    CDP="__next__" ;;
    *)        if [ "$CDP" = "__next__" ]; then CDP="$a"; else PASS+=("$a"); fi ;;
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

exec "$PY" "$HERE/export_coaching.py" "${PASS[@]}"
