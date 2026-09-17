"""PMCP's declarative rule mini-language: the fixed English operator phrases
(``calculated value equals``, ``create text but result is always true``, ...)
and the logic to split a rule expression into structured fields.

Shared between `app/coaching_sim.py` (evaluates a *pre-split* expression
against a variable dict — the HTML-derived `Rule.raw_expr` never carries a
comment prefix, that's already a separate HTML column) and
`tools/coaching-bundle-export/_rules_nav.py` (parses the live Rules-tree
caption, which — unlike the HTML export — concatenates the rule's Comment
and its expression into one string: `"<comment>: <expr>"`, comment
optional). Kept in one place per `docs/stage4_chat_engine_plan.md` Phase 0,
instead of drifting into two copies of the same phrase list.

No Flask / app-package dependency beyond the package name itself, so a
standalone script can import it by putting the repo root on `sys.path`
(see `tools/coaching-bundle-export/enrich_bundle.py` for the pattern).
"""
from __future__ import annotations

ARROW = "→"


def _num(value) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return 0.0


CMP_OPS = {
    "calculated value equals": lambda a, b: _num(a) == _num(b),
    "calculated value not equals": lambda a, b: _num(a) != _num(b),
    "calculated value is bigger or equal than": lambda a, b: _num(a) >= _num(b),
    "calculated value is smaller or equal than": lambda a, b: _num(a) <= _num(b),
    "calculated value is bigger than": lambda a, b: _num(a) > _num(b),
    "calculated value is smaller than": lambda a, b: _num(a) < _num(b),
    "text value equals": lambda a, b: str(a).strip() == str(b).strip(),
    "text value not equals": lambda a, b: str(a).strip() != str(b).strip(),
}
ASSIGN_TRUE = ("calculate value but result is always true", "create text but result is always true")
ASSIGN_FALSE = ("calculate value but result is always false", "create text but result is always false")
DATE_DIFF = "calculate date difference in days and always true"
DATE_ADD = "calculate new date by adding y days and always true"

# every recognised phrase, longest first — a longer phrase that happens to
# share a prefix with a shorter one (none currently do, but stay defensive)
# must be tried first so `find_earliest_phrase` can't return the shorter,
# wrong match at the same start index.
_ALL_PHRASES = sorted(
    [*CMP_OPS, *ASSIGN_TRUE, *ASSIGN_FALSE, DATE_DIFF, DATE_ADD],
    key=len, reverse=True,
)


def parse_expr(expr: str) -> dict:
    """-> {kind: 'cmp'|'assign'|'date_diff'|'date_add'|'unknown', ...}.
    `expr` must already be comment-free (a bare rule expression) — for a
    Rules-tree caption that still has its comment prefix, call
    `parse_rule_caption` instead."""
    target = None
    left = expr
    if ARROW in expr:
        left, target = expr.rsplit(ARROW, 1)
        left, target = left.strip(), target.strip()

    for phrase in CMP_OPS:
        if phrase in left:
            lhs, rhs = left.split(phrase, 1)
            return {"kind": "cmp", "phrase": phrase, "lhs": lhs.strip(), "rhs": rhs.strip()}

    if DATE_DIFF in left:
        lhs, rhs = left.split(DATE_DIFF, 1)
        return {"kind": "date_diff", "lhs": lhs.strip(), "rhs": rhs.strip(), "target": target}
    if DATE_ADD in left:
        lhs, rhs = left.split(DATE_ADD, 1)
        return {"kind": "date_add", "lhs": lhs.strip(), "rhs": rhs.strip(), "target": target}

    for phrase in ASSIGN_TRUE:
        if phrase in left:
            return {"kind": "assign", "lhs": left.split(phrase, 1)[0].strip(),
                    "target": target, "result": True}
    for phrase in ASSIGN_FALSE:
        if phrase in left:
            return {"kind": "assign", "lhs": left.split(phrase, 1)[0].strip(),
                    "target": target, "result": False}

    return {"kind": "unknown", "raw": expr}


def find_earliest_phrase(text: str) -> tuple[str, int, int] | None:
    """The earliest-starting known operator phrase in `text`, as
    (phrase, start, end). None if no recognised phrase occurs at all (a JS
    snippet, a regex rule, or any other free-form condition PMCP allows
    outside this declarative mini-language)."""
    best: tuple[str, int, int] | None = None
    for phrase in _ALL_PHRASES:
        i = text.find(phrase)
        if i != -1 and (best is None or i < best[1]):
            best = (phrase, i, i + len(phrase))
    return best


def parse_rule_caption(caption: str) -> dict:
    """Split a live Rules-tree caption (`"<comment>: <expr>"`, comment
    optional) into `{comment, raw, ...parse_expr(expr) fields...}`.

    The comment/expression boundary is the LAST `": "` before the earliest
    recognised operator phrase — using the last (not first) ": " is what
    keeps this correct even if the comment text itself contains a colon
    (observed live comments only ever put one ": " right before the
    expression, but nothing stops an author writing "Note: see ticket 4:
    ..." as a comment). No recognised phrase at all -> `kind: "unsupported"`
    with an empty comment; we can't safely guess the split point without
    one, and there's nothing to disambiguate a JS-snippet/regex condition
    into `lhs`/`rhs` anyway."""
    hit = find_earliest_phrase(caption)
    if hit is None:
        return {"comment": "", "kind": "unsupported", "raw": caption}
    _, phrase_start, _ = hit
    pre = caption[:phrase_start]
    sep = pre.rfind(": ")
    if sep == -1:
        comment, rest = "", caption
    else:
        comment, rest = pre[:sep].strip(), caption[sep + 2:]
    parsed = parse_expr(rest)
    parsed["comment"] = comment
    parsed["raw"] = caption
    return parsed
