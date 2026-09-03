"""Scrape every micro-dialog message table from the ALEX v01 coaching in the
live PMCP Vaadin editor, to enumerate the `r_` Randomisation Groups that the
Report HTML export drops.

Approach (all over CDP against the already-logged-in Chromium on :9222):
  0. Resize the REAL browser window very wide (~12000px). The `.md-menu`
     MenuBar's `►` overflow submenu will not open via scripted input, but at
     that width every top-level item renders inline and the `►` disappears.
     No viewport emulation -> mouse hit-testing stays correct.
  1. DISCOVERY - DFS the menubar by index (only hovers, no selection, so the
     bar does not reflow). Record a label-path for every leaf micro dialog.
  2. SWEEP - for each leaf, navigate the menu BY LABEL (robust to any reflow
     caused by selecting a dialog), click it, wait for the Vaadin round trip,
     then scroll-and-accumulate every row of the `.v-table`.
  3. Restore the window size. The browser is never closed (not ours).

Run:  PMCP_CDP=http://127.0.0.1:9222 .venv/bin/python scratchpad/pmcp_scrape.py
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import time
from pathlib import Path

from playwright.async_api import async_playwright

CDP_URL = os.environ.get("PMCP_CDP", "http://127.0.0.1:9222").strip()
WIDE = int(os.environ.get("PMCP_WIDE", "12000"))

OUT = Path(os.environ.get("PMCP_OUT", Path.cwd()))
OUT.mkdir(parents=True, exist_ok=True)
GO_FILE = OUT / "GO"
ABORT_FILE = OUT / "ABORT"
RAW_JSONL = OUT / "rgroups_raw.jsonl"
RAW_JSON = OUT / "rgroups_raw.json"
TREE_JSON = OUT / "rgroups_tree.json"

BAR = ".v-menubar.md-menu > .v-menubar-menuitem"

SWEEP_JS = r"""
async () => {
  const table = document.querySelector('.v-table');
  if (!table) return { headers: [], total: 0, rows: [], rGroups: [], note: 'no .v-table' };
  const scroller = table.querySelector('.v-scrollable')
    || table.querySelector('.v-table-body-wrapper')
    || table.querySelector('.v-table-body').parentElement;
  const heads = [...table.querySelectorAll('.v-table-header-cell .v-table-caption-container')]
    .map(e => e.textContent.trim());
  const seen = new Map();
  const grab = () => table.querySelectorAll('.v-table-body tr').forEach(tr => {
    const cells = [...tr.querySelectorAll('.v-table-cell-wrapper')].map(c => c.textContent.trim());
    if (cells.length) seen.set((tr.className.match(/v-table-row-\d+/)||[''])[0] + '|' + cells.join(''), cells);
  });
  scroller.scrollTop = 0; await new Promise(r => setTimeout(r, 160)); grab();
  const step = Math.max(scroller.clientHeight * 0.75, 160);
  let guard = 0;
  while (scroller.scrollTop + scroller.clientHeight < scroller.scrollHeight - 2 && guard++ < 4000) {
    scroller.scrollTop += step;
    await new Promise(r => setTimeout(r, 170));
    grab();
  }
  scroller.scrollTop = scroller.scrollHeight;
  await new Promise(r => setTimeout(r, 200)); grab();
  const rows = [...seen.values()];
  const rgIdx = heads.indexOf('Randomisation Group');
  return {
    headers: heads, total: rows.length, rows,
    rGroups: [...new Set(rows.map(r => r[rgIdx]).filter(v => v && v.startsWith('r_')))],
  };
}
"""


def norm(txt: str) -> str:
    return re.sub(r"\s+", " ", (txt or "").replace("►", "")).strip()


async def bar_loc(page):
    return page.locator(BAR)


async def popups(page):
    return page.locator(".v-menubar-popup")


async def close_menus(page):
    for _ in range(6):
        if await (await popups(page)).count() == 0:
            return
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(110)


async def sub_loc(page, depth: int):
    """Items inside the popup at 1-based depth."""
    return (await popups(page)).nth(depth - 1).locator(
        ".v-menubar-submenu > .v-menubar-menuitem"
    )


async def has_indicator(item) -> bool:
    return await item.locator(".v-menubar-submenu-indicator").count() > 0


async def caption(item) -> str:
    cap = item.locator(".v-menubar-menuitem-caption")
    if await cap.count():
        return norm(await cap.inner_text())
    return norm(await item.inner_text())


async def wait_popup(page, depth: int, tries: int = 40) -> bool:
    for _ in range(tries):
        if await (await popups(page)).count() >= depth:
            return True
        await page.wait_for_timeout(100)
    return False


async def open_folder_path(page, labels: list[str]) -> int:
    """Re-navigate from the bar and hover every segment of `labels` so the
    folder's own submenu popup is open. Returns depth == len(labels)."""
    await close_menus(page)
    bar = await bar_loc(page)
    n = await bar.count()
    top = None
    for i in range(n):
        if await caption(bar.nth(i)) == labels[0]:
            top = bar.nth(i)
            break
    if top is None:
        raise RuntimeError(f"top {labels[0]!r} not found")
    # Vaadin MenuBar: from a closed state a top item opens on CLICK, not hover
    # (hover only switches between already-open top menus). Nudge the virtual
    # mouse first so the click definitely dispatches a fresh move. Retry: a
    # stray click can toggle it shut.
    opened = False
    for _ in range(4):
        await page.mouse.move(3, 3)
        await page.wait_for_timeout(40)
        try:
            await top.click(timeout=6000)
        except Exception:  # noqa: BLE001
            pass
        if await wait_popup(page, 1, tries=15):
            opened = True
            break
        await close_menus(page)
    if not opened:
        raise RuntimeError(f"popup 1 for {labels[0]!r} never opened")
    for depth, lbl in enumerate(labels[1:], start=1):
        items = await sub_loc(page, depth)
        cnt = await items.count()
        tgt = None
        for j in range(cnt):
            if await caption(items.nth(j)) == lbl:
                tgt = items.nth(j)
                break
        if tgt is None:
            raise RuntimeError(f"segment {lbl!r} not found at depth {depth}")
        await tgt.hover(timeout=8000)
        if not await wait_popup(page, depth + 1):
            raise RuntimeError(f"popup {depth+1} for {lbl!r} never opened")
    return len(labels)


