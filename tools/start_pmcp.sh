#!/usr/bin/env bash
# Start a Chromium with a DevTools debug port and log it into the PMCP admin
# using credentials from .env. One self-contained step for every tool that
# drives the live PMCP editor over CDP.
# See tools/coaching-bundle-export/WORKFLOW.md.
#
# Usage:  ./start_pmcp.sh [options]
#   --port N       CDP port (default 9222)
#   --url URL      initial page (default the PMCP admin login)
#   --env FILE     credentials file (default <repo>/.env). Keys:
#                    PMCP_USERNAME     portal username        (required)
#                    PMCP_PASSWORD     portal password        (required)
#                    PMCP_TOTP_SECRET  base32 2FA seed        (optional; if
#                                      unset, user+password are filled and it
#                                      waits ~2 min for you to type the code)
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
    -h|--help)   sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
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
    "${URL}" >"/tmp/pmcp-chrome-${PORT}.log" 2>&1 &
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
    echo "--- tail of /tmp/pmcp-chrome-${PORT}.log ---" >&2
    tail -15 "/tmp/pmcp-chrome-${PORT}.log" >&2 || true
    exit 1
  fi
fi

# ---------------------------------------------------------------------------
# 2. log in from .env  (Playwright: bash can't drive it, so a small embedded
#    Python step. Idempotent — no-op if the admin app is already loaded.)
# ---------------------------------------------------------------------------
if [ "$DO_LOGIN" -eq 1 ]; then
  echo
  echo "--- login ---"
  if PMCP_CDP="http://127.0.0.1:${PORT}" PMCP_ENV_FILE="$ENV_FILE" "$PY" - <<'PY'
import asyncio, base64, hashlib, hmac, os, struct, sys, time
from pathlib import Path
from playwright.async_api import async_playwright

CDP = os.environ["PMCP_CDP"]
ENV_FILE = Path(os.environ["PMCP_ENV_FILE"])


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


LOGGED_IN_JS = r"""
() => {
  if (document.querySelector('input[type=password]')) return false;
  const t = (document.body ? document.body.innerText : '');
  return /Coachings/.test(t) && /Logout/.test(t);
}
"""

FORM_JS = r"""
() => {
  const vis = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const ins = [...document.querySelectorAll('input')].filter(vis)
    .map(el => ({ id: el.id, type: (el.getAttribute('type') || 'text').toLowerCase(), value: el.value }));
  const pwIdx = ins.findIndex(i => i.type === 'password');
  if (pwIdx < 0) return { hasPassword: false };
  let userIdx = -1;
  for (let k = pwIdx - 1; k >= 0; k--) if (ins[k].type !== 'password') { userIdx = k; break; }
  let otpIdx = -1;
  for (let k = pwIdx + 1; k < ins.length; k++) if (ins[k].type !== 'password') { otpIdx = k; break; }
  const notif = [...document.querySelectorAll('.v-Notification-caption, .v-Notification-description, .v-Notification')]
    .map(e => e.textContent.replace(/\s+/g, ' ').trim()).filter(Boolean);
  return { hasPassword: true,
           userId: userIdx >= 0 ? ins[userIdx].id : null,
           passId: ins[pwIdx].id,
           otpId: otpIdx >= 0 ? ins[otpIdx].id : null,
           otpValue: otpIdx >= 0 ? ins[otpIdx].value : null,
           notif };
}
"""


async def vfill(page, el_id, value):
    """Type into a Vaadin .v-textfield with real keystrokes + blur, and verify
    it stuck — on a cold-loaded page the connector may not be bound yet."""
    loc = page.locator(f"#{el_id}")
    for _ in range(3):
        try:
            await loc.click(timeout=5000)
            await loc.press("Control+a"); await loc.press("Delete")
            await loc.press_sequentially(value, delay=15)
            await loc.press("Tab")
            await page.wait_for_timeout(250)
            if (await loc.input_value()) == value:
                return True
        except Exception:
            pass
        await page.wait_for_timeout(1000)
    return False


async def click_login(page):
    for _ in range(3):
        n = page.locator(".v-Notification")
        if not await n.count():
            break
        try:
            await n.first.click(timeout=1000)
        except Exception:
            await page.keyboard.press("Escape")
        await page.wait_for_timeout(300)
    for sel in ('.v-button:has-text("Login")', '.v-button:has-text("Log in")',
                'button[type=submit]', 'input[type=submit]'):
        loc = page.locator(sel)
        if await loc.count():
            try:
                await loc.first.click(timeout=5000)
                return
            except Exception:
                continue
    await page.keyboard.press("Enter")


