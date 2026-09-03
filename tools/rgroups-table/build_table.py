"""Build the randomisation-group tables from a coaching.bundle.v2.json
(produced by ../coaching-bundle-export/).

  rgroups_table.csv    one row per message that carries an r_* group:
                       group, pool, counts, micro dialog, comment, answer type,
                       trigger expressions, full en-GB and ro-RO text
  rgroups_summary.csv  one row per r_* group: totals, pool sizes, whether it
                       still needs top-up (a *pool* = one group x micro dialog,
                       the set actually randomised together at run time)

Run:  .venv/bin/python build_table.py [path/to/coaching.bundle.v2.json]
      TARGET=10 .venv/bin/python build_table.py        # top-up threshold
"""
from __future__ import annotations

import csv
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_BUNDLE = HERE.parents[1] / "data" / "rgroups" / "coaching.bundle.v2.json"
TARGET = int(os.environ.get("TARGET", "10"))

TABLE = HERE / "rgroups_table.csv"
SUMMARY = HERE / "rgroups_summary.csv"

TABLE_COLS = [
    "randomisationGroup", "pool", "groupTotalMessages", "groupMicroDialogs",
    "poolVariants", "microDialog", "folderPath", "order", "nodeUid", "type",
    "comment", "resultVariable", "answerType", "channel", "containsRules",
    "isCommand", "triggerExprs", "en-GB", "ro-RO",
]
SUMMARY_COLS = [
    "randomisationGroup", "totalMessages", "microDialogCount", "poolCount",
    "minPoolVariants", "maxPoolVariants", "needsTopup", "microDialogs",
]


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_BUNDLE
    bundle = json.loads(src.read_text())
    md_by_uid = {m["uid"]: m for m in bundle["microDialogs"]}

    # gather r_ nodes
    rows = []  # (group, mdName, folderPath, node)
    for n in bundle["nodes"]:
        g = (n.get("randomisationGroup") or "").strip()
        if not g.startswith("r_"):
            continue
        md = md_by_uid[n["microDialogUid"]]
        rows.append((g, md["name"], " / ".join(md["folderPath"]), n))

    group_total = defaultdict(int)
    group_mds = defaultdict(set)
    pool_variants = defaultdict(set)  # (group, mdName) -> set of en-GB
    for g, mdn, _fp, n in rows:
        group_total[g] += 1
        group_mds[g].add(mdn)
        en = ((n.get("textByLang") or {}).get("en-GB") or "").strip()
        if en and en != "[not set]":
            pool_variants[(g, mdn)].add(en.lower())

    with TABLE.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=TABLE_COLS)
        w.writeheader()
        for g, mdn, fp, n in rows:
            t = n.get("textByLang") or {}
            w.writerow({
                "randomisationGroup": g,
                "pool": f"{g} @ {mdn}",
                "groupTotalMessages": group_total[g],
                "groupMicroDialogs": len(group_mds[g]),
                "poolVariants": len(pool_variants[(g, mdn)]),
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
                "en-GB": t.get("en-GB", ""),
                "ro-RO": t.get("ro-RO", ""),
            })

    groups = sorted(group_total, key=lambda k: (-group_total[k], k))
    with SUMMARY.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=SUMMARY_COLS)
        w.writeheader()
        for g in groups:
            pv = [len(pool_variants[(g, m)]) for m in sorted(group_mds[g])]
            w.writerow({
                "randomisationGroup": g,
                "totalMessages": group_total[g],
                "microDialogCount": len(group_mds[g]),
                "poolCount": len(pv),
                "minPoolVariants": min(pv) if pv else 0,
                "maxPoolVariants": max(pv) if pv else 0,
                "needsTopup": "yes" if (pv and min(pv) < TARGET) else "no",
                "microDialogs": " ; ".join(sorted(group_mds[g])),
            })

    thin = sum(1 for g in groups
               if min((len(pool_variants[(g, m)]) for m in group_mds[g]), default=0) < TARGET)
    print(f"{len(groups)} r_ groups, {len(rows)} messages -> {TABLE.name}")
    print(f"{len(groups)} rows -> {SUMMARY.name}   ({thin} groups have a pool < {TARGET})")


if __name__ == "__main__":
    main()
