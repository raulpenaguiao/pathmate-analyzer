# A shared, virtualization-safe table-read primitive in `_menu_nav.py`

2026-09-21. Follow-up to the wrong-tab guard hardening
(`autochanges/2026-09-18-wrong-tab-guard-hardening.md`). Flagged in this
session's starter mail: `rgroup_apply.py` has its own separate table-reading
JS (`TABLE_JS`/`read_table()`) that reimplements the same scroll-and-
accumulate technique `_menu_nav.sweep_table()` already uses, but without the
hardening `sweep_table` was given — specifically, it always estimates
`total` from `scrollHeight / rowHeight`, even when the table isn't
scrollable at all, and it never trims a trailing run of fully-blank rows.
That's the same "virtualization-over-read" bug class, not yet ported over —
it caused one flaky retry in an earlier end-to-end test.

## What changed

Rather than editing `rgroup_apply.py` directly (it's Loom's file, per
`agents/RULES.md` rule 2 — this agent reviews/supplies the shared library,
it doesn't rewrite another agent's tool), added a new exported primitive to
the shared library itself:

- **`_menu_nav.py`**: `HEADERS_JS` + `read_table_dense(page)` — grabs
  `.v-table` headers, then calls the existing `sweep_table()` (scrollable
  check + `_trim_trailing_blanks` already built in), and converts its
  `{index: cells}` dict into a DENSE `list[list[str]]` (missing index =
  `[]`) — the shape a caller doing positional row access (row *k*, "is the
  row above also in this group") needs, and the same shape
  `rgroup_apply.py`'s own `TABLE_JS` already returned, so it's a drop-in
  replacement.

Mailed Loom (`agents/loom/mailbox/inbox/`) with the exact two-line swap:
delete the local `TABLE_JS`/`read_table()` and replace with a one-line call
to `S.read_table_dense(page)`. Not applied to `rgroup_apply.py` myself —
that edit belongs in Loom's own pipeline file, and per the RULES.md
protocol I supply/review shared navigation code rather than writing
another agent's feature.

## Verified

Static only — `ast.parse()` on `_menu_nav.py` to confirm it's syntactically
valid. No live browser was opened for this (nothing here touches PMCP
directly), so the actual behavioral fix — that `rgroup_apply.py` stops
mis-estimating row counts — isn't confirmed live yet; that's on Loom's
side once they make the swap and re-run their own `--dry-run --limit 1`
end-to-end test.

## Not done here

- Didn't audit any other tool for the same reinvented-table-read pattern —
  this was the one instance flagged. Worth a grep for other ad hoc
  `.v-table` scroll-and-accumulate JS if this class of bug shows up again
  elsewhere.
