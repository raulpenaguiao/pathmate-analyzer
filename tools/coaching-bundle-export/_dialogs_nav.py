"""Shared navigation helpers for the Micro Dialogs tab, built live 2026-09-16
while rebuilding medication dialogs for ALEX v02 phase 4.1.4. Mirrors the
retry/verify discipline established in _rules_nav.py for the Rules tab.

Key platform mechanics confirmed live this session:
- Row selection: click cell index 0 (TYPE icon) and retry until the row's
  class contains "v-selected". NEVER click cell index 1 (COMMENT) - it
  immediately DESELECTS the row.
- The row-toolbar "Edit" button is a DIFFERENT element from the 4
  dialog-level "Edit" buttons beside Comment/Identifier/Variable Prefix/
  Assigned Units - always find it by position (below the .v-table), never
  by a fixed index.
- Message editor's push/cascade/timeout checkboxes live behind
  "Show additional settings" (a <label>).
- Bilingual popups ("Edit text...", "Edit answer options...") share one
  textarea across "English (GB)"/"Romanian (RO)" tab buttons.
- A DECISION POINT holds a FLAT list of sibling "branches" (NOT a nested
  tree, despite using .v-tree markup for the list) - confirmed via the
  JSON export's raw `branches` array. Each branch is either a pure
  condition gate (Rule[x]/operator/Term[y], no Store-result-variable) or
  an unconditional assignment (Rule[x]="1" or "0", operator="calculate
  value but result is always true", Store-result-variable=target var) -
  exactly the same two leaf shapes as the Rules tab. "New" while the
  decision point's own window is focused (nothing inside its list
  selected) appends a new branch at the end of its own list.
- A branch's own "Edit rule:" popup (opened via the list's 3rd Edit
  button after selecting a branch) has: Comment / Rule[x] / operator /
  Term[y] / Store result to variable / 3 mutually-exclusive checkboxes
  ("Leave this decision point...", "Stop this complete micro dialog...",
  "Update participant...") / Assigned units / 4 jump filterselects
  ("Cascade to other dialog if TRUE", "Jump to other dialog if TRUE",
  "Jump to dialog message if TRUE", "Jump to dialog message if FALSE").
  This nested rule popup opens as its own STACKED .v-window (window[-1]),
  on top of the decision point's own window - target .v-window.last for
  its own fields, never .first.
"""
from __future__ import annotations

import _rules_nav as R


async def select_dialog_row(page, row_index: int, attempts: int = 8) -> bool:
    row = page.locator(".v-table-body tr").nth(row_index)
    cell = row.locator(".v-table-cell-wrapper").nth(0)
    for _ in range(attempts):
        await cell.click()
        await page.wait_for_timeout(350)
        cls = await row.evaluate("(e) => e.className")
        if "v-selected" in cls:
            return True
    return False


async def _enabled_row_button(page, label: str):
    buttons = page.locator(".v-button-caption", has_text=label)
    n = await buttons.count()
    table = page.locator(".v-table").last
    tbox = await table.bounding_box()
    table_bottom = tbox["y"] + tbox["height"] if tbox else 0
    for i in range(n):
        box = await buttons.nth(i).bounding_box()
        if box and box["y"] >= table_bottom - 5:
            return buttons.nth(i)
    return buttons.last


async def open_row_editor(page, row_index: int) -> bool:
    if not await select_dialog_row(page, row_index):
        return False
    btn = await _enabled_row_button(page, "Edit")
    await R._click_retry(page, btn)
    await page.wait_for_timeout(1000)
    return await page.locator(".v-window").count() > 0


async def click_new_row_button(page, label: str) -> bool:
    """Click New Message / New Decision Point / New Event at the row
    toolbar level (dialog page, not inside any modal)."""
    btn = page.locator(".v-button-caption", has_text=label).first
    ok = await R._click_retry(page, btn)
    await page.wait_for_timeout(1000)
    return ok


