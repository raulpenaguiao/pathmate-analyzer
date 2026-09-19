# rgroup_apply.py: --apply dropped (writes by default), new --undo mode

2026-09-18. Follow-up to today's earlier r_ pipeline work. Three changes,
all live-tested including a full add → undo → re-add round trip.

## Why

The old default (dry run unless `--apply`) turned out to be less useful
than it looked: the CSV-only dry run never touches the browser, so it
can't reflect the script's own idempotency check (which only runs live,
per variant, against the actual pool) — it always printed "ADD" for
everything, even variants already present. The real safety net was never
the dry-run default; it's the live idempotency check itself (see below),
which runs the same way whether or not a flag gates it. Given that,
requiring an extra flag to get real behavior was just friction, and it was
inconsistent with `rgroup_expand.py`, which already writes by default and
uses `--dry-run` as the explicit opt-in for preview-only.

## How idempotency actually works (the question that motivated this)

Not a separate log or manifest — `run_apply()` re-derives it live, every
time: before adding a variant, it navigates to the variant's pool, reads
the CURRENT table, and checks whether any row already in that
randomisation group contains a matching prefix (first 18 characters, since
the grid truncates long text) of the candidate's en-GB text. If a match is
adjacent to its group siblings, it's skipped ("already in the pool, row
K"); if present but not adjacent, it repositions rather than re-adding.
This is why re-running the exact same `rgroups_generated_*.csv` twice was
always safe, even before today's change.

## What changed

- **`--apply` removed. Writing is now the default** for the main add flow
  and for `--dedup`. `--dry-run` is the new opt-in for preview-only
  (add/dedup: no browser at all, just the CSV-derived plan; this
  limitation — CSV-only, can't see live state — is now documented
  explicitly in the script's own dry-run message, not left implicit).
- **`--md` in `rgroup_report.py`, for reference since it came up**: writes
  a human-readable markdown summary (default `rgroups_report.md`, fixed
  name) alongside the CSV — one row per `r_` group with message/dialog
  counts and text-resolution status, the same shape as
  `docs/randomisation_groups_*`. Separate from and not affected by
  today's CSV timestamping change.
- **New `--undo` mode**: the literal inverse of the add flow. For every
  `ok` variant in the target CSV (same `--pool`/`--limit` scoping as
  adding), find the matching live row (identical prefix-match logic) and
  **delete** it instead of adding it — reusing the same navigate/read/
  select/confirm machinery the add flow and `--dedup` already had.
  Reports "not found" (not an error) for a variant that was never applied
  or already removed, so it's safe to run against a partially-applied CSV.
  `--dry-run --undo` does a live read and reports what *would* be deleted
  without clicking Delete - unlike the add flow's dry run, this one is
  live because presence can only be known live.

## Verified live: full add → undo → re-add round trip

Using the real `r_TimelessGreetings` variant from today's earlier
end-to-end test:
1. `--undo --dry-run --limit 1` → correctly identified row 8 without
   touching it.
2. `--undo --limit 1` (real) → deleted row 8, confirmed via `[confirm]`
   popup handling.
3. Independent fresh re-navigation (not the script's own report) →
   confirmed 8 rows, variant genuinely gone.
4. `rgroup_apply.py --limit 1` (real, no flags needed now) → **first two
   attempts failed** with `"no existing row with this group"` despite the
   live DOM data being independently confirmed correct both times (checked
   directly, header index and row content were fine) — an intermittent
   timing flake in this script's own `read_table()`/`TABLE_JS`, not a real
   data problem. Third attempt succeeded outright with no code change.
5. Final independent re-check confirmed the variant restored at row 8,
   matching the pre-test state exactly.

## Not fixed here

`rgroup_apply.py`'s own `TABLE_JS`/`read_table()` (separate from, and not
sharing code with, `_menu_nav.py`'s already-hardened `sweep_table()`) has
the same class of virtualization over-read `_menu_nav.sweep_table()` was
fixed for (returned 11-12 "rows" for an 8-row table, with the extra ones
correctly empty rather than corrupting real data) — harmless here since
the empty trailing rows never matched anything, but combined with today's
observed one-off "row briefly not found" flake, this file's own table
reader would benefit from the same `_trim_trailing_blanks`-style treatment
`_menu_nav.py` already got. Not attempted in this pass - flagging for a
follow-up, not a live problem today beyond one flaky retry.
