"""Render the randomisation-group (`r_*`) report — one markdown table, one
row per group — straight from a `coaching.json` export. No browser scrape.

  | Group | Msgs | MDs | Text | Micro dialog(s) |

- Msgs  : messages carrying that `r_` group, across the whole coaching
- MDs   : distinct micro dialogs it appears in
- Text  : "ok" if every one has resolved en-GB text, else "<resolved>/<total>"
- Micro dialog(s): the full folder path(s), one per distinct dialog

This is the committed-deliverable view (see `docs/randomisation_groups_*`).
Per-message detail lives in `rgroups_table.csv` (`build_table.py`).

Run:
  .venv/bin/python tools/rgroups-table/report.py [coaching.json] [--out FILE]
  # default input : data/rgroups/coaching.json
  # default output: tools/rgroups-table/rgroups_report.md
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DEFAULT_IN = REPO / "data" / "rgroups" / "coaching.json"
DEFAULT_OUT = HERE / "rgroups_report.md"


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:48] or "coaching"


def build(bundle: dict) -> str:
    md_by_uid = {m["uid"]: m for m in bundle["microDialogs"]}
    coaching = bundle.get("coaching") or {}
    name = coaching.get("name") or "(unnamed coaching)"

    total = defaultdict(int)                    # group -> message count
    dialogs = defaultdict(set)                  # group -> {full path}
    resolved = defaultdict(int)                 # group -> messages with en-GB text
    for n in bundle["nodes"]:
        g = (n.get("randomisationGroup") or "").strip()
        if not g.startswith("r_"):
            continue
        md = md_by_uid[n["microDialogUid"]]
        total[g] += 1
        dialogs[g].add(" / ".join(md["folderPath"] + [md["name"]]))
        en = ((n.get("textByLang") or {}).get("en-GB") or "").strip()
        if en and en != "[not set]":
            resolved[g] += 1

    groups = sorted(total, key=lambda k: (-total[k], k))
    n_msgs = sum(total.values())
    n_mds = sum(1 for m in bundle["microDialogs"] if not m.get("isFolder"))
    fully = sum(1 for g in groups if resolved[g] == total[g])

    out = [
        f"# Randomisation groups (`r_*`) in {name}",
        "",
        f"Generated from `data/rgroups/coaching.json` "
        f"(`coaching.scrapedAt` = {coaching.get('scrapedAt', '?')}) by "
        f"`tools/rgroups-table/report.py`. The Report-HTML export does not "
        f"carry the Randomisation Group column — this comes from the live "
        f"editor sweep in `tools/coaching-bundle-export/export_coaching.py`.",
        "",
        f"**{len(groups)} distinct `r_` groups**, {n_msgs} grouped messages, "
        f"{len(bundle['nodes'])} nodes, {n_mds} micro dialogs. "
        f"Fully text-resolved: {fully}/{len(groups)} groups.",
        "",
        "Per-message detail (both languages, trigger conditions, pool "
        "membership) is in "
        "[`rgroups_table.csv`](rgroups_table.csv) / `rgroups_summary.csv`.",
        "",
        "| Group | Msgs | MDs | Text | Micro dialog(s) |",
        "| --- | ---: | ---: | :-: | --- |",
    ]
    for g in groups:
        text = "ok" if resolved[g] == total[g] else f"{resolved[g]}/{total[g]}"
        mds = "<br>".join(sorted(dialogs[g]))
        out.append(f"| `{g}` | {total[g]} | {len(dialogs[g])} | {text} | {mds} |")
    out.append("")
    return "\n".join(out)


def main() -> None:
    args = sys.argv[1:]
    out_path = None
    if "--out" in args:
        i = args.index("--out")
        out_path = Path(args[i + 1])
        args = args[:i] + args[i + 2:]
    src = Path(args[0]) if args else DEFAULT_IN
    if not src.is_file():
        sys.exit(f"{src} not found — produce it with "
                 "tools/coaching-bundle-export/export_coaching.sh")
    bundle = json.loads(src.read_text())
    md = build(bundle)

    if out_path is None:
        slug = _slug((bundle.get("coaching") or {}).get("name") or "")
        out_path = DEFAULT_OUT if slug == "coaching" else HERE / f"rgroups_report_{slug}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md)
    ng = md.count("\n| `r_")
    print(f"{ng} r_ groups -> {out_path}")


if __name__ == "__main__":
    main()