async def main():
    fe = load_env(ENV_FILE)
    env = {**os.environ, **{k: v for k, v in fe.items() if v}}
    user, pw = env.get("PMCP_USERNAME"), env.get("PMCP_PASSWORD")
    secret = env.get("PMCP_TOTP_SECRET")
    url = env.get("PMCP_LOGIN_URL", "https://cp22.pathmate.cloud/PMCP/admin")
    log(f"env: {ENV_FILE}  ->  username={'set' if user else 'MISSING'}, "
        f"password={'set' if pw else 'MISSING'}, "
        f"totp_secret={'set' if secret else 'not set (manual code)'}")

    # start() rather than `async with` — we os._exit() the moment we have an
    # answer instead of waiting on playwright's node-driver teardown.
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
            print("PMCP_USERNAME / PMCP_PASSWORD not set in .env — log in by "
                  "hand in the browser.", file=sys.stderr); return 2

        log("waiting for the login form to be ready...")
        try:
            await page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        form = {}
        for i in range(30):  # up to ~45s for a cold Vaadin bootstrap
            form = await page.evaluate(FORM_JS)
            btn = await page.locator('.v-button:has-text("Login"), '
                                     '.v-button:has-text("Log in")').count()
            if form.get("hasPassword") and btn:
                await page.wait_for_timeout(800); break
            if await page.evaluate(LOGGED_IN_JS):
                log("logged in"); return 0
            if i and i % 4 == 0:
                log(f"  ...still waiting for the form ({i * 1.5:.0f}s)")
            await page.wait_for_timeout(1500)
        else:
            print("login form never became ready — reload the page and rerun.",
                  file=sys.stderr); return 2

        log("form ready — typing username + password")
        u_ok = await vfill(page, form["userId"], user) if form.get("userId") else False
        p_ok = await vfill(page, form["passId"], pw)
        if not (u_ok and p_ok):
            log("  fields didn't take — retrying after a longer settle")
            await page.wait_for_timeout(2000)
            form = await page.evaluate(FORM_JS)
            u_ok = await vfill(page, form["userId"], user) if form.get("userId") else u_ok
            p_ok = await vfill(page, form["passId"], pw)
        if not (u_ok and p_ok):
            print("could not type username/password into the form — log in by "
                  "hand.", file=sys.stderr); return 2
        log("  username + password entered")

        otp_id = form.get("otpId")
        if otp_id and secret:
            code = totp(secret)
            await vfill(page, otp_id, code)
            log(f"  2FA code entered ({code})")
        elif otp_id and not secret:
            log("  >>> PMCP_TOTP_SECRET not set — type your 6-digit 2FA code in "
                "the browser now (waiting up to ~2 min).")
            deadline = time.time() + 130
            while time.time() < deadline:
                await page.wait_for_timeout(2000)
                if await page.evaluate(LOGGED_IN_JS):
                    log("logged in"); return 0
                f = await page.evaluate(FORM_JS)
                if f.get("hasPassword") and (f.get("otpValue") or "").strip():
                    break
            else:
                print("timed out waiting for the 2FA code.", file=sys.stderr); return 2

        log("clicking Login...")
        await click_login(page)
        log("waiting for the admin app to load...")
        for _ in range(20):
            await page.wait_for_timeout(1000)
            if await page.evaluate(LOGGED_IN_JS):
                log("logged in"); return 0
            f = await page.evaluate(FORM_JS)
            if f.get("notif"):
                print(f"  login rejected: {' | '.join(f['notif'])}", file=sys.stderr)
                return 2
        print("could not confirm login — finish it by hand in the browser.",
              file=sys.stderr)
        return 2


rc = asyncio.run(main())
# playwright's node driver can linger a moment on teardown; don't make the
# caller wait for it once we have our answer.
sys.stdout.flush()
os._exit(rc)
PY
  then
    echo "login OK. Next: deactivate Monitoring in the browser, then run your export."
  else
    echo "auto-login did not complete — finish it by hand in the browser." >&2
    exit 1
  fi
else
  echo "Browser ready on :${PORT}. Log in by hand."
fi
