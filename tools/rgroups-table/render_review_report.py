"""Turn rgroups_table.expanded.csv into a human-checkable markdown review report.

expand_rgroups.py's output is a 1000+ row flat CSV - fine as data, hard to
actually read through and approve/reject. This renders it per-pool: existing
variants (kept, for context) followed by the LLM-proposed new ones as markdown
checkboxes, so a reviewer can tick approved rows directly in the file.

Only pools that expand_rgroups.py touched (i.e. had < TARGET variants) appear;
already-healthy pools are omitted to keep the report focused on what actually
needs a decision.

Run:
  .venv/bin/python tools/rgroups-table/render_review_report.py
  # or point at a specific expanded CSV:
  .venv/bin/python tools/rgroups-table/render_review_report.py path/to/rgroups_table.expanded.csv
"""
from __future__ import annotations

import csv
import sys
from collections import OrderedDict
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_IN = HERE / "rgroups_table.expanded.csv"
DEFAULT_OUT = HERE / "rgroups_review.md"


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_IN
    if not src.is_file():
        sys.exit(f"{src} not found - run expand_rgroups.py first")

    rows = list(csv.DictReader(src.open(encoding="utf-8")))

    pools: "OrderedDict[str, list[dict]]" = OrderedDict()
    for r in rows:
        pools.setdefault(r["pool"], []).append(r)

    sections = []
    n_pools = n_proposed = n_pending = 0
    for pool, rws in pools.items():
        existing = [r for r in rws if r["kind"] == "existing"]
        generated = [r for r in rws if r["kind"] == "generated"]
        pending = [r for r in rws if r["kind"] == "TO_GENERATE"]
        if not generated and not pending:
            continue  # healthy pool, expand_rgroups.py had nothing to add
        n_pools += 1
        n_proposed += len(generated)
        n_pending += len(pending)

        head = rws[0]
        lines = [f"## `{pool}`", ""]
        lines.append(
            f"*Micro dialog:* {head['microDialog']}  "
            f"*Existing variants:* {len(existing)}  "
            f"*Proposed new:* {len(generated)}"
            + (f"  *Pending/failed (rerun expand_rgroups.py):* {len(pending)}" if pending else "")
        )
        if head.get("comment") and head["comment"] not in ("---", ""):
            lines.append(f"*Comment:* {head['comment']}")
        lines.append("")

        if existing:
            lines.append("**Existing (kept, unchanged):**")
            lines.append("")
            for i, r in enumerate(existing, 1):
                lines.append(f"{i}. en-GB: {r['en-GB']}")
                lines.append(f"   ro-RO: {r['ro-RO']}")
            lines.append("")

        if generated:
            lines.append("**Proposed new — tick to approve:**")
            lines.append("")
            for i, r in enumerate(generated, 1):
                lines.append(f"- [ ] {i}. en-GB: {r['en-GB']}")
                lines.append(f"      ro-RO: {r['ro-RO']}")
            lines.append("")

        if pending:
            lines.append(f"**{len(pending)} variant(s) not yet generated** "
                          "(dry-run skeleton, or the API call failed - rerun "
                          "`expand_rgroups.py` to fill these in).")
            lines.append("")

        sections.append("\n".join(lines))

    header = [
        f"# Randomisation-pool text review",
        "",
        f"Generated from `{src.name}`. {n_pools} pool(s) below the target variant "
        f"count: {n_proposed} new variant(s) proposed"
        + (f", {n_pending} still pending generation" if n_pending else "") + ".",
        "",
        "Review each pool below. Tick the checkbox next to variants you approve; "
        "leave unchecked (or delete the line) to reject. Nothing is written back "
        "to the coaching from this file by itself - see the write-back tool "
        "(planned) for that step.",
        "",
        "---",
        "",
    ]

    DEFAULT_OUT.write_text("\n".join(header) + "\n".join(sections), encoding="utf-8")
    print(f"wrote {DEFAULT_OUT} ({n_pools} pools, {n_proposed} proposed, "
          f"{n_pending} pending)")


if __name__ == "__main__":
    main()
