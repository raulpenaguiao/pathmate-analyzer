"""Discovery spike v2: open each node type's detail editor and dump its fields.

Flow learned from v1: select dialog -> click a node row -> click the node
toolbar's **Edit** button (caption "Edit", inside the `micro-dialogs` layout,
~y=675) -> a modal `.v-window` opens with the node form -> Escape to close.

Read-only: never types, never saves, closes every window with Escape/Cancel.

Run: PMCP_CDP=http://127.0.0.1:9222 .venv/bin/python probe_node_editor.py
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

# dialogs x which row types to probe (row index picked after inspecting the table)
TARGETS = [
    ("Morning greetings (messages + r_ group)", ["👋 Hello", "Morning greetings"], [0, 1]),
    ("Spirometry compliance (decision points)",
     ["Prompt patient to conduct daily spirometry",
      "Feedback on compliance regarding daily spirometry", "Good Compliance"], [0, 1, 2]),
    ("dataEdited (events)", ["⚙️ Controls", "📄 dataEdited"], [0, 1, 2, 3]),
]

FORM_DUMP_JS = r"""
() => {
  const wins = [...document.querySelectorAll('.v-window')];
  return wins.map(w => {
    const fields = [];
    // FormLayout rows: caption cell + value cell
    w.querySelectorAll('.v-formlayout-row, tr').forEach(row => {
      const capEl = row.querySelector('.v-formlayout-captioncell, .v-caption, th');
      const valEl = row.querySelector('.v-formlayout-contentcell, td:last-child');
      if (!capEl && !valEl) return;
      const cap = (capEl ? capEl.textContent : '').replace(/\s+/g,' ').trim();
      let val = '';
      if (valEl) {
        const inp = valEl.querySelector('input, textarea, select');
        if (inp) val = (inp.value != null ? inp.value : inp.textContent);
        else {
          const combo = valEl.querySelector('.v-filterselect-input, .v-select-optiongroup, .v-checkbox');
          val = (combo ? combo.textContent : valEl.textContent);
        }
        val = (val || '').replace(/\s+/g,' ').trim().slice(0, 200);
      }
      const widgets = [...valEl?.querySelectorAll('[class*="v-"]') || []]
        .map(e => e.className.split(' ').find(c => /^v-(textfield|textarea|filterselect|select|checkbox|button|table|tabsheet|richtextarea|datefield|slider|nativeselect)/.test(c)))
        .filter(Boolean);
      fields.push({ cap, val, widgets: [...new Set(widgets)] });
    });
    const tabs = [...w.querySelectorAll('.v-tabsheet-tabitem .v-captiontext, .v-tabsheet-tabitemcell')]
      .map(e => e.textContent.replace(/\s+/g,' ').trim()).filter(Boolean);
    const buttons = [...w.querySelectorAll('.v-button-caption')]
      .map(e => e.textContent.replace(/\s+/g,' ').trim()).filter(Boolean);
    return {
      caption: (w.querySelector('.v-window-header') || {}).textContent || '',
      tabs, buttons,
      fields: fields.filter(f => f.cap || f.val),
      html: w.outerHTML.slice(0, 60000),
    };
  });
}
"""


async def node_edit_button(page):
    """The Edit button in the node toolbar (not the section-edit ones)."""
    handles = await page.evaluate_handle("""() => [...document.querySelectorAll('.v-button')].filter(bt => {
      const cap = (bt.querySelector('.v-button-caption')||{}).textContent||'';
      if (cap.trim() !== 'Edit') return false;
      let p = bt; for (let i=0;i<8&&p;i++){ if ((p.className||'').includes('micro-dialogs')) return true; p=p.parentElement; }
      return false;
    })""")
    props = await handles.get_properties()
    for _, h in props.items():
        el = h.as_element()
        if el:
            return el
    return None


async def close_windows(page):
    for _ in range(6):
        wins = page.locator(".v-window")
        if not await wins.count():
            return
        # prefer an explicit dismiss button - different node-editor modals use
        # "Cancel" or "Close" (Escape alone does not reliably close either)
        dismissed = False
        for label in ("Close", "Cancel", "Exit"):
            btn = page.locator(".v-window .v-button-caption", has_text=label)
            if await btn.count():
                await btn.last.click()
                dismissed = True
                break
        if not dismissed:
            await page.keyboard.press("Escape")
        await page.wait_for_timeout(500)


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
            for tag, labels, row_idxs in TARGETS:
                print(f"\n=== {tag} :: {' / '.join(labels)} ===")
                try:
                    await S.navigate_and_select(page, labels)
                    await S.wait_round_trip(page)
                except Exception as e:  # noqa: BLE001
                    print(f"  select failed: {e!r}")
                    continue
                rows = page.locator(".v-table .v-table-body tr")
                nrows = await rows.count()
                print(f"  {nrows} rows")
                for ri in row_idxs:
                    if ri >= nrows:
                        continue
                    await rows.nth(ri).click()
                    await page.wait_for_timeout(500)
                    btn = await node_edit_button(page)
                    if not btn:
                        print(f"  row {ri}: no node-Edit button"); continue
                    await btn.click()
                    await page.wait_for_timeout(1300)
                    dump = await page.evaluate(FORM_DUMP_JS)
                    slug = f"{tag.split()[0]}_row{ri}"
                    (OUT / f"form_{slug}.json").write_text(
                        json.dumps(dump, indent=1, ensure_ascii=False))
                    try:
                        await page.screenshot(
                            path=str(OUT / f"form_{slug}.png"), timeout=5000)
                    except Exception as e:  # noqa: BLE001
                        print(f"  (screenshot skipped: {e!r})")
                    for w in dump:
                        print(f"  row {ri} -> window {w['caption'][:60]!r} "
                              f"tabs={w['tabs']} buttons={w['buttons']}")
                        for f in w["fields"][:40]:
                            print(f"       - {f['cap'][:42]!r:44} {f['widgets']}  = {f['val'][:60]!r}")
                    await close_windows(page)
        finally:
            await cdp.send("Browser.setWindowBounds", {"windowId": wid, "bounds": {
                "left": 60, "top": 60, "width": 1400, "height": 1000, "windowState": "normal"}})
            print("\nwindow restored")


if __name__ == "__main__":
    asyncio.run(main())
