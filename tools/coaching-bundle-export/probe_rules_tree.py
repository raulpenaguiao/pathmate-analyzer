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

TREE_DUMP_JS = r"""
() => {
  const trees = [...document.querySelectorAll('.v-tree')];
  const dump = (tree) => {
    const nodes = [...tree.querySelectorAll('.v-tree-node')];
    return nodes.map((n, i) => {
      let depth = 0, p = n.parentElement;
      while (p && p !== tree) {
        if (p.classList.contains('v-tree-node-children')) depth++;
        p = p.parentElement;
      }
      const capEl = n.querySelector(':scope > .v-tree-node-caption');
      const cap = capEl ? capEl.textContent.replace(/\s+/g, ' ').trim() : '';
      const iconEl = capEl ? capEl.querySelector('img.v-icon, .v-icon') : null;
      const icon = iconEl ? (iconEl.getAttribute('src') || iconEl.className) : '';
      const kids = n.querySelector(':scope > .v-tree-node-children');
      return {
        i, depth, caption: cap, classes: n.className,
        icon: icon.split('/').pop(),
        leaf: n.classList.contains('v-tree-node-leaf'),
        expanded: n.classList.contains('v-tree-node-expanded'),
        childDivEmpty: !kids || kids.childElementCount === 0,
        rectTop: capEl ? Math.round(capEl.getBoundingClientRect().top) : null,
      };
    });
  };
  return trees.map((t, ti) => ({
    treeIndex: ti, classes: t.className,
    nodeCount: t.querySelectorAll('.v-tree-node').length,
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


async def _node_cap(page, ti: int, caption: str):
    return (page.locator(".v-tree").nth(ti)
            .locator(".v-tree-node", has_text=caption).first
            .locator(".v-tree-node-caption").first)


async def _click_expander(page, ti: int, caption: str) -> None:
    """Expand a node: select it (caption click) then ArrowRight — the method
    that worked in run 1. Fall back to a left-edge click on the node itself
    (the Vaadin +/- triangle) and a double-click."""
    cap = await _node_cap(page, ti, caption)
    try:
        await cap.click(timeout=3000)
        await page.wait_for_timeout(120)
        await page.keyboard.press("ArrowRight")
        await page.wait_for_timeout(200)
        await page.keyboard.press("ArrowRight")   # 1st can just select
        await page.wait_for_timeout(200)
        return
    except Exception:  # noqa: BLE001
        pass
    for attempt in (
        lambda: cap.click(position={"x": 4, "y": 8}, timeout=3000),
        lambda: cap.dblclick(timeout=3000),
    ):
        try:
            await attempt()
            await page.wait_for_timeout(200)
            return
        except Exception:  # noqa: BLE001
            continue
    print(f"    expand {caption[:40]!r}: all methods failed")


async def _liveness_ok(page) -> bool:
    """Try to expand the first non-leaf root; return True if the tree grew.
    A dead (expired) PMCP session leaves the tree DOM on screen but silently
    drops every expand RPC — this catches that before any modal is opened."""
    trees = await page.evaluate(TREE_DUMP_JS)
    roots = [n["caption"] for n in trees[0]["nodes"]
             if n["depth"] == 0 and not n["leaf"] and not n["expanded"]]
    before = sum(t["nodeCount"] for t in trees)
    for cap in roots:
        await _click_expander(page, 0, cap)
        after = await page.evaluate(
            "[...document.querySelectorAll('.v-tree .v-tree-node')].length")
        if after > before:
            return True
    return False


async def expand_all(page, rounds: int = 25) -> dict:
    """Expand every collapsible node. Terminates when a full round adds no
    nodes. Nodes that resist 2 attempts are reported as `stuckRoots`
    (probably empty)."""
    tried: dict[str, int] = {}
    prev_total = -1
    for r in range(rounds):
        trees = await page.evaluate(TREE_DUMP_JS)
        total = sum(t["nodeCount"] for t in trees)
        collapsed = [(ti, n["caption"]) for ti, t in enumerate(trees)
                     for n in t["nodes"]
                     if not n["leaf"] and not n["expanded"] and n["caption"]
                     and tried.get(n["caption"], 0) < 2]
        if not collapsed:
            print(f"  settled after {r} round(s), {total} nodes")
            break
        if total == prev_total and r > 0:
            # a round changed nothing structurally — bump every remaining try
            for _, cap in collapsed:
                tried[cap] = tried.get(cap, 0) + 1
        prev_total = total
        print(f"  round {r}: {total} nodes, {len(collapsed)} still collapsed")
        for ti, cap in collapsed:
            tried[cap] = tried.get(cap, 0) + 1
            await _click_expander(page, ti, cap)
    trees = await page.evaluate(TREE_DUMP_JS)
    stuck = [n["caption"] for t in trees for n in t["nodes"]
             if not n["leaf"] and not n["expanded"] and n["caption"]]
    if stuck:
        print(f"  stuck (likely empty sections): {stuck}")
    return {"stuckRoots": stuck}


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
        node = page.locator(".v-tree").nth(ti).locator(
            ".v-tree-node", has_text=cap).first
        try:
            await node.locator(".v-tree-node-caption").first.click(timeout=4000)
            await page.wait_for_timeout(350)
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
