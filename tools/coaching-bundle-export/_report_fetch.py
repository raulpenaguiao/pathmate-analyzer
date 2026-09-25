"""Auto-fetch the Coaching Report HTML from the Coachings list, instead of
requiring the user to save it by hand (`export_coaching.py`'s "Later:
auto-fetch the Report HTML" item).

Confirmed live 2026-09-14: clicking "Report" on the Coachings list (with a
row selected) does NOT navigate the page or open a popup/new tab —
Playwright's `context.expect_page()` times out and `context.pages` never
grows. It triggers a native Chrome file download, invisible to ordinary
page/popup tracking. Getting it requires `Page.setDownloadBehavior` AND
`Browser.setDownloadBehavior` via CDP, pointed at a directory this script
controls, set BEFORE the click. The downloaded filename is server-decided
(`Coaching_<name, spaces to underscores>.html`) — move/rename it after,
don't try to control it via the click.
"""
from __future__ import annotations

import asyncio
from pathlib import Path


async def _select_coaching_row(page, name: str) -> bool:
    row = page.locator(".v-table-body tr", has_text=name).first
    if not await row.count():
        return False
    for _ in range(6):
        await row.locator(".v-table-cell-wrapper").first.click()
        await page.wait_for_timeout(400)
        cls = await row.evaluate("(e) => e.className")
        if "v-selected" in cls:
            return True
    return False


async def back_to_list(page) -> bool:
    body = await page.evaluate("() => document.body.innerText")
    if "COACHING STATUS" in body:
        return True
    back = page.locator(".v-button-caption", has_text="Back To List")
    if not await back.count():
        return False
    await back.first.click()
    await page.wait_for_timeout(1500)
    body = await page.evaluate("() => document.body.innerText")
    return "COACHING STATUS" in body


async def enter_edit_view(page, coaching_name: str) -> bool:
    """From the Coachings list, select `coaching_name`'s row and click Edit.
    Used to get back into the coaching after fetch_report_html() leaves the
    browser on the list."""
    want = f'Coaching "{coaching_name}"'

    async def in_edit_view() -> bool:
        return want in await page.evaluate("() => document.body.innerText")

    # the row-select retries can land as a DOUBLE-click, which opens the
    # coaching by itself: the row vanishes, selection "fails", and we used to
    # report failure while already in the Edit view (2026-09-25). So ask
    # "are we there?" first, not "did each step work?".
    if not await _select_coaching_row(page, coaching_name):
        return await in_edit_view()
    edit = page.locator(".v-button-caption", has_text="Edit")
    if not await edit.count():
        return await in_edit_view()
    await edit.first.click()
    # poll, don't sleep-once: on 2026-09-25 the editor took >2s to render its
    # 'Coaching "..."' header, and a single fixed 2s check reported failure
    # while the browser was in fact in the Edit view (killed an export).
    for _ in range(40):
        await page.wait_for_timeout(500)
        body = await page.evaluate("() => document.body.innerText")
        if want in body:
            return True
    return False


async def fetch_report_html(page, ctx, coaching_name: str, dl_dir: Path,
                             timeout_ms: int = 30000) -> Path:
    """Download the Report HTML for `coaching_name` into `dl_dir`, wait for
    it to finish writing, and return its path. Leaves the browser on the
    Coachings list — call `enter_edit_view()` afterward if the caller needs
    to resume work inside the coaching."""
    dl_dir.mkdir(parents=True, exist_ok=True)
    before = set(dl_dir.iterdir())

    cdp = await ctx.new_cdp_session(page)
    await cdp.send("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(dl_dir)})
    await cdp.send("Browser.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(dl_dir)})

    if not await back_to_list(page):
        raise RuntimeError("could not get to the Coachings list to fetch the Report")
    if not await _select_coaching_row(page, coaching_name):
        raise RuntimeError(f"could not select coaching row {coaching_name!r} on the list")

    rpt = page.locator(".v-button-caption", has_text="Report")
    if not await rpt.count():
        raise RuntimeError("no 'Report' button on the Coachings list")
    await rpt.first.click()

    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout_ms / 1000
    new_file: Path | None = None
    while loop.time() < deadline:
        await page.wait_for_timeout(500)
        after = set(dl_dir.iterdir())
        candidates = [f for f in (after - before)
                      if f.suffix == ".html" and not f.name.endswith(".crdownload")]
        if candidates:
            candidate = candidates[0]
            size1 = candidate.stat().st_size
            await page.wait_for_timeout(400)  # settle: confirm Chrome finished writing
            if candidate.exists() and candidate.stat().st_size == size1 and size1 > 0:
                new_file = candidate
                break
    if new_file is None:
        raise RuntimeError(f"Report download did not complete within {timeout_ms}ms")
    return new_file
