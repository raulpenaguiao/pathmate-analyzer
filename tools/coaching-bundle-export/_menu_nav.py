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


async def ensure_micro_dialogs(page) -> bool:
    """True once the Micro Dialogs menubar (`.v-menubar.md-menu`) is on screen.
    If it isn't, click the in-app "Micro Dialogs" section tab (same idea as
    `_rules_nav.ensure_rules_tree`) and wait. Returns False if it still isn't
    there — the caller should then ask the operator to open that view and
    check that Monitoring is deactivated (the menubar's popups need it off).
    Never touches the Monitoring toggle itself."""
    if await page.locator(".v-menubar.md-menu").count():
        return True
    for cand in (
        page.get_by_text(re.compile(r"^\s*micro[\s-]?dialog", re.I)),
        page.locator(".v-captiontext", has_text=re.compile("micro", re.I)),
    ):
        try:
            if await cand.count():
                await cand.first.click(timeout=4000)
                await wait_round_trip(page)
                break
        except Exception:  # noqa: BLE001
            continue
    return bool(await page.locator(".v-menubar.md-menu").count())


# ---------------------------------------------------------------------------
# Micro-dialog table sweep (the editor grid) — used by export_coaching.py
# ---------------------------------------------------------------------------

GRAB_JS = r"""
() => {
  const t = document.querySelector('.v-table');
  if (!t) return { total: 0, rows: [], ch: 0, sh: 0 };
  const sc = t.querySelector('.v-table-body-wrapper');
  const trs = [...t.querySelectorAll('.v-table-body tr')];
  const withCells = trs.filter(tr => tr.querySelectorAll('.v-table-cell-wrapper').length);
  const rh = trs[0] ? trs[0].offsetHeight : 24;
  const ch = sc.clientHeight, sh = sc.scrollHeight;
  const scrollable = sh > ch + 4;
  const total = scrollable ? Math.max(withCells.length, Math.round(sh / rh))
                           : withCells.length;
  const base = sc.getBoundingClientRect().top;
  const rows = [];
  withCells.forEach(tr => {
    const cells = [...tr.querySelectorAll('.v-table-cell-wrapper')]
      .map(c => c.textContent.replace(/ /g, ' ').trim());
    const idx = scrollable
      ? Math.round((tr.getBoundingClientRect().top - base + sc.scrollTop) / rh)
      : trs.indexOf(tr);
    rows.push([idx, cells]);
  });
  return { total, rows, ch, sh, top: sc.scrollTop, scrollable };
}
"""

SET_SCROLL_JS = "(y) => { const w = document.querySelector('.v-table .v-table-body-wrapper'); if (w) w.scrollTop = y; }"

COLS = ["Type", "Comment", "Message Text / Events", "Channel", "Answer Type",
        "Result Variable", "Randomisation Group", "Command Message",
        "Contains Media Content", "Contains Link To Survey", "Contains Rules"]


async def sweep_table(page):
    """Scroll-and-accumulate every row of the current micro-dialog `.v-table`.
    Returns (total, {row_index: [cells]}, [missing_indices])."""
    seen: dict[int, list[str]] = {}
    try:
        await page.wait_for_selector(".v-table .v-table-body tr", timeout=8000)
    except Exception:
        pass
    await page.wait_for_timeout(350)
    meta = await page.evaluate(GRAB_JS)
    total = meta["total"]
    for idx, cells in meta["rows"]:
        if 0 <= idx < total:
            seen[idx] = cells
    if total == 0:
        return 0, {}, []
    if not meta["scrollable"]:
        return total, seen, [i for i in range(total) if i not in seen]
    step = meta["ch"] or 240
    y, stale = 0, 0
    while y <= meta["sh"] + step:
        await page.evaluate(SET_SCROLL_JS, y)
        try:
            await page.locator(".v-loading-indicator").wait_for(state="visible", timeout=350)
            await page.locator(".v-loading-indicator").wait_for(state="hidden", timeout=15000)
        except Exception:
            pass
        await page.wait_for_timeout(230)
        g = await page.evaluate(GRAB_JS)
        before = len(seen)
        for idx, cells in g["rows"]:
            if 0 <= idx < total:
                seen[idx] = cells
        stale = stale + 1 if len(seen) == before else 0
        if stale >= 3 and len(seen) >= total:
            break
        y += step
    missing = [i for i in range(total) if i not in seen]
    return total, seen, missing


async def all_targets(page) -> list[dict]:
    """Every menu node (folders + leaves) as {labels, isFolder}, ordered so
    each folder comes just before its children."""
    leaves = await discover(page)
    leafset = {tuple(l["labels"]) for l in leaves}
    folders: set[tuple] = set()
    for l in leaves:
        for k in range(1, len(l["labels"])):
            folders.add(tuple(l["labels"][:k]))
    targets = [{"labels": list(t), "isFolder": True} for t in sorted(folders)]
    targets += [{"labels": l["labels"], "isFolder": False} for l in leaves]
    order = {tuple(l["labels"]): i for i, l in enumerate(leaves)}

    def sortkey(t):
        lab = tuple(t["labels"])
        if t["isFolder"]:
            firstchild = min((order[k] for k in leafset if k[:len(lab)] == lab), default=1e9)
            return (firstchild, 0, len(lab))
        return (order[lab], 1, 0)

    targets.sort(key=sortkey)
    return targets


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
