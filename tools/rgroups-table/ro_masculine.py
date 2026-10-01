"""Masculine version of the ro-RO message text — offline, no API, no browser.

Deterministic rules, applied to every ro-RO message text and answer-option
text (commands are skipped: the patient never sees them):

  sigur/ă, sigur/a, consecvent(ă)    -> sigur, consecvent  (marked alternation)
  pregătit/pregătită, pregătită/pregătit -> pregătit       (two forms of one word)

A slash between two different words ("părinții/îngrijitorii") is an
alternative, not a gender marker, and is left alone.

Nothing else is changed. Possible UNMARKED feminine forms aimed at the
reader (e.g. "ești pregătită", a feminine vocative) go to a review list in
the report and are never guessed. Feminine forms that agree with a feminine
noun ("o zi minunată") are correct as they are.

  .venv/bin/python ro_masculine.py coaching_<name>_<ts>.json
  .venv/bin/python ro_masculine.py rgroups_generated_<ts>.csv     # same rules
      --out-csv FILE  default data/rgroups/masculine_<input stem>.csv
      --report FILE   default data/rgroups/masculine_<input stem>.md

The input file is never modified. The output CSV has one row per text:
dialogPath, row, field, en-GB, ro-RO, ro-RO masculine, changed, review.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DATA_DIR = REPO / "data" / "rgroups"
EXPORTS = REPO / "data" / "exports"

L = r"[A-Za-zĂÂÎȘȚŞŢăâîșțşţ]"          # one Romanian letter
WORD = rf"{L}+"

# x/ă, x/a, x(ă), x(a) - also with spaces around the slash
SUFFIX_ALT = re.compile(rf"\b({WORD})\s*(?:/\s*|\(\s*)(ă|a)\s*\)?(?!{L})")
# two full forms of the same word joined by a slash, either order
PAIR_ALT = re.compile(rf"\b({WORD})\s*/\s*({WORD})\b")

# reader-directed contexts whose next adjective/participle agrees with the reader
READER = re.compile(
    rf"\b(ești|esti|fii|să fii|ai fost|ai rămas|ai devenit|te simți|te simti|"
    rf"te-ai simțit|rămâi|devii|pari|arăți|te consideri|sunt|mă simt|ma simt)\s+"
    rf"(?:(?:foarte|prea|super|destul de|mai|atât de|tot|cam|deja|încă|puțin|"
    rf"un pic|așa de)\s+)*({WORD})", re.I)
FEM_END = re.compile(r"(ă|oasă|ită|ată|ută|ică|ie)$", re.I)
# words that end like a feminine form but are adverbs/invariable
NOT_GENDERED = {"afară", "acasă", "gata", "aici", "acolo", "bine", "rău", "ok",
                "totuși", "mâine", "astăzi", "ziua", "seara", "dimineața", "doar",
                "una", "nimica", "foarte", "prea", "încă", "deja", "cam", "tot",
                "mai", "super", "puțin",
                # function words ending in -ă: prepositions/conjunctions
                "că", "să", "lângă", "până", "după", "fără", "contra", "asupra",
                "deasupra", "dedesubtul", "împotriva", "datorită", "mulțumită"}
VOCATIVE = re.compile(rf"(?<!\bo )(?<!\bO )\b(dragă mea|draga mea|prietenă|prieteno|"
                      rf"campioană|campioano|iubito|scumpo|eroino)\b", re.I)


def _masc_of_pair(a: str, b: str) -> str | None:
    """The masculine of two forms of one word ('pregătit','pregătită'), or
    None if they're different words."""
    for m, f in ((a, b), (b, a)):
        if f.lower().endswith(("ă", "a")) and not m.lower().endswith(("ă", "a")):
            stem = f[:-1]
            if m.lower() == stem.lower() or (len(stem) > 3 and m.lower().startswith(stem[:-1].lower())
                                             and len(m) - len(stem) <= 1):
                return m
    return None


def masculine(text: str) -> tuple[str, list[str]]:
    """-> (masculine text, notes on what changed)."""
    notes = []

    def suf(m):
        notes.append(f"{m.group(0)} -> {m.group(1)}")
        return m.group(1)
    out = SUFFIX_ALT.sub(suf, text)

    def pair(m):
        masc = _masc_of_pair(m.group(1), m.group(2))
        if masc is None:
            return m.group(0)          # two different words: an alternative, keep
        notes.append(f"{m.group(0)} -> {masc}")
        return masc
    out = PAIR_ALT.sub(pair, out)
    return out, notes