async def set_plain_field(page, window, edit_index: int, text: str) -> bool:
    edits = window.locator(".v-button-caption", has_text="Edit")
    if not await R._click_retry(page, edits.nth(edit_index)):
        return False
    await page.wait_for_timeout(600)
    popup = page.locator(".v-window").last
    inp = popup.locator("textarea, input[type=text]").first
    await inp.click()
    await page.keyboard.press("Control+A")
    await page.keyboard.press("Delete")
    await page.wait_for_timeout(150)
    await page.keyboard.type(text, delay=8)
    await page.wait_for_timeout(200)
    ok_btn = popup.locator(".v-button-caption", has_text="OK")
    ok = await R._click_retry(page, ok_btn)
    await page.wait_for_timeout(600)
    return ok


async def set_bilingual_field(page, window, edit_index: int, en_text: str, ro_text: str) -> bool:
    edits = window.locator(".v-button-caption", has_text="Edit")
    if not await R._click_retry(page, edits.nth(edit_index)):
        return False
    await page.wait_for_timeout(600)
    popup = page.locator(".v-window").last

    en_tab = popup.locator(".v-button-caption", has_text="English (GB)")
    ro_tab = popup.locator(".v-button-caption", has_text="Romanian (RO)")
    ta = popup.locator("textarea").first

    await R._click_retry(page, en_tab)
    await page.wait_for_timeout(300)
    await ta.click()
    await page.keyboard.press("Control+A")
    await page.keyboard.press("Delete")
    await page.wait_for_timeout(150)
    await page.keyboard.type(en_text, delay=6)
    await page.wait_for_timeout(200)

    await R._click_retry(page, ro_tab)
    await page.wait_for_timeout(300)
    await ta.click()
    await page.keyboard.press("Control+A")
    await page.keyboard.press("Delete")
    await page.wait_for_timeout(150)
    await page.keyboard.type(ro_text, delay=6)
    await page.wait_for_timeout(200)

    ok_btn = popup.locator(".v-button-caption", has_text="OK")
    ok = await R._click_retry(page, ok_btn)
    await page.wait_for_timeout(600)
    return ok


async def set_checkbox_by_label(page, window, label_substr: str, checked: bool) -> bool:
    cb = window.locator(f"text={label_substr}").locator(
        "xpath=preceding-sibling::input[@type='checkbox'][1]")
    if not await cb.count():
        return False
    now = await cb.is_checked()
    if now == checked:
        return True
    try:
        await cb.click(force=True, timeout=5000)
    except Exception:
        return False
    await page.wait_for_timeout(300)
    return (await cb.is_checked()) == checked


async def reveal_additional_settings(page, window) -> bool:
    label = window.locator("text=Show additional settings")
    if not await label.count():
        return False
    await label.click(force=True)
    await page.wait_for_timeout(500)
    return True


async def close_editor(page, window) -> bool:
    close_btn = window.locator(".v-button-caption", has_text="Close").last
    ok = await R._click_retry(page, close_btn)
    await page.wait_for_timeout(800)
    return ok


# ---------------------------------------------------------------------------
# Decision-point branch helpers
# ---------------------------------------------------------------------------

async def dp_branch_count(window) -> int:
    return await window.locator(".v-tree-node").count()


async def dp_add_branch(page, dp_window) -> bool:
    """Click New at the decision-point level to append a fresh branch."""
    new_btn = dp_window.locator(".v-button-caption", has_text="New").first
    ok = await R._click_retry(page, new_btn)
    await page.wait_for_timeout(700)
    return ok


async def dp_select_branch(page, dp_window, branch_index: int, attempts: int = 6) -> bool:
    node = dp_window.locator(".v-tree-node").nth(branch_index)
    cap = node.locator(":scope > .v-tree-node-caption")
    for _ in range(attempts):
        try:
            await cap.click(position={"x": 20, "y": 8}, timeout=3000)
        except Exception:
            pass
        await page.wait_for_timeout(300)
        cls = await node.get_attribute("class") or ""
        sel = await cap.get_attribute("class") or ""
        if "selected" in sel or "v-tree-node-selected" in cls:
            return True
    return False


