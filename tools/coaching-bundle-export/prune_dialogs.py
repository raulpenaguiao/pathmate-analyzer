"""ALEX v02 redesign, Phase 2 (docs/ALEX_v02_redesign_spec.md 2.4 / 5 /
Appendix A): delete the pile-up-mechanism dialogs and the P4 dev/test
dialogs from the sandbox coaching, via the Micro Dialogs menubar's
dialog-level toolbar ("Delete Dialog" - distinct from the per-row node
toolbar other tools here use; see
autochanges/2026-09-11-alex-v02-phase0-recon.md).

Targets are all TOP-LEVEL menu items.

**Correction, confirmed live 2026-09-11 (see autochanges same-day log):**
"Delete Dialog" on a folder does NOT cascade-delete its children - it
deletes the folder node only and PROMOTES its children to the level above
(here, to top-level). `Attic` and `Controls` were assumed to carry their P4
children down with them; instead their children re-surfaced as new
top-level items after deletion, INCLUDING `📄 dataEdited` - real P3 content
(a personal-data-edited intent handler, not a dev/test dialog) that was
nested under `Controls` and must NOT be deleted. WAVE_2_TARGETS below is
the follow-up cleanup for the dead ones among those promoted children -
always re-check what a folder actually contained before assuming a
delete removes it wholesale.

Safety: calls `_pmcp_safety.assert_expected_coaching()` before any write.
Dry run by default - prints what it would do; `--apply` to actually delete.
`--limit N` caps how many dialogs get deleted in one run (required with
`--apply`), matching the convention in `tools/rgroups-table/rgroup_apply.py`.
`--only NAME` restricts to a single target, for a first controlled test.

Run:
  PMCP_CDP=http://127.0.0.1:9222 .venv/bin/python prune_dialogs.py
  PMCP_CDP=http://127.0.0.1:9222 .venv/bin/python prune_dialogs.py --apply --limit 1 --only "..."
"""
from __future__ import annotations

import argparse
import asyncio
import os
import re

from playwright.async_api import async_playwright

import _menu_nav as S
import _pmcp_safety as safety

CDP = os.environ.get("PMCP_CDP", "http://127.0.0.1:9222")

# top-level-only; see module docstring for why Andreas Test / Test Andreas /
# PLAYGROUND are not listed (nested under Attic / Controls respectively).
TARGETS = [
    "Transition message when interrupting dialog kicks in",
    "Transition message when interrupting dialog has finished",
    "Clearing microdialogs of the day related to spirometry",
    "Attic",
    "⚙️ Controls",
    "☑️ Testing",
    "Testing of gamification concept",
    "Testing of gamification concept II",
    "Testing infocards",
    "Testing Media Objects",
    "Testing questionnaires",
    "Testing of streak concept",
    "Testing REDCap data",
    "🐞 Testing sensor data retrieval",
    "🐞 Testing time line of scheduled periodic events",
]

# follow-up: dead children promoted to top-level when Attic/Controls were
# deleted (see the correction note above). Deliberately excludes
# "📄 dataEdited" (real P3 content, also promoted, must stay).
WAVE_2_TARGETS = [
    "Test dialog for debugging",
    "Andreas Test",
    "Test Andreas",
    "System",
    "Morning greetings + inquire about sleep",
]


async def top_level_items(page, min_expected: int = 40, tries: int = 6) -> list[str]:
    """The widened MenuBar's layout recompute can lag the resize on a cold
    browser (~1s isn't always enough) - poll until the item count looks
    sane rather than trusting one read right after widening."""
    items: list[str] = []
    for _ in range(tries):
        items = await page.locator(".v-menubar.md-menu > .v-menubar-menuitem").all_inner_texts()
        if len(items) >= min_expected:
            return items
        await page.wait_for_timeout(500)
    return items


async def delete_dialog_toolbar_button(page, caption: str):
    handle = await page.evaluate_handle(
        """(cap) => [...document.querySelectorAll('.v-button')].find(bt =>
          ((bt.querySelector('.v-button-caption')||{}).textContent||'').trim() === cap)""",
        caption,
    )
    return handle.as_element() if handle else None


