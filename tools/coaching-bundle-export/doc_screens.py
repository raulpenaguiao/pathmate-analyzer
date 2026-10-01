"""Annotated screenshots of every PMCP editor, for the editor documentation.

Raul, 2026-10-01 (top priority): screenshot each editor and state, label
every control, and put a RED box on everything whose meaning is unknown.
alex-sandbox ONLY (asserted by exact name). Nothing is saved: an editor's
only dismiss button, 'Close', commits, so every editor is discarded with a
page reload (which ends the PMCP session) and a re-login via start_pmcp.sh.

    .venv/bin/python doc_screens.py [VIEW ...]     (default: all views)

Writes docs/pmcp-ui/screens/<NN>-<view>.png plus <NN>-<view>.md (the legend:
number -> control caption; red boxes -> the open question). The red-box
list is UNKNOWN below, taken from Raul's notes (docs/pmcp-ui/raul-2026-10-01/)
and the Simone email draft.
"""
from __future__ import annotations

import asyncio
import json
import re
import subprocess
import sys
from pathlib import Path

from playwright.async_api import async_playwright

import _browser_lock as BL
import _dialogs_nav as DN
import _menu_nav as M
import _pmcp_safety as S
import _report_fetch as RF
import _rules_nav as R
import _variables_nav as V

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = REPO / "docs" / "pmcp-ui" / "screens"
CDP = "http://127.0.0.1:9222"
SANDBOX = "ALEX v01 zum Ausprobieren"   # alex-sandbox, the ONLY coaching touched

# control-text substring -> the open question (a red box)
UNKNOWN = [
    ("Mark case as solved", "What does 'mark case as solved' do, and where is a 'case' visible?"),
    ("Finish coaching", "What happens to the participant when the coaching is finished by a rule?"),
    ("participantNextMicroDialogIdentifier", "Why is this variable shown even when 'start micro dialog' is unticked?"),
    ("DOES NOT answer", "When do 'does NOT answer' rules apply? The tab stays disabled in every state we tried."),
    ("DOES answer", "When do 'does answer' rules apply? The tab stays disabled in every state we tried."),
    ("handled as not answered", "What happens when this time runs out (default 4 h)? Does it apply to dialog starts?"),
    ("Update transition point", "What is a transition point, and what does updating it do?"),
    ("Update participant to newer coaching", "What does moving a participant to a newer coaching involve?"),
    ("Assigned units to reset", "What are 'units', and what does resetting them do?"),
    ("Cascade to other dialog", "Difference between CASCADE and JUMP to another dialog?"),
    ("Jump to other dialog", "Difference between JUMP and CASCADE to another dialog?"),
    ("answer can be cancelled", "What does 'cancel' mean for the participant (no value is set)?"),
    ("sticky in the client", "What does 'sticky in the client' mean?"),
    ("deactivates and remembers", "Exact semantics of deactivating and remembering open questions?"),
    ("recalls former deactivated questions from last", "Which questions are recalled, from which deactivation?"),
    ("most recent still filled", "What is a 'still filled' deactivation?"),
    ("clears the current dialog cascade", "What is a dialog cascade, and what does clearing it do?"),
    ("clears all dialog cascades", "Difference to clearing the current cascade?"),
    ("will not be cleared on clear all", "What is protected from 'clear all', and when does clear-all happen?"),
    ("blocks the micro dialog", "Exact blocking behaviour: until answered, or also until 'unanswered'?"),
    ("Event identifier", "What are event identifiers (format, where are they defined)?"),
    ("Identifier", "What is an identifier used for, and where is it referenced?"),
    ("PRIVACY SETTING", "What do the privacy settings (private / ...) change?"),
    ("Switch Privacy", "What do the privacy settings change?"),
    ("ACCESS SETTING", "Meaning of the access levels: internal / externally readable / manageable by service?"),
    ("Switch Access", "Meaning of the access levels?"),
    ("AUTO SYNC", "What is synchronised, and with what?"),
    ("Switch Auto Sync", "What is synchronised, and with what?"),
    ("SENSITIVE DATA", "What does marking a variable as sensitive change?"),
    ("Switch Sensitiv", "What does marking a variable as sensitive change?"),
]

