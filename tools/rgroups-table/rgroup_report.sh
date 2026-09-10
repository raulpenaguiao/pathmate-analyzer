#!/usr/bin/env bash
# Thin wrapper for step: rgroup_report.py  — see that file's docstring / -h.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
PY="$REPO/.venv/bin/python"; [ -x "$PY" ] || PY="python3"
[ -f "$REPO/.env" ] && { set -a; . "$REPO/.env"; set +a; }
exec "$PY" "$HERE/rgroup_report.py" "$@"
