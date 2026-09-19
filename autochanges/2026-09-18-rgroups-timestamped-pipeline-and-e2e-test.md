# r_ pipeline: timestamped filenames + full end-to-end test (export → apply)

2026-09-18. Two things: (1) every stage of the r_ pipeline now embeds the
run's own YYMMDDHHMMSS in its output filename, with each downstream step
defaulting to the most RECENTLY-RUN input, not a fixed name; (2) ran the
whole chain for real — fresh coaching export, report, prepare, a real LLM
call, and a real Playwright write-back — to prove it still works end to
end after the change.

## Timestamped filenames

New shared helper `tools/rgroups-table/_rgroups_files.py`: `now_ts()`
(`YYMMDDHHMMSS`) and `latest(data_dir, prefix, suffix)` (most recent
`{prefix}_*{suffix}` file, sorted as a plain string — the fixed-width
format sorts correctly without touching mtimes).

- `rgroup_report.py` → writes `rgroups_table_<ts>.csv` (was the fixed
  `rgroups_table.csv`). `--md`'s `rgroups_report.md` stays a fixed name on
  purpose — it's the "current deliverable snapshot" doc, not a per-run
  artifact, and wasn't part of what was asked to change.
- `rgroup_prepare.py` → reads the latest `rgroups_table_*.csv`, writes
  `rgroups_requests_<ts>.csv`.
- `rgroup_expand.py` → reads the latest `rgroups_requests_*.csv`, writes
  `rgroups_generated_<ts>.csv` **and** `expand_prompts_<ts>.txt` sharing
  the same run's timestamp (so a generated CSV and its prompt log always
  pair up unambiguously). `expand_raw_failures.txt` stays a single
  fixed-name append-only log across every run — it's a diagnostic
  history, not a per-run artifact, so this one wasn't timestamped.
- `rgroup_apply.py` → reads the latest `rgroups_generated_*.csv`.
- `rgroup_pipeline.sh` → added a `latest_file()` bash helper mirroring
  the Python one; checkpoint messages now print the actual filename each
  step just produced instead of a hardcoded name.

Every script prints which input file it picked ("using X") before
proceeding, so a run's provenance is always visible in its own output,
not just inferable from the filename.

## End-to-end test

1. **Export** (`export_coaching.sh --yes --with-rgroups`): took **11m 11s**
   — my first attempt used a 10-minute timeout and got killed mid-run;
   re-ran with 15 minutes and it completed.

   **Real bug surfaced**: the Micro Dialogs sweep hit the previously-known,
   never-fixed `_menu_nav.py::open_folder_path` failure mode past a
   certain menu size — 30 of 90 menu targets (from item 60 onward) failed
   with `"top item '...' not found"` and were silently dropped. Coherence
   check correctly caught it (`ok = False`): nodesTotal 699 vs baseline
   1049 (**-33%**), messageNodes -35%, decisionNodes -28%. This was a
   "still open" self-check TODO in the progress tracker; today it actually
   caught a real, materially-incomplete export. **This run's
   `coaching_alex-v01-zum-ausprobieren_20260918-103948.json` is known
   incomplete — do not treat it as a reliable full snapshot.**

2. **Report** (via `--with-rgroups`, off the incomplete export above):
   80 r_ groups, 330 messages, 100 pools (91 thin) →
   `rgroups_table_260918105100.csv`. Pool completeness inherits the same
   caveat as the export.

3. **Prepare**: correctly picked up `rgroups_table_260918105100.csv` (not
   any of the stale bare-named files from earlier sessions sitting in the
   same directory) → `rgroups_requests_260918105139.csv`, 91 pools / 725
   variants needed.

4. **Expand**: `--dry-run --limit 1` sanity check, then a real
   `--limit 1` call → 3/3 variants generated for
   `r_TimelessGreetings @ Timeless Greetings` →
   `rgroups_generated_260918105201.csv` + matching `expand_prompts_*.txt`.

5. **Apply**: `--limit 1` dry-run printed the correct plan. The first real
   `--apply --limit 1` attempt failed — `"top '👋 Hello' not found"`,
   the same symptom as the export bug, briefly alarming. **Root cause was
   different and much simpler**: the browser was sitting on the *Rules*
   tab (left over from the export run), and `rgroup_apply.py`'s
   `pick_page()` only picks a page that *already* shows the Micro Dialogs
   menubar — it never switches tabs itself. Manually clicking to the
   Micro Dialogs tab and re-running succeeded: `added=1 skipped=0
   errors=0`, landed at row 8, 0 moves needed. **Verified independently**
   via a fresh `sweep_table()` re-navigation, not just the script's own
   report — row 8 reads exactly `"Hey $participantName! 👋"` /
   `"Hei, $participantName! 👋"`, correctly grouped under
   `r_TimelessGreetings` alongside its 6 existing siblings.

## Open, not decided here

- **`rgroup_apply.py` doesn't ensure the Micro Dialogs tab itself** before
  navigating — a real robustness gap, not just today's test artifact.
  Worth adding an `M.ensure_micro_dialogs(page)` call (already exists,
  used elsewhere) at the top of `run_apply()`.
- **The `_menu_nav.py::open_folder_path` sweep-failure bug is now confirmed
  to also cost real write-back attempts**, not just read sweeps — it
  should move up in priority above being just an export self-check TODO.
- **Stale bare-named files** (`rgroups_table.csv`, `rgroups_requests.csv`,
  `rgroups_generated.csv`, `expand_prompts.txt`) from before this change
  are still sitting in `data/rgroups/` — the new "latest" logic correctly
  ignores them (confirmed live), but they're now orphaned dead weight,
  not cleaned up here.
- One real variant (`r_TimelessGreetings`, "Hey $participantName! 👋") is
  now live in the sandbox from this test — not reverted, since it's a
  legitimate, correctly-generated addition to a genuinely thin pool, not
  test junk.
