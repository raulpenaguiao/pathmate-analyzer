#!/usr/bin/env bash
# Start a Chromium with a DevTools debug port and log it into CoachStudio
# Designer (the "PCMS" portal at my.pathmate.app) using credentials from
# .env. Mirrors tools/start_pmcp.sh, adapted for this app's login form,
# which is a plain React/antd form (stable #id selectors, no Vaadin
# dynamic-ID discovery needed) rather than PMCP admin's Vaadin one.
#
# Usage:  ./start_pcms.sh [options]
#   --port N       CDP port (default 9224 - different from start_pmcp.sh's
#                  9222 so both portals can run side by side)
#   --url URL      initial page (default the PCMS-ALEX login page)
#   --env FILE     credentials file (default <repo>/.env). Keys:
#                    PCMS_USERNAME     portal username        (required)
#                    PCMS_PASSWORD     portal password        (required)
#                    PCMS_TOTP_SECRET  base32 2FA seed        (optional; if
#                                      unset, the form's own hint - "enter
#                                      your authentication code, or 0 if
#                                      not configured" - is followed: "0"
#                                      is tried first, and if login is then
#                                      rejected it falls back to waiting
#                                      ~2 min for you to type the real code)
#   --no-login     just launch the browser; log in by hand
#
# Verified end to end 2026-09-17 (fresh browser, real credentials incl. TOTP).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY="python3"

PORT=9224
URL="https://my.pathmate.app/pcms-alex/login"
ENV_FILE="$REPO/.env"
DO_LOGIN=1
PROFILE="${PCMS_CDP_PROFILE:-/tmp/pcms-cdp-profile}"

while [ $# -gt 0 ]; do
  case "$1" in
    --port)      PORT="$2"; shift 2 ;;
    --url)       URL="$2"; shift 2 ;;
    --env)       ENV_FILE="$2"; shift 2 ;;
    --no-login)  DO_LOGIN=0; shift ;;
    -h|--help)   sed -n '2,26p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *)           echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

# ---------------------------------------------------------------------------
# 1. launch the browser (skip if one is already on the port)
# ---------------------------------------------------------------------------
if curl -sf "http://127.0.0.1:${PORT}/json/version" >/dev/null 2>&1; then
  echo "A CDP browser is already listening on :${PORT} — reusing it."
else
  CANDIDATES=(
    "${CHROME:-}"
    "$HOME"/.cache/ms-playwright/chromium-*/chrome-linux*/chrome
    /usr/bin/google-chrome /usr/bin/chromium /usr/bin/chromium-browser /snap/bin/chromium
  )
  CHROME_BIN=""
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
    "${URL}" >"/tmp/pcms-chrome-${PORT}.log" 2>&1 &
  disown || true

  # Cold profile + slow Wayland/GL init: the debug port usually comes up in
  # ~10-20s, occasionally up to a minute.
  echo "Waiting for the debug port (cold start can take up to ~1 min)..."
  for _ in $(seq 1 120); do
    if curl -sf "http://127.0.0.1:${PORT}/json/version" >/dev/null 2>&1; then
      echo "CDP live on http://127.0.0.1:${PORT}"
      break
    fi
    sleep 0.5
  done
  if ! curl -sf "http://127.0.0.1:${PORT}/json/version" >/dev/null 2>&1; then
    echo "Browser started but :${PORT} never came up after ~1 min." >&2
    echo "--- tail of /tmp/pcms-chrome-${PORT}.log ---" >&2
    tail -15 "/tmp/pcms-chrome-${PORT}.log" >&2 || true
    exit 1
  fi
fi

# ---------------------------------------------------------------------------
# 2. log in from .env  (Playwright: bash can't drive it, so a small embedded
#    Python step. Idempotent — no-op if already past the login page.)
# ---------------------------------------------------------------------------
if [ "$DO_LOGIN" -eq 1 ]; then
  echo
  echo "--- login ---"
  if PCMS_CDP="http://127.0.0.1:${PORT}" PCMS_ENV_FILE="$ENV_FILE" "$PY" - <<'PY'
import asyncio, base64, hashlib, hmac, os, struct, sys, time
from pathlib import Path
from playwright.async_api import async_playwright

CDP = os.environ["PCMS_CDP"]
ENV_FILE = Path(os.environ["PCMS_ENV_FILE"])


def log(m): print(m, flush=True)