async def read_children(page, depth: int) -> list[tuple[str, bool]]:
    items = await sub_loc(page, depth)
    m = await items.count()
    out = []
    for j in range(m):
        it = items.nth(j)
        out.append((await caption(it), await has_indicator(it)))
    return out


async def discover(page) -> list[dict]:
    """Recursive DFS where every folder is opened by a fresh re-navigation from
    the bar (no lingering popups -> no accidental parent collapse)."""
    leaves: list[dict] = []

    async def expand(labels: list[str]):
        depth = await open_folder_path(page, labels)
        kids = await read_children(page, depth)
        await close_menus(page)
        print(f"  {'  '*depth}{' / '.join(labels)} -> {len(kids)}")
        for lbl, folder in kids:
            if lbl in ("", "·", "►", "."):
                continue
            if folder:
                try:
                    await expand(labels + [lbl])
                except Exception as e:  # noqa: BLE001
                    print(f"  ! folder {' / '.join(labels+[lbl])}: {e!r}")
                    await close_menus(page)
            else:
                leaves.append({"labels": labels + [lbl]})

    bar = await bar_loc(page)
    n = await bar.count()
    print(f"menubar: {n} top-level items")
    tops: list[tuple[str, bool]] = []
    for i in range(n):
        it = bar.nth(i)
        lbl = await caption(it)
        if lbl in ("", "·", "►", "."):
            continue
        tops.append((lbl, await has_indicator(it)))
    for lbl, folder in tops:
        if ABORT_FILE.exists():
            break
        if folder:
            try:
                await expand([lbl])
            except Exception as e:  # noqa: BLE001
                print(f"  ! top folder {lbl!r}: {e!r}")
                await close_menus(page)
        else:
            leaves.append({"labels": [lbl]})
    await close_menus(page)

    # flag duplicate label-paths (ambiguous navigation)
    seen: dict[str, int] = {}
    for lf in leaves:
        key = " / ".join(lf["labels"])
        seen[key] = seen.get(key, 0) + 1
    dups = {k: v for k, v in seen.items() if v > 1}
    if dups:
        print(f"  ! duplicate leaf paths: {dups}")
    return leaves


async def navigate_and_select(page, labels: list[str]):
    """Open the menu path by label and click the final leaf."""
    if len(labels) == 1:
        await close_menus(page)
        bar = await bar_loc(page)
        n = await bar.count()
        await page.mouse.move(3, 3)
        for i in range(n):
            if await caption(bar.nth(i)) == labels[0]:
                await bar.nth(i).click(timeout=8000)
                return
        raise RuntimeError(f"top item {labels[0]!r} not found")
    # reuse the folder-opening logic, then click the leaf in the deepest popup
    await open_folder_path(page, labels[:-1])
    depth = len(labels) - 1
    items = await sub_loc(page, depth)
    cnt = await items.count()
    for j in range(cnt):
        if await caption(items.nth(j)) == labels[-1]:
            await items.nth(j).click(timeout=8000)
            return
    raise RuntimeError(f"leaf {labels[-1]!r} not found at depth {depth}")


