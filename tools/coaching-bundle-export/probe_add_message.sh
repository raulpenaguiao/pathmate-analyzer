#!/usr/bin/env bash
# Run the "add a new message" discovery spike against a Chromium already
# launched with a CDP debug port (use the coaching-export workflow's
# tools/start_pmcp.sh) and logged in to PMCP on the Micro Dialogs view.
# READ-ONLY: opens the create-message modal, dumps its fields/tabs/buttons,
# then cancels. Never types, never saves.
#
#   tools/coaching-bundle-export/probe_add_message.sh
#       -> tries a few common greeting dialogs, uses the first that opens
#
#   tools/coaching-bundle-export/probe_add_message.sh "Timeless Greetings"
#       -> probes that specific micro dialog
#
#   tools/coaching-bundle-export/probe_add_message.sh "👋 Hello" "Morning greetings"
#       -> open folder "👋 Hello", then dialog "Morning greetings"
#
# Each argument is ONE segment of the micro dialog's path in the Micro Dialogs
# menu: the folder(s) you would click through, then the dialog leaf. The spike
# just needs some dialog open so it can find the node toolbar's "add" control
# and the create modal - any small pool works.
#
# Output: tools/coaching-bundle-export/spike/add_toolbar.{json,png},
#         tools/coaching-bundle-export/spike/add_modal.{json,png}
#
# Env: PMCP_CDP (default http://127.0.0.1:9222), PYTHON (default .venv/bin/python)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"

if [ -n "${PYTHON:-}" ]; then :
elif [ -x "$REPO/.venv/bin/python" ]; then PYTHON="$REPO/.venv/bin/python"
else PYTHON="python3"; fi

export PMCP_CDP="${PMCP_CDP:-http://127.0.0.1:9222}"

if ! "$PYTHON" -c 'import playwright' 2>/dev/null; then
  echo "playwright not available for '$PYTHON'." >&2
  echo "  run from the repo's virtualenv, or: $PYTHON -m pip install playwright" >&2
  exit 1
fi

if [ "$#" -gt 0 ]; then
  PROBE_LABELS="$("$PYTHON" -c 'import json,sys; print(json.dumps(sys.argv[1:], ensure_ascii=False))' "$@")"
  export PROBE_LABELS
  echo "target micro dialog path: $PROBE_LABELS"
else
  echo "no dialog path given - spike will try common greeting dialogs"
fi

exec "$PYTHON" "$HERE/probe_add_message.py"
