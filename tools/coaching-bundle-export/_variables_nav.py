"""Variables tab sweep for export_coaching.py.

Added ALEX v02 Phase 3.7 follow-up (2026-09-12): neither export_coaching.py
nor the analyzer's own "Variables" tab (app/coaching_model.py) ever read
PMCP's actual Variables tab - both only *infer* variable existence
indirectly from `$name` references inside captured rule/dialog text. That
means a variable that exists but isn't referenced anywhere yet (a real risk
right after a variable-creation pass like create_variables.py, before the
rules that use it are built) is invisible to the export, and even a
referenced variable's actual current value is never captured, only the fact
that it's mentioned.

`open_variables_tab()` below is lifted from create_variables.py (same
mechanics, confirmed live 2026-09-11) rather than duplicated by hand.

Table columns confirmed live 2026-09-12: Variable Name (unlabeled first
column), Variable Value, Privacy Setting, Access Setting, Auto Sync,
Multilingual Array Variable, Sensitive Data.

IMPORTANT sweep-correctness finding (2026-09-12): the Variables table is
virtualized AND server-paginated. A "jump straight to scrollTop =
scrollHeight" sweep (create_variables.py's original all_variable_names, and
this project's earlier micro-dialogs-node sweep pattern) looks like it
converges - scrollHeight and the seen-count both stop growing - but a big
jump lets the virtualizer skip rendering whole windows of rows in between,
which then never get grabbed. Confirmed on the live 'ALEX v01 zum
Ausprobieren' Variables tab: a big-jump sweep found only 84-85 of the
coaching's real 334 variables (~25% coverage) despite reporting a stable
result; $currentDaySlot, $spiroReminderEngaged and every other Phase-3
spirometry variable were silently among the missing 75%, confirmed present
only by a targeted scroll-search for each name individually. Scrolling in
small increments (~1 viewport height per step, waiting out the
'.v-loading-indicator' each time) instead of one jump fixed it: 334/334,
reproducibly. This is the same *class* of virtualization gap already
documented for the Micro Dialogs node sweep (`missingRows`) - here it's
silent instead of reported, so there is no equivalent 'MISSING [...]'
signal to notice the gap from; don't trust a stable scrollHeight alone as
proof of full coverage on any PMCP `.v-table`.
"""
from __future__ import annotations

COLS = ["Variable Name", "Variable Value", "Privacy Setting", "Access Setting",
        "Auto Sync", "Multilingual Array Variable", "Sensitive Data"]


async def on_variables_view(page) -> bool:
    body = await page.evaluate("() => document.body.innerText")
    return "VARIABLE NAME" in body


async def open_variables_tab(page) -> bool:
    """Confirmed live 2026-09-11: a plain get_by_text('Variables', exact=True)
    also matches the left-nav 'Documentation' context-help button (its
    second line just reads 'Variables') and opens a blocking help iframe
    instead of the real section tab - never use it. Check content first
    (idempotent - the `role=tab` attribute on the tab bar isn't reliably
    present once already on the view) and only click if not already there."""
    if await on_variables_view(page):
        return True
    tab = page.locator(".v-captiontext", has_text="Variables").filter(
        has_not=page.locator("xpath=ancestor::*[contains(@class,'sub-button')]"))
    if not await tab.count():
        return False
    await tab.first.click()
    await page.wait_for_timeout(1200)
    return await on_variables_view(page)


# Incremental-scroll sweep - see the module docstring for why a straight
# jump-to-bottom sweep silently undercounts by ~75% on this table.
SWEEP_ROWS_JS = r"""
async () => {
  const t = document.querySelector('.v-table');
  if (!t) return [];
  const scroller = t.querySelector('.v-table-body-wrapper') || t.querySelector('.v-scrollable');
  const seen = new Map();
  const grab = () => t.querySelectorAll('.v-table-body tr').forEach(tr => {
    const cells = [...tr.querySelectorAll('.v-table-cell-wrapper')].map(c => c.textContent.trim());
    if (cells.length) seen.set(cells[0], cells);
  });
  const waitForLoad = async (maxMs) => {
    const start = Date.now();
    await new Promise(r => setTimeout(r, 100));
    while (document.querySelector('.v-loading-indicator') && Date.now() - start < maxMs) {
      await new Promise(r => setTimeout(r, 100));
    }
    await new Promise(r => setTimeout(r, 100));
  };
  scroller.scrollTop = 0; await waitForLoad(4000); grab();
  const step = Math.max(scroller.clientHeight * 1.0, 200);
  let stableAtBottom = 0, guard = 0;
  while (guard++ < 300) {
    scroller.scrollTop = scroller.scrollTop + step;
    await waitForLoad(4000);
    grab();
    const atBottom = scroller.scrollTop + scroller.clientHeight >= scroller.scrollHeight - 2;
    if (atBottom) {
      stableAtBottom++;
      if (stableAtBottom >= 3) break;
    } else {
      stableAtBottom = 0;
    }
  }
  scroller.scrollTop = 0; await new Promise(r => setTimeout(r, 150));
  return [...seen.values()];
}
"""


async def sweep_variables(page) -> list[dict]:
    """Full read sweep of the Variables tab. Caller must already be on the
    Variables view (open_variables_tab). Returns one dict per variable,
    keyed by COLS, sorted by name."""
    rows = await page.evaluate(SWEEP_ROWS_JS)
    out = []
    for cells in rows:
        row = {COLS[j]: (cells[j] if j < len(cells) else "") for j in range(len(COLS))}
        out.append(row)
    out.sort(key=lambda r: r["Variable Name"].lower())
    return out
