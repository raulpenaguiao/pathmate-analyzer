"""Export a PMCP coaching's **rule tree** (with per-rule timing & routing) to
JSON, and splice it into `coaching.bundle`.

`export_bundle.py` sweeps the Micro Dialogs `.v-menubar` -> node content +
randomisation groups. This does the other half: the **Rules** tab `.v-tree`
-> every rule in order, plus, for each message/dialog-sending rule, the
fields from its "Edit rule:" modal (action, target micro dialog / message
group, send-hour variable, not-answered timeout, DOES / DOES-NOT-answer
subtrees).

  export_rules.py                 -> coaching.rules.json
  export_rules.py --merge         -> also coaching.bundle.v3.json
                                     (v2 bundle + a "rules" key)

WRITES to the live coaching: opening an "Edit rule:" modal and closing it
fires "The rule has been updated." with zero fields touched (the modal is
read-only; the dismiss button commits anyway). So this is ~25 no-op
re-saves. **Sandbox coaching "ALEX v01 zum Ausprobieren" only**, and add an
`autochanges/` entry. `--no-modals` skips phase 3 (tree skeleton only, zero
writes).

Prereqs: a hand-logged-in Chromium on CDP :9222, and the browser on the
coaching's **Rules** tab (the script will click the in-app "Rules" tab if
the view has drifted, but you must be inside Edit for that coaching).

Env: PMCP_CDP (default http://127.0.0.1:9222), PMCP_OUT (default cwd).
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

from playwright.async_api import async_playwright

import _rules_nav as R

OUT = Path(os.environ.get("PMCP_OUT", Path.cwd()))
OUT.mkdir(parents=True, exist_ok=True)
CDP = os.environ.get("PMCP_CDP", "http://127.0.0.1:9222")
RULES_JSON = OUT / "coaching.rules.json"

SENDER_ICON = "message-icon-small.png"
CONDITION_ICON = "rule-icon-small.png"


def build_rule_tree(nodes: list[dict]) -> list[dict]:
    """Flat, ordered rule list with stable uids and parent links. Section
    roots (depth 0) become the `section` of everything under them."""
    out: list[dict] = []
    # uid of the last node seen at each depth, to resolve parents
    last_at_depth: dict[int, str] = {}
    section = None
    counter = 0
    for n in nodes:
        d = n["depth"]
        if d == 0:
            section = R.SECTION_ICON.get(n["icon"], n["caption"])
            last_at_depth = {0: None}
            continue
        uid = f"r-{counter:03d}"
        counter += 1
        kind = ("sender" if SENDER_ICON in n["icon"]
                else "condition" if CONDITION_ICON in n["icon"]
                else "other")
        out.append({
            "uid": uid,
            "section": section,
            "depth": d,
            "order": counter,
            "parentUid": last_at_depth.get(d - 1),
            "kind": kind,
            "icon": n["icon"],
            "caption": n["caption"],
            "treeIndex": n["i"],
        })
        last_at_depth[d] = uid
        # a deeper level starting fresh under this node
        for deeper in list(last_at_depth):
            if deeper > d:
                del last_at_depth[deeper]
    return out


async def main() -> None:
    merge = "--merge" in sys.argv
    no_modals = "--no-modals" in sys.argv

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
            "left": 0, "top": 0, "width": 2400, "height": 1600,
            "windowState": "normal"}})
        await page.wait_for_timeout(1000)

        result: dict = {
            "coaching": {"scrapedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                         "url": page.url, "stage": 3},
            "source": "export_rules.py — live PMCP Rules .v-tree + Edit-rule modals",
        }
        try:
            if not await R.ensure_rules_tree(page):
                sys.exit("no .v-tree on screen — open the coaching's Rules tab "
                         "(Edit -> Rules) and rerun.")

            print("--- expand tree ---")
            if not await R.liveness_ok(page):
                sys.exit("tree did not respond to an expand click — the PMCP "
                         "session has likely expired. Re-login, reopen the "
                         "Rules tab, rerun. Nothing was written.")
            exp = await R.expand_all(page)
            print(f"  {exp['expandedNodes']} expanded, {exp['leafNodes']} leaves, "
                  f"{exp['nodeCount']} nodes; empty sections: {exp['emptyRoots']}")
            result["expand"] = exp

            trees = await R.dump_tree(page)
            nodes = trees[0]["nodes"]
            (OUT / "rules_tree_full.json").write_text(
                json.dumps(trees, indent=1, ensure_ascii=False))
            rule_tree = build_rule_tree(nodes)
            result["sections"] = sorted({r["section"] for r in rule_tree})
            result["ruleTree"] = rule_tree
            senders = [r for r in rule_tree if r["kind"] == "sender"]
            print(f"  rule tree: {len(rule_tree)} rules "
                  f"({len(senders)} senders, "
                  f"{sum(1 for r in rule_tree if r['kind']=='condition')} conditions)")

            if no_modals:
                print("--no-modals: skipping the Edit-rule sweep")
                result["sendingRules"] = None
            else:
                print(f"--- reading {len(senders)} sender modals "
                      f"(~{len(senders)} no-op re-saves) ---")
                committed = 0
                sending_rules = []
                for k, r in enumerate(senders):
                    print(f"[{k + 1}/{len(senders)}] {r['caption'][:66]!r}")
                    await R.close_windows(page)
                    dump = await R.open_rule_modal(page, 0, r["treeIndex"])
                    if not dump:
                        print("    FAILED to open — skipping")
                        continue
                    parsed = R.parse_rule_fields(dump)
                    parsed["uid"] = r["uid"]
                    parsed["caption"] = r["caption"]
                    parsed["section"] = r["section"]
                    parsed["parentChain"] = R.parent_chain(nodes, r["treeIndex"])
                    sending_rules.append(parsed)
                    (OUT / f"rules_modal_{r['uid']}.json").write_text(
                        json.dumps({"rule": r, "modal": dump}, indent=1,
                                   ensure_ascii=False))
                    print(f"    {parsed['primaryAction']}"
                          f" -> {parsed['microDialogToStart'] or parsed['messageGroup']}"
                          f"  hour={parsed['sendHourVariable']}"
                          f"  timeout={parsed['notAnsweredTimeoutMinutes']}min")
                    committed += await R.close_windows(page)
                result["sendingRules"] = sending_rules
                result["noOpReSaves"] = committed
                print(f"  {len(sending_rules)}/{len(senders)} captured; "
                      f"{committed} no-op re-saves committed")

            RULES_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False))
            print(f"\nwrote {RULES_JSON}")

            if merge:
                merged = _merge_into_bundle(result)
                if merged:
                    print(f"wrote {merged}")
        finally:
            await cdp.send("Browser.setWindowBounds", {"windowId": wid, "bounds": orig})
            print("window restored")


def _merge_into_bundle(rules: dict) -> Path | None:
    src = OUT / "coaching.bundle.v2.json"
    if not src.is_file():
        src = OUT / "coaching.bundle.json"
    if not src.is_file():
        print("(no coaching.bundle.v2.json / .json in PMCP_OUT — skipping --merge)")
        return None
    bundle = json.loads(src.read_text())
    bundle["rules"] = {
        "sections": rules.get("sections"),
        "ruleTree": rules.get("ruleTree"),
        "sendingRules": rules.get("sendingRules"),
        "scrapedAt": rules["coaching"]["scrapedAt"],
    }
    bundle.get("coaching", {})["stage"] = 3
    dst = OUT / "coaching.bundle.v3.json"
    dst.write_text(json.dumps(bundle, indent=2, ensure_ascii=False))
    return dst


if __name__ == "__main__":
    asyncio.run(main())
