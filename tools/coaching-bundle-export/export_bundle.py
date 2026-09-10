"""Build coaching.bundle.json: an accurate flat node list for every micro dialog
of a PMCP coaching (folders included) - stable uids, order, every grid column,
and the randomisation group - scraped from the live Vaadin editor over CDP.

No LLM anywhere in here: it drives a browser you already logged into and parses
the page. See README.md.

  export_bundle.py                     -> coaching.bundle.json  (grid data only)
  export_bundle.py --enrich REPORT.html-> also coaching.bundle.v2.json
                                          (full per-language text + decision
                                           branches, joined from the Report HTML)

Env:
  PMCP_CDP   CDP endpoint of the logged-in Chromium   (default http://127.0.0.1:9222)
  PMCP_OUT   output directory                          (default: current dir)
  PMCP_WIDE  window width px to defeat the menu overflow (default 12000)
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

from playwright.async_api import async_playwright

import _menu_nav as S  # menu discovery + navigation helpers

OUT = Path(os.environ.get("PMCP_OUT", Path.cwd()))
OUT.mkdir(parents=True, exist_ok=True)
BUNDLE = OUT / "coaching.bundle.json"
CDP_URL = os.environ.get("PMCP_CDP", "http://127.0.0.1:9222")
WIDE = int(os.environ.get("PMCP_WIDE", "12000"))

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
      .map(c => c.textContent.replace(/ /g, ' ').trim());
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


async def sweep_table(page) -> tuple[int, dict[int, list[str]], list[int]]:
    seen: dict[int, list[str]] = {}
    # let the table settle: rows present + scroll area sized
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
        # whole table already in the DOM
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
    """Every menu node (folders + leaves) as {labels, isFolder}."""
    leaves = await S.discover(page)          # leaves only
    leafset = {tuple(l["labels"]) for l in leaves}
    folders: set[tuple] = set()
    for l in leaves:
        for k in range(1, len(l["labels"])):
            folders.add(tuple(l["labels"][:k]))
    targets = [{"labels": list(t), "isFolder": True} for t in sorted(folders)]
    targets += [{"labels": l["labels"], "isFolder": False} for l in leaves]
    # keep discovery order for leaves; put each folder just before its children
    order = {tuple(l["labels"]): i for i, l in enumerate(leaves)}
    def sortkey(t):
        lab = tuple(t["labels"])
        if t["isFolder"]:
            firstchild = min((order[k] for k in leafset if k[:len(lab)] == lab), default=1e9)
            return (firstchild, 0, len(lab))
        return (order[lab], 1, 0)
    targets.sort(key=sortkey)
    return targets


def report_counts(html_path: str | None) -> dict[str, int]:
    if not html_path:
        return {}
    try:
        import enrich_bundle
        m = enrich_bundle.parse_report(Path(html_path).read_bytes())
        return {d.name: len(d.nodes) for d in m.micro_dialogs}
    except Exception as e:  # noqa: BLE001
        print(f"(report cross-check unavailable: {e!r})")
        return {}


async def main() -> None:
    enrich_html = None
    if "--enrich" in sys.argv:
        i = sys.argv.index("--enrich")
        enrich_html = sys.argv[i + 1] if i + 1 < len(sys.argv) else None
        if not enrich_html or not Path(enrich_html).is_file():
            sys.exit("--enrich needs a path to the coaching's Report HTML export")
    rc = report_counts(enrich_html)
    async with async_playwright() as pw:
        b = await pw.chromium.connect_over_cdp(CDP_URL)
        ctx = b.contexts[0]
        page = ctx.pages[0]
        cdp = await ctx.new_cdp_session(page)
        wid = (await cdp.send("Browser.getWindowForTarget"))["windowId"]
        orig = {"left": 60, "top": 60, "width": 1400, "height": 1000, "windowState": "normal"}
        await cdp.send("Browser.setWindowBounds", {"windowId": wid, "bounds": {
            "left": 0, "top": 0, "width": WIDE, "height": 1400, "windowState": "normal"}})
        await page.wait_for_timeout(1500)
        try:
            if not await S.ensure_micro_dialogs(page):
                await cdp.send("Browser.setWindowBounds", {"windowId": wid, "bounds": orig})
                sys.exit("Micro Dialogs menu not on screen. In the browser: open "
                         "this coaching's Edit view, deactivate Monitoring, then "
                         "click 'Micro Dialogs' — and rerun. (Monitoring must be "
                         "off or the menu's popups silently fail.)")
            print("--- discovery ---")
            targets = await all_targets(page)
            print(f"{len(targets)} targets "
                  f"({sum(t['isFolder'] for t in targets)} folders, "
                  f"{sum(not t['isFolder'] for t in targets)} leaves)")

            micro_dialogs, nodes = [], []
            mism = []
            for seq, t in enumerate(targets):
                name = " / ".join(t["labels"])
                md_uid = f"md-{seq:03d}"
                try:
                    await S.navigate_and_select(page, t["labels"])
                    await S.wait_round_trip(page)
                    total, seen, missing = await sweep_table(page)
                except Exception as e:  # noqa: BLE001
                    print(f"[{seq}] {name}  ERROR {e!r}")
                    micro_dialogs.append({"uid": md_uid, "name": t["labels"][-1],
                                          "folderPath": t["labels"][:-1],
                                          "isFolder": t["isFolder"], "error": repr(e)})
                    continue
                node_uids = []
                for i in range(total):
                    cells = seen.get(i, [""] * len(COLS))
                    row = {COLS[j]: (cells[j] if j < len(cells) else "")
                           for j in range(len(COLS))}
                    nuid = f"{md_uid}#{i:03d}"
                    node_uids.append(nuid)
                    nodes.append({
                        "uid": nuid, "microDialogUid": md_uid, "order": i,
                        "type": {"Message": "message", "DECISION POINT": "decision",
                                 "Command Message": "command", "EVENT": "event"}
                                .get(row["Type"], row["Type"].lower() or "message"),
                        "rawType": row["Type"],
                        "comment": row["Comment"],
                        "gridText": row["Message Text / Events"],
                        "channel": row["Channel"],
                        "answerType": row["Answer Type"],
                        "resultVariable": row["Result Variable"],
                        "randomisationGroup": row["Randomisation Group"],
                        "flags": {
                            "commandMessage": row["Command Message"],
                            "containsMedia": row["Contains Media Content"],
                            "containsSurvey": row["Contains Link To Survey"],
                            "containsRules": row["Contains Rules"],
                        },
                    })
                leaf_name = t["labels"][-1]
                exp = rc.get(leaf_name)
                flag = ""
                if exp is not None and exp != total:
                    flag = f"  !! report={exp}"
                    mism.append({"name": name, "grid": total, "report": exp})
                if missing:
                    flag += f"  MISSING {missing[:5]}"
                micro_dialogs.append({
                    "uid": md_uid, "name": leaf_name, "folderPath": t["labels"][:-1],
                    "isFolder": t["isFolder"], "nodeCount": total, "nodeUids": node_uids,
                    "missingRows": missing,
                })
                print(f"[{seq}/{len(targets)}] {name}  nodes={total}{flag}")

            bundle = {
                "coaching": {
                    "name": "ALEX v01 (Coaching \"ALEX v01 zum Ausprobieren\")",
                    "languages": ["en-GB", "ro-RO"],
                    "scrapedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "stage": 1,
                },
                "microDialogs": micro_dialogs,
                "nodes": nodes,
                "validation": {
                    "reportHtmlAvailable": bool(rc),
                    "countMismatches": mism,
                    "dialogsWithMissingRows": [m["name"] for m in micro_dialogs
                                               if m.get("missingRows")],
                },
            }
            BUNDLE.write_text(json.dumps(bundle, indent=2, ensure_ascii=False))
            print(f"\nwrote {BUNDLE}")
            print(f"  microDialogs={len(micro_dialogs)}  nodes={len(nodes)}")
            print(f"  count mismatches vs report: {len(mism)}")
            for m in mism:
                print(f"    {m['name']}  grid={m['grid']} report={m['report']}")
        finally:
            await cdp.send("Browser.setWindowBounds", {"windowId": wid, "bounds": orig})
            print("window restored")

    if enrich_html:
        print("\n--- enrich from Report HTML ---")
        import enrich_bundle
        enrich_bundle.enrich(BUNDLE, Path(enrich_html), OUT)


if __name__ == "__main__":
    asyncio.run(main())