def review_reasons(text: str) -> list[str]:
    """Possible unmarked feminine forms aimed at the reader - for a human."""
    why = []
    for m in READER.finditer(text):
        w = m.group(2)
        if w.lower() not in NOT_GENDERED and FEM_END.search(w):
            why.append(f"'{m.group(0)}' may be feminine for the reader")
    for m in VOCATIVE.finditer(text):
        why.append(f"feminine form of address '{m.group(0)}'")
    return why


def _s(v) -> str:
    return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False) if v else ""


def load(path: Path) -> list[dict]:
    """-> [{dialogPath, row, field, en, ro}]"""
    items = []
    if path.suffix == ".json":
        bundle = json.loads(path.read_text(encoding="utf-8"))
        for n in bundle["nodes"]:
            for field, key in (("text", "textByLang"), ("answers", "answerOptionsByLang")):
                by = n.get(key) or {}
                ro = _s(by.get("ro-RO"))
                if ro.strip():
                    items.append({"dialogPath": n.get("dialogPath", ""), "row": n["order"],
                                  "field": field, "en": _s(by.get("en-GB")), "ro": ro})
    else:
        for r in csv.DictReader(path.open(encoding="utf-8")):
            if (r.get("ro-RO") or "").strip():
                items.append({"dialogPath": r["pool"],
                              "row": r.get("variantIndex") or r.get("order", ""),
                              "field": "text", "en": r.get("en-GB", ""), "ro": r["ro-RO"]})
    return items


def resolve(name: str) -> Path:
    for cand in (Path(name), DATA_DIR / name, EXPORTS / name):
        if cand.is_file():
            return cand
    sys.exit(f"not found: {name}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="export .json or an r_ CSV (table / generated)")
    ap.add_argument("--out-csv")
    ap.add_argument("--report")
    args = ap.parse_args()

    src = resolve(args.input)
    rows, changed, review = [], [], []
    for it in load(src):
        masc, notes = masculine(it["ro"])
        why = review_reasons(masc)
        row = {"dialogPath": it["dialogPath"], "row": it["row"], "field": it["field"],
               "en-GB": it["en"], "ro-RO": it["ro"], "ro-RO masculine": masc,
               "changed": "yes" if masc != it["ro"] else "", "review": "; ".join(why)}
        rows.append(row)
        if masc != it["ro"]:
            changed.append((row, notes))
        if why:
            review.append(row)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = Path(args.out_csv) if args.out_csv else DATA_DIR / f"masculine_{src.stem}.csv"
    report = Path(args.report) if args.report else DATA_DIR / f"masculine_{src.stem}.md"
    with out_csv.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["dialogPath"])
        w.writeheader()
        w.writerows(rows)

    esc = lambda s: str(s).replace("|", "\\|").replace("\n", " ⏎ ")
    md = [f"# Masculine ro-RO: {src.name}", "",
          f"{len(rows)} ro-RO texts checked (message text + answer options; commands "
          f"skipped). **{len(changed)} changed** by the deterministic rules; "
          f"**{len(review)} for review** (possible unmarked feminine forms aimed at "
          f"the reader - never changed automatically). Full table: `{out_csv.name}`.",
          "", "## Changed", ""]
    if changed:
        md += ["| dialog | row | field | change | masculine text |", "|---|---|---|---|---|"]
        for r, notes in changed:
            md.append(f"| {esc(r['dialogPath'])} | {r['row']} | {r['field']} | "
                      f"{esc(', '.join(notes))} | {esc(r['ro-RO masculine'])} |")
    else:
        md.append("Nothing.")
    md += ["", "## For review", ""]
    if review:
        md += ["| dialog | row | field | why | ro-RO |", "|---|---|---|---|---|"]
        for r in review:
            md.append(f"| {esc(r['dialogPath'])} | {r['row']} | {r['field']} | "
                      f"{esc(r['review'])} | {esc(r['ro-RO masculine'])} |")
    else:
        md.append("Nothing.")
    report.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"{len(rows)} texts, {len(changed)} changed, {len(review)} for review -> "
          f"{out_csv} + {report}")


if __name__ == "__main__":
    main()
