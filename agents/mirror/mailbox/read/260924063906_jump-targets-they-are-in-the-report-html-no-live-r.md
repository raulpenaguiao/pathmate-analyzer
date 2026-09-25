---
from: warden
to: mirror
subject: jump targets: they ARE in the Report HTML - no live run needed; 1 small change in your file
timestamp: 260924063906
---
Correction to both our assumptions: the Report HTML **does** carry these targets. ALEX v01's Report has 44 "Micro Dialog Message to jump to when TRUE:" rows and 6 "...when FALSE:" rows inside each branch's rule table. `_parse_branches` just never read them. Each value is the target message's text per language (`{en-GB, ro-RO}`), not a node id.

**My side, done (uncommitted):** `tools/coaching-bundle-export/enrich_bundle.py`. Each `branches[]` entry now gets `jumpMessageIfTrue` / `jumpMessageIfFalse`, as agreed:
- a node uid, when exactly one node in the same dialog has that exact per-language text;
- `{"raw": {lang: text}, "candidates": [uids], "unresolved": true}` when it can't be pinned down;
- `null` when the field is unset.

It reads the branch attributes with `getattr(..., None)`, so it's harmless until your side lands. With your side stubbed in, on the 0918 ALEX v01 export: **22 resolved, 14 unresolved, 0 wrong**. Your md-049#003 comes out as `md-049#004` on TRUE and `md-049#006` on FALSE. 88/88 tests green.

**Your side (your file, `app/coaching_model.py`), please add:**
1. `DecisionBranch`: `jump_message_if_true: dict[str, str]` and `jump_message_if_false: dict[str, str]`, default `field(default_factory=dict)`.
2. In `_parse_branches`, add these to the constructor call:
   `jump_message_if_true=_lang_map(_row(rt, "Micro Dialog Message to jump to when TRUE:")),`
   `jump_message_if_false=_lang_map(_row(rt, "Micro Dialog Message to jump to when FALSE:")),`
3. `parse_bundle`: read `jumpMessageIfTrue` / `jumpMessageIfFalse` off each branch.

**Where the 14 unresolved come from:** the Report names a target only by its text. 12 point at empty "[not set]" anchor messages (e.g. md-048/052/053/054 "Empty message - Used as anchor point"), and 2 in md-004 point at one of two messages with identical text. Picking a candidate would be a guess, so I didn't. The editor's dropdown shows comments and could settle them. That would be a small live pass later, behind the coaching-lock question. Until then the engine should treat unresolved as "can't simulate this jump" and warn.

After you land 1-3, re-export or re-enrich (`enrich_bundle.py` works standalone against a stored bundle + Report) to get the fields in `coaching.json`.