def load_env(path):
    env = {}
    if path.is_file():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def totp(secret, digits=6, period=30, at=None):
    raw = "".join(secret.split()).upper()
    raw += "=" * (-len(raw) % 8)
    key = base64.b32decode(raw)
    counter = int((at if at is not None else time.time()) // period)
    mac = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    off = mac[-1] & 0x0F
    code = struct.unpack(">I", mac[off:off + 4])[0] & 0x7FFFFFFF
    return str(code % (10 ** digits)).zfill(digits)


# Confirmed live 2026-09-17: a plain React/antd login form with STABLE ids
# (#login_username / #login_password / #login_authCode) - none of PMCP
# admin's Vaadin dynamic-ID discovery is needed here. The authCode field's
# own validation message ("Please enter your authentication code, or "0"
# if not configured.") is the form's own documented convention for
# accounts without 2FA enabled.
LOGIN_PAGE_JS = r"""
() => !!document.querySelector('#login_username')
"""

LOGGED_IN_JS = r"""
() => !location.pathname.endsWith('/login') && !document.querySelector('#login_password')
"""

ERROR_JS = r"""
() => [...document.querySelectorAll(
    '.ant-message-notice-content, .ant-notification-notice-message, '
  + '.ant-notification-notice-description, .ant-form-item-explain-error')]
  .map(e => e.textContent.trim()).filter(Boolean)
"""


async def vfill(page, sel, value):
    loc = page.locator(sel)
    for _ in range(3):
        try:
            await loc.click(timeout=5000)
            await loc.press("Control+a"); await loc.press("Delete")
            await loc.press_sequentially(value, delay=15)
            await page.wait_for_timeout(200)
            if (await loc.input_value()) == value:
                return True
        except Exception:
            pass
        await page.wait_for_timeout(800)
    return False


async def _acquire_page(apw, url):
    b = await apw.chromium.connect_over_cdp(CDP)
    ctx = b.contexts[0]
    pages = [p for p in ctx.pages if not p.is_closed()]
    page = next((p for p in pages if "pathmate" in (p.url or "")),
                pages[0] if pages else None)
    if page is None:
        page = await ctx.new_page()
    if "pathmate" not in (page.url or ""):
        await page.goto(url, wait_until="domcontentloaded")
    return page


async def do_login(apw, user, pw, secret, url) -> int:
    page = await _acquire_page(apw, url)
    log(f"attached to page: {page.url}")

    if await page.evaluate(LOGGED_IN_JS):
        log("already logged in"); return 0
    if not (user and pw):
        print("PCMS_USERNAME / PCMS_PASSWORD not set in .env — log in by "
              "hand in the browser.", file=sys.stderr); return 2

    log("waiting for the login form to be ready...")
    for i in range(30):
        if await page.evaluate(LOGIN_PAGE_JS):
            break
        if await page.evaluate(LOGGED_IN_JS):
            log("logged in"); return 0
        await page.wait_for_timeout(1500)
    else:
        print("login form never became ready — reload the page and rerun.",
              file=sys.stderr); return 2

    log("form ready — typing username + password")
    u_ok = await vfill(page, "#login_username", user)
    p_ok = await vfill(page, "#login_password", pw)
    if not (u_ok and p_ok):
        print("could not type username/password into the form — log in by "
              "hand.", file=sys.stderr); return 2
    log("  username + password entered")

    async def fill_code(code):
        await vfill(page, "#login_authCode", code)

    if secret:
        code = totp(secret)
        await fill_code(code)
        log(f"  2FA code entered ({code})")
    else:
        # this form's own validation hint: "...or '0' if not configured"
        await fill_code("0")
        log("  no PCMS_TOTP_SECRET set — tried the form's own \"0\" "
            "(not-configured) convention first")

    log("clicking Log in...")
    await page.locator("button", has_text="Log in").click()
    for _ in range(20):
        await page.wait_for_timeout(1000)
        if await page.evaluate(LOGGED_IN_JS):
            log("logged in"); return 0
        errs = await page.evaluate(ERROR_JS)
        if errs:
            if not secret and any("authentication code" in e.lower() or "2fa" in e.lower()
                                   or "two-factor" in e.lower() for e in errs):
                log("  \"0\" didn't work - this account has real 2FA. "
                    ">>> type your 6-digit code in the browser now "
                    "(waiting up to ~2 min).")
                deadline = time.time() + 130
                while time.time() < deadline:
                    await page.wait_for_timeout(2000)
                    if await page.evaluate(LOGGED_IN_JS):
                        log("logged in"); return 0
                print("timed out waiting for the 2FA code.", file=sys.stderr)
                return 2
            print(f"  login rejected: {' | '.join(errs)}", file=sys.stderr)
            return 2
    print("could not confirm login — finish it by hand in the browser.",
          file=sys.stderr)
    return 2


async def main():
    fe = load_env(ENV_FILE)
    env = {**os.environ, **{k: v for k, v in fe.items() if v}}
    user, pw = env.get("PCMS_USERNAME"), env.get("PCMS_PASSWORD")
    secret = env.get("PCMS_TOTP_SECRET")
    url = env.get("PCMS_LOGIN_URL", "https://my.pathmate.app/pcms-alex/login")
    log(f"env: {ENV_FILE}  ->  username={'set' if user else 'MISSING'}, "
        f"password={'set' if pw else 'MISSING'}, "
        f"totp_secret={'set' if secret else 'not set (will try 0, then manual)'}")

    apw = await async_playwright().start()
    for attempt in range(3):
        try:
            return await do_login(apw, user, pw, secret, url)
        except Exception as e:  # noqa: BLE001
            msg = repr(e)
            if "closed" in msg.lower() or "Target" in msg:
                log(f"  browser target closed mid-login (don't click in the "
                    f"window while this runs) — reconnecting [{attempt + 1}/3]")
                await asyncio.sleep(2)
                continue
            raise
    print("could not complete login (target kept closing) — finish it by hand "
          "in the browser.", file=sys.stderr)
    return 2


rc = asyncio.run(main())
sys.stdout.flush()
os._exit(rc)
PY
  then
    LOGIN_RC=0
  else
    LOGIN_RC=1
  fi
  # The Python step above hard-exits (os._exit) to skip waiting on
  # Playwright's Node driver subprocess teardown - that subprocess inherits
  # this terminal's stdin, and being killed out from under it like that can
  # leave the TTY in raw mode (arrow keys then print literal escape bytes
  # instead of cycling shell history). Restore it unconditionally; harmless
  # no-op if stdin isn't actually a terminal.
  [ -t 0 ] && stty sane 2>/dev/null || true
  if [ "$LOGIN_RC" -eq 0 ]; then
    echo "login OK."
  else
    echo "auto-login did not complete — finish it by hand in the browser." >&2
    exit 1
  fi
else
  echo "Browser ready on :${PORT}. Log in by hand."
fi
