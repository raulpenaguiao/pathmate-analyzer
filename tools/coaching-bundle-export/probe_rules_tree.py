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

# The tree JS, the Vaadin-tree nav recipe, the "Edit rule:" modal JS and the
# field parser all live in _rules_nav.py (shared with export_rules.py) so
# there is one source of truth. This file is the discovery wrapper around it.
import _rules_nav as R
from _rules_nav import (  # noqa: F401
    TREE_DUMP_JS, RULE_MODAL_JS, expand_all, rule_edit_button, close_windows,
    parent_chain as _parent_chain,
)

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("PMCP_OUT", HERE / "spike"))
OUT.mkdir(parents=True, exist_ok=True)
CDP = os.environ.get("PMCP_CDP", "http://127.0.0.1:9222")
WIDE = int(os.environ.get("PMCP_WIDE", "3000"))
RULE_ICONS = [s.strip() for s in os.environ.get("PMCP_RULE_ICONS", "message").split(",") if s.strip()]
SAMPLE_LIMIT = int(os.environ.get("PMCP_RULE_SAMPLE", "40"))

_select_node = R.select_node
_click_expander = R.click_expander
_liveness_ok = R.liveness_ok


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
            # make sure no stale modal is still up before we start
            await close_windows(page)
            await page.wait_for_selector(".v-window", state="detached", timeout=3000)
        except Exception:  # noqa: BLE001
            pass
        d1 = {}
        try:
            for attempt in range(2):
                await _select_node(page, ti, j)
                await page.wait_for_timeout(450)
                btn = await rule_edit_button(page)
                if not btn:
                    print("    no Edit button — retrying select")
                    await page.wait_for_timeout(500)
                    continue
                await btn.click()
                try:
                    await page.wait_for_selector(".v-window .v-window-header",
                                                 timeout=6000)
                except Exception:  # noqa: BLE001
                    pass
                await page.wait_for_timeout(900)
                d1 = await page.evaluate(RULE_MODAL_JS)
                if d1.get("caption"):
                    break
                print(f"    modal didn't open (attempt {attempt + 1}) — closing, retrying")
                await close_windows(page)
                await page.wait_for_timeout(600)
            if not d1.get("caption"):
                print("    FAILED to open modal after retries")
                continue
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
            cbs = {c["label"].split(" if ")[0]: c["checked"]
                   for c in d1.get("checkboxes", [])}
            action = next((lbl for lbl, v in cbs.items() if v == "true"), "(none)")
            print(f"    action: {action}")
            print(f"    sendHour={d1.get('sendHourClock')!r}  "
                  f"timeout={d1.get('notAnsweredText')!r}")
            for fk in ("microDialogToStart", "messageGroup", "hourToSendMessage",
                       "storeResultVar"):
                fv = (d1.get("fields") or {}).get(fk)
                if fv and fv.get("value"):
                    print(f"      {fk:18} = {fv['value']!r}")
            print(f"    DOES-answer inner: {[t['nodes'] for t in d1.get('innerTrees', [])]}")
            print(f"    DOES-NOT-answer  : {does_not}")
            dumps.append({"caption": cap, "parentChain": chain,
                          "icon": n["icon"], "action": action,
                          "checkboxes": cbs,
                          "sendHourClock": d1.get("sendHourClock"),
                          "notAnsweredText": d1.get("notAnsweredText"),
                          "fields": d1.get("fields"),
                          "captions": d1.get("allCaptions"),
                          "doesAnswerInnerTrees": d1.get("innerTrees"),
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