async def accept_confirm_popup(page, timeout_ms: int = 5000) -> bool:
    """Vaadin confirm popups vary in label across this app (Cancel/No/Nein/
    Abbrechen/anulează on the negative side, per rgroup_apply.py's NEG set);
    click whichever button is NOT one of those. Also accepts a native
    confirm() just in case. Returns True if a popup was found and handled."""
    NEG = {"cancel", "no", "abbrechen", "nein", "close", "anulează", "nu"}
    try:
        await page.wait_for_selector(".v-window", timeout=timeout_ms)
    except Exception:  # noqa: BLE001
        return False
    win = page.locator(".v-window").last
    buttons = win.locator(".v-button-caption")
    n = await buttons.count()
    for i in range(n):
        text = (await buttons.nth(i).inner_text()).strip().lower()
        if text and text not in NEG:
            await buttons.nth(i).click()
            await page.wait_for_timeout(600)
            return True
    return False


async def prune_one(page, name: str, apply: bool) -> str:
    items = await top_level_items(page)
    norm = [re.sub(r"\s+", " ", i).strip() for i in items]
    if name not in norm:
        return "NOT FOUND (already gone, or nested/renamed)"
    if not apply:
        return "would delete (dry run)"

    # select it: a plain click on the top-level item selects it without
    # opening its submenu-navigation flow (ensure_micro_dialogs pattern);
    # ensure_micro_dialogs/navigate_and_select are for opening a leaf's
    # table, not selecting a folder for the dialog-level toolbar, so we
    # click the menubar item directly.
    item = page.locator(".v-menubar.md-menu > .v-menubar-menuitem", has_text=name).first
    await item.click()
    await S.wait_round_trip(page)

    btn = await delete_dialog_toolbar_button(page, "Delete Dialog")
    if not btn:
        return "ERROR: 'Delete Dialog' button not found after selecting it"
    await btn.click()
    handled = await accept_confirm_popup(page)
    await S.wait_round_trip(page)

    items_after = await top_level_items(page)
    still_there = name in [re.sub(r"\s+", " ", i).strip() for i in items_after]
    if still_there:
        return f"ERROR: still present after delete (confirm popup handled={handled})"
    return f"deleted (confirm popup handled={handled})"


async def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="actually delete (default: dry run)")
    ap.add_argument("--limit", type=int, help="max dialogs to delete this run (required with --apply)")
    ap.add_argument("--only", help="restrict to one target name, for a controlled first test")
    ap.add_argument("--wave2", action="store_true",
                     help="use WAVE_2_TARGETS (children promoted to top-level "
                          "by wave 1's folder deletes) instead of TARGETS")
    args = ap.parse_args()

    base = WAVE_2_TARGETS if args.wave2 else TARGETS
    targets = [t for t in base if not args.only or t == args.only]
    if args.only and not targets:
        raise SystemExit(f"--only {args.only!r} does not match any TARGETS entry")
    if args.apply and not args.limit:
        raise SystemExit("--apply requires --limit")
    if args.limit:
        targets = targets[: args.limit]

    async with async_playwright() as pw:
        b = await pw.chromium.connect_over_cdp(CDP)
        page = b.contexts[0].pages[0]
        try:
            coaching = await safety.assert_expected_coaching(page)
        except safety.WrongCoachingError as e:
            raise SystemExit(f"refusing to run: {e}")
        print(f"confirmed coaching: {coaching!r}")

        if not await S.ensure_micro_dialogs(page):
            raise SystemExit("Micro Dialogs menubar not on screen - open that view and rerun.")

        cdp = await b.contexts[0].new_cdp_session(page)
        wid = (await cdp.send("Browser.getWindowForTarget"))["windowId"]
        await cdp.send("Browser.setWindowBounds", {"windowId": wid, "bounds": {
            "left": 0, "top": 0, "width": 12000, "height": 1600, "windowState": "normal"}})
        await page.wait_for_timeout(1200)
        try:
            for name in targets:
                result = await prune_one(page, name, args.apply)
                print(f"{'[APPLY]' if args.apply else '[dry-run]'} {name!r}: {result}")
        finally:
            await cdp.send("Browser.setWindowBounds", {"windowId": wid, "bounds": {
                "left": 60, "top": 60, "width": 1400, "height": 1000, "windowState": "normal"}})

        if not args.apply:
            print("\ndry run - pass --apply --limit N to actually delete. Nothing was changed.")


if __name__ == "__main__":
    asyncio.run(main())
