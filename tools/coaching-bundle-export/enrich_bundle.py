"""Enrich coaching.bundle.json with the data the editor grid does not show:
full per-language message text, decision-point branches, trigger expressions and
answer options. These come from the coaching's *Report HTML* export, which the
analyzer already knows how to parse (app/coaching_model.py).

Join key: (micro-dialog leaf name, node order). A dialog is merged only when
exactly one Report dialog matches by name AND node count - otherwise its nodes
are left text-unresolved and listed for follow-up.

Usable as a module (`export_coaching.py` calls `enrich_dict()`) or standalone:

  .venv/bin/python enrich_bundle.py coaching.bundle.json Coaching_XXX.html [OUT_DIR]

Writes  <OUT_DIR>/coaching.bundle.v2.json
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

# The Report-HTML parser lives in the analyzer app. Point PMCP_REPO at the repo
# root if you run this from somewhere else.
REPO = Path(os.environ.get("PMCP_REPO", Path(__file__).resolve().parents[2]))


def parse_report(html_bytes: bytes):
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    try:
        from app.coaching_model import parse_model
    except ModuleNotFoundError as e:  # noqa: BLE001
        raise SystemExit(
            f"cannot import app.coaching_model ({e}). Run from the "
            f"pathmate-analyzer repo, or set PMCP_REPO to its path.") from None
    return parse_model(html_bytes)


def report_dialog_counts(report_html: Path) -> dict[str, int]:
    """{micro-dialog name: node count} from the Report HTML — for the
    coherence check."""
    m = parse_report(Path(report_html).read_bytes())
    return {d.name: len(d.nodes) for d in m.micro_dialogs}


def _resolve_jump_target(target: dict | None, dialog_nodes: list[dict]):
    """A decision branch's 'Jump to dialog message if TRUE/FALSE' target, as
    the Report HTML gives it (the target message's text per language), ->
    that node's uid when exactly one node in the same dialog carries that
    exact text. Otherwise `{"raw", "candidates", "unresolved": True}`: the
    Report names the target only by its text, so empty "[not set]" anchor
    messages and duplicate-text messages can't be told apart from it
    (verified 2026-09-24 on ALEX v01: 22/36 unique, 14 not). The editor's own
    filterselect shows comments and could resolve those, but that needs a
    live pass."""
    if not target:
        return None
    hits = [n["uid"] for n in dialog_nodes if (n.get("textByLang") or {}) == target]
    if len(hits) == 1:
        return hits[0]
    return {"raw": target, "candidates": hits, "unresolved": True}


def _nest_branches(branches: list[dict]) -> None:
    """Give each decision-point branch its `parentIndex` (index into the same
    list, None at top level) from its `depth`. PMCP docs (Rules §2.2):
    decision points use "AND logic (child rules)" and "OR logic (same
    hierarchy level)", so the rules form a tree. The Report prints them flat
    in pre-order, with the nesting only as each row's indentation (see
    DecisionBranch.depth), so a depth stack rebuilds the parent links."""
    stack: list[int] = []  # index of the open ancestor at each depth
    for i, br in enumerate(branches):
        d = br.get("depth") or 0
        del stack[d:]
        br["parentIndex"] = stack[-1] if stack else None
        stack.append(i)


def enrich_dict(bundle: dict, report_html: Path) -> dict:
    """Join Report-HTML text/branches into an in-memory bundle dict, in place.
    Returns the same dict (with an `enrich` summary block added)."""
    model = parse_report(Path(report_html).read_bytes())
    by_name = defaultdict(list)
    for d in model.micro_dialogs:
        by_name[d.name].append(d)

    nodes_by_md = defaultdict(list)
    for n in bundle["nodes"]:
        nodes_by_md[n["microDialogUid"]].append(n)
    for lst in nodes_by_md.values():
        lst.sort(key=lambda n: n["order"])

    # stable cross-export names (uids are positional, see export_coaching);
    # backfilled here so pre-2026-09-24 exports get them on re-enrich too
    for md in bundle["microDialogs"]:
        md.setdefault("path", " / ".join(md.get("folderPath", []) + [md["name"]]))
        for n in nodes_by_md.get(md["uid"], []):
            n.setdefault("dialogPath", md["path"])

    merged, empty, unresolved = 0, 0, []
    for md in bundle["microDialogs"]:
        bnodes = nodes_by_md.get(md["uid"], [])
        if not bnodes:
            md["textResolved"] = True  # nothing to resolve
            empty += 1
            continue
        cands = by_name.get(md["name"], [])
        rd = next((c for c in cands if len(c.nodes) == len(bnodes)), None)
        if rd is None:
            md["textResolved"] = False
            unresolved.append({"name": " / ".join(md["folderPath"] + [md["name"]]),
                               "bundleNodes": len(bnodes),
                               "reportCandidates": [len(c.nodes) for c in cands]})
            continue
        md["textResolved"] = True
        merged += 1
        for bn, rn in zip(bnodes, rd.nodes):
            bn["textByLang"] = rn.text_by_lang
            bn["answerOptionsByLang"] = rn.answer_options_by_lang
            bn["commandByLang"] = rn.command_by_lang
            bn["triggerExprs"] = rn.trigger_exprs
            bn["mediaFile"] = rn.media_file
            if rn.branches:
                bn["branches"] = [{
                    "condition": b.expr, "comment": b.comment, "writesVar": b.writes_var,
                    "stopMicroDialog": b.stop_micro_dialog,
                    "leaveDecisionPoint": b.leave_decision_point,
                    "jumpDialog": b.jump_dialog, "cascadeDialog": b.cascade_dialog,
                    "supported": b.supported,
                    # raw per-language text for now; resolved below, once
                    # every node in this dialog has its textByLang
                    "jumpMessageIfTrue": getattr(b, "jump_message_if_true", None) or None,
                    "jumpMessageIfFalse": getattr(b, "jump_message_if_false", None) or None,
                    "depth": getattr(b, "depth", 0),
                } for b in rn.branches]
        for bn in bnodes:
            for br in bn.get("branches") or ():
                for key in ("jumpMessageIfTrue", "jumpMessageIfFalse"):
                    br[key] = _resolve_jump_target(br[key], bnodes)
            _nest_branches(bn.get("branches") or [])

    bundle["enrich"] = {"reportHtml": Path(report_html).name,
                        "dialogsMerged": merged, "emptyDialogs": empty,
                        "dialogsUnresolved": len(unresolved),
                        "unresolved": unresolved}
    print(f"enriched {merged} dialogs, {empty} empty, "
          f"{len(unresolved)} unresolved (of {len(bundle['microDialogs'])})")
    for u in unresolved:
        print(f"  unresolved: {u['name']}  bundle={u['bundleNodes']} "
              f"report={u['reportCandidates']}")
    return bundle


def enrich(bundle_path: Path, report_html: Path, out_dir: Path) -> dict:
    """File wrapper: read a bundle JSON, enrich, write coaching.bundle.v2.json."""
    bundle = enrich_dict(json.loads(Path(bundle_path).read_text()), report_html)
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    out = Path(out_dir) / "coaching.bundle.v2.json"
    out.write_text(json.dumps(bundle, indent=2, ensure_ascii=False))
    print(f"  -> {out}")
    return bundle


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    enrich(Path(sys.argv[1]), Path(sys.argv[2]),
           Path(sys.argv[3]) if len(sys.argv) > 3 else Path.cwd())
