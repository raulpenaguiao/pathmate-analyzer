"""Stage-3 discovery probe: the live PMCP editor's **Rules tab** (a `.v-tree`).

The randomisation-group sweep (`export_bundle.py`) walks the Micro Dialogs
`.v-menubar`. Rule-level timing lives somewhere else entirely: the Rules tab,
which is a Vaadin `.v-tree`, and each rule's "Edit rule:" modal. This script
is the discovery pass that precedes the bulk Stage-3 scraper.

What the "Edit rule:" modal holds (mapped from run 1, 2026-09-10):
  Comment · Rule[x] / operator / Comparison term[y] · Store-result-var
  · 4 action checkboxes:
      - Send message if rule result is TRUE
      - Start micro dialog if rule result is TRUE
      - Mark case as solved (unexpected message) and stop the current rule
        execution run if result is TRUE
      - Stop current rule execution run and finish coaching for this
        participant if rule result is TRUE
  · Message group to send messages from
  · Micro dialog to start           (a " > "-joined dialog path)
  · Hour to send message (24h, 0 = immediately)   (a $variable OR a slider)
  · Minutes after sending until message is handled as not answered
        (slider + 1/5/10/30/60 presets; shown as "N days, N hours, N minutes")
  · tabs: Rules if participant DOES answer / DOES NOT answer  (nested .v-tree)

The modal is `v-readonly` (every field is behind an inner "Edit" button), so
opening + Close *should* be harmless. Memory still records a "The rule has
been updated." toast on Close, so treat each open as a no-op re-save anyway:
sandbox coaching "ALEX v01 zum Ausprobieren" only, and write an
`autochanges/` entry per run.

Prereqs: hand-logged-in Chromium on CDP :9222, Monitoring deactivated,
browser already on the coaching's **Rules** tab with the tree visible.

Env:
  PMCP_CDP           CDP endpoint            (default http://127.0.0.1:9222)
  PMCP_OUT           output dir              (default: this file's spike/)
  PMCP_RULE_ICONS    comma list of row-icon stems to open modals for
                     (default "message" -> only message-icon-small.png rows,
                      i.e. the dialog/message senders; "message,rule" for all)
  PMCP_RULE_SAMPLE   cap on modals opened   (default 40)

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
RULE_ICONS = [s.strip() for s in os.environ.get("PMCP_RULE_ICONS", "message").split(",") if s.strip()]
SAMPLE_LIMIT = int(os.environ.get("PMCP_RULE_SAMPLE", "40"))

# ---------------------------------------------------------------------------
# Tree structure dump
# ---------------------------------------------------------------------------

#   Vaadin 7 tree facts confirmed live (2026-09-10):
#   - state is `aria-expanded="true|false"` on the .v-tree-node[role=treeitem];
#     absent means either a leaf OR a parent never yet touched this session.
#   - `.v-tree-node-children` is PRE-RENDERED even while collapsed, so a
#     non-empty child container == "this node has children" regardless of
#     expand state. Collapsed children have a zero-size caption rect.
#   - the gesture that expands: click the caption, then press ArrowRight.
#   - `.v-tree-node` node COUNT never changes on expand — do not use it as a
#     progress signal; use caption visibility.
TREE_DUMP_JS = r"""
() => {
  const trees = [...document.querySelectorAll('.v-tree')];
  const dump = (tree) => {
    const nodes = [...tree.querySelectorAll('.v-tree-node[role=treeitem]')];
    return nodes.map((n, i) => {
      const capEl = n.querySelector(':scope > .v-tree-node-caption');
      const cap = capEl ? capEl.textContent.replace(/\s+/g, ' ').trim() : '';
      const iconEl = capEl ? capEl.querySelector('img.v-icon, .v-icon') : null;
      const icon = (iconEl ? (iconEl.getAttribute('src') || iconEl.className) : '').split('/').pop();
      const kids = n.querySelector(':scope > .v-tree-node-children');
      const r = capEl ? capEl.getBoundingClientRect() : {width: 0, height: 0, top: 0};
      const aria = n.getAttribute('aria-expanded');
      return {
        i,
        depth: parseInt(n.getAttribute('aria-level') || '1', 10) - 1,
        caption: cap, classes: n.className, icon,
        ariaExpanded: aria,                       // 'true' | 'false' | null
        hasChildEls: !!kids && kids.childElementCount > 0,
        visible: r.width > 0 && r.height > 0,
        expanded: aria === 'true',
        leaf: aria === null && !(kids && kids.childElementCount > 0),
        rectTop: Math.round(r.top),
      };
    });
  };
  return trees.map((t, ti) => ({
    treeIndex: ti, classes: t.className,
    nodeCount: t.querySelectorAll('.v-tree-node[role=treeitem]').length,
    nodes: dump(t),
    outerHTMLHead: t.outerHTML.slice(0, 3000),
  }));
}
"""

# ---------------------------------------------------------------------------
# "Edit rule:" modal — targeted extraction keyed on the known label strings
# ---------------------------------------------------------------------------

RULE_MODAL_JS = r"""
() => {
  const w = [...document.querySelectorAll('.v-window')].pop();
  if (!w) return { error: 'no .v-window' };
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();

  // ordered stream of form items in document order
  const ITEM_SEL = '.v-label, .v-checkbox, .v-filterselect, .v-slider, .v-caption, .v-textfield';
  const items = [...w.querySelectorAll(ITEM_SEL)].map(el => {
    const cl = el.className;
    let kind = 'label';
    if (cl.includes('v-checkbox')) kind = 'checkbox';
    else if (cl.includes('v-filterselect')) kind = 'select';
    else if (cl.includes('v-slider')) kind = 'slider';
    else if (cl.includes('v-caption')) kind = 'caption';
    else if (cl.includes('v-textfield') && el.tagName === 'INPUT') kind = 'textfield';
    let value = '';
    if (kind === 'checkbox') {
      const inp = el.querySelector('input[type=checkbox]');
      value = inp ? String(inp.checked) : '';
    } else if (kind === 'select') {
      const inp = el.querySelector('.v-filterselect-input');
      value = inp ? norm(inp.value) : '';
      if (el.className.includes('v-disabled')) value += '  [disabled]';
    } else if (kind === 'slider') {
      const h = el.querySelector('.v-slider-handle');
      value = h ? (h.style.marginLeft || '') : '';
      if (el.className.includes('v-disabled')) value += '  [disabled]';
    } else if (kind === 'textfield') {
      value = norm(el.value);
    }
    const r = el.getBoundingClientRect();
    return { kind, text: norm(el.textContent).slice(0, 160), value,
             top: Math.round(r.top), left: Math.round(r.left) };
  });

  // for a known label, the value = the nearest control on the SAME visual row
  // (closest |top| delta), falling back to next control in document order.
  const CONTROL = new Set(['select', 'slider', 'textfield', 'caption']);
  const valueFor = (labelText) => {
    const li = items.findIndex(it => it.kind === 'label' && it.text.startsWith(labelText));
    if (li < 0) return null;
    const lab = items[li];
    let best = null, bestDy = 1e9;
    items.forEach((it, j) => {
      if (j === li || !CONTROL.has(it.kind)) return;
      const dy = Math.abs(it.top - lab.top);
      if (it.left >= lab.left - 5 && dy < bestDy && dy < 22) { best = it; bestDy = dy; }
    });
    if (!best) for (let j = li + 1; j < items.length; j++)
      if (CONTROL.has(items[j].kind)) { best = items[j]; break; }
    return best ? { via: best.kind, value: best.value, text: best.text } : null;
  };

  const checkboxes = items.filter(it => it.kind === 'checkbox')
    .map(it => ({ label: it.text, checked: it.value }));

  const dumpInnerTrees = () => [...w.querySelectorAll('.v-tree')].map(t => ({
    nodeCount: t.querySelectorAll('.v-tree-node').length,
    nodes: [...t.querySelectorAll('.v-tree-node')].map(n => norm(
      (n.querySelector(':scope > .v-tree-node-caption') || {}).textContent).slice(0, 140))
      .filter(Boolean),
  }));

  const L = {
    comment: 'Comment:',
    ruleX: 'Rule [x]',
    termY: 'Comparison term [y]',
    storeResultVar: 'Store rule result to variable',
    messageGroup: 'Message group to send messages from',
    microDialogToStart: 'Micro dialog to start',
    hourToSendMessage: 'Hour to send message',
    notAnsweredTimeout: 'Minutes after sending until message is handled as not answered',
    innerVarStore: 'Variable to store calculation result of selected rule',
    innerSendMessage: 'Send message after execution of selected rule',
  };
  const out = { fields: {} };
  for (const [k, lbl] of Object.entries(L)) out.fields[k] = valueFor(lbl);

  return {
    caption: norm((w.querySelector('.v-window-header') || {}).textContent),
    windowClasses: w.className,
    buttons: [...w.querySelectorAll('.v-button-caption')].map(e => norm(e.textContent)).filter(Boolean),
    tabs: [...w.querySelectorAll('.v-tabsheet-tabitemcell')].map(e => norm(e.textContent)).filter(Boolean),
    activeTab: norm((w.querySelector('.v-tabsheet-tabitem-selected') || {}).textContent),
    checkboxes,
    fields: out.fields,
    allCaptions: items.filter(it => it.kind === 'caption').map(it => it.text),
    innerTrees: dumpInnerTrees(),
    itemStream: items,
    html: w.outerHTML,
  };
}
"""


async def dump_tree(page, tag: str) -> list[dict]:
    trees = await page.evaluate(TREE_DUMP_JS)
    (OUT / f"rules_tree_{tag}.json").write_text(
        json.dumps(trees, indent=1, ensure_ascii=False))
    for t in trees:
        print(f"  tree[{t['treeIndex']}]  {t['nodeCount']} nodes")
        for n in t["nodes"]:
            mark = "▾" if n["expanded"] else ("·" if n["leaf"] else "▸")
            print(f"    {'  ' * n['depth']}{mark} {n['caption'][:66]!r}"
                  f"  {n['icon'][:22]!r} leaf={n['leaf']} exp={n['expanded']}")
    return trees


async def _aria_of(page, ti: int, i: int) -> str | None:
    trees = await page.evaluate(TREE_DUMP_JS)
    return next((n["ariaExpanded"] for n in trees[ti]["nodes"] if n["i"] == i), None)


async def _select_node(page, ti: int, i: int) -> None:
    """Click a tree node's caption to select it. Click at x=20 (on the icon/
    text), NOT the box centre — a short caption leaves the box's centre in
    dead space past the text, where Vaadin ignores the click (verified live
    2026-09-10: centre click -> aria-selected stays false)."""
    cap = (page.locator(".v-tree").nth(ti)
           .locator(".v-tree-node[role=treeitem]").nth(i)
           .locator(":scope > .v-tree-node-caption"))
    await cap.click(position={"x": 20, "y": 8}, timeout=4000)


async def _click_expander(page, ti: int, i: int) -> bool:
    """Expand the i-th treeitem of tree ti; report whether it is now
    aria-expanded=true. Recipe verified live: select the caption (x=20 click),
    wait ~600ms for the selection round-trip, THEN ArrowRight."""
    for _ in range(2):
        try:
            await _select_node(page, ti, i)
            await page.wait_for_timeout(600)
            await page.keyboard.press("ArrowRight")
            await page.wait_for_timeout(500)
        except Exception as e:  # noqa: BLE001
            print(f"    expand {ti}/{i}: {e!r}")
            return False
        if await _aria_of(page, ti, i) == "true":
            return True
    return False


async def _liveness_ok(page) -> bool:
    """Expand the first visible not-yet-expanded node. Catches an expired PMCP
    session (tree DOM stays put, expand RPCs are silently dropped)."""
    trees = await page.evaluate(TREE_DUMP_JS)
    for n in trees[0]["nodes"]:
        if n["visible"] and n["ariaExpanded"] != "true":
            if await _click_expander(page, 0, n["i"]):
                return True
    return False


async def expand_all(page, max_nodes: int = 400) -> dict:
    """Fully expand tree 0. ONE expansion per iteration, re-dumping every time:
    opening a node can lazy-load new children, which shifts every later index,
    so a batch built from a stale dump would click the wrong rows. Pick the
    next node by (depth, caption) identity, expand it at its CURRENT index,
    repeat. A node that never reaches aria-expanded=true is a leaf."""
    tried: set[tuple] = set()
    leaves = expanded = 0
    for _ in range(max_nodes):
        trees = await page.evaluate(TREE_DUMP_JS)
        nxt = next(((n["i"], (n["depth"], n["caption"]))
                    for n in trees[0]["nodes"]
                    if n["visible"] and n["ariaExpanded"] != "true" and n["caption"]
                    and (n["depth"], n["caption"]) not in tried), None)
        if nxt is None:
            print(f"  settled: {expanded} expanded, {leaves} leaves, "
                  f"{trees[0]['nodeCount']} nodes")
            break
        i, key = nxt
        tried.add(key)
        if await _click_expander(page, 0, i):
            expanded += 1
        else:
            leaves += 1
        if (expanded + leaves) % 15 == 0:
            print(f"  ... {expanded} expanded / {leaves} leaves")
    trees = await page.evaluate(TREE_DUMP_JS)
    empty_roots = [n["caption"] for n in trees[0]["nodes"]
                   if n["depth"] == 0 and n["ariaExpanded"] != "true"]
    if empty_roots:
        print(f"  roots that never expanded (truly empty): {empty_roots}")
    return {"emptyRoots": empty_roots,
            "expandedNodes": sum(1 for n in trees[0]["nodes"]
                                 if n["ariaExpanded"] == "true")}


async def rule_edit_button(page):
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


async def close_windows(page) -> int:
    committed = 0
    for _ in range(6):
        if not await page.locator(".v-window").count():
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
        await page.wait_for_timeout(450)
    return committed


def _parent_chain(nodes: list[dict], idx: int) -> list[str]:
    """Caption chain from the section root down to (not incl.) node idx."""
    chain: list[str] = []
    want = nodes[idx]["depth"] - 1
    for j in range(idx - 1, -1, -1):
        if nodes[j]["depth"] == want:
            chain.insert(0, nodes[j]["caption"])
            want -= 1
            if want < 0:
                break
    return chain


async def sample_rule_modals(page, trees: list[dict]) -> list[dict]:
    nodes = trees[0]["nodes"] if trees else []
    picks = [(0, j, n) for j, n in enumerate(nodes)
             if n["depth"] >= 1 and n["caption"]
             and any(ic in n["icon"] for ic in RULE_ICONS)]
    picks = picks[:SAMPLE_LIMIT]
    print(f"\n--- sampling {len(picks)} '{','.join(RULE_ICONS)}'-icon rule "
          f"modals (of {len(nodes)} tree nodes) ---")
    dumps = []
    for k, (ti, j, n) in enumerate(picks):
        cap = n["caption"]
        chain = _parent_chain(nodes, j)
        print(f"[{k + 1}/{len(picks)}] d{n['depth']} {n['icon']}  {cap[:64]!r}")
        try:
            await _select_node(page, ti, j)
            await page.wait_for_timeout(400)
            btn = await rule_edit_button(page)
            if not btn:
                print("    no Edit button — skipping")
                continue
            await btn.click()
            await page.wait_for_timeout(1300)
            d1 = await page.evaluate(RULE_MODAL_JS)
            # flip to the DOES NOT answer tab and re-dump inner trees
            does_not = None
            tab = page.locator(".v-window .v-tabsheet-tabitemcell",
                               has_text="DOES NOT answer")
            if await tab.count():
                try:
                    await tab.first.click()
                    await page.wait_for_timeout(500)
                    does_not = await page.evaluate(
                        "() => [...document.querySelectorAll('.v-window .v-tree')]"
                        ".map(t => [...t.querySelectorAll('.v-tree-node > "
                        ".v-tree-node-caption')].map(c => c.textContent.trim()))")
                except Exception:  # noqa: BLE001
                    pass
            slug = f"rule{k:02d}"
            (OUT / f"form_{slug}.json").write_text(json.dumps(
                {"pickedCaption": cap, "parentChain": chain, "icon": n["icon"],
                 "doesAnswerTab": d1, "doesNotAnswerInnerTrees": does_not},
                indent=1, ensure_ascii=False))
            try:
                await page.screenshot(path=str(OUT / f"form_{slug}.png"),
                                      timeout=5000)
            except Exception:  # noqa: BLE001
                pass
            cbs = {c["label"][:34]: c["checked"] for c in d1.get("checkboxes", [])}
            print(f"    win={d1.get('windowClasses', '')[:40]!r} tabs={d1.get('tabs')}")
            print(f"    checkboxes: {cbs}")
            for fk, fv in (d1.get("fields") or {}).items():
                if fv and fv.get("value") not in ("", None):
                    print(f"      {fk:20} = {fv.get('value')!r:40}  (via {fv.get('via')})")
            print(f"    captions: {d1.get('allCaptions')}")
            print(f"    innerTrees: {[t['nodes'] for t in d1.get('innerTrees', [])]}")
            dumps.append({"caption": cap, "parentChain": chain,
                          "icon": n["icon"], "fields": d1.get("fields"),
                          "checkboxes": d1.get("checkboxes"),
                          "captions": d1.get("allCaptions"),
                          "innerTrees": d1.get("innerTrees"),
                          "doesNotAnswerInnerTrees": does_not})
        except Exception as e:  # noqa: BLE001
            print(f"    ERROR {e!r}")
        finally:
            nc = await close_windows(page)
            if nc:
                print(f"    (dismiss committed {nc}x — no-op re-save)")
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
                        "url": page.url, "ruleIcons": RULE_ICONS,
                        "sampleLimit": SAMPLE_LIMIT}
        try:
            if not await page.evaluate("document.querySelectorAll('.v-tree').length"):
                print("\n!! no .v-tree on screen. Navigate to the coaching's "
                      "Rules tab (Edit -> Rules) first, then rerun.")
                report["error"] = "no .v-tree visible"
                return

            print("\n--- phase 1: tree as-is ---")
            await dump_tree(page, "asis")

            print("\n--- liveness check ---")
            if not await _liveness_ok(page):
                print("!! No tree node expanded on a live click. The PMCP "
                      "session has almost certainly expired (the tree DOM "
                      "stays on screen but the server drops expand calls).\n"
                      "   Fix: in the browser, reload -> log in again -> "
                      "Coachings -> ALEX v01 -> Edit -> Monitoring off -> "
                      "Rules tab, confirm you can expand a section by hand, "
                      "then rerun. No modals were opened.")
                report["error"] = "session likely expired (no expand response)"
                return
            print("  ok - tree responds to expand")

            print("\n--- phase 2: expand all ---")
            report["expand"] = await expand_all(page)
            trees = await dump_tree(page, "expanded")
            report["treeSummary"] = [
                {"treeIndex": t["treeIndex"], "nodeCount": t["nodeCount"],
                 "topCaptions": [n["caption"] for n in t["nodes"] if n["depth"] == 0],
                 "iconCounts": _icon_counts(t["nodes"])}
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


def _icon_counts(nodes: list[dict]) -> dict[str, int]:
    c: dict[str, int] = {}
    for n in nodes:
        c[n["icon"]] = c.get(n["icon"], 0) + 1
    return c


if __name__ == "__main__":
    asyncio.run(main())
