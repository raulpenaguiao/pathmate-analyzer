"""Pause a live run when the browser stops rendering, and resume in place.

Why (2026-09-29, twice): a HEADED Chromium gets no composited frames once
the screen blanks or goes to power saving. From then on every Playwright
click waits for a frame that never comes, the run burns through its retries
("popup never opened", screenshots timing out), and the PMCP session expires
behind it. Raul asked for the run to idle and ask to pick up instead.

    ok = await RG.guard(page, reenter)     # before each live step

`guard` is cheap when all is well (one 20x20px screenshot). When the page
isn't rendering it:
  - interactive terminal: beeps, prints a banner, and waits for Enter until
    the screen is awake again; if PMCP logged out meanwhile, asks for a
    manual login in the window, then Enter;
  - no terminal (an agent's background run): polls for up to WAIT_S for
    rendering to come back, re-logs in via tools/start_pmcp.sh if needed;
then calls `reenter()` (back into the same coaching and view) and returns
True, so the caller retries the step it was on. Returns False only when it
couldn't recover (non-interactive timeout / failed login).
Headless runs always render, so this never triggers there.
"""
from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

import _pmcp_safety as S

WAIT_S = int(os.environ.get("PMCP_RENDER_WAIT_S", "1800"))
START_PMCP = Path(__file__).resolve().parents[1] / "start_pmcp.sh"


async def rendering(page, timeout_ms: int = 4000) -> bool:
    """True if the page can produce a frame (a tiny clipped screenshot)."""
    try:
        await page.screenshot(clip={"x": 0, "y": 0, "width": 20, "height": 20},
                              timeout=timeout_ms)
        return True
    except Exception:  # noqa: BLE001
        return False


async def _logged_out(page) -> bool:
    try:
        if await page.locator("input[type=password]").count():
            return True
    except Exception:  # noqa: BLE001
        pass
    return await S.session_expired(page)


def _interactive() -> bool:
    return sys.stdin is not None and sys.stdin.isatty()


async def _ask(prompt: str) -> None:
    print("\a", end="", flush=True)
    await asyncio.to_thread(input, prompt)


def _banner(lines: list[str]) -> None:
    bar = "=" * 70
    print(f"\n{bar}\n" + "\n".join(f"  {ln}" for ln in lines) + f"\n{bar}", flush=True)


async def guard(page, reenter) -> bool:
    """See module docstring. `reenter` is an async callable with no args that
    brings the page back to where the caller works (coaching + view)."""
    is_rendering = await rendering(page)
    if is_rendering and not await _logged_out(page):
        return True
    t0 = time.monotonic()
    if not is_rendering:
        _banner([time.strftime("%H:%M:%S") + "  PAUSED: the browser stopped rendering.",
                 "Most likely the screen went to sleep / power saving, or the",
                 "browser window was minimized. The run is waiting, nothing is lost."])
    while not await rendering(page):
        if _interactive():
            await _ask("  Wake the screen (window visible, not minimized), then press Enter... ")
        else:
            if time.monotonic() - t0 > WAIT_S:
                print(f"  still not rendering after {WAIT_S}s - giving up", flush=True)
                return False
            await asyncio.sleep(20)
    if not is_rendering:
        print(f"  {time.strftime('%H:%M:%S')}  rendering again (paused "
              f"{time.monotonic() - t0:.0f}s)", flush=True)

    # the session may have died while we waited
    while await _logged_out(page):
        if _interactive():
            _banner(["PMCP logged you out while the run was paused.",
                     "Log in by hand in the browser window (just log in,",
                     "the run re-opens the coaching itself)."])
            try:
                await page.reload()
            except Exception:  # noqa: BLE001
                pass
            await _ask("  Press Enter once you are logged in... ")
        else:
            print("  session expired while paused - re-login via start_pmcp.sh", flush=True)
            port = os.environ.get("PMCP_CDP", "http://127.0.0.1:9222").rsplit(":", 1)[-1].strip("/")
            proc = await asyncio.create_subprocess_exec(
                str(START_PMCP), "--port", port,
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
            if await proc.wait() != 0:
                print("  re-login failed - giving up", flush=True)
                return False
        await page.wait_for_timeout(2000)

    await reenter()
    print(f"  {time.strftime('%H:%M:%S')}  resumed where it left off", flush=True)
    return True