ANNOTATE_JS = r"""
([unknown, rootSel, minLeft, minTop]) => {
  document.querySelectorAll('.wd-anno').forEach(e => e.remove());
  const root = rootSel ? [...document.querySelectorAll(rootSel)].pop() : document.body;
  if (!root) return null;
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const sel = '.v-checkbox, .v-filterselect, .v-slider, .v-textfield, .v-textarea, '
            + '.v-button, .v-tabsheet-tabitemcell, .v-caption, .v-label, .v-optiongroup, '
            + '.v-table-caption-container, .v-tree-node[aria-level="1"] > .v-tree-node-caption';
  const seen = new Set(), items = [];
  root.querySelectorAll(sel).forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) return;
    if (r.left < (minLeft || 0) || r.top < (minTop || 0)) return;   // app navigation
    let text = norm(el.textContent) || norm((el.querySelector('input') || {}).value);
    if (!text && el.classList.contains('v-filterselect')) text = '(dropdown)';
    if (!text || text.length > 600) return;
    const key = text + '@' + Math.round(r.top / 6);
    if (seen.has(key)) return; seen.add(key);
    const dis = el.classList.contains('v-disabled') || !!el.closest('.v-disabled');
    let q = unknown.find(([sub]) => text.toLowerCase().includes(sub.toLowerCase()));
    // a rule at the TOP of the Rules tree that is not one of the 4 sections
    if (!q && el.classList.contains('v-tree-node-caption') && !/^Execution on /.test(text))
      q = ['', 'Rule OUTSIDE the 4 execution sections: does PMCP ever run it? Should this be allowed?'];
    items.push({el, r, text, dis, q: q ? q[1] : null,
                kind: el.classList.contains('v-tree-node-caption') ? 'v-rule' : el.classList.contains('v-table-caption-container') ? 'v-column'
                  : [...el.classList].find(c => /^v-(checkbox|filterselect|slider|textfield|textarea|button|tabsheet-tabitemcell|caption|label|optiongroup)$/.test(c))});
  });
  items.sort((a, b) => a.r.top - b.r.top || a.r.left - b.r.left);
  const legend = [];
  items.forEach((it, k) => {
    const n = k + 1;
    const badge = document.createElement('div');
    badge.className = 'wd-anno';
    badge.textContent = n;
    Object.assign(badge.style, {position: 'fixed', left: (it.r.left - 2) + 'px', top: (it.r.top - 9) + 'px',
      background: it.q ? '#d00' : '#1565c0', color: '#fff', font: 'bold 10px sans-serif',
      padding: '0 3px', borderRadius: '7px', zIndex: 2147483647, pointerEvents: 'none'});
    document.body.appendChild(badge);
    if (it.q) {
      const box = document.createElement('div');
      box.className = 'wd-anno';
      Object.assign(box.style, {position: 'fixed', left: (it.r.left - 2) + 'px', top: (it.r.top - 1) + 'px',
        width: (it.r.width + 4) + 'px', height: (it.r.height + 2) + 'px', border: '2px solid #e00',
        boxSizing: 'border-box',
        zIndex: 2147483646, pointerEvents: 'none'});
      document.body.appendChild(box);
    }
    legend.push({n, kind: (it.kind || '').replace('v-', ''), text: it.text.length > 160 ? it.text.slice(0, 157) + '...' : it.text, disabled: it.dis, question: it.q});
  });
  const rr = root.getBoundingClientRect();
  return {legend, clip: {x: Math.max(0, rr.left - 12), y: Math.max(0, rr.top - 12),
                         width: rr.width + 24, height: rr.height + 24}};
}
"""


