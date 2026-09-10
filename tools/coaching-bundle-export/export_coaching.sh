#!/usr/bin/env bash
# Step 3 of the coaching-export workflow: drive the already-logged-in Chromium
# and write one JSON describing the coaching. See WORKFLOW.md.
#
# Usage:
#   ./export_coaching.sh [options] <output.json>
#
# Options:
#   --report FILE     Report-HTML export of the same coaching. Adds full
#                     per-language text + decision-branch logic. Recommended.
#   --dialogs-only    only the Micro Dialogs sweep (content + randomisation
#                     groups). No Rules sweep, no live writes.
#   --rules-only      only the Rules sweep (rule tree + per-rule timing).
#   --no-rules        alias for --dialogs-only.
#   --cdp URL         CDP endpoint (default http://127.0.0.1:9222).
#   --workdir DIR     scratch dir for intermediate bundles
#                     (default: <repo>/data/rgroups).
#   --yes             don't pause for the "switch the browser view" prompts.
#
# The Rules sweep opens every sending rule's "Edit rule:" modal; closing each
# one fires a no-op "The rule has been updated." toast. Use it on sandbox
# coachings only, and add an entry under autochanges/.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY="python3"

CDP="http://127.0.0.1:9222"
WORKDIR="$REPO/data/rgroups"
REPORT=""
DO_DIALOGS=1
DO_RULES=1
ASSUME_YES=0
OUT=""

while [ $# -gt 0 ]; do
  case "$1" in
    --report)        REPORT="$2"; shift 2 ;;
    --dialogs-only|--no-rules) DO_RULES=0; shift ;;
    --rules-only)     DO_DIALOGS=0; shift ;;
    --cdp)           CDP="$2"; shift 2 ;;
    --workdir)       WORKDIR="$2"; shift 2 ;;
    --yes|-y)        ASSUME_YES=1; shift ;;
    -h|--help)       sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*)              echo "unknown option: $1" >&2; exit 2 ;;
    *)               OUT="$1"; shift ;;
  esac
done

[ -n "$OUT" ] || { echo "need an output filename, e.g. ./export_coaching.sh alex_v01.json" >&2; exit 2; }
case "$OUT" in *.json) ;; *) OUT="$OUT.json" ;; esac
mkdir -p "$WORKDIR"

if ! curl -sf "${CDP}/json/version" >/dev/null 2>&1; then
  echo "No CDP browser at ${CDP}. Run ./open_chromium.sh first." >&2
  exit 1
fi
if [ -n "$REPORT" ] && [ ! -f "$REPORT" ]; then
  echo "--report file not found: $REPORT" >&2; exit 1
fi

export PMCP_CDP="$CDP"
export PMCP_OUT="$WORKDIR"

pause() {
  [ "$ASSUME_YES" -eq 1 ] && return 0
  printf '\n>>> %s\n    Press Enter when ready (Ctrl-C to abort)... ' "$1"
  read -r _
}

echo "workdir : $WORKDIR"
echo "output  : $OUT"
echo "cdp     : $CDP"
echo

if [ "$DO_DIALOGS" -eq 1 ]; then
  pause "Put the browser on this coaching's MICRO DIALOGS view (Edit -> Micro Dialogs, Monitoring inactive, one dialog's table visible)."
  echo "--- Micro Dialogs sweep (export_bundle.py) ---"
  if [ -n "$REPORT" ]; then
    "$PY" "$HERE/export_bundle.py" --enrich "$REPORT"
  else
    "$PY" "$HERE/export_bundle.py"
  fi
fi

if [ "$DO_RULES" -eq 1 ]; then
  pause "Now put the browser on this coaching's RULES tab (Edit -> Rules, the tree with the four 'Execution on ...' rows visible)."
  echo "--- Rules sweep (export_rules.py --merge) ---"
  "$PY" "$HERE/export_rules.py" --merge
fi

# pick the richest bundle that got produced
SRC=""
for cand in \
  "$WORKDIR/coaching.bundle.v3.json" \
  "$WORKDIR/coaching.bundle.v2.json" \
  "$WORKDIR/coaching.bundle.json" \
  "$WORKDIR/coaching.rules.json" ; do
  if [ -f "$cand" ]; then SRC="$cand"; break; fi
done
[ -n "$SRC" ] || { echo "no bundle was produced in $WORKDIR" >&2; exit 1; }

cp "$SRC" "$OUT"
echo
echo "wrote $OUT   (from $(basename "$SRC"))"
"$PY" - "$OUT" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
md = d.get("microDialogs") or []
nd = d.get("nodes") or []
rules = (d.get("rules") or {})
print(f"  micro dialogs : {len(md)}")
print(f"  nodes         : {len(nd)}")
rt = rules.get("ruleTree")
sr = rules.get("sendingRules")
if rt is not None:
    print(f"  rule tree     : {len(rt)} rules")
if sr is not None:
    print(f"  sending rules : {len(sr)}")
PY
