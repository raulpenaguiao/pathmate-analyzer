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


async def _fill_first(page, selectors: list[str], value: str) -> bool:
    for sel in selectors:
        loc = page.locator(sel)
        for i in range(await loc.count()):
            el = loc.nth(i)
            try:
                if await el.is_visible():
                    await el.fill(value)
                    return True
            except Exception:  # noqa: BLE001
                continue
    return False


async def _click_submit(page) -> None:
    for sel in ('button[type=submit]', 'input[type=submit]',
                'button:has-text("Log in")', 'button:has-text("Login")',
                'button:has-text("Sign in")', 'button:has-text("Anmelden")',
                'button:has-text("Continue")', 'button:has-text("Verify")',
                '.v-button:has-text("Log in")', '.v-button:has-text("Login")'):
        loc = page.locator(sel)
        if await loc.count() and await loc.first.is_visible():
            await loc.first.click()
            return
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
        if not secret:
            print("PMCP_TOTP_SECRET not set — will fill username + password, "
                  "then wait for you to type the 2FA code in the browser.")

        otp_sels = [
            "input[autocomplete='one-time-code']:visible",
            "input[name*='otp' i]:visible",
            "input[name*='totp' i]:visible",
            "input[name*='code' i]:visible",
            "input[name*='token' i]:visible",
            "input[inputmode='numeric']:visible",
            "input[type='tel']:visible",
        ]
        pw_submitted = otp_submitted = False
        waiting_msg_shown = False
        deadline = time.time() + 150  # allow time for a manual 2FA code

        while time.time() < deadline:
            if await page.evaluate(LOGGED_IN_JS):
                print("logged in")
                return 0

            if await page.locator("input[type=password]:visible").count():
                await _fill_first(page, [
                    "input[type=email]:visible",
                    "input[name*='user' i]:visible",
                    "input[name*='login' i]:visible",
                    "input[name*='email' i]:visible",
                    "input[type=text]:visible",
                ], user)
                await _fill_first(page, ["input[type=password]:visible"], pw)
                await _click_submit(page)
                print("  submitted username + password")
                pw_submitted = True
                await page.wait_for_timeout(2500)
                continue

            has_otp = any(await page.locator(s).count() for s in otp_sels)
            if has_otp and secret and not otp_submitted:
                code = totp(secret)
                if await _fill_first(page, otp_sels, code):
                    await _click_submit(page)
                    print(f"  submitted TOTP {code}")
                    otp_submitted = True
                    await page.wait_for_timeout(2500)
                    continue

            if has_otp and not secret:
                if not waiting_msg_shown:
                    print("  >>> type your 6-digit 2FA code in the browser "
                          "(waiting up to ~2 min)...")
                    waiting_msg_shown = True
                await page.wait_for_timeout(2000)
                continue

            # nothing to do yet — page still loading, or an unknown step
            await page.wait_for_timeout(1500)

        if await page.evaluate(LOGGED_IN_JS):
            print("logged in")
            return 0
        _ = pw_submitted  # (filled but login not confirmed)
        print("could not confirm login — finish it by hand in the browser, "
              "then rerun the export.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
