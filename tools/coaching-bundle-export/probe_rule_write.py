"""Phase-1 recon for ALEX v02: the outer "Edit rule:" modal (read by
`_rules_nav.open_rule_modal`) shows every field read-only, with (per the
Stage-3 dumps) exactly 4 "Edit" buttons before the timeout quick-picks. This
maps each of those 4 buttons to the field-group it actually opens, on one
real sender rule - the spirometry compliance-feedback rule already sampled
harmlessly during the Stage-3 sweep (`rule00`).

Read-only discovery for buttons 1-3 (open -> dump -> Cancel/Close, never
OK/Save). Button 4 (expected: the timing group - hour-to-send +
not-answered-timeout, the two fields Phase 3 needs first) gets one
controlled end-to-end write test: read the current value, re-submit the
*same* value via the real OK/commit path, then read it back to confirm nothing
changed. This is the same class of action already accepted as harmless on
this sandbox (~40 no-op "Edit rule:" re-saves during the Stage-3 sweep) - a
same-value re-save, not a real behavior change - and it's the only way to
confirm the write path actually works before Phase 3 relies on it.

Run: PMCP_CDP=http://127.0.0.1:9222 .venv/bin/python probe_rule_write.py
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent
OUT = HERE / "spike"
OUT.mkdir(exist_ok=True)
CDP = os.environ.get("PMCP_CDP", "http://127.0.0.1:9222")
import _rules_nav as R

TARGET_CAPTION_SUBSTR = "send feedback on poor compliance with lung function"

SUBWINDOW_DUMP_JS = r"""
() => {
  const wins = [...document.querySelectorAll('.v-window')];
  const w = wins[wins.length - 1];
  if (!w) return null;
  return {
    caption: (w.querySelector('.v-window-header') || {}).textContent || '',
    buttons: [...w.querySelectorAll('.v-button-caption')].map(e => e.textContent.trim()),
    visible_text: (w.innerText || '').replace(/\n{2,}/g, '\n'),
  };
}
"""


async def nth_edit_button_in_outer(page, n: int):
    """The n-th (0-indexed) 'Edit' .v-button in the OUTER (first) .v-window,
    in DOM order - the outer modal, not any nested one that may have opened
    since."""
    handle = await page.evaluate_handle(
        """(n) => {
          const wins = [...document.querySelectorAll('.v-window')];
          const w = wins[0];
          if (!w) return null;
          const edits = [...w.querySelectorAll('.v-button')].filter(bt =>
            ((bt.querySelector('.v-button-caption')||{}).textContent||'').trim() === 'Edit');
          return edits[n] || null;
        }""",
        n,
    )
    return handle.as_element() if handle else None


async def cancel_last_modal(page):
    for label in ("Cancel", "Close", "Exit"):
        btn = page.locator(".v-window .v-button-caption", has_text=label)
        if await btn.count():
            await btn.last.click()
            await page.wait_for_timeout(600)
            return True
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(600)
    return False


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.connect_over_cdp(CDP)
        page = b.contexts[0].pages[0]
        if not await R.ensure_rules_tree(page):
            print("Rules .v-tree not on screen - open that tab and rerun.")
            return
        print("expanding tree...")
        info = await R.expand_all(page)
        print("expand_all:", info)

        trees = await R.dump_tree(page)
        idx = next((n["i"] for n in trees[0]["nodes"]
                    if TARGET_CAPTION_SUBSTR in n["caption"]), None)
        if idx is None:
            print(f"caption containing {TARGET_CAPTION_SUBSTR!r} not found")
            return
        print(f"found target rule at index {idx}")

        dump = await R.open_rule_modal(page, 0, idx)
        if not dump:
            print("could not open rule modal")
            return
        print("outer modal buttons:", dump.get("buttons"))
        (OUT / "rulewrite_00_outer.json").write_text(json.dumps(dump, indent=1, ensure_ascii=False))

        # Buttons 0-2: discovery only, cancel after each
        for n in range(3):
            btn = await nth_edit_button_in_outer(page, n)
            if not btn:
                print(f"Edit[{n}]: not found")
                continue
            await btn.click()
            await page.wait_for_timeout(1000)
            sub = await page.evaluate(SUBWINDOW_DUMP_JS)
            (OUT / f"rulewrite_edit{n}.json").write_text(json.dumps(sub, indent=1, ensure_ascii=False))
            print(f"\nEdit[{n}] -> {sub['caption'][:60]!r} buttons={sub['buttons']}")
            print(sub["visible_text"][:800])
            await cancel_last_modal(page)  # never OK/Save here

        # Button 3: expected timing group - controlled same-value write test
        btn = await nth_edit_button_in_outer(page, 3)
        if not btn:
            print("Edit[3]: not found - cannot test the write path")
        else:
            await btn.click()
            await page.wait_for_timeout(1000)
            sub_before = await page.evaluate(SUBWINDOW_DUMP_JS)
            (OUT / "rulewrite_edit3_before.json").write_text(json.dumps(sub_before, indent=1, ensure_ascii=False))
            print(f"\nEdit[3] -> {sub_before['caption'][:60]!r} buttons={sub_before['buttons']}")
            print(sub_before["visible_text"][:800])
            # deliberately DO NOT type anything - commit via OK with the
            # value exactly as loaded, to test the round trip without risk
            ok = page.locator(".v-window .v-button-caption", has_text="OK")
            if await ok.count():
                print("\n(same-value OK-commit test: found an OK button, "
                      "NOT clicking it automatically - reporting only)")
                # Intentionally not clicking OK here: this first pass is
                # discovery-only. A follow-up pass (once the target field's
                # exact selector is known) will do the controlled re-save.
            await cancel_last_modal(page)

        await R.close_windows(page)
        n = await page.evaluate("() => document.querySelectorAll('.v-window').length")
        print(f"\nopen modals remaining: {n}")


if __name__ == "__main__":
    asyncio.run(main())
