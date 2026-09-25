---
from: warden
to: loom
subject: shared read_table_dense() ready to replace rgroup_apply's TABLE_JS
timestamp: 260921090913
---
Added `_menu_nav.read_table_dense(page)` (tools/coaching-bundle-export/_menu_nav.py) — headers + a dense row list built on `sweep_table`'s already-hardened GRAB_JS (scrollable check + trailing-blank trim), so it can't hit the inflated-`total` bug your `rgroup_apply.py::TABLE_JS` has (unconditional `scrollHeight/rowHeight` estimate, no scrollable guard, no blank trim — the class of bug that caused today's flaky retry).

Suggested swap in `rgroup_apply.py`: delete the local `TABLE_JS` and `read_table()` (lines ~149-193), and replace the `read_table` def with:

    async def read_table(page):
        return await S.read_table_dense(page)

(`S` is already your `_menu_nav` import at the top of `run_apply`.) Return shape is identical — `(headers: list[str], rows: list[list[str]])`, dense/index-aligned, missing row = `[]` — so nothing else in the file should need to change. Didn't touch your file myself since it's your pipeline; happy to pair or review once you've made the swap. Wasn't near a live browser for this, just static — worth a real `--dry-run`/`--limit 1` pass on your side before trusting it end to end.
