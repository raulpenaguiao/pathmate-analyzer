"""Phase-0 recon for the ALEX v02 redesign (docs/ALEX_v02_redesign_spec.md
S6): find the live UI for configuring a Micro Dialog Message as PMCP's
"time-out question" type with a custom expiry + fallback message, if that
field exists at all outside the "Answer type" combobox.

The outer "Edit micro dialog message:" window (probe_node_editor.py) shows
every field DISABLED/read-only with its own per-field "Edit" sub-button, and
a collapsed "Show additional settings" toggle. This probe:
  1. Opens the spirometry reminder dialog's own message row (not a subfolder).
  2. Expands "Show additional settings".
  3. Clicks the "Edit" sub-button beside "Answer type:" and dumps whatever
     sub-editor opens (expected: the real answer-type option list).
  4. Cancels every nested modal it opens - never clicks OK/Save/Apply.

Read-only by construction: only Cancel/Close/Escape are ever pressed on a
sub-modal; the outer modal is left in its original disabled state throughout.

Run: PMCP_CDP=http://127.0.0.1:9222 .venv/bin/python probe_answer_type.py
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

# top-level dialog, no subfolder - the reminder message itself
TARGET_PATH = ["Prompt patient to conduct daily spirometry"]
ROW_INDEX = int(os.environ.get("PMCP_ROW", "4"))

DUMP_TOP_MODAL_JS = r"""
() => {
  const wins = [...document.querySelectorAll('.v-window')];
  const w = wins[wins.length - 1];
  if (!w) return null;
  return {
    caption: (w.querySelector('.v-window-header') || {}).textContent || '',
    buttons: [...w.querySelectorAll('.v-button-caption')]
      .map(e => e.textContent.replace(/\s+/g,' ').trim()).filter(Boolean),
    visible_text: (w.innerText || '').replace(/\n{2,}/g, '\n'),
    html: w.outerHTML.slice(0, 80000),
  };
}
"""


async def click_button_near_label(page, win_selector: str, label_substr: str, button_caption: str):
    """Find the row whose label text contains label_substr, inside the most
    recently opened .v-window, and click the button in that same row whose
    caption == button_caption. Returns True if clicked."""
    handle = await page.evaluate_handle(
        """([labelSub, btnCap]) => {
          const wins = [...document.querySelectorAll('.v-window')];
          const w = wins[wins.length - 1];
          if (!w) return null;
          // find the label element
          const labels = [...w.querySelectorAll('.v-label')]
            .filter(l => (l.textContent || '').includes(labelSub));
          if (!labels.length) return null;
          const label = labels[0];
          // the row is the ancestor .v-gridlayout-slot's parent gridlayout;
          // search forward siblings within the same gridlayout row band for
          // a button with the right caption, else fall back to nearest
          // following .v-button in DOM order within the same modal.
          const allBtns = [...w.querySelectorAll('.v-button')];
          const labelRect = label.getBoundingClientRect();
          let best = null, bestDy = Infinity;
          for (const b of allBtns) {
            const cap = (b.querySelector('.v-button-caption')||{}).textContent||'';
            if (cap.trim() !== btnCap) continue;
            const r = b.getBoundingClientRect();
            const dy = Math.abs(r.top - labelRect.top);
            if (dy < bestDy) { bestDy = dy; best = b; }
          }
          return best;
        }""",
        [label_substr, button_caption],
    )
    el = handle.as_element() if handle else None
    if not el:
        return False
    await el.click()
    return True


async def dump_and_save(page, slug: str):
    dump = await page.evaluate(DUMP_TOP_MODAL_JS)
    if dump is None:
        print(f"  [{slug}] no window open")
        return None
    (OUT / f"answertype_{slug}.json").write_text(
        json.dumps(dump, indent=1, ensure_ascii=False))
    try:
        await page.screenshot(path=str(OUT / f"answertype_{slug}.png"), timeout=5000)
    except Exception as e:  # noqa: BLE001
        print(f"  (screenshot skipped: {e!r})")
    print(f"  [{slug}] window {dump['caption'][:60]!r} buttons={dump['buttons']}")
    return dump


async def cancel_top_modal(page):
    for label in ("Cancel", "Close", "Exit"):
        btn = page.locator(".v-window .v-button-caption", has_text=label)
        if await btn.count():
            await btn.last.click()
            await page.wait_for_timeout(500)
            return True
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(500)
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
                print("Micro Dialogs menubar not on screen - open that view and rerun.")
                return
            await S.navigate_and_select(page, TARGET_PATH)
            await S.wait_round_trip(page)
            rows = page.locator(".v-table .v-table-body tr")
            nrows = await rows.count()
            print(f"{nrows} rows in 'Prompt patient to conduct daily spirometry'")
            if nrows == 0:
                print("no rows - this dialog is likely a pure folder, adjust TARGET_PATH")
                return
            await rows.nth(ROW_INDEX).click()
            await page.wait_for_timeout(500)
            from probe_node_editor import node_edit_button
            btn = await node_edit_button(page)
            if not btn:
                print(f"no node-Edit button on row {ROW_INDEX}")
                return
            await btn.click()
            await page.wait_for_timeout(1300)
            await dump_and_save(page, f"00_outer_before_expand_row{ROW_INDEX}")

            # expand "Show additional settings" if present
            more = page.locator(".v-window").last.locator(
                "text=/Show additional settings/i")
            if await more.count():
                await more.first.click()
                await page.wait_for_timeout(700)
                await dump_and_save(page, f"01_outer_expanded_row{ROW_INDEX}")
            else:
                print("  no 'Show additional settings' toggle found")

            # click the Edit sub-button next to "Answer type:"
            clicked = await click_button_near_label(page, ".v-window", "Answer type", "Edit")
            if clicked:
                await page.wait_for_timeout(1000)
                await dump_and_save(page, f"02_answertype_subeditor_row{ROW_INDEX}")
                await cancel_top_modal(page)  # close the sub-editor, never save
                await page.wait_for_timeout(500)
            else:
                print("  could not locate an Edit button next to 'Answer type:'")

            await dump_and_save(page, f"03_outer_after_subeditor_closed_row{ROW_INDEX}")
            await cancel_top_modal(page)  # close the outer message editor
        finally:
            await cdp.send("Browser.setWindowBounds", {"windowId": wid, "bounds": {
                "left": 60, "top": 60, "width": 1400, "height": 1000, "windowState": "normal"}})
            print("\nwindow restored")


if __name__ == "__main__":
    asyncio.run(main())
