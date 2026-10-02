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

import re

import _rules_nav as R


LOCATE_ROW_JS = r"""
([target, scroll]) => {
  const t = document.querySelector('.v-table');
  if (!t) return -1;
  const sc = t.querySelector('.v-table-body-wrapper');
  const trs = [...t.querySelectorAll('.v-table-body tr')];
  const rh = trs[0] ? trs[0].offsetHeight : 24;
  const scrollable = sc.scrollHeight > sc.clientHeight + 4;
  if (!scrollable) return target < trs.length ? target : -1;
  if (scroll) { sc.scrollTop = Math.max(0, target * rh - sc.clientHeight / 3); return -2; }
  const base = sc.getBoundingClientRect().top;
  return trs.findIndex(tr => tr.querySelectorAll('.v-table-cell-wrapper').length &&
    Math.round((tr.getBoundingClientRect().top - base + sc.scrollTop) / rh) === target);
}
"""


async def locate_row(page, row_index: int) -> int:
    """DOM position (nth among `.v-table-body tr`) of dialog row `row_index`,
    scrolling it into the rendered window first. The table is virtualized:
    only the rows near the viewport exist in the DOM, so `tr.nth(row_index)`
    only works for rows near the top (2026-09-25: Welcome rows 77/90 timed out).
    Same index arithmetic as _menu_nav.GRAB_JS. Returns -1 if not found."""
    k = await page.evaluate(LOCATE_ROW_JS, [row_index, False])
    if k >= 0:
        return k
    await page.evaluate(LOCATE_ROW_JS, [row_index, True])
    for _ in range(20):
        await page.wait_for_timeout(250)
        k = await page.evaluate(LOCATE_ROW_JS, [row_index, False])
        if k >= 0:
            return k
    return -1


async def select_dialog_row(page, row_index: int, attempts: int = 8) -> bool:
    k = await locate_row(page, row_index)
    row = page.locator(".v-table-body tr").nth(k if k >= 0 else row_index)
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
    # a fixed 1s missed slow openings ('decision point editor did not
    # open', 2026-09-29 daytime)
    for _ in range(32):
        await page.wait_for_timeout(250)
        if await page.locator(".v-window").count():
            return True
    return False


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


MESSAGE_SETTINGS_JS = r"""
() => {
  const w = [...document.querySelectorAll('.v-window')].pop();
  if (!w) return null;
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const dis = e => e.classList.contains('v-disabled') || !!e.closest('.v-disabled')
    || !!(e.querySelector('input') || {}).disabled;
  const boxes = [...w.querySelectorAll('.v-checkbox')].map(c => ({
    label: norm(c.textContent), checked: !!(c.querySelector('input') || {}).checked, disabled: dis(c)}));
  const ctl = [...w.querySelectorAll('.v-filterselect, .v-textfield, .v-label, .v-caption')].map(e => {
    const r = e.getBoundingClientRect();
    const v = e.classList.contains('v-filterselect') ? (e.querySelector('input') || {}).value
            : e.tagName === 'INPUT' ? e.value : e.textContent;
    return {kind: e.classList.contains('v-filterselect') ? 'select' : 'text', text: norm(v),
            top: Math.round(r.top), left: Math.round(r.left), disabled: dis(e)};
  }).filter(x => x.text || x.kind === 'select');   // an EMPTY select is a value too
  // label text -> the value shown on its row, right of it (or just below it)
  const valueFor = (lab) => {
    const l = ctl.find(x => x.text.startsWith(lab));
    if (!l) return null;
    // never another field's caption ('...:') as a value (2026-10-02: an empty
    // 'Linked intermediate survey' read as 'Message key (must not be unique):')
    const isLabel = x => x.kind === 'text' && /:$/.test(x.text);
    const row = ctl.filter(x => x !== l && !isLabel(x) && x.left > l.left + 40
                                && Math.abs(x.top - l.top) <= 20);
    row.sort((a, b) => (a.kind === 'select' ? 0 : 1) - (b.kind === 'select' ? 0 : 1));
    const best = row[0] || ctl.find(x => x !== l && !isLabel(x) && x.top > l.top
                                       && x.top - l.top <= 40 && Math.abs(x.left - l.left) < 30);
    return best ? {value: best.text, disabled: best.disabled} : null;
  };
  return {
    caption: norm((w.querySelector('.v-window-header') || {}).textContent),
    boxes,
    fields: {
      channel: valueFor('Channel to use for message sending'),
      answerType: valueFor('Answer type'),
      answerOptions: valueFor('Answer options'),
      storeReplyVariable: valueFor('Store message reply to variable'),
      noReplyValue: valueFor('Store the following value in case of no reply'),
      unanswered: valueFor('Minutes after sending until message is handled as unanswered'),
      linkedSurvey: valueFor('Linked intermediate survey'),
      messageKey: valueFor('Message key'),
      randomisationGroup: valueFor('Randomisation group'),
    },
  };
}
"""

