"""Log the CDP-attached Chromium into the PMCP admin, using credentials from
`.env`. Idempotent: if the admin app is already loaded it does nothing.

`.env` keys (repo root, gitignored — see `.env.example`):
  PMCP_USERNAME       portal username     (required for any auto-fill)
  PMCP_PASSWORD       portal password     (required for any auto-fill)
  PMCP_TOTP_SECRET    optional — the base32 seed from the authenticator
                      setup. If set, the 6-digit code is generated too;
                      if not, username + password are still filled and the
                      script waits ~2 min for you to type the code.
  PMCP_LOGIN_URL      optional, default https://cp22.pathmate.cloud/PMCP/admin

Run standalone:  PMCP_CDP=http://127.0.0.1:9222 .venv/bin/python pmcp_login.py
Exit 0 = logged in (or already was). Exit 2 = could not.

The Monitoring toggle and picking a coaching are still done by hand — this
only gets past the username / password / 2FA screen.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import os
import struct
import sys
import time
from pathlib import Path

from playwright.async_api import async_playwright

CDP = os.environ.get("PMCP_CDP", "http://127.0.0.1:9222")
REPO = Path(__file__).resolve().parents[2]


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.is_file():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def totp(secret: str, digits: int = 6, period: int = 30, at: float | None = None) -> str:
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
  // the admin shell always shows these nav items
  return /Coachings/.test(t) && /Logout/.test(t);
}
"""


FORM_JS = r"""
() => {
  const vis = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const ins = [...document.querySelectorAll('input')].filter(vis)
    .map(el => ({ id: el.id, type: (el.getAttribute('type') || 'text').toLowerCase(),
                  value: el.value }));
  const pwIdx = ins.findIndex(i => i.type === 'password');
  if (pwIdx < 0) return { hasPassword: false };
  // username = last text-ish field before the password; otp = first after it
  let userIdx = -1;
  for (let k = pwIdx - 1; k >= 0; k--) if (ins[k].type !== 'password') { userIdx = k; break; }
  let otpIdx = -1;
  for (let k = pwIdx + 1; k < ins.length; k++) if (ins[k].type !== 'password') { otpIdx = k; break; }
  const notif = [...document.querySelectorAll('.v-Notification-caption, .v-Notification-description, .v-Notification')]
    .map(e => e.textContent.replace(/\s+/g, ' ').trim()).filter(Boolean);
  return {
    hasPassword: true,
    userId:  userIdx >= 0 ? ins[userIdx].id : null,
    passId:  ins[pwIdx].id,
    otpId:   otpIdx >= 0 ? ins[otpIdx].id : null,
    otpValue: otpIdx >= 0 ? ins[otpIdx].value : null,
    notif,
  };
}
"""


async def _vfill(page, el_id: str, value: str) -> None:
    """Fill a Vaadin .v-textfield and blur it — VTextField only pushes its
    value to the server on blur / the value-change timer, so a fill without a
    blur submits an empty string."""
    loc = page.locator(f"#{el_id}")
    await loc.fill(value)
    await loc.blur()
    await page.wait_for_timeout(150)


async def _click_login(page) -> None:
    # dismiss a stale error notification first — it intercepts pointer events
    for _ in range(3):
        n = page.locator(".v-Notification")
        if not await n.count():
            break
        try:
            await n.first.click(timeout=1000)
        except Exception:  # noqa: BLE001
            await page.keyboard.press("Escape")
        await page.wait_for_timeout(300)
    for sel in ('.v-button:has-text("Login")', '.v-button:has-text("Log in")',
                'button[type=submit]', 'input[type=submit]'):
        loc = page.locator(sel)
        if await loc.count():
            try:
                await loc.first.click(timeout=5000)
                return
            except Exception:  # noqa: BLE001
                continue
    await page.keyboard.press("Enter")


async def main() -> int:
    env_path = REPO / ".env"
    if "--env" in sys.argv:
        env_path = Path(sys.argv[sys.argv.index("--env") + 1])
    env = {**load_env(env_path), **os.environ}
    user = env.get("PMCP_USERNAME")
    pw = env.get("PMCP_PASSWORD")
    secret = env.get("PMCP_TOTP_SECRET")
    url = env.get("PMCP_LOGIN_URL", "https://cp22.pathmate.cloud/PMCP/admin")

    async with async_playwright() as apw:
        try:
            b = await apw.chromium.connect_over_cdp(CDP)
        except Exception as e:  # noqa: BLE001
            print(f"no CDP browser at {CDP}: {e}", file=sys.stderr)
            return 2
        ctx = b.contexts[0]
        page = next((p for p in ctx.pages if "pathmate" in (p.url or "")),
                    ctx.pages[0] if ctx.pages else None)
        if page is None:
            print("browser has no pages", file=sys.stderr)
            return 2

        if "pathmate" not in (page.url or ""):
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_timeout(1500)

        if await page.evaluate(LOGGED_IN_JS):
            print("already logged in")
            return 0

        if not (user and pw):
            print("PMCP_USERNAME / PMCP_PASSWORD not set in .env — log in by "
                  "hand in the browser, then rerun the export.", file=sys.stderr)
            return 2
        # wait for the login form to render
        form = {}
        for _ in range(12):
            form = await page.evaluate(FORM_JS)
            if form.get("hasPassword"):
                break
            await page.wait_for_timeout(1000)
        if not form.get("hasPassword"):
            if await page.evaluate(LOGGED_IN_JS):
                print("logged in")
                return 0
            print("no login form found — finish login by hand, then rerun.",
                  file=sys.stderr)
            return 2

        if form.get("userId"):
            await _vfill(page, form["userId"], user)
        await _vfill(page, form["passId"], pw)
        print("  filled username + password")

        otp_id = form.get("otpId")
        if otp_id and secret:
            code = totp(secret)
            await _vfill(page, otp_id, code)
            print(f"  filled 2FA code {code}")
        elif otp_id and not secret:
            print("  >>> PMCP_TOTP_SECRET not set — type your 6-digit 2FA code "
                  "in the browser now (waiting up to ~2 min).")
            deadline = time.time() + 130
            while time.time() < deadline:
                await page.wait_for_timeout(2000)
                if await page.evaluate(LOGGED_IN_JS):
                    print("logged in")
                    return 0
                f = await page.evaluate(FORM_JS)
                if f.get("hasPassword") and (f.get("otpValue") or "").strip():
                    break  # code typed — submit it below
            else:
                print("timed out waiting for the 2FA code.", file=sys.stderr)
                return 2

        await _click_login(page)

        for _ in range(15):
            await page.wait_for_timeout(1000)
            if await page.evaluate(LOGGED_IN_JS):
                print("logged in")
                return 0
            f = await page.evaluate(FORM_JS)
            if f.get("notif"):
                print(f"  login rejected: {' | '.join(f['notif'])}", file=sys.stderr)
                return 2
        print("could not confirm login — finish it by hand in the browser, "
              "then rerun the export.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
