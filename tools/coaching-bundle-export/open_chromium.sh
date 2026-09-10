#!/usr/bin/env bash
# Step 1 of the coaching-export workflow: launch a Chromium with a DevTools
# debug port that the export scripts attach to. See WORKFLOW.md.
#
# Usage:  ./open_chromium.sh [port] [url]
#   port  CDP port (default 9222)
#   url   initial page (default the PMCP admin login)
set -euo pipefail

PORT="${1:-9222}"
URL="${2:-https://cp22.pathmate.cloud/PMCP/admin}"
PROFILE="${PMCP_CDP_PROFILE:-/tmp/pmcp-cdp-profile}"

if curl -sf "http://127.0.0.1:${PORT}/json/version" >/dev/null 2>&1; then
  echo "A CDP browser is already listening on :${PORT} — reusing it."
  echo "If it's the wrong one, close it and re-run this script."
  exit 0
fi

# Find a Chromium/Chrome binary. Playwright's bundled one is preferred
# (no flatpak sandbox surprises).
CANDIDATES=(
  "${CHROME:-}"
  "$HOME"/.cache/ms-playwright/chromium-*/chrome-linux*/chrome
  /usr/bin/google-chrome
  /usr/bin/chromium
  /usr/bin/chromium-browser
  /snap/bin/chromium
)
CHROME_BIN=""
for c in "${CANDIDATES[@]}"; do
  [ -n "$c" ] || continue
  for expanded in $c; do
    if [ -x "$expanded" ]; then CHROME_BIN="$expanded"; break 2; fi
  done
done
if [ -z "$CHROME_BIN" ]; then
  echo "No Chromium/Chrome binary found." >&2
  echo "Install one, or set CHROME=/path/to/chrome and re-run." >&2
  echo "Playwright's: .venv/bin/python -m playwright install chromium" >&2
  exit 1
fi

echo "Launching: $CHROME_BIN"
echo "  debug port : ${PORT}"
echo "  profile dir: ${PROFILE}  (throwaway — you log in each session)"
setsid nohup "$CHROME_BIN" \
  --remote-debugging-port="${PORT}" \
  --user-data-dir="${PROFILE}" \
  --no-first-run --no-default-browser-check --start-maximized \
  "${URL}" >/tmp/pmcp-chrome-${PORT}.log 2>&1 &
disown || true

# cold profile + slow GL init can take ~10-20s to bring the debug port up
for _ in $(seq 1 60); do
  if curl -sf "http://127.0.0.1:${PORT}/json/version" >/dev/null 2>&1; then
    echo
    echo "Ready. CDP is live on http://127.0.0.1:${PORT}"
    echo
    echo "Next (by hand, in the browser window): open your coaching -> Edit"
    echo "  -> Basic Settings and Modules -> Monitoring: click to DEACTIVATE."
    echo "Login is handled by export_coaching.sh from .env; then run:"
    echo "  ./export_coaching.sh <output-name>.json"
    exit 0
  fi
  sleep 0.5
done

echo "Browser started but :${PORT} never came up after 30s." >&2
echo "--- tail of /tmp/pmcp-chrome-${PORT}.log ---" >&2
tail -15 "/tmp/pmcp-chrome-${PORT}.log" >&2 || true
echo "If you see 'DevTools listening on ws://127.0.0.1:${PORT}' above, it's" >&2
echo "just slow — wait a few seconds and re-run the export directly." >&2
exit 1