# checkbox caption (exact PMCP text, 2026-10-01) -> the export's key
_MSG_BOXES = {
    "This message is a command": "isCommand",
    "This message expects to be answered": "expectsAnswer",
    "answer can be cancelled": "answerCancellable",
    "blocks the micro dialog": "blocksMicroDialog",
    "sticky in the client": "sticky",
    "ONLY a push notification": "pushOnly",
    "ALWAYS announced by a push notification": "alwaysPush",
    "deactivates and remembers all former open questions": "_mem_deactivate",
    "recalls former deactivated questions from last deactivation": "_mem_recall_last",
    "recalls former deactivated questions from most recent still filled": "_mem_recall_filled",
    "clears the current dialog cascade": "_casc_clear_current",
    "clears all dialog cascades": "_casc_clear_all",
    "will not be cleared on clear all": "cascadeProtected",
}


_PUBLIC = {"_mem_deactivate": "memory:deactivate", "_mem_recall_last": "memory:recall_last",
           "_mem_recall_filled": "memory:recall_most_recent_filled",
           "_casc_clear_current": "cascade:clear_current", "_casc_clear_all": "cascade:clear_all"}


def _unanswered_minutes(text: str | None) -> int | None:
    m = re.match(r"(\d+)\s*days?,\s*(\d+)\s*hours?,\s*(\d+)\s*minutes?", text or "")
    return int(m[1]) * 1440 + int(m[2]) * 60 + int(m[3]) if m else None


def parse_message_settings(dump: dict) -> dict:
    """MESSAGE_SETTINGS_JS dump -> the per-message settings record (Mirror's
    coverage map 6.1-5, field names agreed 2026-10-02): booleans per setting,
    `memory` and `cascade` as one enum each, `disabled` = settings greyed."""
    out: dict = {}
    disabled = []
    for b in dump.get("boxes") or []:
        key = next((k for cap, k in _MSG_BOXES.items() if cap in b["label"]), None)
        if not key:
            continue
        out[key] = b["checked"]
        if b["disabled"]:
            disabled.append(_PUBLIC.get(key, key))
    out["memory"] = ("deactivate" if out.pop("_mem_deactivate", False)
                     else "recall_last" if out.pop("_mem_recall_last", False)
                     else "recall_most_recent_filled" if out.pop("_mem_recall_filled", False)
                     else None)
    out["cascade"] = ("clear_current" if out.pop("_casc_clear_current", False)
                      else "clear_all" if out.pop("_casc_clear_all", False) else None)
    for k in ("_mem_deactivate", "_mem_recall_last", "_mem_recall_filled",
              "_casc_clear_current", "_casc_clear_all"):
        out.pop(k, None)
    f = dump.get("fields") or {}
    val = lambda k: ((f.get(k) or {}).get("value") or None)   # noqa: E731
    unset = lambda v: None if v in (None, "(no value set)") else v   # noqa: E731
    for k in ("channel", "answerType", "storeReplyVariable", "noReplyValue",
              "linkedSurvey", "messageKey", "randomisationGroup"):
        out[k] = unset(val(k))
    ut = val("unanswered")
    out["unansweredText"] = ut
    out["unansweredInfinite"] = (ut or "").strip().lower() == "infinite"
    out["unansweredMinutes"] = _unanswered_minutes(ut)
    out["disabled"] = sorted(set(disabled))
    return out


async def read_message_settings(page, row_index: int) -> dict | None:
    """Open the message editor of row `row_index`, reveal its additional
    settings, read everything (parse_message_settings), and close it with
    Close - a NO-OP RE-SAVE (the only dismiss). Callers gate this like the
    other editor modals (never on alex-live without --allow-noop-resaves).
    Returns None if the editor didn't open."""
    if not await open_row_editor(page, row_index):
        return None
    win = page.locator(".v-window").last
    try:
        await reveal_additional_settings(page, win)
        await page.wait_for_timeout(500)
        dump = await page.evaluate(MESSAGE_SETTINGS_JS)
    finally:
        await R.close_windows(page)
    if not dump or "message" not in (dump.get("caption") or "").lower():
        return None
    return parse_message_settings(dump)


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
    # poll: a fixed 0.9s sometimes returned before the stacked 'Edit rule:'
    # window existed, and callers then read the DP window instead (2026-09-29)
    for _ in range(32):
        await page.wait_for_timeout(250)
        if await page.locator(".v-window").count() > (1 if dp_window else 0):
            return True
    return False


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
    fs, best = None, None
    for i in range(n):
        box = await fss.nth(i).bounding_box()
        if not (box and lbox):
            continue
        dy = box["y"] - lbox["y"]
        # same row, or the control placed just below its caption
        if -20 < dy < 60 and (best is None or abs(dy) < best):
            fs, best = fss.nth(i), abs(dy)
    if fs is None and n == 5:
        # known layout (probe 2026-09-25): 0 operator, 1 cascade, 2 jump
        # dialog, 3 jump message if TRUE, 4 jump message if FALSE
        fs = fss.nth(3 if label.endswith("TRUE") else 4)
    if fs is None:
        return None
    value = await fs.locator(".v-filterselect-input").input_value()
    if not value.strip():
        return {"value": "", "text": None, "index": None}
    await fs.locator(".v-filterselect-button").click()
    # the popup fills in after a server round trip; a fixed 1.2s read it
    # before the highlight arrived on ~half the reads (2026-09-29)
    pop = None
    for _ in range(24):
        await page.wait_for_timeout(250)
        pop = await page.evaluate(JUMP_POPUP_JS)
        if pop and any(it["selected"] for it in pop["items"]):
            break
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
