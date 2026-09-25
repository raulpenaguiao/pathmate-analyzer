"""One-off fix: spirometry v02 rows 3-4 Answer Options stored as one line.

Same bug/fix as autochanges/2026-09-19-medication-answer-options-bugfix.md.
Default = dry run: reads each target row's text + current answer options
(opens popups, always Cancels). --apply writes `Yes:1\nNo:0` / `Da:1\nNu:0`,
then re-navigates fresh and re-reads to verify the commit.

Run from tools/coaching-bundle-export/:
  PMCP_CDP=http://127.0.0.1:9222 ../../.venv/bin/python <this> [--rows=3,4,...] [--apply]
Rows come from the fresh export (every row asking "spirometer handy" with one-line options).
"""
from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.getcwd())
from playwright.async_api import async_playwright  # noqa: E402

import _dialogs_nav as D  # noqa: E402
import _menu_nav as S  # noqa: E402
import _pmcp_safety as P  # noqa: E402

CDP = os.environ.get("PMCP_CDP", "http://127.0.0.1:9222")
PATH = ["Prompt patient to conduct daily spirometry",
        "Prompt patient to conduct daily spirometry (v02)"]
ROWS = [int(x) for a in sys.argv if a.startswith("--rows=") for x in a.split("=")[1].split(",")] or [3, 4]
EXPECT_TEXT = "spirometer"  # rows 3-6: handy / within reach / with you / nearby
NEW_EN, NEW_RO = "Yes:1\nNo:0", "Da:1\nNu:0"
APPLY = "--apply" in sys.argv

EDIT_INDEX_NEAR_LABEL_JS = r"""
(labelSub) => {
  const wins = [...document.querySelectorAll('.v-window')];
  const w = wins[wins.length - 1];
  const label = [...w.querySelectorAll('.v-label, .v-caption')]
    .find(l => (l.textContent || '').includes(labelSub));
  if (!label) return -1;
  const ly = label.getBoundingClientRect().top;
  const edits = [...w.querySelectorAll('.v-button-caption')]
    .filter(c => c.textContent.trim() === 'Edit');
  let best = -1, bestDy = Infinity;
  edits.forEach((c, i) => {
    const dy = Math.abs(c.getBoundingClientRect().top - ly);
    if (dy < bestDy) { bestDy = dy; best = i; }
  });
  return bestDy < 40 ? best : -1;
}
"""


async def open_dialog(page):
    if not await S.ensure_micro_dialogs(page):
        raise SystemExit("Micro Dialogs view not reachable (Monitoring off?)")
    await S.navigate_and_select(page, PATH)
    await S.wait_round_trip(page)


async def read_options(page, window, idx):
    """Open the bilingual answer-options popup, read both tabs, Cancel."""
    n_before = await page.locator(".v-window").count()
    edits = window.locator(".v-button-caption", has_text="Edit")
    await edits.nth(idx).click()
    await page.wait_for_timeout(700)
    popup = page.locator(".v-window").last
    ta = popup.locator("textarea").first
    out = {}
    for tab, key in (("English (GB)", "en"), ("Romanian (RO)", "ro")):
        await popup.locator(".v-button-caption", has_text=tab).first.click()
        await page.wait_for_timeout(300)
        out[key] = await ta.input_value()
    cancel = popup.locator(".v-button-caption", has_text="Cancel")
    if await cancel.count():
        await cancel.last.click()
    else:
        await page.keyboard.press("Escape")
    await page.wait_for_timeout(500)
    if await page.locator(".v-window").count() != n_before:
        raise SystemExit("options popup did not close on Cancel/Escape - stopping")
    return out


async def process_row(page, row, write):
    if not await D.open_row_editor(page, row):
        raise SystemExit(f"row {row}: could not open editor")
    win = page.locator(".v-window").last
    text = await win.inner_text()
    if EXPECT_TEXT not in text:
        await D.close_editor(page, win)
        raise SystemExit(f"row {row}: not the expected question - aborting")
    await D.reveal_additional_settings(page, win)
    idx = await page.evaluate(EDIT_INDEX_NEAR_LABEL_JS, "Answer options")
    if idx < 0:
        await D.close_editor(page, win)
        raise SystemExit(f"row {row}: no Edit button beside 'Answer options'")
    before = await read_options(page, win, idx)
    print(f"row {row}: edit#{idx} before={before!r}")
    if write and before == {"en": NEW_EN, "ro": NEW_RO}:
        print(f"row {row}: already correct, skipping")
    elif write:
        ok = await D.set_bilingual_field(page, win, idx, NEW_EN, NEW_RO)
        print(f"row {row}: write ok={ok}")
    await D.close_editor(page, win)  # Close = commit on this editor
    await S.wait_round_trip(page)


async def main():
    import _browser_lock as BL
    try:
        BL.claim("fix_spiro_answer_options")
    except BL.BrowserBusy as e:
        sys.exit(str(e))
    async with async_playwright() as pw:
        b = await pw.chromium.connect_over_cdp(CDP)
        page = b.contexts[0].pages[0]
        name = await P.assert_expected_coaching(page)
        print(f"coaching: {name}  mode: {'APPLY' if APPLY else 'dry run'}")
        # widen so the Micro Dialogs menubar doesn't collapse (probe_answer_type.py pattern)
        cdp = await b.contexts[0].new_cdp_session(page)
        wid = (await cdp.send("Browser.getWindowForTarget"))["windowId"]
        await cdp.send("Browser.setWindowBounds", {"windowId": wid, "bounds": {
            "left": 0, "top": 0, "width": 12000, "height": 1600, "windowState": "normal"}})
        await page.wait_for_timeout(1400)
        try:
            await open_dialog(page)
            for row in ROWS:
                await process_row(page, row, APPLY)
            if APPLY:
                print("--- verify via fresh re-navigation ---")
                await S.navigate_and_select(page, ["Prompt patient to conduct daily spirometry"])
                await S.wait_round_trip(page)
                await open_dialog(page)
                for row in ROWS:
                    await process_row(page, row, False)
        except Exception:
            if await P.session_expired(page):
                print("ERROR:", P.EXPIRED_HINT)
            raise
        finally:
            await cdp.send("Browser.setWindowBounds", {"windowId": wid, "bounds": {
                "left": 60, "top": 60, "width": 1400, "height": 1000, "windowState": "normal"}})


if __name__ == "__main__":
    asyncio.run(main())
