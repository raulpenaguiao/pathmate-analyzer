"""Export ONE PMCP coaching to ONE JSON, in a single run.

Drives the already-logged-in Chromium (see ../start_pmcp.sh) over CDP:

  phase 0  fetch the Report HTML automatically from the Coachings list —
           no manual save needed (`_report_fetch.fetch_report_html`).
           Skipped if `--report FILE` is given, or with `--no-report`.
  phase 1  Micro Dialogs .v-menubar  -> every node, in order, with the
           randomisation group (`_menu_nav.sweep_table`)
  phase 2  Variables tab -> every defined variable's name/value/settings,
           independent of whether it's referenced anywhere yet
           (`_variables_nav.sweep_variables`)
  phase 3  join the Report-HTML export for full per-language text + decision
           branches                  (phase 0's fetch, or `--report FILE`;
           `enrich_bundle`)
  phase 4  Rules .v-tree + each sending rule's "Edit rule:" modal -> the rule
           tree and per-rule timing/routing (`_rules_nav`)
  phase 5  coherence check: does the DOM sweep still agree with the HTML
           export and the committed baseline? A canary for PMCP UI changes
           that would otherwise silently break the export.

Output: the single file you name, or (default)
data/exports/coaching_<slug>_<YYYYMMDD-HHMMSS>.json, plus (phase 0)
data/exports/Report_<slug>_<YYYYMMDD-HHMMSS>.html alongside it. No
coaching.bundle.json / .v2 / .v3 / coaching.rules.json — those are gone.
Prints total run time.

  export_coaching.py [OUT.json] [--report REPORT.html] [--no-report]
                     [--dialogs-only] [--rules-only] [--no-modals]
                     [--no-variables] [--update-baseline] [--resolve-jumps]
                     [--allow-noop-resaves]  (alex-live only: a human accepts
                      the editors' no-op re-saves for a full export)

Phase 0 clicks "Report" on the Coachings list, which is a native Chrome
FILE DOWNLOAD, not a page navigation or popup — confirmed live 2026-09-14,
see _report_fetch.py's docstring for why that isn't detectable the normal
Playwright way. A fetch failure degrades gracefully (the rest of the
export proceeds without the coherence check's HTML cross-reference), same
as when `--report` is simply omitted.

phase 2's Variables-tab sweep takes ~2 minutes on its own (334 rows on ALEX
v01, virtualized + server-paginated table, incremental-scroll sweep
required — see _variables_nav.py for why a plain jump-to-bottom sweep
silently undercounts by ~75%). --dialogs-only / --rules-only each already
imply skipping it; --no-variables skips it on an otherwise-full run.

phase 4 opens ~25 "Edit rule:" modals; each dismiss commits a no-op re-save.
Sandbox coachings only; add an autochanges/ entry.

IDs ARE NOT STABLE NAMES. `md-NNN` / `md-NNN#MMM` uids are positions in
this run's menu sweep and row order. They are valid only inside one export
file. A dialog added or moved in PMCP renumbers everything after it (e.g.
md-049 was v01 "second dose" on 09-14 and v02 "first dose" on 09-17). Use
them to cross-reference within a file (jump targets, nodeUids, ...), never to
name a dialog or node across exports, in docs, tests or saved state. Across
exports, use `path` (the dialog's full menu path) plus the node's order or
comment.

Env: PMCP_CDP (default http://127.0.0.1:9222). The window is never resized.
Exits non-zero if the coherence check fails (so it can gate a workflow).
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path

from playwright.async_api import async_playwright

import _browser_lock as BL
import _menu_nav as M
import _pmcp_safety as S
import _run_diag as D
import _render_guard as RG
import _report_fetch as RF
import _rules_nav as R
import _variables_nav as V
import enrich_bundle

HERE = Path(__file__).resolve().parent
CDP = os.environ.get("PMCP_CDP", "http://127.0.0.1:9222")
BASELINE = HERE / "coherence_baseline.json"  # alex-sandbox's


def baseline_path(coaching: str | None) -> Path:
    """One baseline per coaching: alex-sandbox keeps coherence_baseline.json,
    any other coaching (e.g. alex-live) gets coherence_baseline_<slug>.json,
    so comparing one coaching against another's metrics can't happen."""
    if not coaching or coaching == S.DEFAULT_EXPECTED:
        return BASELINE
    return HERE / f"coherence_baseline_{_slug(coaching)}.json"

_TYPE = {"Message": "message", "DECISION POINT": "decision",
         "Command Message": "command", "EVENT": "event"}


# ---------------------------------------------------------------------------
# phase 1 — micro dialogs
# ---------------------------------------------------------------------------

RUN = {"name": None}  # the coaching this run works on (read at start)


async def _reenter_micro_dialogs(page) -> None:
    if not await _enter_edit_view_retrying(page, RUN["name"]):
        sys.exit(f"could not get back into {RUN['name']!r}'s Edit view after a pause — rerun.")
    if not await M.ensure_micro_dialogs(page):
        sys.exit("Micro Dialogs menubar missing after a pause — rerun.")


async def _guard(page, reenter) -> None:
    """Pause while the browser isn't rendering / is logged out, then resume
    in place (see _render_guard). Exits only if it can't recover."""
    if not await RG.guard(page, reenter):
        sys.exit("the browser stopped rendering (screen asleep?) or the session "
                 "expired, and the run could not recover — rerun.")


