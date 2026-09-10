"""Step 2 of the r_ pipeline — rgroups_table.csv -> rgroups_requests.csv

One row per **thin pool** (fewer than TARGET distinct variants): the pool,
its micro dialog / folder, how many variants it has and how many it needs,
the existing en-GB / ro-RO texts, and the context (comment, trigger). This
is the request manifest — one row = one LLM call step 3 will make. It does
NOT contain the prompt text; step 3 builds that.

  .venv/bin/python rgroup_prepare.py
    default input : rgroups_table.csv   (from rgroup_report.py)
    TARGET=10     : "thin pool" threshold (env; must match step 1)
"""
from __future__ import annotations

import csv
import os
import sys
from collections import OrderedDict
from pathlib import Path

HERE = Path(__file__).resolve().parent
TABLE = HERE / "rgroups_table.csv"
OUT = HERE / "rgroups_requests.csv"
TARGET = int(os.environ.get("TARGET", "10"))

SEP = "\n"  # existing variants joined with newlines inside a quoted CSV cell

COLS = [
    "pool", "randomisationGroup", "microDialog", "folderPath",
    "haveVariants", "needVariants", "comment", "triggerExprs",
    "existing_enGB", "existing_roRO",
]


def build_requests(table_rows: list[dict]) -> list[dict]:
    pools: "OrderedDict[str, list[dict]]" = OrderedDict()
    for r in table_rows:
        pools.setdefault(r["pool"], []).append(r)

    out = []
    for pool, rws in pools.items():
        head = rws[0]
        seen, en_list, ro_list = set(), [], []
        for r in rws:
            en = (r.get("en-GB") or "").strip()
            if not en or en == "[not set]" or en.lower() in seen:
                continue
            seen.add(en.lower())
            en_list.append(en)
            ro_list.append((r.get("ro-RO") or "").strip())
        have = len(en_list)
        if have >= TARGET:
            continue
        triggers = sorted({r["triggerExprs"] for r in rws if r.get("triggerExprs")})
        out.append({
            "pool": pool,
            "randomisationGroup": head["randomisationGroup"],
            "microDialog": head["microDialog"],
            "folderPath": head.get("folderPath", ""),
            "haveVariants": have,
            "needVariants": TARGET - have,
            "comment": head.get("comment", ""),
            "triggerExprs": " | ".join(triggers),
            "existing_enGB": SEP.join(en_list),
            "existing_roRO": SEP.join(ro_list),
        })
    return out


def main() -> None:
    if not TABLE.is_file():
        sys.exit(f"{TABLE.name} not found — run rgroup_report.py first")
    rows = list(csv.DictReader(TABLE.open(encoding="utf-8")))
    reqs = build_requests(rows)
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(reqs)
    total_calls = len(reqs)
    total_variants = sum(int(r["needVariants"]) for r in reqs)
    print(f"{total_calls} thin pools -> {OUT.name}  "
          f"({total_calls} API calls, {total_variants} variants to generate)")
    print("review it, then:  rgroup_expand.py --limit N   (N caps the API calls)")


if __name__ == "__main__":
    main()