async def dp_open_branch_rule(page, dp_window, branch_index: int) -> bool:
    if not await dp_select_branch(page, dp_window, branch_index):
        return False
    edits = dp_window.locator(".v-button-caption", has_text="Edit")
    n = await edits.count()
    if not await R._click_retry(page, edits.nth(n - 1)):
        return False
    await page.wait_for_timeout(900)
    return await page.locator(".v-window").count() > (1 if dp_window else 0)


async def set_branch_operator(page, operator_text: str, verify: bool = True) -> bool:
    """Same as _rules_nav.set_rule_operator, but targets .v-window.LAST
    instead of .first - required here because a decision-point branch's
    'Create/Edit rule:' popup is a SECOND, stacked window on top of the
    decision point's own window, and set_rule_operator's .first would grab
    the wrong (outer) window and hang waiting for a filterselect that
    doesn't match on it."""
    for attempt in range(2 if verify else 1):
        w = page.locator(".v-window").last
        fs = w.locator(".v-filterselect:not(.v-disabled)").first
        if not await R._click_retry(page, fs):
            continue
        await page.wait_for_timeout(500)
        popup = page.locator(".v-filterselect-suggestpopup")
        if not await popup.count():
            continue
        opt = popup.get_by_text(operator_text, exact=False).first
        if not await opt.count():
            return False
        if not await R._click_retry(page, opt):
            continue
        await page.wait_for_timeout(500)
        if not verify:
            return True
        now = await fs.inner_text() if await fs.count() else ""
        if operator_text in now or now == "":
            # confirmed live 2026-09-16: this particular filterselect's
            # innerText reads back EMPTY even on a fully successful
            # selection (visually confirmed via screenshot) - unlike the
            # Rules tab's own operator filterselect. Don't treat empty as
            # failure here; only a MISMATCHED non-empty value is real.
            return True
    return False


async def dp_add_branch_and_get_window(page, dp_window):
    """Click New on the decision point to open a fresh 'Create rule:'
    popup (stacked window) and return it directly - a branch does NOT
    appear in the decision point's own list until this popup is filled
    and Closed (same 'New opens a Create modal' mechanic as the Rules
    tab)."""
    new_btn = dp_window.locator(".v-button-caption", has_text="New").first
    ok = await R._click_retry(page, new_btn)
    await page.wait_for_timeout(900)
    return page.locator(".v-window").last if ok else None


async def set_jump_to_message(page, rule_window, filterselect_index: int, target_comment: str) -> bool:
    """Set 'Jump to dialog message if TRUE/FALSE' (filterselect index 3
    or 4 respectively in the branch rule form) to the row whose comment
    matches target_comment. Small single-dialog list - matched by the
    comment substring shown in the option's preview text."""
    fs_list = rule_window.locator(".v-filterselect:not(.v-disabled)")
    fs = fs_list.nth(filterselect_index)
    if not await R._click_retry(page, fs):
        return False
    await page.wait_for_timeout(600)
    popup = page.locator(".v-filterselect-suggestpopup")
    if not await popup.count():
        return False
    opt = popup.get_by_text(target_comment, exact=False).first
    if not await opt.count():
        return False
    ok = await R._click_retry(page, opt)
    await page.wait_for_timeout(500)
    return ok


async def set_branch_fields(page, rule_window, comment: str, rule_x: str,
                             operator: str | None, term_y: str | None,
                             store_var: str | None = None,
                             stop_micro_dialog: bool = False) -> dict:
    """Fill a branch's 'Edit rule:' popup fields. Returns per-field ok
    dict for the caller to verify/retry."""
    result = {}
    edits = rule_window.locator(".v-button-caption", has_text="Edit")
    # order confirmed live: 0=Comment, 1=Rule[x], 2=Term[y], 3=Store result
    # var, 4=Assigned units. Operator is a separate filterselect (index 0
    # among filterselects, same convention as the Rules tab).
    result["comment"] = await set_plain_field(page, rule_window, 0, comment)
    result["x"] = await set_plain_field(page, rule_window, 1, rule_x)
    if operator is not None:
        result["operator"] = await set_branch_operator(page, operator)
    if term_y is not None:
        result["y"] = await set_plain_field(page, rule_window, 2, term_y)
    if store_var is not None:
        result["store_var"] = await set_plain_field(page, rule_window, 3, store_var)
    if stop_micro_dialog:
        result["stop"] = await set_checkbox_by_label(
            page, rule_window, "Stop this complete micro dialog after this rule if rule result is TRUE", True)
    return result