async def _navigate_retrying(page, cdp, wid, labels, label: str, tries: int = 3):
    """navigate_and_select with retries. Menu clicks/popups time out now and
    then on a perfectly healthy page (2026-09-25: 3 of 87 dialogs lost to
    single-shot click timeouts - the failure snapshots showed nothing wrong).
    Menus collapsed into `►` are reached through the overflow list.
    Each attempt first checks the browser is rendering and logged in, and
    pauses for the operator if not (screen asleep, 2026-09-29)."""
    for attempt in range(1, tries + 1):
        await _guard(page, lambda: _reenter_micro_dialogs(page))
        try:
            await M.navigate_and_select(page, labels)
            return
        except Exception as e:  # noqa: BLE001
            # an expired session or a sleeping screen looks exactly like a
            # flaky click: the guard at the top of the next attempt pauses
            # for it; on the last attempt, give the guard one more chance
            if attempt == tries:
                if not (await RG.rendering(page)) or await S.session_expired(page):
                    await _guard(page, lambda: _reenter_micro_dialogs(page))
                    await M.navigate_and_select(page, labels)
                    return
                raise
            print(f"  {label}  navigation failed (try {attempt}/{tries}): "
                  f"{str(e).splitlines()[0][:120]} — retrying")
            await M.close_menus(page)
            await page.wait_for_timeout(1000 * attempt)


