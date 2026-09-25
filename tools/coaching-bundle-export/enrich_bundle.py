"""Enrich coaching.bundle.json with the data the editor grid does not show:
full per-language message text, decision-point branches, trigger expressions and
answer options. These come from the coaching's *Report HTML* export, which the
analyzer already knows how to parse (app/coaching_model.py).

Join key: (micro-dialog leaf name, node order). A dialog is merged only when
exactly one same-name, same-size Report dialog ALSO agrees with the swept grid
text (see _pick_report_dialog) - otherwise its nodes are left text-unresolved
and listed, with a reason, for follow-up.

Usable as a module (`export_coaching.py` calls `enrich_dict()`) or standalone:

  .venv/bin/python enrich_bundle.py coaching.bundle.json Coaching_XXX.html [OUT_DIR]

Writes  <OUT_DIR>/coaching.bundle.v2.json
"""
from __future__ import annotations

import json
import re
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


def _grid_en(grid_text: str) -> str:
    """The en-GB part of a grid cell ('en-GB: ... / ro-RO: ...'), normalised
    for a prefix comparison (the grid truncates long texts)."""
    g = re.sub(r"\s+", " ", grid_text or "").strip().lower()
    m = re.match(r"en-gb:\s*(.*?)(?:\s*/\s*ro-ro:.*)?$", g)
    return (m.group(1) if m else g).rstrip(".…").strip()


def _text_agreement(bnodes: list[dict], rd) -> tuple[int, int]:
    """(agreeing, comparable) nodes between the sweep's grid text and a Report
    dialog's en-GB text, position by position."""
    agree = comparable = 0
    for bn, rn in zip(bnodes, rd.nodes):
        g = _grid_en(bn.get("gridText", ""))
        en = re.sub(r"\s+", " ", (rn.text_by_lang or {}).get("en-GB", "")).strip().lower()
        if not g or not en or en == "[not set]":
            continue
        comparable += 1
        agree += g[:30] in en
    return agree, comparable


def _pick_report_dialog(bnodes: list[dict], same_size: list):
    """Choose the Report dialog whose text matches the swept rows. Matching
    on leaf name + node count alone was wrong twice on the 2026-09-25 export:
    (1) two "Good Compliance" dialogs (spirometry / nighttime) have the same
    name and size, so the first one won and nighttime nodes got spirometry
    text; (2) a stale table read (Timeless Greetings swept with Hello's rows)
    had the right count, so the wrong rows got merged. Returns (dialog, None)
    or (None, reason)."""
    if not same_size:
        return None, "no Report dialog with this name and node count"
    scored = [(c, *_text_agreement(bnodes, c)) for c in same_size]
    comparable = max(n for _, _, n in scored)
    if comparable == 0:  # nothing to compare (no message text) - count only
        return (same_size[0], None) if len(same_size) == 1 else \
            (None, f"{len(same_size)} same-size Report dialogs, no text to tell apart")
    good = [c for c, a, n in scored if n and a / n >= 0.8]
    if len(good) == 1:
        return good[0], None
    if not good:
        best = max(scored, key=lambda s: s[1])
        return None, (f"grid text disagrees with the Report ({best[1]}/{best[2]} "
                      f"rows match) - likely a stale table read")
    return None, f"{len(good)} Report dialogs match equally"


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
        rd, why = _pick_report_dialog(bnodes, [c for c in cands if len(c.nodes) == len(bnodes)])
        if rd is None:
            md["textResolved"] = False
            unresolved.append({"name": " / ".join(md["folderPath"] + [md["name"]]),
                               "bundleNodes": len(bnodes),
                               "reportCandidates": [len(c.nodes) for c in cands],
                               "reason": why})
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