async def wait_round_trip(page):
    ind = page.locator(".v-loading-indicator")
    try:
        await ind.wait_for(state="visible", timeout=1000)
    except Exception:
        pass
    try:
        await ind.wait_for(state="hidden", timeout=45000)
    except Exception:
        pass
    await page.wait_for_timeout(400)


async def main() -> None:
    RAW_JSONL.unlink(missing_ok=True)
    for f in (GO_FILE, ABORT_FILE):
        f.unlink(missing_ok=True)

    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(CDP_URL)
        ctx = browser.contexts[0]
        page = ctx.pages[0]
        print(f"attached: {page.url}")

        cdp = await ctx.new_cdp_session(page)
        win = await cdp.send("Browser.getWindowForTarget")
        wid, orig = win["windowId"], win["bounds"]
        print(f"window {wid} original bounds {orig}")

        async def set_width(w: int):
            await cdp.send("Browser.setWindowBounds", {"windowId": wid, "bounds": {
                "left": 0, "top": 0, "width": w, "height": 1400,
                "windowState": "normal"}})
            await page.wait_for_timeout(1500)

        try:
            await set_width(WIDE)
            bar = await bar_loc(page)
            n = await bar.count()
            last = norm(await bar.nth(n - 1).inner_text())
            print(f"at {WIDE}px: {n} bar items, last = {last!r}")
            if last == "►":
                await set_width(min(WIDE * 2, 20000))
                n = await (await bar_loc(page)).count()
                last = norm(await (await bar_loc(page)).nth(n - 1).inner_text())
                print(f"widened again: {n} bar items, last = {last!r}")
                if last == "►":
                    print("WARNING: overflow ► still present; some dialogs may be missed")

            print("\n--- phase 1: discovery ---")
            leaves = await discover(page)
            TREE_JSON.write_text(json.dumps(leaves, indent=2, ensure_ascii=False))
            print(f"discovered {len(leaves)} leaf micro dialogs")

            print("\n--- phase 2: sweep ---")
            all_msgs: list[dict] = []
            per_dialog: list[dict] = []
            for k, leaf in enumerate(leaves, 1):
                if ABORT_FILE.exists():
                    print("ABORT seen - stopping sweep"); break
                name = " / ".join(leaf["labels"])
                try:
                    await navigate_and_select(page, leaf["labels"])
                    await wait_round_trip(page)
                    res = await page.evaluate(SWEEP_JS)
                except Exception as e:  # noqa: BLE001
                    print(f"[{k}/{len(leaves)}] {name}  ERROR {e!r}")
                    per_dialog.append({"microDialog": name, "labels": leaf["labels"],
                                       "error": repr(e)})
                    await close_menus(page)
                    continue
                heads = res["headers"]

                def col(h):
                    return heads.index(h) if h in heads else -1

                ci, mi, ri, gi = (col("Comment"), col("Message Text / Events"),
                                  col("Result Variable"), col("Randomisation Group"))
                rows_out = []
                for cells in res["rows"]:
                    def g(idx):
                        return cells[idx] if 0 <= idx < len(cells) else ""
                    rec = {"microDialog": name, "comment": g(ci),
                           "messageText": g(mi), "resultVariable": g(ri),
                           "randomisationGroup": g(gi), "cells": cells}
                    rows_out.append(rec)
                    all_msgs.append(rec)
                entry = {"microDialog": name, "labels": leaf["labels"],
                         "headers": heads, "total": res["total"],
                         "rGroups": res["rGroups"], "rows": rows_out}
                per_dialog.append(entry)
                with RAW_JSONL.open("a") as fh:
                    fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
                print(f"[{k}/{len(leaves)}] {name}  rows={res['total']:>3}  "
                      f"r_groups={res['rGroups']}")

            bundle = {"generatedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                      "coaching": "ALEX v01 (live PMCP editor)",
                      "leafCount": len(leaves), "dialogs": per_dialog,
                      "messages": all_msgs}
            RAW_JSON.write_text(json.dumps(bundle, indent=2, ensure_ascii=False))
            print(f"\nwrote {RAW_JSON}  ({len(all_msgs)} message rows)")
        finally:
            try:
                await cdp.send("Browser.setWindowBounds",
                               {"windowId": wid, "bounds": orig})
                print("restored window size")
            except Exception as e:  # noqa: BLE001
                print(f"could not restore window: {e!r}")


if __name__ == "__main__":
    asyncio.run(main())