async def sweep_micro_dialogs(page, cdp, wid) -> tuple[list[dict], list[dict]]:
    if not await M.ensure_micro_dialogs(page):
        sys.exit("Micro Dialogs menu not on screen — open the coaching's Edit "
                 "view, deactivate Monitoring, then rerun.")
    M.GUARD = lambda: _guard(page, lambda: _reenter_micro_dialogs(page))
    targets = await M.all_targets(page)
    print(f"  {len(targets)} menu targets "
          f"({sum(t['isFolder'] for t in targets)} folders)")
    if M.DISCOVERY_ERRORS:
        print(f"  ! {len(M.DISCOVERY_ERRORS)} folder(s) could not be expanded - "
              f"their dialogs are MISSING: "
              + "; ".join(d["path"] for d in M.DISCOVERY_ERRORS))
    micro_dialogs, nodes = [], []
    n_errors = 0
    for seq, t in enumerate(targets):
        name = " / ".join(t["labels"])
        md_uid = f"md-{seq:03d}"
        D.step(f"phase 1: dialog {seq}/{len(targets)} {name}")
        try:
            prev_sig = await M.table_signature(page)
            await _navigate_retrying(page, cdp, wid, t["labels"], f"[{seq}] {name}")
            await M.wait_round_trip(page)
            # don't read until THIS dialog's table is really on screen
            # (stale-table reads, see M.wait_dialog_ready); one re-navigation
            not_ready = await M.wait_dialog_ready(page, t["labels"], prev_sig)
            if not_ready and await S.session_expired(page):
                sys.exit(f"[{seq}] {name}: {S.EXPIRED_HINT}")
            if not_ready:
                print(f"  [{seq}] {name}  not ready ({not_ready}) — re-navigating")
                await _navigate_retrying(page, cdp, wid, t["labels"], f"[{seq}] {name}")
                await M.wait_round_trip(page)
                not_ready = await M.wait_dialog_ready(page, t["labels"], prev_sig)
                if not_ready:
                    raise RuntimeError(f"dialog never became ready: {not_ready}")
            total, seen, missing = await M.sweep_table(page)
        except Exception as e:  # noqa: BLE001
            print(f"  [{seq}] {name}  ERROR {e!r}")
            n_errors += 1
            if n_errors <= 3:  # the first few say why; the rest repeat it
                await D.snapshot(page, f"dialog{seq:03d}", repr(e))
            micro_dialogs.append({"uid": md_uid, "path": name, "name": t["labels"][-1],
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
                "uid": nuid, "microDialogUid": md_uid, "dialogPath": name, "order": i,
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
            "uid": md_uid, "path": name,
            "name": t["labels"][-1], "folderPath": t["labels"][:-1],
            "isFolder": t["isFolder"], "nodeCount": total, "nodeUids": node_uids,
            "missingRows": missing,
        })
        if seq % 20 == 0 or missing:
            print(f"  [{seq}/{len(targets)}] {name}  nodes={total}"
                  f"{'  MISSING ' + str(missing[:4]) if missing else ''}")
    return micro_dialogs, nodes


# ---------------------------------------------------------------------------
# phase 2 — variables
# ---------------------------------------------------------------------------

async def sweep_variables_phase(page) -> list[dict]:
    if not await V.open_variables_tab(page):
        sys.exit("Variables tab not on screen — open the coaching's Edit view "
                 "and rerun.")
    rows = await V.sweep_variables(page)
    print(f"  {len(rows)} variables")
    return rows


# ---------------------------------------------------------------------------
# phase 3b — resolve ambiguous jump-to-message targets live
# ---------------------------------------------------------------------------

async def _enter_edit_view_retrying(page, name: str) -> bool:
    """RF.enter_edit_view, plus one retry from the sidebar's Coachings list:
    it intermittently leaves the row selected without opening it
    (2026-09-29 09:26, right after a Report fetch; a retry went in fine).
    It can also raise (row lookup timeout, 11:12) - same retry."""
    for attempt in (1, 2):
        try:
            if await RF.enter_edit_view(page, name):
                return True
        except Exception as e:  # noqa: BLE001
            if attempt == 2:
                raise
            print(f"  ~ entering the Edit view: {str(e).splitlines()[0][:100]} — retrying")
        await page.get_by_text("Coachings", exact=True).first.click()
        await page.wait_for_timeout(2000)
    return False


