"""Stage-3 discovery probe: the live PMCP editor's **Rules tab** (a `.v-tree`).

The randomisation-group sweep (`export_bundle.py`) walks the Micro Dialogs
`.v-menubar`. Rule-level timing lives somewhere else entirely: the Rules tab,
which is a Vaadin `.v-tree` (expand/collapse triangles), and each rule's
"Edit rule:" modal. This script is the read-only-ish discovery pass that must
happen *before* the bulk Stage-3 scraper is written — it answers the open
schema questions in DESIGN.md's "Not yet captured" section:

  1. tree markup: node selectors, depth, per-row icon set (icon src -> action
     type?), aria-expanded, the four top sections
     (DAILY / PERIODIC BASIS / UNEXPECTED MESSAGE / USER INTENTION).
  2. "Edit rule:" modal field set, for a SAMPLE of rules across all four
     sections and both action paths ("Send message" vs "Start micro dialog").
     Fields of interest: which micro dialog is started, "Hour to send
     message", "Minutes ... not answered" timeout, the DOES / DOES NOT answer
     sub-trees, "Message group to send messages from".

NOT fully read-only. Confirmed live (see root README hurdles): the "Edit
rule:" modal's dismiss button **commits the form** ("The rule has been
updated." toast fires with zero fields touched). There is no known safe
cancel. So every opened rule modal = one no-op re-save. Only run this against the
**sandbox** coaching "ALEX v01 zum Ausprobieren" (explicitly not production,
writes low-stakes and logged), and write an `autochanges/` entry afterwards.
`SAMPLE_LIMIT` caps how many modals are opened.

Prereqs (same as export_bundle.py): a hand-logged-in Chromium on CDP :9222,
Monitoring deactivated, and the browser already navigated to the target
coaching's **Rules** tab with the tree visible.

Run:
  PMCP_CDP=http://127.0.0.1:9222 PMCP_OUT="$PWD/tools/coaching-bundle-export/spike" \\
    .venv/bin/python tools/coaching-bundle-export/probe_rules_tree.py
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path

from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("PMCP_OUT", HERE / "spike"))
OUT.mkdir(parents=True, exist_ok=True)
CDP = os.environ.get("PMCP_CDP", "http://127.0.0.1:9222")
WIDE = int(os.environ.get("PMCP_WIDE", "3000"))

# how many "Edit rule:" modals to open (each one is a no-op re-save)
SAMPLE_LIMIT = int(os.environ.get("PMCP_RULE_SAMPLE", "8"))

# ---------------------------------------------------------------------------
# Tree structure dump (pure read)
# ---------------------------------------------------------------------------

TREE_DUMP_JS = r"""
() => {
  const trees = [...document.querySelectorAll('.v-tree')];
  const dump = (tree) => {
    const nodes = [...tree.querySelectorAll('.v-tree-node')];
    return nodes.map((n, i) => {
      // DOM-nesting depth: count .v-tree-node-children ancestors within this tree
      let depth = 0, p = n.parentElement;
      while (p && p !== tree) {
        if (p.classList.contains('v-tree-node-children')) depth++;
        p = p.parentElement;
      }
      const capEl = n.querySelector(':scope > .v-tree-node-caption') ||
                    n.querySelector('.v-tree-node-caption');
      const cap = capEl ? capEl.textContent.replace(/\s+/g, ' ').trim() : '';
      const iconEl = capEl ? capEl.querySelector('img.v-icon, .v-icon') : null;
      const icon = iconEl ? (iconEl.getAttribute('src') ||
                             iconEl.className) : '';
      const li = n.querySelector(':scope > .v-tree-node-caption [role="treeitem"], :scope > [role="treeitem"]');
      return {
        i, depth, caption: cap,
        classes: n.className,
        icon,
        ariaExpanded: (li || n).getAttribute && (li || n).getAttribute('aria-expanded'),
        leaf: n.classList.contains('v-tree-node-leaf'),
        expanded: n.classList.contains('v-tree-node-expanded'),
        childCount: (n.querySelector(':scope > .v-tree-node-children') || {childElementCount: 0}).childElementCount,
      };
    });
  };
  return trees.map((t, ti) => ({
    treeIndex: ti,
    classes: t.className,
    nodeCount: t.querySelectorAll('.v-tree-node').length,
    nodes: dump(t),
    outerHTMLHead: t.outerHTML.slice(0, 4000),
  }));
}
"""

# reused from probe_node_editor.py — dumps every .v-window's form fields
FORM_DUMP_JS = r"""
() => {
  const wins = [...document.querySelectorAll('.v-window')];
  return wins.map(w => {
    const fields = [];
    w.querySelectorAll('.v-formlayout-row, .v-slot, tr').forEach(row => {
      const capEl = row.querySelector('.v-formlayout-captioncell, .v-caption, .v-captiontext, th');
      const valEl = row.querySelector('.v-formlayout-contentcell, td:last-child') || row;
      const cap = (capEl ? capEl.textContent : '').replace(/\s+/g, ' ').trim();
      if (!cap) return;
      let val = '';
      const inp = valEl.querySelector('input, textarea, select');
      if (inp) val = (inp.value != null ? inp.value : inp.textContent) || '';
      else {
        const combo = valEl.querySelector('.v-filterselect-input, .v-select-optiongroup, .v-checkbox, .v-slider, .v-label');
        val = combo ? combo.textContent : '';
      }
      val = (val || '').replace(/\s+/g, ' ').trim().slice(0, 240);
      const checked = [...valEl.querySelectorAll('input[type=checkbox]')].map(c => c.checked);
      const widgets = [...valEl.querySelectorAll('[class*="v-"]')]
        .map(e => (e.className || '').split(' ').find(c => /^v-(textfield|textarea|filterselect|select|checkbox|button|table|tree|tabsheet|richtextarea|datefield|slider|nativeselect)$/.test(c)))
        .filter(Boolean);
      fields.push({ cap, val, checked, widgets: [...new Set(widgets)] });
    });
    return {
      caption: (w.querySelector('.v-window-header') || {}).textContent || '',
      buttons: [...w.querySelectorAll('.v-button-caption')].map(e => e.textContent.replace(/\s+/g, ' ').trim()).filter(Boolean),
      tabs: [...w.querySelectorAll('.v-tabsheet-tabitemcell')].map(e => e.textContent.replace(/\s+/g, ' ').trim()).filter(Boolean),
      fields: fields.filter(f => f.cap),
      html: w.outerHTML.slice(0, 120000),
    };
  });
}
"""


async def dump_tree(page, tag: str) -> list[dict]:
    trees = await page.evaluate(TREE_DUMP_JS)
    (OUT / f"rules_tree_{tag}.json").write_text(
        json.dumps(trees, indent=1, ensure_ascii=False))
    for t in trees:
        print(f"  tree[{t['treeIndex']}]  {t['nodeCount']} nodes  ({t['classes']})")
        for n in t["nodes"]:
            mark = "▸" if not n["leaf"] and not n["expanded"] else (
                "▾" if n["expanded"] else " ")
            print(f"    {'  ' * n['depth']}{mark} {n['caption'][:70]!r}"
                  f"  icon={n['icon'].split('/')[-1][:28]!r}"
                  f"  leaf={n['leaf']} exp={n['expanded']}")
    return trees


async def expand_all(page, rounds: int = 12) -> None:
    """Vaadin tree: selecting a node + ArrowRight expands it. Repeat until no
    collapsed non-leaf nodes remain (or `rounds` exhausted)."""
    for r in range(rounds):
        trees = await page.evaluate(TREE_DUMP_JS)
        collapsed = [(ti, n["i"]) for ti, t in enumerate(trees)
                     for n in t["nodes"]
                     if not n["leaf"] and not n["expanded"]]
        if not collapsed:
            print(f"  fully expanded after {r} round(s)")
            return
        print(f"  round {r}: {len(collapsed)} collapsed node(s)")
        for ti, ni in collapsed:
            node = page.locator(".v-tree").nth(ti).locator(".v-tree-node").nth(ni)
            cap = node.locator(".v-tree-node-caption").first
            try:
                await cap.click(timeout=4000)
                await page.wait_for_timeout(120)
                await page.keyboard.press("ArrowRight")
                await page.wait_for_timeout(180)
            except Exception as e:  # noqa: BLE001
                print(f"    node {ti}/{ni}: {e!r}")
    print(f"  still collapsed after {rounds} rounds — see rules_tree_expanded.json")


async def rule_edit_button(page):
    """The Rules-tab toolbar 'Edit' button (rule editor), not a section-edit."""
    handles = await page.evaluate_handle(
        """() => [...document.querySelectorAll('.v-button')].filter(bt => {
        const cap = (bt.querySelector('.v-button-caption')||{}).textContent||'';
        return cap.trim() === 'Edit';
      })""")
    props = await handles.get_properties()
    for _, h in props.items():
        el = h.as_element()
        if el and await el.is_visible():
            return el
    return None


async def close_windows(page):
    """WARNING: on the rule editor the only dismiss button commits the form.
    We click it anyway (sandbox only) and record the count."""
    committed = 0
    for _ in range(6):
        wins = page.locator(".v-window")
        if not await wins.count():
            return committed
        clicked = False
        for label in ("Cancel", "Close", "Exit", "OK"):
            btn = page.locator(".v-window .v-button-caption", has_text=label)
            if await btn.count():
                await btn.last.click()
                if label in ("Close", "OK"):
                    committed += 1
                clicked = True
                break
        if not clicked:
            await page.keyboard.press("Escape")
        await page.wait_for_timeout(500)
    return committed


async def sample_rule_modals(page, trees: list[dict]) -> list[dict]:
    """Open 'Edit rule:' for up to SAMPLE_LIMIT rules, spread across the four
    top sections. Each open is a no-op re-save."""
    # pick leaf-ish rule rows: not the four section headers (depth 0), spread out
    candidates: list[tuple[int, int, str]] = []
    for ti, t in enumerate(trees):
        for n in t["nodes"]:
            if n["depth"] >= 1 and n["caption"]:
                candidates.append((ti, n["i"], n["caption"]))
    # even spread
    picks = candidates[:: max(1, len(candidates) // SAMPLE_LIMIT)][:SAMPLE_LIMIT]
    print(f"\n--- sampling {len(picks)} rule modals (of {len(candidates)} rule rows) ---")
    dumps = []
    for k, (ti, ni, cap) in enumerate(picks):
        print(f"[{k + 1}/{len(picks)}] {cap[:70]!r}")
        node = page.locator(".v-tree").nth(ti).locator(".v-tree-node").nth(ni)
        try:
            await node.locator(".v-tree-node-caption").first.click(timeout=4000)
            await page.wait_for_timeout(400)
            btn = await rule_edit_button(page)
            if not btn:
                print("    no Edit button visible — skipping")
                continue
            await btn.click()
            await page.wait_for_timeout(1400)
            dump = await page.evaluate(FORM_DUMP_JS)
            slug = f"rule{k:02d}"
            (OUT / f"form_{slug}.json").write_text(
                json.dumps({"pickedCaption": cap, "windows": dump},
                           indent=1, ensure_ascii=False))
            try:
                await page.screenshot(path=str(OUT / f"form_{slug}.png"),
                                      timeout=5000)
            except Exception:  # noqa: BLE001
                pass
            for w in dump:
                print(f"    window {w['caption'][:50]!r}  buttons={w['buttons']}"
                      f"  tabs={w['tabs']}")
                for f in w["fields"][:60]:
                    print(f"       - {f['cap'][:44]!r:46} {f['widgets']}"
                          f" checked={f['checked']}  = {f['val'][:70]!r}")
            dumps.append({"caption": cap, "windows": dump})
        except Exception as e:  # noqa: BLE001
            print(f"    ERROR {e!r}")
        finally:
            n_committed = await close_windows(page)
            if n_committed:
                print(f"    (dismiss committed the form {n_committed}x — no-op re-save)")
    return dumps


async def main() -> None:
    async with async_playwright() as pw:
        b = await pw.chromium.connect_over_cdp(CDP)
        ctx = b.contexts[0]
        page = ctx.pages[0]
        print(f"attached: {page.url}")
        cdp = await ctx.new_cdp_session(page)
        wid = (await cdp.send("Browser.getWindowForTarget"))["windowId"]
        orig = {"left": 60, "top": 60, "width": 1400, "height": 1000,
                "windowState": "normal"}
        await cdp.send("Browser.setWindowBounds", {"windowId": wid, "bounds": {
            "left": 0, "top": 0, "width": WIDE, "height": 1600,
            "windowState": "normal"}})
        await page.wait_for_timeout(1200)

        report: dict = {"probedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                        "url": page.url, "sampleLimit": SAMPLE_LIMIT}
        try:
            n_trees = await page.evaluate("document.querySelectorAll('.v-tree').length")
            if not n_trees:
                print("\n!! no .v-tree on screen. Navigate the browser to the "
                      "coaching's Rules tab first (Edit -> Rules), then rerun.")
                report["error"] = "no .v-tree visible"
                (OUT / "rules_probe_report.json").write_text(
                    json.dumps(report, indent=1, ensure_ascii=False))
                return

            print("\n--- phase 1: tree as-is ---")
            await dump_tree(page, "asis")
            print("\n--- phase 2: expand all ---")
            await expand_all(page)
            trees = await dump_tree(page, "expanded")
            report["treeSummary"] = [
                {"treeIndex": t["treeIndex"], "nodeCount": t["nodeCount"],
                 "topCaptions": [n["caption"] for n in t["nodes"] if n["depth"] == 0],
                 "iconSet": sorted({n["icon"].split("/")[-1] for n in t["nodes"]
                                    if n["icon"]})}
                for t in trees]
            print("\n--- phase 3: sample 'Edit rule:' modals ---")
            report["ruleModals"] = await sample_rule_modals(page, trees)
        finally:
            await cdp.send("Browser.setWindowBounds",
                           {"windowId": wid, "bounds": orig})
            (OUT / "rules_probe_report.json").write_text(
                json.dumps(report, indent=1, ensure_ascii=False))
            print(f"\nwrote {OUT / 'rules_probe_report.json'}")
            print("window restored")


if __name__ == "__main__":
    asyncio.run(main())
