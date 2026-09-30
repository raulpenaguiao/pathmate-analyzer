"""Duplicate-wording check for r_ pools — report only, never blocking. No API.

Within each pool (`group @ micro dialog`) and each language, every pair of
wordings is compared after normalising case, diacritics, punctuation, emoji
and whitespace (`$placeholders` are kept):

  exact  the normalised texts are equal
  near   difflib similarity >= THRESHOLD (default 0.95) - a one-word or
         one-letter change, e.g. a typo copy

Clearly different wordings stay unflagged ("Do you have your spirometer
handy?" vs "Is your spirometer within reach?" is ~0.6).

  .venv/bin/python rgroup_dupcheck.py coaching_<name>_<ts>.json
  .venv/bin/python rgroup_dupcheck.py rgroups_table_<ts>.csv
  .venv/bin/python rgroup_dupcheck.py rgroups_generated_<ts>.csv [--table rgroups_table_<ts>.csv]
      --table     also compare the new wordings with the pool's existing ones
                  (existing-vs-existing pairs are left to the table's own check)
      --threshold near-match cutoff (default 0.95)
      --out FILE  report path (default data/rgroups/dupcheck_<input stem>.md)

A bare file name is looked up in data/rgroups/ and data/exports/. Generated
rows whose status isn't `ok` are skipped: expand already rejected those.
Exit code is always 0.
"""
from __future__ import annotations

import argparse
import csv
import difflib
import json
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

from _rgroups_files import norm_text

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DATA_DIR = REPO / "data" / "rgroups"
EXPORTS = REPO / "data" / "exports"
LANGS = ("en-GB", "ro-RO")


def resolve(name: str) -> Path:
    p = Path(name)
    for cand in (p, DATA_DIR / name, EXPORTS / name):
        if cand.is_file():
            return cand
    sys.exit(f"not found: {name}")


def load(path: Path, source: str) -> list[dict]:
    """-> [{pool, ref, en-GB, ro-RO, source}] from an export JSON, a table
    CSV or a generated CSV. `ref` says where a wording lives: '#<order>' for
    an existing message, 'new<variantIndex>' for a generated one."""
    if path.suffix == ".json":
        from rgroup_report import collect
        rows = collect(json.loads(path.read_text(encoding="utf-8")))
    else:
        rows = list(csv.DictReader(path.open(encoding="utf-8")))
    out = []
    for r in rows:
        if "variantIndex" in r:            # generated CSV
            if r.get("status") != "ok":
                continue
            ref = f"new{r['variantIndex']}"
        else:
            ref = f"#{r['order']}"
        out.append({"pool": r["pool"], "ref": ref, "source": source,
                    "en-GB": r.get("en-GB") or "", "ro-RO": r.get("ro-RO") or ""})
    return out


def check(items: list[dict], threshold: float) -> list[dict]:
    by_pool = defaultdict(list)
    for it in items:
        by_pool[it["pool"]].append(it)
    hits = []
    for pool, members in by_pool.items():
        for lang in LANGS:
            keyed = [(m, norm_text(m[lang])) for m in members]
            keyed = [(m, k) for m, k in keyed if k and k != "not set"]
            for (a, ka), (b, kb) in combinations(keyed, 2):
                if a["source"] == b["source"] == "existing" and any(
                        m["source"] == "new" for m in members):
                    continue  # generated-CSV mode: only pairs touching a new wording
                if ka == kb:
                    kind, ratio = "exact", 1.0
                else:
                    ratio = difflib.SequenceMatcher(None, ka, kb).ratio()
                    if ratio < threshold:
                        continue
                    kind = "near"
                hits.append({"pool": pool, "lang": lang, "kind": kind,
                             "ratio": round(ratio, 3),
                             "a": a["ref"], "a_text": a[lang].strip(),
                             "b": b["ref"], "b_text": b[lang].strip()})
    hits.sort(key=lambda h: (h["pool"], h["lang"], h["kind"] != "exact", -h["ratio"]))
    return hits


def report(hits: list[dict], label: str, n_items: int, n_pools: int,
           threshold: float) -> str:
    exact = sum(h["kind"] == "exact" for h in hits)
    lines = [f"# r_ duplicate check: {label}", "",
             f"{n_items} wordings in {n_pools} pools. Threshold for near "
             f"matches: {threshold}. Report only.", "",
             f"**{len(hits)} flagged pairs**: {exact} exact, {len(hits) - exact} near, "
             f"in {len({h['pool'] for h in hits})} pools.", ""]
    if not hits:
        return "\n".join(lines + ["Nothing flagged."]) + "\n"
    lines += ["| pool | lang | kind | sim | A | B |", "|---|---|---|---|---|---|"]
    esc = lambda s: s.replace("|", "\\|").replace("\n", " ⏎ ")
    for h in hits:
        lines.append(f"| {esc(h['pool'])} | {h['lang']} | {h['kind']} | {h['ratio']} | "
                     f"{h['a']}: {esc(h['a_text'])} | {h['b']}: {esc(h['b_text'])} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="export .json, rgroups_table_*.csv or rgroups_generated_*.csv")
    ap.add_argument("--table", help="with a generated CSV: the table CSV of the same coaching")
    ap.add_argument("--threshold", type=float, default=0.95)
    ap.add_argument("--out")
    args = ap.parse_args()

    src = resolve(args.input)
    items = load(src, "new" if src.name.startswith("rgroups_generated") else "existing")
    if args.table:
        pools = {it["pool"] for it in items}
        items += [it for it in load(resolve(args.table), "existing") if it["pool"] in pools]
    hits = check(items, args.threshold)

    label = src.name + (f" + {Path(args.table).name}" if args.table else "")
    out = Path(args.out) if args.out else DATA_DIR / f"dupcheck_{src.stem}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report(hits, label, len(items), len({i["pool"] for i in items}),
                          args.threshold), encoding="utf-8")
    exact = sum(h["kind"] == "exact" for h in hits)
    print(f"{len(hits)} flagged pairs ({exact} exact, {len(hits) - exact} near) "
          f"in {len({h['pool'] for h in hits})} pools -> {out}")


if __name__ == "__main__":
    main()
