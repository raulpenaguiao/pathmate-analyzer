"""Step 1 of the r_ pipeline — coaching.json -> rgroups_table.csv

One row per message that carries an `r_*` randomisation group: the group,
the pool (`group @ micro dialog` — the set actually randomised together at
run time), how many distinct variants that pool has, whether it's thin, and
the full en-GB / ro-RO text + context.

  .venv/bin/python rgroup_report.py [coaching.json] [--md OUT.md]
    default input : ../../data/exports/coaching.json
    output        : ../../data/rgroups/rgroups_table_YYMMDDHHMMSS.csv
                    (dir created if missing; YYMMDDHHMMSS = this run's time)
    --md          : also write the per-group markdown summary to
                    ../../data/rgroups/rgroups_report.md (fixed name - the
                    `docs/randomisation_groups_*` deliverable view, meant to
                    reflect the current/latest run, not one timestamped copy
                    per run)
    TARGET=10     : "thin pool" threshold (env)

  All paths are computed from this file's own location (Path(__file__)),
  not the current working directory - run it from anywhere.

Parses the JSON — no browser.
"""
from __future__ import annotations

import csv
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

from _rgroups_files import now_ts

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DATA_DIR = REPO / "data" / "rgroups"
DEFAULT_IN = REPO / "data" / "exports" / "coaching.json"
TARGET = int(os.environ.get("TARGET", "10"))

COLS = [
    "randomisationGroup", "pool", "microDialog", "folderPath", "order",
    "nodeUid", "type", "comment", "resultVariable", "answerType", "channel",
    "containsRules", "isCommand", "triggerExprs",
    "poolVariants", "poolNeeds", "thin",           # per-pool topup info
    "groupTotalMessages", "groupMicroDialogs",
    "en-GB", "ro-RO",
]


def collect(bundle: dict) -> list[dict]:
    """-> the rgroups_table rows (list of dicts keyed by COLS)."""
    md_by_uid = {m["uid"]: m for m in bundle["microDialogs"]}
    raw = []  # (group, mdName, folderPath, node)
    for n in bundle["nodes"]:
        g = (n.get("randomisationGroup") or "").strip()
        if not g.startswith("r_"):
            continue
        md = md_by_uid[n["microDialogUid"]]
        raw.append((g, md["name"], " / ".join(md["folderPath"]), n))

    group_total: dict[str, int] = defaultdict(int)
    group_mds: dict[str, set] = defaultdict(set)
    pool_variants: dict[tuple, set] = defaultdict(set)
    for g, mdn, _fp, n in raw:
        group_total[g] += 1
        group_mds[g].add(mdn)
        en = ((n.get("textByLang") or {}).get("en-GB") or "").strip()
        if en and en != "[not set]":
            pool_variants[(g, mdn)].add(en.lower())

    rows = []
    for g, mdn, fp, n in raw:
        pv = len(pool_variants[(g, mdn)])
        t = n.get("textByLang") or {}
        rows.append({
            "randomisationGroup": g,
            "pool": f"{g} @ {mdn}",
            "microDialog": mdn,
            "folderPath": fp,
            "order": n["order"],
            "nodeUid": n["uid"],
            "type": n.get("type", ""),
            "comment": n.get("comment", ""),
            "resultVariable": n.get("resultVariable", ""),
            "answerType": n.get("answerType", ""),
            "channel": n.get("channel", ""),
            "containsRules": (n.get("flags") or {}).get("containsRules", ""),
            "isCommand": (n.get("flags") or {}).get("commandMessage", ""),
            "triggerExprs": " ; ".join(n.get("triggerExprs") or []),
            "poolVariants": pv,
            "poolNeeds": max(0, TARGET - pv),
            "thin": "yes" if pv < TARGET else "no",
            "groupTotalMessages": group_total[g],
            "groupMicroDialogs": len(group_mds[g]),
            "en-GB": t.get("en-GB", ""),
            "ro-RO": t.get("ro-RO", ""),
        })
    return rows


def _markdown(bundle: dict, rows: list[dict]) -> str:
    name = (bundle.get("coaching") or {}).get("name") or "(unnamed coaching)"
    scraped = (bundle.get("coaching") or {}).get("scrapedAt", "?")
    by_group: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_group[r["randomisationGroup"]].append(r)
    order = sorted(by_group, key=lambda g: (-len(by_group[g]), g))
    n_mds = sum(1 for m in bundle["microDialogs"] if not m.get("isFolder"))
    fully = sum(1 for g in order if all(
        (r["en-GB"] or "").strip() not in ("", "[not set]") for r in by_group[g]))
    out = [
        f"# Randomisation groups (`r_*`) in {name}", "",
        f"Generated from `data/exports/coaching.json` (`scrapedAt` = {scraped}) "
        f"by `tools/rgroups-table/rgroup_report.py --md`.", "",
        f"**{len(order)} distinct `r_` groups**, {len(rows)} grouped messages, "
        f"{len(bundle['nodes'])} nodes, {n_mds} micro dialogs. "
        f"Fully text-resolved: {fully}/{len(order)} groups.", "",
        "| Group | Msgs | MDs | Text | Micro dialog(s) |",
        "| --- | ---: | ---: | :-: | --- |",
    ]
    for g in order:
        grp = by_group[g]
        res = sum(1 for r in grp
                  if (r["en-GB"] or "").strip() not in ("", "[not set]"))
        text = "ok" if res == len(grp) else f"{res}/{len(grp)}"
        mds = "<br>".join(sorted({
            " / ".join(p for p in [r["folderPath"], r["microDialog"]] if p)
            for r in grp}))
        out.append(f"| `{g}` | {len(grp)} | {len({r['microDialog'] for r in grp})} "
                   f"| {text} | {mds} |")
    out.append("")
    return "\n".join(out)


def main() -> None:
    args = sys.argv[1:]
    md_out = None
    if "--md" in args:
        i = args.index("--md")
        md_out = Path(args[i + 1]) if i + 1 < len(args) and not args[i + 1].startswith("-") \
            else DATA_DIR / "rgroups_report.md"
        args = [a for a in args if a != "--md" and a != str(md_out)]
    src = Path(args[0]) if args else DEFAULT_IN
    if not src.is_file():
        sys.exit(f"{src} not found — produce it with "
                 "tools/coaching-bundle-export/export_coaching.sh")
    bundle = json.loads(src.read_text())
    rows = collect(bundle)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    TABLE = DATA_DIR / f"rgroups_table_{now_ts()}.csv"
    with TABLE.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    groups = {r["randomisationGroup"] for r in rows}
    thin_pools = {r["pool"] for r in rows if r["thin"] == "yes"}
    print(f"{len(groups)} r_ groups, {len(rows)} messages, "
          f"{len({r['pool'] for r in rows})} pools "
          f"({len(thin_pools)} thin, < {TARGET} variants) -> {TABLE.name}")
    if md_out:
        md_out.parent.mkdir(parents=True, exist_ok=True)
        md_out.write_text(_markdown(bundle, rows))
        print(f"markdown summary -> {md_out}")


if __name__ == "__main__":
    main()
