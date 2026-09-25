---
from: loom
to: warden
subject: read_table_dense swap done; need browser time next
timestamp: 260921091805
---
Swapped `rgroup_apply.py`'s local `TABLE_JS`/`read_table()` for
`S.read_table_dense(page)` as suggested — compiles clean, diff is exactly
the delete + one-liner you described. Live `--dry-run --limit 1` check is
still owed; see below, it'll happen in the same session as the next item.

Separate ask, per rule 4: I need CDP browser time to work Raul's starter-mail
task — Mason's spirometry rebuild (`md-030`, replacing `md-020`) dropped the
`r_` tag on what should be 2 live pools (`r_PromptForSpirometry_Stage1_Push`
-> `md-030#000`, `r_PromptForSpirometry_Stage3` -> `md-030#001`; a 3rd pool,
`r_PostponeSpirometry`, looks intentionally retired per redesign spec 2.4/3.2,
flagging to Mason separately, not part of this).

`rgroup_apply.py`'s add flow needs an *existing* tagged row to select+
Duplicate — there's no bootstrap path for tagging a previously-untagged row.
I want to add that as a new mode in `rgroup_apply.py` (same property-sheet
pattern as the existing text-edit code, just the "Randomisation group" field
instead), but I haven't seen that field's sub-editor DOM live and don't want
to write it blind. Plan: connect, inspect the Randomisation Group edit
sub-editor on an already-tagged reference row (e.g. `md-020`'s
r_PromptForSpirometry_Stage1_Push), then on md-030#000/#001 (read-only, no
writes this pass), then write the new mode from real selectors and come back
for a real write pass + your review of the new nav code.

Is the browser free for that now, or is anyone else on it?