async def relogin_sandbox(page) -> None:
    """Discard any open editor (reload drops it unsaved), log in again,
    re-open alex-sandbox. Never Close: it commits."""
    await page.reload()
    await page.wait_for_timeout(3000)
    if await page.locator("input[type=password]").count() or await S.session_expired(page):
        subprocess.run([str(REPO / "tools" / "start_pmcp.sh")], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        await page.wait_for_timeout(2000)
    for attempt in range(3):   # the app may still be loading right after a login
        if await RF.enter_edit_view(page, SANDBOX):
            break
        await page.wait_for_timeout(3000)
    else:
        raise SystemExit("could not re-open alex-sandbox")
    await guard(page)


async def guard(page) -> None:
    name = await S.current_coaching_name(page)
    if name != SANDBOX:
        raise SystemExit(f"REFUSED: on {name!r}, not alex-sandbox")


async def shot(page, nn: int, view: str, title: str, root_sel: str | None, note: str = "") -> None:
    await page.wait_for_timeout(600)
    # full-page views: skip the app's own navigation (left sidebar, header, tab bar)
    min_left, min_top = (0, 0) if root_sel else (225, 150)
    res = await page.evaluate(ANNOTATE_JS, [UNKNOWN, root_sel, min_left, min_top])
    if not res:
        print(f"  ! {view}: nothing to annotate ({root_sel})")
        return
    png = OUT / f"{nn:02d}-{view}.png"
    # never full_page: it resizes the page and the overlay boxes drift off
    await page.screenshot(path=str(png), clip=res["clip"] if root_sel else None)
    await page.evaluate("() => document.querySelectorAll('.wd-anno').forEach(e => e.remove())")
    reds = [x for x in res["legend"] if x["question"]]
    lines = [f"# {nn:02d} {title}", "", f"![{title}]({png.name})", "",
             f"alex-sandbox, captured by doc_screens.py. {note}".strip(), "",
             "Blue numbers label each control; **red boxes** mark controls whose meaning is unknown.", "",
             "| # | control | caption | greyed out | open question |", "|---|---|---|---|---|"]
    for x in res["legend"]:
        lines.append(f"| {x['n']} | {x['kind']} | {x['text'].replace('|', '/')} | "
                     f"{'yes' if x['disabled'] else ''} | {x['question'] or ''} |")
    (OUT / f"{nn:02d}-{view}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  {png.name}: {len(res['legend'])} controls, {len(reds)} red boxes")


# --------------------------------------------------------------------------- views

async def view_rule_editor(page):
    """A sender rule's 'Edit rule:' window: default, then each action box ticked."""
    assert await R.ensure_rules_tree(page)
    await R.expand_all(page)
    nodes = (await R.dump_tree(page))[0]["nodes"]
    senders = [r for r in R.build_rule_tree(nodes) if r["kind"] == "sender"
               and r["section"] != R.OUTSIDE_SECTIONS]
    target = senders[0]
    if not await R.open_rule_modal(page, 0, target["treeIndex"]):
        raise SystemExit("rule editor did not open")
    await shot(page, 10, "rule-editor-default", "Rule editor (sender rule, as is)", ".v-window",
               f"Rule: {target['caption'][:80]}")
    win = page.locator(".v-window").last
    boxes = win.locator(".v-checkbox")
    labels = [await boxes.nth(i).inner_text() for i in range(await boxes.count())]
    for k, lab in enumerate(labels[:6]):
        cb = win.locator(".v-checkbox", has_text=lab).first
        await cb.locator("label").first.click()
        await shot(page, 11 + k, f"rule-editor-tick{k + 1}",
                   f"Rule editor with '{lab.strip()[:50]}' toggled", ".v-window",
                   "Toggled for the screenshot only; discarded by reload, nothing saved.")
        await cb.locator("label").first.click()
    for tab_name in ("DOES answer", "DOES NOT answer"):
        tab = win.locator(".v-tabsheet-tabitemcell", has_text=tab_name)
        if await tab.count():
            try:
                await tab.first.click(timeout=3000)
            except Exception:  # noqa: BLE001
                pass
    await relogin_sandbox(page)


async def view_message_editor(page):
    """A message's editor: full, additional settings in the answer and the
    no-answer state, and the answer-type list."""
    await M.navigate_and_select(page, ["START"])
    await M.wait_round_trip(page)
    if not await DN.open_row_editor(page, 1):
        raise SystemExit("message editor did not open")
    win = page.locator(".v-window").last
    await shot(page, 20, "message-editor", "Message editor (full)", ".v-window")
    await DN.reveal_additional_settings(page, win)
    await shot(page, 21, "message-additional-settings-a", "Message editor: additional settings (as is)", ".v-window")
    exp = win.locator(".v-checkbox", has_text="expects to be answered").first
    if await exp.count():
        await exp.locator("label").first.click()
        await page.wait_for_timeout(800)
        await shot(page, 22, "message-additional-settings-b",
                   "Message editor: additional settings, 'expects to be answered' toggled", ".v-window",
                   "Toggled for the screenshot only; discarded by reload.")
    # the lower part of the (scrolling) editor: not-answered time, message rules
    await page.evaluate("""() => { const w = [...document.querySelectorAll('.v-window')].pop();
        const sc = [...w.querySelectorAll('*')].filter(e => { const st = getComputedStyle(e);
            return /(auto|scroll)/.test(st.overflowY) && e.scrollHeight > e.clientHeight + 5; })
          .sort((a, b) => b.clientHeight - a.clientHeight)[0];
        if (sc) sc.scrollTop = sc.scrollHeight; }""")
    await page.wait_for_timeout(600)
    await shot(page, 24, "message-editor-bottom", "Message editor (scrolled to the bottom)", ".v-window",
               "Same editor as 22, scrolled down.")
    # answer types: the dropdown on the 'Answer type:' row
    fs = await page.evaluate("""() => { const w = [...document.querySelectorAll('.v-window')].pop();
        const lab = [...w.querySelectorAll('.v-label, .v-caption')].find(e => /^Answer type:/.test(e.textContent.trim()));
        if (!lab) return -1; lab.scrollIntoView({block: 'center'});
        const ly = lab.getBoundingClientRect().top;
        const all = [...w.querySelectorAll('.v-filterselect')];
        let best = -1, bd = 1e9;
        all.forEach((f, i) => { const d = Math.abs(f.getBoundingClientRect().top - ly); if (d < bd) { bd = d; best = i; } });
        return bd < 30 ? best : -1; }""")
    if fs >= 0:
        sel = win.locator(".v-filterselect").nth(fs)
        await sel.locator(".v-filterselect-button").click()
        await page.wait_for_timeout(1200)
        status = """() => ((document.querySelector('.v-filterselect-suggestpopup .v-filterselect-status')
                            || {}).textContent || '').trim()"""
        # page with the KEYBOARD: clicking the popup's page arrows closes it.
        # PageUp/PageDown only move the highlight; nothing is selected.
        for _ in range(8):
            if (await page.evaluate(status)).startswith("1-"):
                break
            await page.keyboard.press("PageUp")
            await page.wait_for_timeout(500)
        types, k = [], 0
        while True:
            k += 1
            types += await page.evaluate("""() => [...document.querySelectorAll(
                '.v-filterselect-suggestpopup .gwt-MenuItem')].map(e => e.textContent.trim())""")
            await shot(page, 23, f"answer-types-p{k}", f"Answer types (dropdown page {k})",
                       ".v-filterselect-suggestpopup", "Opened only to read the list; nothing selected.")
            st = await page.evaluate(status)
            m = re.match(r"(\d+)-(\d+)/(\d+)", st)
            if not m or int(m.group(2)) >= int(m.group(3)) or k > 8:
                break
            await page.keyboard.press("PageDown")
            await page.wait_for_timeout(700)
        (OUT / "23-answer-types.md").write_text(
            "# 23 Answer types (all pages)\n\n" + "\n".join(
                f"{i + 1}. {t or '(blank: no answer type)'}" for i, t in enumerate(types)) + "\n",
            encoding="utf-8")
        print(f"  answer types: {len(types)} entries over {k} page(s)")
        await page.keyboard.press("Escape")
    else:
        print("  ! no 'Answer type:' dropdown found")
    await relogin_sandbox(page)


async def view_decision_point(page):
    """A decision point's editor and one of its rules' menu."""
    await M.navigate_and_select(page, ["START"])
    await M.wait_round_trip(page)
    rows = await page.evaluate("() => [...document.querySelectorAll('.v-table-body tr')]"
                               ".map(tr => tr.textContent)")
    k = next(i for i, t in enumerate(rows) if "DECISION POINT" in t)
    if not await DN.open_row_editor(page, k):
        raise SystemExit("DP editor did not open")
    dpw = page.locator(".v-window").last
    await shot(page, 30, "decision-point", "Decision point editor", ".v-window")
    await DN.dp_expand_all(page, dpw)
    if await DN.dp_open_branch_rule(page, dpw, 0):
        await shot(page, 31, "decision-point-rule", "Decision point: a rule's editor", ".v-window")
    await relogin_sandbox(page)


async def view_event(page):
    """The 'New Event' window (opened, never closed: reload discards it)."""
    await M.navigate_and_select(page, ["START"])
    await M.wait_round_trip(page)
    btn = page.locator(".v-button-caption", has_text="New Event").first
    await btn.click()
    await page.wait_for_timeout(1500)
    await shot(page, 40, "event-new", "Event editor ('New Event', not saved)", ".v-window",
               "Opened with New Event and discarded by reload: no event was created.")
    await relogin_sandbox(page)


async def view_variables(page):
    """Variables tab: the table and the per-variable buttons."""
    assert await V.open_variables_tab(page)
    await page.wait_for_timeout(1500)
    await shot(page, 50, "variables", "Variables tab", None)


async def view_rules_tab(page):
    """The Rules tab itself, collapsed: the 4 sections and anything outside them."""
    assert await R.ensure_rules_tree(page)
    await page.wait_for_timeout(1000)
    await shot(page, 5, "rules-tab", "Rules tab (collapsed): the 4 sections and rules outside them", None)


VIEWS = {"rules-tab": view_rules_tab, "rule": view_rule_editor, "message": view_message_editor,
         "decision-point": view_decision_point, "event": view_event, "variables": view_variables}


async def main() -> None:
    want = sys.argv[1:] or list(VIEWS)
    OUT.mkdir(parents=True, exist_ok=True)
    BL.claim("warden:doc_screens")
    async with async_playwright() as pw:
        b = await pw.chromium.connect_over_cdp(CDP)
        page = next(p for p in b.contexts[0].pages if "pathmate" in (p.url or ""))
        await M.neutralize_tooltips(page)
        assert await RF.enter_edit_view(page, SANDBOX), "could not open alex-sandbox"
        await guard(page)
        for v in want:
            print(f"--- {v}")
            await guard(page)
            await VIEWS[v](page)
        await RF.back_to_list(page)


if __name__ == "__main__":
    asyncio.run(main())