async def _reload_edit_view(page, name: str) -> None:
    """Start over from a clean page: reload (drops any stuck Vaadin window;
    phase 3b only reads, so nothing unsaved is lost), then back into the
    coaching's Edit view. Exits loudly if that fails.
    A reload ends the PMCP session (lands on the login form, 2026-09-29), so
    log in again with start_pmcp.sh, which reuses the running browser."""
    await page.reload()
    await page.wait_for_timeout(3000)
    if await page.locator("input[type=password]").count():
        port = CDP.rsplit(":", 1)[-1].strip("/")
        proc = await asyncio.create_subprocess_exec(
            str(HERE.parent / "start_pmcp.sh"), "--port", port,
            stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
        if await proc.wait() != 0:
            sys.exit("phase 3b: re-login after a reload failed — run tools/start_pmcp.sh")
        await page.wait_for_timeout(2000)
    if await S.session_expired(page):
        sys.exit(f"phase 3b: {S.EXPIRED_HINT}")
    if not await _enter_edit_view_retrying(page, name):
        sys.exit(f"phase 3b: could not get back into {name!r}'s Edit view "
                 f"after a reload — rerun.")
    if not await M.ensure_micro_dialogs(page):
        sys.exit("phase 3b: Micro Dialogs menubar missing after a reload — rerun.")


async def resolve_jumps_live(page, cdp, wid, bundle: dict) -> tuple[int, int]:
    """The Report names a jump target only by its text, so jumps to empty
    anchor messages or duplicate-text messages stay ambiguous after enrich
    (14 on ALEX, 2026-09-25). Read those few live from the branch's own
    'Edit rule:' window (DN.read_jump_selection, read-only) and accept the
    answer only if it is one of the Report's candidates. Opening a branch
    rule and closing it is the same no-op re-save as phase 4.
    Returns (resolved, still_unresolved)."""
    import _dialogs_nav as DN
    mds = {m["uid"]: m for m in bundle["microDialogs"]}
    by_md: dict[str, list] = {}
    for n in bundle["nodes"]:
        by_md.setdefault(n["microDialogUid"], []).append(n)
    todo = []  # (md, node, branch_index, key)
    for n in bundle["nodes"]:
        for bi, br in enumerate(n.get("branches") or ()):
            for key in ("jumpMessageIfTrue", "jumpMessageIfFalse"):
                if isinstance(br.get(key), dict) and br[key].get("unresolved"):
                    todo.append((mds[n["microDialogUid"]], n, bi, key))
    name = bundle["coaching"].get("name")
    resolved = 0
    for md, node, bi, key in todo:
        labels = md["folderPath"] + [md["name"]]
        label = "Jump to dialog message if " + ("TRUE" if key.endswith("True") else "FALSE")
        tag = f"{md['path']} row {node['order']} rule {bi} {label[-5:]}"
        D.step(f"phase 3b: {tag}")
        br = node["branches"][bi]
        # a failed read gets one retry from a freshly reloaded Edit view
        # (2026-09-29: 'editor did not open' / 'popup never opened' on 7 of
        # 14, then a rule window whose Close stayed 'not enabled' killed the
        # whole export)
        for attempt in (1, 2):
            try:
                # consecutive targets often share a dialog: re-opening its menu
                # path right after a DP editor was the main 'popup never
                # opened' source (2026-09-29), so skip it when already there
                if await page.evaluate(M.BREADCRUMB_JS) != " > ".join(labels):
                    prev = await M.table_signature(page)
                    await _navigate_retrying(page, cdp, wid, labels, tag)
                    await M.wait_round_trip(page)
                    if await M.wait_dialog_ready(page, labels, prev):
                        await M.wait_dialog_ready(page, labels, "")
                if not await DN.open_row_editor(page, node["order"]):
                    raise RuntimeError("decision point editor did not open")
                dpw = page.locator(".v-window").last
                count = await DN.dp_expand_all(page, dpw)
                if count != len(node["branches"]):
                    raise RuntimeError(f"{count} rules on screen, Report has {len(node['branches'])}")
                if not await DN.dp_open_branch_rule(page, dpw, bi):
                    raise RuntimeError("rule window did not open")
                sel = await DN.read_jump_selection(page, page.locator(".v-window").last, label)
            except Exception as e:  # noqa: BLE001
                sel, err = None, e
            else:
                # an unset jump reads as {'value': ''}; None means the read failed
                err = None if sel is not None else RuntimeError("jump dropdown read nothing")
            try:
                await R.close_windows(page)
                stuck = False
            except RuntimeError as e:
                print(f"  ~ {tag}: {e} — reloading")
                stuck = True
            if stuck:
                await _reload_edit_view(page, name)
            if not err:
                break
        msgs = [x for x in sorted(by_md[md["uid"]], key=lambda x: x["order"])
                if x["type"] != "decision"]
        uid = (msgs[sel["index"]]["uid"]
               if sel and sel.get("index") is not None and 0 <= sel["index"] < len(msgs) else None)
        if sel is not None and not (sel.get("value") or "").strip():
            # the dropdown is EMPTY: no jump is set at all. The Report's
            # '[not set]' made it look like a jump to an empty anchor
            # (2026-09-29, alex-live spirometry row 35)
            br[key] = None
            br.setdefault("resolvedLive", []).append(key)
            resolved += 1
            print(f"  jump resolved: {tag} -> (no jump set)")
        elif uid and uid in br[key]["candidates"]:
            br[key] = uid
            br.setdefault("resolvedLive", []).append(key)
            resolved += 1
            print(f"  jump resolved: {tag} -> {uid}")
        else:
            br[key]["liveRead"] = {"selection": sel, "error": repr(err) if err else None}
            print(f"  ~ jump still ambiguous: {tag} (live read {sel or err!r}, "
                  f"not one of the Report's candidates)")
    return resolved, len(todo) - resolved


# ---------------------------------------------------------------------------
# phase 4 — rules
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
        async def reenter_rules():
            if not await _enter_edit_view_retrying(page, RUN["name"]):
                sys.exit(f"could not get back into {RUN['name']!r} after a pause — rerun.")
            if not await R.ensure_rules_tree(page):
                sys.exit("Rules tab not on screen after a pause — rerun.")
            await R.expand_all(page)  # same expansion -> same treeIndex positions

        for k, r in enumerate(senders):
            await _guard(page, reenter_rules)
            await R.close_windows(page)
            dump = await R.open_rule_modal(page, 0, r["treeIndex"])
            if not dump:
                print(f"  [{k + 1}/{len(senders)}] {r['caption'][:50]!r} FAILED")
                # say WHY (session gone? window stuck? not selected?): on
                # 2026-09-30 0/6 failed with nothing to go on
                await D.snapshot(page, f"sender{k + 1:02d}",
                                 f"sender modal did not open: {r['caption'][:60]}")
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
# phase 5 — coherence check
# ---------------------------------------------------------------------------

def _metrics(bundle: dict) -> dict:
    nodes = bundle["nodes"]
    rg = {n["randomisationGroup"] for n in nodes if n.get("randomisationGroup")}
    rules = bundle.get("rules") or {}
    rt = rules.get("ruleTree") or []
    sr = rules.get("sendingRules")
    variables = bundle.get("variables")
    return {
        "microDialogs": sum(1 for m in bundle["microDialogs"] if not m.get("isFolder")),
        "nodesTotal": len(nodes),
        "messageNodes": sum(1 for n in nodes if n["type"] == "message"),
        "decisionNodes": sum(1 for n in nodes if n["type"] == "decision"),
        "randomisationGroups": len(rg),
        "ruleTreeNodes": len(rt),
        "sendingRules": len(sr) if sr is not None else None,
        "variablesTotal": len(variables) if variables is not None else None,
    }


def coherence_check(bundle: dict, report_html: str | None) -> dict:
    cur = _metrics(bundle)
    warnings: list[str] = []
    ok = True

    # Dialogs the sweep failed to open. Checked first and named explicitly:
    # on 2026-09-18 30 of them failed, and the only warnings were "nodesTotal
    # down 33%" etc., which read like a content change rather than a partial
    # export. That export then got used downstream.
    lost = bundle.get("discoveryErrors") or []
    if lost:
        ok = False
        warnings.append(f"PARTIAL EXPORT: {len(lost)} menu folder(s) could not "
                        f"be expanded, so every dialog under them is missing: "
                        + "; ".join(d["path"] for d in lost))

    failed = [m for m in bundle.get("microDialogs", []) if m.get("error")]
    if failed:
        ok = False
        warnings.append(
            f"PARTIAL EXPORT: {len(failed)} micro dialog(s) failed to sweep "
            f"({failed[0]['uid']}..{failed[-1]['uid']}; first error: "
            f"{failed[0]['error'][:120]}) — their nodes are missing, the "
            f"metric drops below are a consequence, not a content change")

    # Rows the table sweep knowingly skipped (virtualization gap) - printed
    # as "MISSING [...]" during phase 1 but never failed the run before.
    holes = {m["path"] if "path" in m else m["name"]: m["missingRows"]
             for m in bundle.get("microDialogs", []) if m.get("missingRows")}
    if holes:
        ok = False
        warnings.append(f"ROWS MISSING in {len(holes)} dialog(s): "
                        + "; ".join(f"{k} {v[:6]}" for k, v in holes.items()))

    # enrich refused a dialog because the swept rows' text doesn't match the
    # Report's: the sweep read the wrong table (see enrich._pick_report_dialog)
    mism = [u for u in (bundle.get("enrich") or {}).get("unresolved", [])
            if "disagrees" in (u.get("reason") or "")]
    if mism:
        ok = False
        warnings.append(f"TEXT != REPORT in {len(mism)} dialog(s) - swept rows "
                        f"belong to another dialog: "
                        + "; ".join(f"{u['name']} ({u['reason'].split(' - ')[0]})" for u in mism))

    amb = sum(1 for n in bundle.get("nodes", []) for br in n.get("branches") or ()
              for k in ("jumpMessageIfTrue", "jumpMessageIfFalse")
              if isinstance(br.get(k), dict))
    if amb:
        warnings.append(f"{amb} decision-branch jump target(s) still ambiguous "
                        f"(see phase 3b)")

    # every sender found in the rule tree must have been read. A failed
    # sender modal used to be only a printed 'FAILED' line (2026-09-30: 0 of
    # 6 captured, ok = True)
    rules = bundle.get("rules") or {}
    sr = rules.get("sendingRules")
    if sr is not None:
        found = [r for r in rules.get("ruleTree") or [] if r.get("kind") == "sender"]
        got = {r.get("uid") for r in sr}
        missing = [r.get("caption", "?")[:50] for r in found if r.get("uid") not in got]
        if missing:
            ok = False
            warnings.append(f"SENDER RULES MISSING: captured {len(sr)} of {len(found)}; "
                            f"not read: " + "; ".join(missing))

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
    bpath = baseline_path(bundle["coaching"].get("name"))
    if bpath.is_file():
        base = json.loads(bpath.read_text())
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
                # the Report's per-dialog node count is authoritative: a new
                # mismatch means the sweep read the wrong/stale table (seen
                # 2026-09-25: "Quit spirometry dialog" got 51 rows of another
                # dialog, the Report says 7). Fail, and name them.
                ok = False
                warnings.append(
                    f"NODE COUNT != REPORT in {len(new_deltas)} dialog(s) "
                    f"(sweep, report) - likely a stale/wrong table read: "
                    + "; ".join(f"{k} {v}" for k, v in new_deltas.items()))
    else:
        warnings.append(f"no {bpath.name} for this coaching — run with "
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
    bpath = baseline_path(base["coaching"])
    bpath.write_text(json.dumps(base, indent=2, ensure_ascii=False))
    print(f"wrote baseline -> {bpath}")


# ---------------------------------------------------------------------------

def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:48] or "coaching"


async def main() -> int:
    t0 = time.monotonic()
    timings: dict[str, float] = {}
    args = sys.argv[1:]
    flags = {a for a in args if a.startswith("--")}
    report = None
    if "--report" in args:
        report = args[args.index("--report") + 1]
        if not Path(report).is_file():
            sys.exit(f"--report file not found: {report}")
    pos = [a for a in args if not a.startswith("--") and a != report]
    ts = time.strftime("%Y%m%d-%H%M%S")
    explicit_out = Path(pos[0]).with_suffix(".json") if pos else None
    out_dir = HERE.parents[1] / "data" / "exports"
    do_dialogs = "--rules-only" not in flags
    do_rules = "--dialogs-only" not in flags
    do_variables = ("--no-variables" not in flags and "--rules-only" not in flags
                    and "--dialogs-only" not in flags)
    auto_report = "--report" not in args and "--no-report" not in flags and do_dialogs

    # one tool on the shared browser at a time (see _browser_lock)
    try:
        BL.claim("export_coaching")
    except BL.BrowserBusy as e:
        sys.exit(str(e))

    # timestamped log in data/logs/export/ + a stall heartbeat (see _run_diag)
    log_path = D.start_run_log("export")
    D.Heartbeat().__enter__()  # daemon thread, ends with the process
    D.step("connect to CDP + login check")

    async with async_playwright() as pw:
        b = await pw.chromium.connect_over_cdp(CDP)
        ctx = b.contexts[0]
        page = next((p for p in ctx.pages if "pathmate" in (p.url or "")),
                    ctx.pages[0])
        logged_in = await page.evaluate(
            "(()=>{if(document.querySelector('input[type=password]'))return false;"
            # a dead session keeps the old page under a "Session expired!"
            # banner - see start_pmcp.sh SESSION_EXPIRED_JS
            "if([...document.querySelectorAll('.v-Notification')].some("
            "n=>/session expired/i.test(n.textContent||'')))return false;"
            "const t=document.body?document.body.innerText:'';"
            "return /Coachings/.test(t)&&/Logout/.test(t);})()")
        if not logged_in:
            await D.snapshot(page, "fail", "not logged in")
            sys.exit("not logged in to PMCP — run ../start_pmcp.sh first.")
        cdp = await ctx.new_cdp_session(page)
        wid = (await cdp.send("Browser.getWindowForTarget"))["windowId"]

        # coaching name from the editor header (Coaching "…")
        name = await page.evaluate(
            r"""(()=>{const m=(document.body?document.body.innerText:'')
                 .match(/Coaching\s+"([^"]+)"/); return m?m[1]:null;})()""")
        RUN["name"] = name
        if S.is_protected(name):
            # clean reference copy: export only. Phase 3b and phase 4's
            # modals close editors with 'Close' = a no-op re-save (same
            # values saved back). Only a human's explicit
            # --allow-noop-resaves lets a full export do that here (Raul ran
            # alex-live himself that way, 2026-09-29).
            if "--allow-noop-resaves" in flags:
                print(f"  {name!r} is the CLEAN reference coaching: FULL export, "
                      f"no-op re-saves ACCEPTED via --allow-noop-resaves")
            else:
                print(f"  {name!r} is the CLEAN reference coaching (agents/RULES.md): "
                      f"read-only run, no editor modals (--no-modals), no phase 3b. "
                      f"A human may pass --allow-noop-resaves for a full export.")
                flags.add("--no-modals")
                flags.discard("--resolve-jumps")
        bundle: dict = {"coaching": {
            "name": name, "languages": ["en-GB", "ro-RO"],
            "scrapedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z")}}
        out_path = explicit_out or (
            out_dir / f"coaching_{_slug(name) if name else 'coaching'}_{ts}.json")
        print(f"coaching: {name!r}")
        print(f"output -> {out_path}")

        try:
            if auto_report:
                print("--- phase 0: fetch report html ---")
                D.step("phase 0: fetch report html")
                t = time.monotonic()
                try:
                    fetched = await RF.fetch_report_html(page, ctx, name, out_dir)
                    report_path = out_dir / f"Report_{_slug(name) if name else 'coaching'}_{ts}.html"
                    fetched.rename(report_path)
                    report = str(report_path)
                    print(f"  fetched -> {report_path}")
                    if not await _enter_edit_view_retrying(page, name):
                        if await S.session_expired(page):
                            sys.exit(f"fetched the Report, then {S.EXPIRED_HINT}.")
                        sys.exit(f"fetched the Report but could not re-enter {name!r}'s "
                                 f"Edit view afterward — rerun.")
                except SystemExit:
                    raise
                except Exception as e:  # noqa: BLE001
                    print(f"  ! auto-fetch failed ({e!r}) — continuing without a Report HTML")
                    if not await _enter_edit_view_retrying(page, name):
                        if await S.session_expired(page):
                            sys.exit(f"Report auto-fetch failed: {S.EXPIRED_HINT}.")
                        sys.exit(f"Report auto-fetch failed AND could not get back into "
                                 f"{name!r}'s Edit view — rerun.")
                timings["phase0_report"] = time.monotonic() - t

            if do_dialogs:
                print("--- phase 1: micro dialogs ---")
                D.step("phase 1: micro dialogs")
                t = time.monotonic()
                # no window resizing: menus collapsed into `►` are reached
                # through the overflow list (Raul, 2026-09-30)
                md, nodes = await sweep_micro_dialogs(page, cdp, wid)
                bundle["microDialogs"] = md
                bundle["nodes"] = nodes
                bundle["discoveryErrors"] = list(M.DISCOVERY_ERRORS)
                timings["phase1_dialogs"] = time.monotonic() - t
            else:
                bundle["microDialogs"], bundle["nodes"] = [], []

            if do_variables:
                print("--- phase 2: variables ---")
                D.step("phase 2: variables")
                t = time.monotonic()
                bundle["variables"] = await sweep_variables_phase(page)
                timings["phase2_variables"] = time.monotonic() - t
            else:
                bundle["variables"] = None

            if report and do_dialogs:
                print("--- phase 3: enrich from Report HTML ---")
                D.step("phase 3: enrich from Report HTML")
                t = time.monotonic()
                enrich_bundle.enrich_dict(bundle, Path(report))
                timings["phase3_enrich"] = time.monotonic() - t
                # opt-in until it is stable on long dialogs (row virtualization)
                if "--resolve-jumps" in flags and "--no-modals" not in flags:
                    print("--- phase 3b: resolve ambiguous jump targets live ---")
                    D.step("phase 3b: jump targets")
                    t = time.monotonic()
                    ok_n, left = await resolve_jumps_live(page, cdp, wid, bundle)
                    print(f"  {ok_n} jump target(s) resolved live, {left} still ambiguous")
                    timings["phase3b_jumps"] = time.monotonic() - t

            if do_rules:
                print("--- phase 4: rules ---")
                D.step("phase 4: rules")
                t = time.monotonic()
                bundle["rules"] = await sweep_rules(
                    page, open_modals="--no-modals" not in flags)
                timings["phase4_rules"] = time.monotonic() - t
        except SystemExit as e:
            await D.snapshot(page, "fail", str(e.code))
            raise
        except Exception as e:  # noqa: BLE001
            await D.snapshot(page, "fail", repr(e))
            raise

    # check FIRST, against the previous baseline, and only then (if it
    # passed) refresh the baseline. Writing it first made a run compare
    # against itself: on 2026-09-30 a run that lost 82 of 190 rule nodes and
    # captured 0 of 6 senders still reported ok = True (Raul: "how is it even
    # possible that it fails silently?").
    print("--- phase 5: coherence check ---")
    bundle["validation"] = coherence_check(bundle, report if do_dialogs else None)
    for w in bundle["validation"]["warnings"]:
        print(f"  ! {w}")
    print(f"  ok = {bundle['validation']['ok']}")
    if "--update-baseline" in flags:
        if bundle["validation"]["ok"]:
            write_baseline(bundle, report)
        else:
            print("  ! NOT updating the baseline: this run failed the coherence "
                  "check, so it can't become the new reference")

    elapsed = time.monotonic() - t0
    bundle["run"] = {"seconds": round(elapsed, 1),
                     "phaseSeconds": {k: round(v, 1) for k, v in timings.items()},
                     "finishedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                     "log": str(log_path)}
    if not explicit_out and (any(m.get("error") for m in bundle["microDialogs"])
                             or bundle.get("discoveryErrors")):
        # make a partial export obvious to anyone who picks the file up later
        out_path = out_path.with_name(out_path.stem + "_PARTIAL.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(bundle, indent=2, ensure_ascii=False))
    m = bundle["validation"]["metrics"]
    print(f"\nwrote {out_path}")
    print(f"  microDialogs={m['microDialogs']}  nodes={m['nodesTotal']}  "
          f"r_groups={m['randomisationGroups']}  "
          f"ruleTree={m['ruleTreeNodes']}  senders={m['sendingRules']}  "
          f"variables={m['variablesTotal']}")
    mm, ss = divmod(int(elapsed), 60)
    parts = "  ".join(f"{k.split('_', 1)[1]} {v:.0f}s" for k, v in timings.items())
    print(f"  run time: {mm}m {ss:02d}s   ({parts})" if parts
          else f"  run time: {mm}m {ss:02d}s")
    return 0 if bundle["validation"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
