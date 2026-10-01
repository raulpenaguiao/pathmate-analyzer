"""Read-only probe (Mason, 2026-10-01): which "Edit rule:" fields un-grey per
action checkbox, and the exact captions of the answer tabs and of a message
editor's additional settings. Sandbox coaching only. NEVER clicks Close
(it commits); every change is discarded with page.reload().

Run from tools/coaching-bundle-export/:
  ../../.venv/bin/python probe_rule_modal_options.py rule  OUT_DIR
  ../../.venv/bin/python probe_rule_modal_options.py msg   OUT_DIR
(re-login with tools/start_pmcp.sh --headless between the two, since reload
ends the PMCP session)
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.getcwd())
from playwright.async_api import async_playwright  # noqa: E402

import _browser_lock as BL  # noqa: E402
import _pmcp_safety as P  # noqa: E402
import _report_fetch as R  # noqa: E402
import _rules_nav as RN  # noqa: E402

CDP = os.environ.get("PMCP_CDP", "http://127.0.0.1:9222")
SANDBOX = "Minimal Coaching for Development 2 for Raul"
MODE, OUT = sys.argv[1], Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

STATE_JS = """() => {
  const w = [...document.querySelectorAll('.v-window')].pop();
  if (!w) return null;
  const out = [];
  w.querySelectorAll('.v-checkbox, .v-filterselect, .v-slider, .v-textfield, .v-button, .v-tabsheet-tabitemcell, .v-caption, .v-label').forEach(el => {
    const txt = (el.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 160);
    const inp = el.querySelector('input');
    const dis = el.classList.contains('v-disabled') || !!el.closest('.v-disabled')
      || (inp ? inp.disabled : false) || el.getAttribute('aria-disabled') === 'true';
    const chk = inp && inp.type === 'checkbox' ? inp.checked : null;
    out.push({kind: [...el.classList].find(c => c.startsWith('v-')), text: txt, disabled: dis, checked: chk});
  });
  return out;
}"""


async def go_sandbox(page) -> None:
    if not await R.back_to_list(page):
        nav = page.get_by_text("Coachings", exact=True).first
        await nav.click()
        await page.wait_for_timeout(2500)
    ok = await R.enter_edit_view(page, SANDBOX)
    if not ok:
        raise SystemExit("could not enter sandbox edit view")
    name = await P.assert_expected_coaching(page, SANDBOX)
    print("in coaching:", name)


async def rule_mode(page) -> None:
    if not await RN.ensure_rules_tree(page):
        raise SystemExit("rules tree not visible")
    trees = await RN.dump_tree(page)
    nodes = trees[0]["nodes"]
    json.dump([{k: n[k] for k in ("i", "depth", "caption", "visible", "expanded")} for n in nodes],
              open(OUT / "tree.json", "w"), ensure_ascii=False, indent=1)
    pick = next((n for n in nodes if n["depth"] >= 1 and n["visible"]), None)
    if pick is None:   # all collapsed: expand the first section root
        root = next(n for n in nodes if n["depth"] == 0 and n["visible"])
        await RN.click_expander(page, 0, root["i"])
        await page.wait_for_timeout(1500)
        nodes = (await RN.dump_tree(page))[0]["nodes"]
        pick = next((n for n in nodes if n["depth"] >= 1 and n["visible"]), None)
    if pick is None:
        raise SystemExit("no rule node found under a section")
    print("opening rule:", pick["caption"][:100])
    dump = await RN.open_rule_modal(page, 0, pick["i"])
    if not dump:
        raise SystemExit("modal did not open")
    # open_rule_modal leaves us on the DOES NOT answer tab; record it first
    await page.screenshot(path=str(OUT / "00_does_not_answer_tab.png"))
    res = {"rule": pick.get("caption"), "doesNotTab": await page.evaluate(STATE_JS)}
    tab = page.locator(".v-window .v-tabsheet-tabitemcell", has_text="DOES answer").first
    if await tab.count():
        await tab.click()
        await page.wait_for_timeout(500)
        await page.screenshot(path=str(OUT / "01_does_answer_tab.png"))
        res["doesTab"] = await page.evaluate(STATE_JS)
    res["baseline"] = await page.evaluate(STATE_JS)
    await page.screenshot(path=str(OUT / "02_baseline.png"))
    labels = ["Send message if rule result is TRUE",
              "Start micro dialog if rule result is TRUE",
              "Mark case as solved",
              "finish coaching for this participant"]
    for k, lab in enumerate(labels):
        cb = page.locator(".v-window .v-checkbox", has_text=lab).first
        inp = cb.locator("input[type=checkbox]")
        was = await inp.is_checked()
        await cb.locator("label").first.click()
        await page.wait_for_timeout(700)
        res[f"ticked_{k}"] = {"label": lab, "wasChecked": was, "state": await page.evaluate(STATE_JS)}
        await page.screenshot(path=str(OUT / f"1{k}_ticked.png"))
        await cb.locator("label").first.click()   # untick again (still discarded by reload)
        await page.wait_for_timeout(500)
    json.dump(res, open(OUT / "rule_modal.json", "w"), ensure_ascii=False, indent=1)
    print("DISCARD: reload (never Close)")
    await page.reload()


async def msg_mode(page) -> None:
    import _menu_nav as S
    import _dialogs_nav as D
    await S.ensure_micro_dialogs(page)
    tops = await S.top_items(page)
    print("top dialogs:", tops[:8])
    first = [t for t, _ in tops if t and t != "."][0]
    await S.navigate_and_select(page, [first])
    await page.wait_for_timeout(1200)
    if not await D.open_row_editor(page, 0):
        raise SystemExit("row editor did not open")
    win = page.locator(".v-window").last
    await D.reveal_additional_settings(page, win)
    await page.wait_for_timeout(700)
    await page.screenshot(path=str(OUT / "20_message_editor.png"), full_page=True)
    res = {"dialog": first, "editor": await page.evaluate(STATE_JS)}
    json.dump(res, open(OUT / "message_editor.json", "w"), ensure_ascii=False, indent=1)
    print("DISCARD: reload (never Close)")
    await page.reload()


async def main() -> None:
    BL.claim(f"mason:{MODE}")
    async with async_playwright() as pw:
        b = await pw.chromium.connect_over_cdp(CDP)
        page = b.contexts[0].pages[0]
        await go_sandbox(page)
        await (rule_mode(page) if MODE == "rule" else msg_mode(page))


asyncio.run(main())
