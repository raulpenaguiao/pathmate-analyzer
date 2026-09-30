"""Duplicate-wording check for r_ pools — report only, never blocking. No API.

Within each pool and each language, every pair of wordings is compared after normalising case, diacritics, punctuation, emoji
and whitespace (`$placeholders` are kept):

  exact  the normalised texts are equal
  near   difflib similarity >= THRESHOLD (default 0.95) - a one-word or
         one-letter change, e.g. a typo copy

A pool here is one run of consecutive rows of an r_ group, since that is
what PMCP randomises: a block of the group copied into another branch of
the same dialog is a separate pool, so the copies aren't flagged as
repeats of each other.

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
import re
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
                    "order": int(r["order"]) if "order" in r else None,
                    "cond": (r.get("triggerExprs") or "").strip() if "order" in r else None,
                    "en-GB": r.get("en-GB") or "", "ro-RO": r.get("ro-RO") or ""})
    _mark_blocks(out)
    return out


def _mark_blocks(items: list[dict]) -> None:
    """PMCP randomises only within a run of CONSECUTIVE rows of one group
    (docs/pmcp-docs micro-dialogs §8). A dialog can hold several such runs
    of the same group, e.g. the same block copied into each branch (Streak
    Week rows 5-10, 11-16, ...). Those copies are separate pools at run
    time, so they aren't repeats of each other: tag each existing row with
    its run number, and check() only pairs rows of the same run."""
    by_pool = defaultdict(list)
    for it in items:
        if it["order"] is not None:
            by_pool[it["pool"]].append(it)
    for rows in by_pool.values():
        rows.sort(key=lambda it: it["order"])
        block, prev = 0, None
        for it in rows:
            if prev is not None and it["order"] != prev + 1:
                block += 1
            it["block"], prev = block, it["order"]


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
                if a["source"] == b["source"] == "existing":
                    if any(m["source"] == "new" for m in members):
                        continue  # generated-CSV mode: only pairs touching a new wording
                    if a.get("block") != b.get("block"):
                        continue  # separate consecutive runs = separate pools
                    # (a new wording is compared with every run: apply adds it
                    # next to one of them, and a repeat of any is still a repeat)
                if ka == kb:
                    kind, ratio = "exact", 1.0
                else:
                    ratio = difflib.SequenceMatcher(None, ka, kb).ratio()
                    if ratio < threshold:
                        continue
                    kind = "near"
                # rows of one pool with different send conditions ("Shown
                # when") may be meant as alternatives, not siblings - e.g. one
                # question worded identically per branch. Flag, but say so.
                cond = ("n/a" if a["cond"] is None or b["cond"] is None
                        else "same" if a["cond"] == b["cond"] else "different")
                hits.append({"pool": pool, "lang": lang, "kind": kind,
                             "ratio": round(ratio, 3), "cond": cond,
                             "a": a["ref"], "a_text": a[lang].strip(),
                             "b": b["ref"], "b_text": b[lang].strip()})
    hits.sort(key=lambda h: (h["pool"], h["lang"], h["kind"] != "exact", -h["ratio"]))
    return hits


def check_untranslated(items: list[dict]) -> list[dict]:
    """ro-RO cells that hold English: the normalised ro-RO equals the en-GB
    of its own row or of any row in the same pool (the 09-30 case: en 'Ciao
    $participantName! 🤗' with ro 'Hi $participantName! 🤗', which is row 1's
    en-GB). Texts with no letters outside $placeholders are skipped - an
    emoji or a bare name reads the same in both languages."""
    by_pool = defaultdict(list)
    for it in items:
        by_pool[it["pool"]].append(it)
    out = []
    for pool, members in by_pool.items():
        en_of = {}
        for m in members:
            k = norm_text(m["en-GB"])
            if k:
                en_of.setdefault(k, m["ref"])
        for m in members:
            k = norm_text(m["ro-RO"])
            if k == "not set" or not re.search(r"[^\W\d_]", re.sub(r"\$\w+", "", k)):
                continue  # PMCP's empty-cell marker, or no words at all
            if k == norm_text(m["en-GB"]):
                src = "its own en-GB"
            elif k in en_of:
                src = f"the en-GB of {en_of[k]}"
            else:
                continue
            out.append({"pool": pool, "ref": m["ref"], "en": m["en-GB"].strip(),
                        "ro": m["ro-RO"].strip(), "matches": src})
    return out


def report(hits: list[dict], label: str, n_items: int, n_pools: int,
           threshold: float, untranslated: list[dict]) -> str:
    exact = sum(h["kind"] == "exact" for h in hits)
    diff = sum(h["cond"] == "different" for h in hits)
    lines = [f"# r_ duplicate check: {label}", "",
             f"{n_items} wordings in {n_pools} pools. Threshold for near "
             f"matches: {threshold}. Emoji, punctuation, case and accents are "
             f"ignored. Report only.", "",
             f"**{len(hits)} flagged pairs**: {exact} exact, {len(hits) - exact} near, "
             f"in {len({h['pool'] for h in hits})} pools. {diff} of them are between "
             f"rows with different send conditions (`cond = different`): those may "
             f"be deliberate alternatives rather than repeats.",
             f"**{len(untranslated)} ro-RO cells hold English** (the ro-RO text "
             f"equals an en-GB text of the pool).", ""]
    esc = lambda s: s.replace("|", "\\|").replace("\n", " ⏎ ")
    lines += ["## Repeats", ""]
    if hits:
        lines += ["| pool | lang | kind | sim | cond | A | B |",
                  "|---|---|---|---|---|---|---|"]
        for h in hits:
            lines.append(f"| {esc(h['pool'])} | {h['lang']} | {h['kind']} | {h['ratio']} | "
                         f"{h['cond']} | {h['a']}: {esc(h['a_text'])} | {h['b']}: {esc(h['b_text'])} |")
    else:
        lines.append("Nothing flagged.")
    lines += ["", "## ro-RO holds English", ""]
    if untranslated:
        lines += ["| pool | row | en-GB | ro-RO | equals |", "|---|---|---|---|---|"]
        for u in untranslated:
            lines.append(f"| {esc(u['pool'])} | {u['ref']} | {esc(u['en'])} | "
                         f"{esc(u['ro'])} | {u['matches']} |")
    else:
        lines.append("Nothing flagged.")
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
    untranslated = check_untranslated(items)
    if args.table:  # generated mode: report only the new wordings' cells
        untranslated = [u for u in untranslated if u["ref"].startswith("new")]

    label = src.name + (f" + {Path(args.table).name}" if args.table else "")
    out = Path(args.out) if args.out else DATA_DIR / f"dupcheck_{src.stem}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report(hits, label, len(items), len({i["pool"] for i in items}),
                          args.threshold, untranslated), encoding="utf-8")
    exact = sum(h["kind"] == "exact" for h in hits)
    diff = sum(h["cond"] == "different" for h in hits)
    print(f"{len(hits)} flagged pairs ({exact} exact, {len(hits) - exact} near; "
          f"{diff} across different send conditions) "
          f"in {len({h['pool'] for h in hits})} pools; "
          f"{len(untranslated)} ro-RO cells hold English -> {out}")


if __name__ == "__main__":
    main()
