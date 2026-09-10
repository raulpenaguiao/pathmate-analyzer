#!/usr/bin/env bash
# Start a Chromium with a DevTools debug port and log it into the PMCP admin
# from .env. Shared by the tools that drive the live PMCP editor over CDP.
# See tools/coaching-bundle-export/WORKFLOW.md.
#
# Usage:  ./start_pmcp.sh [options]
#   --port N       CDP port (default 9222)
#   --url URL      initial page (default the PMCP admin login)
#   --env FILE     credentials file (default <repo>/.env; keys PMCP_USERNAME /
#                  PMCP_PASSWORD / PMCP_TOTP_SECRET)
#   --no-login     just launch the browser; log in by hand
#
# After this: in the browser, open your coaching -> Edit -> deactivate
# Monitoring, then run the tool's export (e.g.
# tools/coaching-bundle-export/export_coaching.sh <name>.json).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY="python3"

PORT=9222
URL="https://cp22.pathmate.cloud/PMCP/admin"
ENV_FILE="$REPO/.env"
DO_LOGIN=1
PROFILE="${PMCP_CDP_PROFILE:-/tmp/pmcp-cdp-profile}"

while [ $# -gt 0 ]; do
  case "$1" in
    --port)      PORT="$2"; shift 2 ;;
    --url)       URL="$2"; shift 2 ;;
    --env)       ENV_FILE="$2"; shift 2 ;;
    --no-login)  DO_LOGIN=0; shift ;;
    -h|--help)   sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *)           echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

launch_browser() {
  if curl -sf "http://127.0.0.1:${PORT}/json/version" >/dev/null 2>&1; then
    echo "A CDP browser is already listening on :${PORT} — reusing it."
    return 0
  fi

  # Find a Chromium/Chrome binary. Playwright's bundled one is preferred
  # (no flatpak sandbox surprises).
  local CANDIDATES=(
    "${CHROME:-}"
    "$HOME"/.cache/ms-playwright/chromium-*/chrome-linux*/chrome
    /usr/bin/google-chrome /usr/bin/chromium /usr/bin/chromium-browser /snap/bin/chromium
  )
  local CHROME_BIN="" c expanded
  for c in "${CANDIDATES[@]}"; do
    [ -n "$c" ] || continue
    for expanded in $c; do
      if [ -x "$expanded" ]; then CHROME_BIN="$expanded"; break 2; fi
    done
  done
  if [ -z "$CHROME_BIN" ]; then
    echo "No Chromium/Chrome binary found. Set CHROME=/path/to/chrome, or:" >&2
    echo "  $PY -m playwright install chromium" >&2
    exit 1
  fi

  echo "Launching: $CHROME_BIN"
  echo "  debug port : ${PORT}"
  echo "  profile dir: ${PROFILE}  (throwaway — you log in each session)"
  # --no-sandbox: Debian 13 / Ubuntu 23.10+ restrict unprivileged user
  # namespaces (AppArmor), so Chromium's zygote sandbox fails to start
  # ("No usable sandbox!"). Fine here — throwaway profile, one known site.
  setsid nohup "$CHROME_BIN" \
    --remote-debugging-port="${PORT}" \
    --user-data-dir="${PROFILE}" \
    --no-sandbox \
    --no-first-run --no-default-browser-check --start-maximized \
    "${URL}" >"/tmp/pmcp-chrome-${PORT}.log" 2>&1 &
  disown || true

  # A cold profile + slow Wayland/GL init: the debug port usually comes up in
  # ~10-20s, occasionally up to a minute.
  echo "Waiting for the debug port (cold start can take up to ~1 min)..."
  local i
  for i in $(seq 1 120); do
    if curl -sf "http://127.0.0.1:${PORT}/json/version" >/dev/null 2>&1; then
      echo "CDP live on http://127.0.0.1:${PORT}"
      return 0
    fi
    sleep 0.5
  done
  echo "Browser started but :${PORT} never came up after ~1 min." >&2
  echo "--- tail of /tmp/pmcp-chrome-${PORT}.log ---" >&2
  tail -15 "/tmp/pmcp-chrome-${PORT}.log" >&2 || true
  exit 1
}

launch_browser

if [ "$DO_LOGIN" -eq 1 ]; then
  echo
  echo "--- login (pmcp_login.py) ---"
  if PMCP_CDP="http://127.0.0.1:${PORT}" "$PY" "$HERE/pmcp_login.py" --env "$ENV_FILE"; then
    echo "login OK."
  else
    echo "auto-login did not complete — finish it by hand in the browser." >&2
    exit 1
  fi
fi

echo
echo "Ready. Next:"
echo "  1. In the browser: open your coaching -> Edit -> Basic Settings and"
echo "     Modules -> Monitoring: click to DEACTIVATE."
echo "  2. Run the export, e.g.:"
echo "     tools/coaching-bundle-export/export_coaching.sh <output-name>.json"
