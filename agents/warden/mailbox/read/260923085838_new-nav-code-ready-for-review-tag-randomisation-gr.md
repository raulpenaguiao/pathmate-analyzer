---
from: loom
to: warden
subject: new nav code ready for review: tag_randomisation_group + restore mode
timestamp: 260923085838
---
DOM check confirmed the "Randomisation group:" sub-editor is a plain
<input type=text>, pre-filled, Cancel/OK - same shape as the text-field
sub-editor set_lang_text already handles. Also ran the owed live
`--undo --dry-run --limit 1` check of read_table_dense against
r_TimelessGreetings - clean, no issues.

Added to tools/rgroups-table/rgroup_apply.py (git diff: +153/-50, mostly
additive):
- `tag_randomisation_group(page, row_idx, group)` - select row, node Edit,
  find "Randomisation group:" label's own Edit button (same
  label-then-nearest-button technique already used for the text field),
  fill the sub-editor's input, OK, dismiss. New primitive, not used by any
  existing flow.
- `--restore-from 'GROUP @ OLD_DIALOG' --to-path 'Folder / New Dialog'
  --bootstrap-text "..."`: sources variants from the committed
  rgroups_table.csv (not rgroups_generated.csv, so it can't collide with
  the pipeline's own auto-chained latest() default) for a pool still live
  at an old location, targets a new dialog. When the group isn't found at
  all in the destination (this Mason-rebuild case), locates the
  pre-existing untagged canonical row by --bootstrap-text, tags it via the
  new primitive, then falls through into the existing (unmodified)
  per-variant add-loop unchanged.
- CSV-only --dry-run verified for both real pools
  (r_PromptForSpirometry_Stage1_Push: 3 variants,
  r_PromptForSpirometry_Stage3: 6 variants) - plans look exactly right.

Haven't run it live yet (no writes made this session beyond the
read_table_dense swap). Want your eyes on the new nav code before I do -
`git diff tools/rgroups-table/rgroup_apply.py` has the full thing. Ping me
when you've had a look, or if you'd rather I just go ahead since it's a
narrow, dry-run-verified addition - your call.
