"""Step 2 of the r_ pipeline — rgroups_table.csv -> rgroups_requests.csv

One row per **thin pool** (fewer than TARGET distinct variants): the pool,
its micro dialog / folder, how many variants it has and how many it needs,
the existing en-GB / ro-RO texts, and the context (comment, trigger). This
is the request manifest — one row = one LLM call step 3 will make. It does
NOT contain the prompt text; step 3 builds that.

  .venv/bin/python rgroup_prepare.py
    default input : ../../data/rgroups/rgroups_table_*.csv (the most
                    RECENTLY-RUN one, by its embedded timestamp - not
                    necessarily the most recently modified file on disk)
    output        : ../../data/rgroups/rgroups_requests_YYMMDDHHMMSS.csv
                    (dir created if missing; YYMMDDHHMMSS = this run's time)
    TARGET=10     : "thin pool" threshold (env; must match step 1)

  All paths are computed from this file's own location (Path(__file__)),
  not the current working directory - run it from anywhere.
"""
from __future__ import annotations

import csv
import os
import sys
from collections import OrderedDict
from pathlib import Path

from _rgroups_files import latest, now_ts

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parents[1] / "data" / "rgroups"
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
    table = latest(DATA_DIR, "rgroups_table", ".csv")
    if table is None:
        sys.exit(f"no rgroups_table_*.csv in {DATA_DIR} — run rgroup_report.py first")
    rows = list(csv.DictReader(table.open(encoding="utf-8")))
    reqs = build_requests(rows)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / f"rgroups_requests_{now_ts()}.csv"
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(reqs)
    total_calls = len(reqs)
    total_variants = sum(int(r["needVariants"]) for r in reqs)
    print(f"using {table.name}")
    print(f"{total_calls} thin pools -> {out.name}  "
          f"({total_calls} API calls, {total_variants} variants to generate)")
    print("review it, then:  rgroup_expand.py --limit N   (N caps the API calls)")


if __name__ == "__main__":
    main()