# ---------------------------------------------------------------------------
# Read-only helpers (2026-09-25): resolve decision-branch jump targets live
# ---------------------------------------------------------------------------

async def dp_expand_all(page, dp_window, max_rounds: int = 8) -> int:
    """Expand every node of a decision point's rule tree. Child rules (AND
    logic, see enrich._nest_branches) are only rendered once their parent is
    expanded, so a collapsed tree hides branches that the Report lists
    (confirmed live 2026-09-25 on Hello's "Jump to the end of the dialog":
    1 node shown, 2 after expanding). Returns the final node count, in the
    same pre-order as the Report's branch list."""
    count = await dp_branch_count(dp_window)
    for _ in range(max_rounds):
        for i in range(count):
            if await dp_select_branch(page, dp_window, i):
                await page.keyboard.press("ArrowRight")
                await page.wait_for_timeout(350)
        new = await dp_branch_count(dp_window)
        if new == count:
            return count
        count = new
    return count


JUMP_POPUP_JS = r"""
() => {
  const p = document.querySelector('.v-filterselect-suggestpopup');
  if (!p) return null;
  const items = [...p.querySelectorAll('.gwt-MenuItem')]
    .map(e => ({ text: e.textContent.replace(/\s+/g, ' ').trim(),
                 selected: e.className.includes('gwt-MenuItem-selected') }));
  const st = (p.querySelector('.v-filterselect-status') || {}).textContent || '';
  const m = st.match(/(\d+)-(\d+)\/(\d+)/);
  return { items, first: m ? +m[1] : 1, total: m ? +m[3] : items.length };
}
"""


async def read_jump_selection(page, rule_window, label: str) -> dict | None:
    """Open the 'Jump to dialog message if TRUE/FALSE' dropdown (`label`) of
    a branch's 'Edit rule:' window READ-ONLY, report the highlighted entry,
    and close it again with Escape (no selection is made).

    The dropdown lists the dialog's messages in order as '[comment] text',
    with the current target highlighted. The displayed value alone is useless
    for anchor messages (every empty one shows '(not set)'), but the
    highlighted entry's POSITION identifies the exact message. Returns
    {'value', 'text', 'index'} where index is the 0-based position among
    real entries (the leading blank 'no target' entry excluded), or None
    when nothing is selected."""
    labels = rule_window.locator(".v-label, .v-caption")
    fss = rule_window.locator(".v-filterselect")
    n = await fss.count()
    # the filterselect sits on the same row as its label
    lab = labels.filter(has_text=label).first
    if not await lab.count():
        return None
    lbox = await lab.bounding_box()
    fs = None
    for i in range(n):
        box = await fss.nth(i).bounding_box()
        if box and lbox and abs(box["y"] - lbox["y"]) < 20:
            fs = fss.nth(i)
            break
    if fs is None:
        return None
    value = await fs.locator(".v-filterselect-input").input_value()
    if not value.strip():
        return {"value": "", "text": None, "index": None}
    await fs.locator(".v-filterselect-button").click()
    await page.wait_for_timeout(1200)
    pop = await page.evaluate(JUMP_POPUP_JS)
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(400)
    if not pop:
        return None
    sel = next((k for k, it in enumerate(pop["items"]) if it["selected"]), None)
    if sel is None:
        return None
    # the first page starts with the blank 'no target' entry
    blank = 1 if pop["first"] == 1 and pop["items"] and not pop["items"][0]["text"] else 0
    index = (pop["first"] - 1) + sel - blank
    return {"value": value, "text": pop["items"][sel]["text"], "index": index}
