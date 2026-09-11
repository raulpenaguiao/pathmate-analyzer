"""Phase-0 follow-up v2: the outer 'Edit micro dialog message:' window shows
every field read-only (v-disabled), including the "clears dialog cascade"
checkboxes - they need their own nested sub-editor, opened by one specific
"Edit" button among the ~8 in that window. This locates it by DOM order
(the "Edit" immediately preceding the "Answer options" label, i.e. the one
governing command/expects-answer/answer-type/the whole behavior-checkbox
block) rather than vertical-distance heuristics, which failed last time.

Only ever dismisses with Cancel/Close/Exit - never OK/Save/Apply. Toggling a
checkbox inside an unsaved sub-form and then cancelling changes nothing in
the live coaching.

Run: PMCP_CDP=http://127.0.0.1:9222 .venv/bin/python probe_cascade_checkbox.py
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent
OUT = HERE / "spike"
OUT.mkdir(exist_ok=True)
CDP = os.environ.get("PMCP_CDP", "http://127.0.0.1:9222")
import _menu_nav as S
from probe_node_editor import node_edit_button

TARGET_PATH = ["Testing of gamification concept"]
ROW_INDEX = 0

FIND_EDIT_BEFORE_ANSWEROPTIONS_JS = r"""
() => {
  const wins = [...document.querySelectorAll('.v-window')];
  const w = wins[wins.length - 1];
  if (!w) return null;
  // walk all elements in document order; remember the last "Edit" button
  // seen; return it the moment we hit the "Answer options" label.
  const all = [...w.querySelectorAll('*')];
  let lastEdit = null;
  for (const el of all) {
    if (el.classList && el.classList.contains('v-button')) {
      const cap = (el.querySelector('.v-button-caption') || {}).textContent || '';
      if (cap.trim() === 'Edit') lastEdit = el;
    }
    if (el.classList && el.classList.contains('v-label') &&
        (el.textContent || '').includes('Answer options')) {
      return lastEdit;
    }
  }
  return null;
}
"""

DUMP_SUBWINDOW_JS = r"""
() => {
  const wins = [...document.querySelectorAll('.v-window')];
  const w = wins[wins.length - 1];
  if (!w) return null;
  const checks = [...w.querySelectorAll('.v-checkbox')].map(cb => {
    const input = cb.querySelector('input[type=checkbox]');
    return {
      label: cb.textContent.replace(/\s+/g,' ').trim(),
      checked: input ? input.checked : null,
      disabled: input ? input.disabled : null,
    };
  });
  return {
    caption: (w.querySelector('.v-window-header') || {}).textContent || '',
    buttons: [...w.querySelectorAll('.v-button-caption')].map(e => e.textContent.trim()),
    checks,
  };
}
"""


async def close_top(page):
    for label in ("Cancel", "Close", "Exit"):
        btn = page.locator(".v-window .v-button-caption", has_text=label)
        if await btn.count():
            await btn.last.click()
            await page.wait_for_timeout(600)
            return True
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(600)
    return False


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.connect_over_cdp(CDP)
        ctx = b.contexts[0]
        page = ctx.pages[0]
        cdp = await ctx.new_cdp_session(page)
        win = await cdp.send("Browser.getWindowForTarget")
        wid = win["windowId"]
        await cdp.send("Browser.setWindowBounds", {"windowId": wid, "bounds": {
            "left": 0, "top": 0, "width": 12000, "height": 1600, "windowState": "normal"}})
        await page.wait_for_timeout(1400)
        try:
            if not await S.ensure_micro_dialogs(page):
                print("Micro Dialogs menubar not on screen.")
                return
            await S.navigate_and_select(page, TARGET_PATH)
            await S.wait_round_trip(page)
            rows = page.locator(".v-table .v-table-body tr")
            await rows.nth(ROW_INDEX).click()
            await page.wait_for_timeout(500)
            btn = await node_edit_button(page)
            if not btn:
                print("no node-Edit button")
                return
            await btn.click()
            await page.wait_for_timeout(1300)

            more = page.locator(".v-window").last.locator("text=/Show additional settings/i")
            if await more.count():
                await more.first.click()
                await page.wait_for_timeout(900)

            handle = await page.evaluate_handle(FIND_EDIT_BEFORE_ANSWEROPTIONS_JS)
            el = handle.as_element() if handle else None
            if not el:
                print("could not locate the behavior-block Edit button")
                await close_top(page)
                return
            await el.click()
            await page.wait_for_timeout(1200)

            sub = await page.evaluate(DUMP_SUBWINDOW_JS)
            (OUT / "cascade_v2_subwindow.json").write_text(json.dumps(sub, indent=1, ensure_ascii=False))
            print(f"Sub-window: {sub['caption'][:70]!r} buttons={sub['buttons']}")
            print("Checkboxes in sub-editor (should now be enabled):")
            for c in sub["checks"]:
                print(f"  [{'x' if c['checked'] else ' '}]{'(disabled)' if c['disabled'] else '':10s} {c['label'][:90]}")

            # find + toggle the cascade checkbox, observe reactive changes
            idx = next((i for i, c in enumerate(sub["checks"])
                        if "clears the current dialog cascade" in c["label"]), -1)
            if idx >= 0 and not sub["checks"][idx]["disabled"]:
                cb = page.locator(".v-window").last.locator(".v-checkbox").nth(idx).locator("input[type=checkbox]")
                await cb.click(timeout=5000)
                await page.wait_for_timeout(500)
                after = await page.evaluate(DUMP_SUBWINDOW_JS)
                (OUT / "cascade_v2_after_toggle.json").write_text(json.dumps(after, indent=1, ensure_ascii=False))
                print("\nAfter toggling 'clears the current dialog cascade':")
                for c in after["checks"]:
                    print(f"  [{'x' if c['checked'] else ' '}]{'(disabled)' if c['disabled'] else '':10s} {c['label'][:90]}")
                print("\nDIFF:")
                for cb_, ca in zip(sub["checks"], after["checks"]):
                    if cb_["checked"] != ca["checked"] or cb_["disabled"] != ca["disabled"]:
                        print(f"  {cb_['label'][:90]}: checked {cb_['checked']}->{ca['checked']}, disabled {cb_['disabled']}->{ca['disabled']}")
            else:
                print(f"\ncascade checkbox not found or still disabled (idx={idx})")

            try:
                await page.screenshot(path=str(OUT / "cascade_v2.png"), timeout=5000)
            except Exception as e:  # noqa: BLE001
                print(f"(screenshot skipped: {e!r})")

            await close_top(page)  # close sub-editor, never save
            await close_top(page)  # close outer editor
        finally:
            n = await page.evaluate("() => document.querySelectorAll('.v-window').length")
            print(f"\nopen modals remaining: {n}")
            await cdp.send("Browser.setWindowBounds", {"windowId": wid, "bounds": {
                "left": 60, "top": 60, "width": 1400, "height": 1000, "windowState": "normal"}})
            print("window restored")


if __name__ == "__main__":
    asyncio.run(main())
