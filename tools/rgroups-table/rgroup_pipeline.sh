#!/usr/bin/env bash
# The r_ randomisation-group pipeline, one interactive run. Four steps, a
# checkpoint between each ("here's the output, next is X, continue?").
#
#   1  rgroup_report.py    coaching.json  -> rgroups_table_<ts>.csv
#   2  rgroup_prepare.py   rgroups_table  -> rgroups_requests_<ts>.csv  (the API-call manifest)
#   3  rgroup_expand.py    + API key + --limit -> rgroups_generated_<ts>.csv
#   4  rgroup_apply.py     + --limit           -> writes to the live coaching (default;
#                                                 pass --dry-run to only preview step 4)
#
# Each step's own output is timestamped (YYMMDDHHMMSS, the run's own clock
# time) and each downstream step defaults to the most RECENTLY-RUN input
# matching file, not a fixed name - re-running an earlier step never
# silently clobbers a prior run's file. The checkpoint messages below
# resolve and print the actual filename each step just produced.
#
# It does NOT run the coaching export — that's costly and rare. You must pass
# a pre-made coaching.json.
#
# Usage:
#   tools/rgroups-table/rgroup_pipeline.sh --json data/exports/coaching.json --limit 10
#     --json FILE   REQUIRED: a coaching.json (from export_coaching.sh)
#     --limit N     REQUIRED: caps API calls in step 3 and variants in step 4
#     --yes         don't pause at the checkpoints
#     --dry-run     preview step 4 instead of writing (step 4 writes by default)
#     --stop-after N  stop after step N (1..4)
#
# ANTHROPIC_API_KEY / OPENAI_API_KEY (step 3) is read from <repo>/.env or env.
# Step 4 needs a logged-in PMCP tab on the CDP browser (tools/start_pmcp.sh).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
PY="$REPO/.venv/bin/python"; [ -x "$PY" ] || PY="python3"
[ -f "$REPO/.env" ] && { set -a; . "$REPO/.env"; set +a; }
DATA="$REPO/data/rgroups"   # where the .py scripts actually read/write these files

JSON=""; LIMIT=""; ASSUME_YES=0; DRY_RUN=0; STOP_AFTER=4
while [ $# -gt 0 ]; do
  case "$1" in
    --json)       JSON="$2"; shift 2 ;;
    --limit)      LIMIT="$2"; shift 2 ;;
    --yes|-y)     ASSUME_YES=1; shift ;;
    --dry-run)    DRY_RUN=1; shift ;;
    --stop-after) STOP_AFTER="$2"; shift 2 ;;
    -h|--help)    sed -n '2,24p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *)            echo "unknown option: $1" >&2; exit 2 ;;
  esac
done
[ -n "$JSON" ]  || { echo "--json FILE is required (a coaching.json)" >&2; exit 2; }
[ -f "$JSON" ]  || { echo "not found: $JSON" >&2; exit 2; }
[ -n "$LIMIT" ] || { echo "--limit N is required" >&2; exit 2; }

step() { printf '\n\033[1m=== step %s ===\033[0m\n' "$*"; }
# most recent $DATA/<prefix>_*.csv by embedded timestamp (sorts correctly as
# a plain string) - mirrors _rgroups_files.latest()'s own logic.
latest_file() { ls -1 "$DATA/$1"_*.csv 2>/dev/null | sort | tail -1; }
checkpoint() {   # $1 = what was produced, $2 = what's next
  [ "$STOP_AFTER" -le "$CUR" ] && { echo "(--stop-after $STOP_AFTER) stopping."; exit 0; }
  [ "$ASSUME_YES" -eq 1 ] && return 0
  printf '\n  output: %s\n  next  : %s\n  continue? [y/N] ' "$1" "$2"
  read -r a; case "$a" in [yY]|[yY][eE][sS]) ;; *) echo "stopped."; exit 0 ;; esac
}

CUR=1
step "1/4  rgroup_report.py"
"$PY" "$HERE/rgroup_report.py" "$JSON"
checkpoint "$(latest_file rgroups_table)" "step 2 — build the API-call manifest"

CUR=2
step "2/4  rgroup_prepare.py"
"$PY" "$HERE/rgroup_prepare.py"
checkpoint "$(latest_file rgroups_requests)" "step 3 — call the LLM for up to $LIMIT pools"

CUR=3
step "3/4  rgroup_expand.py --limit $LIMIT"
"$PY" "$HERE/rgroup_expand.py" --limit "$LIMIT"
checkpoint "$(latest_file rgroups_generated)" \
  "step 4 — $([ "$DRY_RUN" -eq 1 ] && echo 'dry-run against' || echo 'WRITE to') the live coaching (--limit $LIMIT)"

CUR=4
step "4/4  rgroup_apply.py --limit $LIMIT $([ "$DRY_RUN" -eq 1 ] && echo --dry-run)"
if [ "$DRY_RUN" -eq 1 ]; then
  "$PY" "$HERE/rgroup_apply.py" --limit "$LIMIT" --dry-run
else
  "$PY" "$HERE/rgroup_apply.py" --limit "$LIMIT"
fi
echo; echo "done."
