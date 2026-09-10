"""Export ONE PMCP coaching to ONE JSON, in a single run.

Drives the already-logged-in Chromium (see ../start_pmcp.sh) over CDP:

  phase 1  Micro Dialogs .v-menubar  -> every node, in order, with the
           randomisation group (`_menu_nav.sweep_table`)
  phase 2  join the Report-HTML export for full per-language text + decision
           branches                  (`--report FILE`, `enrich_bundle`)
  phase 3  Rules .v-tree + each sending rule's "Edit rule:" modal -> the rule
           tree and per-rule timing/routing (`_rules_nav`)
  phase 4  coherence check: does the DOM sweep still agree with the HTML
           export and the committed baseline? A canary for PMCP UI changes
           that would otherwise silently break the export.

Output: the single file you name. No coaching.bundle.json / .v2 / .v3 /
coaching.rules.json — those are gone.

  export_coaching.py OUT.json [--report REPORT.html] [--dialogs-only]
                     [--rules-only] [--no-modals] [--update-baseline]

phase 3 opens ~25 "Edit rule:" modals; each dismiss commits a no-op re-save.
Sandbox coachings only; add an autochanges/ entry.

Env: PMCP_CDP (default http://127.0.0.1:9222), PMCP_WIDE (default 12000).
Exits non-zero if the coherence check fails (so it can gate a workflow).
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

from playwright.async_api import async_playwright

import _menu_nav as M
import _rules_nav as R
import enrich_bundle

HERE = Path(__file__).resolve().parent
CDP = os.environ.get("PMCP_CDP", "http://127.0.0.1:9222")
WIDE = int(os.environ.get("PMCP_WIDE", "12000"))
BASELINE = HERE / "coherence_baseline.json"

_TYPE = {"Message": "message", "DECISION POINT": "decision",
         "Command Message": "command", "EVENT": "event"}


# ---------------------------------------------------------------------------
# phase 1 — micro dialogs
# ---------------------------------------------------------------------------

async def sweep_micro_dialogs(page) -> tuple[list[dict], list[dict]]:
    if not await M.ensure_micro_dialogs(page):
        sys.exit("Micro Dialogs menu not on screen — open the coaching's Edit "
                 "view, deactivate Monitoring, then rerun.")
    targets = await M.all_targets(page)
    print(f"  {len(targets)} menu targets "
          f"({sum(t['isFolder'] for t in targets)} folders)")
    micro_dialogs, nodes = [], []
    for seq, t in enumerate(targets):
        name = " / ".join(t["labels"])
        md_uid = f"md-{seq:03d}"
        try:
            await M.navigate_and_select(page, t["labels"])
            await M.wait_round_trip(page)
            total, seen, missing = await M.sweep_table(page)
        except Exception as e:  # noqa: BLE001
            print(f"  [{seq}] {name}  ERROR {e!r}")
            micro_dialogs.append({"uid": md_uid, "name": t["labels"][-1],
                                  "folderPath": t["labels"][:-1],
                                  "isFolder": t["isFolder"], "error": repr(e)})
            continue
        node_uids = []
        for i in range(total):
            cells = seen.get(i, [""] * len(M.COLS))
            row = {M.COLS[j]: (cells[j] if j < len(cells) else "")
                   for j in range(len(M.COLS))}
            nuid = f"{md_uid}#{i:03d}"
            node_uids.append(nuid)
            nodes.append({
                "uid": nuid, "microDialogUid": md_uid, "order": i,
                "type": _TYPE.get(row["Type"], row["Type"].lower() or "message"),
                "rawType": row["Type"], "comment": row["Comment"],
                "gridText": row["Message Text / Events"], "channel": row["Channel"],
                "answerType": row["Answer Type"],
                "resultVariable": row["Result Variable"],
                "randomisationGroup": row["Randomisation Group"],
                "flags": {"commandMessage": row["Command Message"],
                          "containsMedia": row["Contains Media Content"],
                          "containsSurvey": row["Contains Link To Survey"],
                          "containsRules": row["Contains Rules"]},
            })
        micro_dialogs.append({
            "uid": md_uid, "name": t["labels"][-1], "folderPath": t["labels"][:-1],
            "isFolder": t["isFolder"], "nodeCount": total, "nodeUids": node_uids,
            "missingRows": missing,
        })
        if seq % 20 == 0 or missing:
            print(f"  [{seq}/{len(targets)}] {name}  nodes={total}"
                  f"{'  MISSING ' + str(missing[:4]) if missing else ''}")
    return micro_dialogs, nodes


# ---------------------------------------------------------------------------
# phase 3 — rules
# ---------------------------------------------------------------------------

async def sweep_rules(page, open_modals: bool) -> dict:
    if not await R.ensure_rules_tree(page):
        sys.exit("Rules tab not on screen — open the coaching's Edit view and "
                 "rerun.")
    if not await R.liveness_ok(page):
        sys.exit("tree did not respond to an expand click — the PMCP session "
                 "has likely expired. Re-login (../start_pmcp.sh) and rerun.")
    exp = await R.expand_all(page)
    print(f"  {exp['expandedNodes']} expanded, {exp['leafNodes']} leaves, "
          f"{exp['nodeCount']} nodes; empty sections: {exp['emptyRoots']}")
    trees = await R.dump_tree(page)
    tree_nodes = trees[0]["nodes"]
    rule_tree = R.build_rule_tree(tree_nodes)
    senders = [r for r in rule_tree if r["kind"] == "sender"]
    print(f"  rule tree: {len(rule_tree)} rules ({len(senders)} senders)")

    sending_rules = None
    if open_modals:
        sending_rules, committed = [], 0
        print(f"  reading {len(senders)} sender modals "
              f"(~{len(senders)} no-op re-saves)...")
        for k, r in enumerate(senders):
            await R.close_windows(page)
            dump = await R.open_rule_modal(page, 0, r["treeIndex"])
            if not dump:
                print(f"  [{k + 1}/{len(senders)}] {r['caption'][:50]!r} FAILED")
                continue
            parsed = R.parse_rule_fields(dump)
            parsed["uid"] = r["uid"]
            parsed["caption"] = r["caption"]
            parsed["section"] = r["section"]
            parsed["parentChain"] = R.parent_chain(tree_nodes, r["treeIndex"])
            sending_rules.append(parsed)
            committed += await R.close_windows(page)
        print(f"  {len(sending_rules)}/{len(senders)} sender rules captured; "
              f"{committed} no-op re-saves")
    return {"sections": sorted({r["section"] for r in rule_tree}),
            "ruleTree": rule_tree, "sendingRules": sending_rules}


# ---------------------------------------------------------------------------
# phase 4 — coherence check
# ---------------------------------------------------------------------------

def _metrics(bundle: dict) -> dict:
    nodes = bundle["nodes"]
    rg = {n["randomisationGroup"] for n in nodes if n.get("randomisationGroup")}
    rules = bundle.get("rules") or {}
    rt = rules.get("ruleTree") or []
    sr = rules.get("sendingRules")
    return {
        "microDialogs": sum(1 for m in bundle["microDialogs"] if not m.get("isFolder")),
        "nodesTotal": len(nodes),
        "messageNodes": sum(1 for n in nodes if n["type"] == "message"),
        "decisionNodes": sum(1 for n in nodes if n["type"] == "decision"),
        "randomisationGroups": len(rg),
        "ruleTreeNodes": len(rt),
        "sendingRules": len(sr) if sr is not None else None,
    }


def coherence_check(bundle: dict, report_html: str | None) -> dict:
    cur = _metrics(bundle)
    warnings: list[str] = []
    ok = True

    html_vs_sweep = None
    if report_html:
        rc = enrich_bundle.report_dialog_counts(Path(report_html))
        by_name = {}
        for m in bundle["microDialogs"]:
            if not m.get("isFolder"):
                by_name.setdefault(m["name"], m)
        deltas = {}
        for name, md in by_name.items():
            exp = rc.get(name)
            if exp is not None and exp != md.get("nodeCount"):
                deltas[" / ".join(md["folderPath"] + [name])] = [md.get("nodeCount"), exp]
        html_vs_sweep = {
            "microDialogsReport": len(rc),
            "microDialogsSweep": cur["microDialogs"],
            "perDialogDeltas": deltas,
        }
        # a broken sweep gives near-zero dialogs
        if cur["microDialogs"] < 0.5 * len(rc):
            ok = False
            warnings.append(f"sweep found only {cur['microDialogs']} dialogs vs "
                            f"{len(rc)} in the Report HTML — navigation likely broke")

    vs_baseline = None
    if BASELINE.is_file():
        base = json.loads(BASELINE.read_text())
        bm = base.get("metrics", {})
        accepted = base.get("acceptedPerDialogDeltas", {})
        changed = {}
        for k, bv in bm.items():
            cv = cur.get(k)
            if bv in (None, 0) or cv is None:
                continue
            drop = (bv - cv) / bv
            if abs(drop) > 1e-9:
                changed[k] = {"baseline": bv, "now": cv}
            if drop > 0.20:  # lost >20% — the sweep collapsed / UI changed
                ok = False
                warnings.append(f"{k}: {cv} now vs baseline {bv} (down "
                                f"{drop * 100:.0f}%)")
            elif abs(drop) > 1e-9:
                warnings.append(f"{k}: {cv} vs baseline {bv} (drift)")
        vs_baseline = {"metricsNow": cur, "metricsBaseline": bm, "changed": changed}
        # per-dialog deltas that aren't on the accepted list
        if html_vs_sweep:
            new_deltas = {k: v for k, v in html_vs_sweep["perDialogDeltas"].items()
                          if accepted.get(k) != v}
            html_vs_sweep["newDeltas"] = new_deltas
            if new_deltas:
                warnings.append(f"{len(new_deltas)} per-dialog node-count "
                                f"delta(s) not on the accepted baseline list")
    else:
        warnings.append("no coherence_baseline.json — run with "
                        "--update-baseline once against a known-good export")

    return {"ok": ok, "metrics": cur, "htmlVsSweep": html_vs_sweep,
            "vsBaseline": vs_baseline, "warnings": warnings}


def write_baseline(bundle: dict, report_html: str | None) -> None:
    base = {"coaching": bundle["coaching"].get("name"),
            "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "metrics": _metrics(bundle),
            "acceptedPerDialogDeltas": {}}
    if report_html:
        rc = enrich_bundle.report_dialog_counts(Path(report_html))
        for m in bundle["microDialogs"]:
            if m.get("isFolder"):
                continue
            exp = rc.get(m["name"])
            if exp is not None and exp != m.get("nodeCount"):
                base["acceptedPerDialogDeltas"][
                    " / ".join(m["folderPath"] + [m["name"]])] = [m.get("nodeCount"), exp]
    BASELINE.write_text(json.dumps(base, indent=2, ensure_ascii=False))
    print(f"wrote baseline -> {BASELINE}")


# ---------------------------------------------------------------------------

async def main() -> int:
    args = sys.argv[1:]
    flags = {a for a in args if a.startswith("--")}
    report = None
    if "--report" in args:
        report = args[args.index("--report") + 1]
        if not Path(report).is_file():
            sys.exit(f"--report file not found: {report}")
    pos = [a for a in args if not a.startswith("--")
           and a != report]
    if not pos:
        sys.exit("usage: export_coaching.py OUT.json [--report R.html] "
                 "[--dialogs-only] [--rules-only] [--no-modals] [--update-baseline]")
    out_path = Path(pos[0])
    if out_path.suffix != ".json":
        out_path = out_path.with_suffix(".json")
    do_dialogs = "--rules-only" not in flags
    do_rules = "--dialogs-only" not in flags

    async with async_playwright() as pw:
        b = await pw.chromium.connect_over_cdp(CDP)
        ctx = b.contexts[0]
        page = next((p for p in ctx.pages if "pathmate" in (p.url or "")),
                    ctx.pages[0])
        logged_in = await page.evaluate(
            "(()=>{if(document.querySelector('input[type=password]'))return false;"
            "const t=document.body?document.body.innerText:'';"
            "return /Coachings/.test(t)&&/Logout/.test(t);})()")
        if not logged_in:
            sys.exit("not logged in to PMCP — run ../start_pmcp.sh first.")
        cdp = await ctx.new_cdp_session(page)
        wid = (await cdp.send("Browser.getWindowForTarget"))["windowId"]
        orig = {"left": 60, "top": 60, "width": 1400, "height": 1000,
                "windowState": "normal"}

        bundle: dict = {"coaching": {
            "name": None, "languages": ["en-GB", "ro-RO"],
            "scrapedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z")}}
        try:
            if do_dialogs:
                print("--- phase 1: micro dialogs ---")
                await cdp.send("Browser.setWindowBounds", {"windowId": wid, "bounds": {
                    "left": 0, "top": 0, "width": WIDE, "height": 1400,
                    "windowState": "normal"}})
                await page.wait_for_timeout(1500)
                md, nodes = await sweep_micro_dialogs(page)
                bundle["microDialogs"] = md
                bundle["nodes"] = nodes
            else:
                bundle["microDialogs"], bundle["nodes"] = [], []

            if report and do_dialogs:
                print("--- phase 2: enrich from Report HTML ---")
                enrich_bundle.enrich_dict(bundle, Path(report))

            if do_rules:
                print("--- phase 3: rules ---")
                await cdp.send("Browser.setWindowBounds", {"windowId": wid, "bounds": {
                    "left": 0, "top": 0, "width": 2400, "height": 1600,
                    "windowState": "normal"}})
                await page.wait_for_timeout(800)
                bundle["rules"] = await sweep_rules(
                    page, open_modals="--no-modals" not in flags)
        finally:
            await cdp.send("Browser.setWindowBounds", {"windowId": wid, "bounds": orig})

    if "--update-baseline" in flags:
        write_baseline(bundle, report)
    print("--- phase 4: coherence check ---")
    bundle["validation"] = coherence_check(bundle, report if do_dialogs else None)
    for w in bundle["validation"]["warnings"]:
        print(f"  ! {w}")
    print(f"  ok = {bundle['validation']['ok']}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(bundle, indent=2, ensure_ascii=False))
    m = bundle["validation"]["metrics"]
    print(f"\nwrote {out_path}")
    print(f"  microDialogs={m['microDialogs']}  nodes={m['nodesTotal']}  "
          f"r_groups={m['randomisationGroups']}  "
          f"ruleTree={m['ruleTreeNodes']}  senders={m['sendingRules']}")
    return 0 if bundle["validation"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
