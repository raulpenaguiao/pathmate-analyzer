#!/usr/bin/env bash
# The r_ randomisation-group pipeline, one interactive run. Four steps, a
# checkpoint between each ("here's the output, next is X, continue?").
#
#   1  rgroup_report.py    coaching.json  -> rgroups_table.csv
#   2  rgroup_prepare.py   rgroups_table  -> rgroups_requests.csv  (the API-call manifest)
#   3  rgroup_expand.py    + API key + --limit -> rgroups_generated.csv
#   4  rgroup_apply.py     + --limit --apply   -> writes to the live coaching
#
# It does NOT run the coaching export — that's costly and rare. You must pass
# a pre-made coaching.json.
#
# Usage:
#   tools/rgroups-table/rgroup_pipeline.sh --json data/exports/coaching.json --limit 10
#     --json FILE   REQUIRED: a coaching.json (from export_coaching.sh)
#     --limit N     REQUIRED: caps API calls in step 3 and variants in step 4
#     --yes         don't pause at the checkpoints
#     --apply       let step 4 actually write (default: step 4 dry-run)
#     --stop-after N  stop after step N (1..4)
#
# ANTHROPIC_API_KEY / OPENAI_API_KEY (step 3) is read from <repo>/.env or env.
# Step 4 needs a logged-in PMCP tab on the CDP browser (tools/start_pmcp.sh).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
PY="$REPO/.venv/bin/python"; [ -x "$PY" ] || PY="python3"
[ -f "$REPO/.env" ] && { set -a; . "$REPO/.env"; set +a; }

JSON=""; LIMIT=""; ASSUME_YES=0; DO_APPLY=0; STOP_AFTER=4
while [ $# -gt 0 ]; do
  case "$1" in
    --json)       JSON="$2"; shift 2 ;;
    --limit)      LIMIT="$2"; shift 2 ;;
    --yes|-y)     ASSUME_YES=1; shift ;;
    --apply)      DO_APPLY=1; shift ;;
    --stop-after) STOP_AFTER="$2"; shift 2 ;;
    -h|--help)    sed -n '2,24p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *)            echo "unknown option: $1" >&2; exit 2 ;;
  esac
done
[ -n "$JSON" ]  || { echo "--json FILE is required (a coaching.json)" >&2; exit 2; }
[ -f "$JSON" ]  || { echo "not found: $JSON" >&2; exit 2; }
[ -n "$LIMIT" ] || { echo "--limit N is required" >&2; exit 2; }

step() { printf '\n\033[1m=== step %s ===\033[0m\n' "$*"; }
checkpoint() {   # $1 = what was produced, $2 = what's next
  [ "$STOP_AFTER" -le "$CUR" ] && { echo "(--stop-after $STOP_AFTER) stopping."; exit 0; }
  [ "$ASSUME_YES" -eq 1 ] && return 0
  printf '\n  output: %s\n  next  : %s\n  continue? [y/N] ' "$1" "$2"
  read -r a; case "$a" in [yY]|[yY][eE][sS]) ;; *) echo "stopped."; exit 0 ;; esac
}

CUR=1
step "1/4  rgroup_report.py"
"$PY" "$HERE/rgroup_report.py" "$JSON"
checkpoint "$HERE/rgroups_table.csv" "step 2 — build the API-call manifest"

CUR=2
step "2/4  rgroup_prepare.py"
"$PY" "$HERE/rgroup_prepare.py"
checkpoint "$HERE/rgroups_requests.csv" "step 3 — call the LLM for up to $LIMIT pools"

CUR=3
step "3/4  rgroup_expand.py --limit $LIMIT"
"$PY" "$HERE/rgroup_expand.py" --limit "$LIMIT"
checkpoint "$HERE/rgroups_generated.csv" \
  "step 4 — $([ "$DO_APPLY" -eq 1 ] && echo 'WRITE to' || echo 'dry-run against') the live coaching (--limit $LIMIT)"

CUR=4
step "4/4  rgroup_apply.py --limit $LIMIT $([ "$DO_APPLY" -eq 1 ] && echo --apply)"
if [ "$DO_APPLY" -eq 1 ]; then
  "$PY" "$HERE/rgroup_apply.py" --limit "$LIMIT" --apply
else
  "$PY" "$HERE/rgroup_apply.py" --limit "$LIMIT"
  echo "(dry run — pass --apply to write)"
fi
echo; echo "done."
