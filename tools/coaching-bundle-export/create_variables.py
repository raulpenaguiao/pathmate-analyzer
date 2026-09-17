"""ALEX v02 redesign, Phase 3 (docs/ALEX_v02_redesign_spec.md 2.3 / 3.1):
create the new coaching variables needed before any new rule can reference
them - the day-slot infrastructure (spec 2.3, a shared prerequisite, not
spirometry-specific) plus spirometry's own new state/hyperparameter
variables (spec 3.1). Reused existing variables ($spiroMesTime,
$spiroMesDone, $totalNumberOfConsecutiveDaysWithoutSpirometry) are NOT
created here.

Mechanics confirmed live 2026-09-11: on the Variables tab, "New" opens an
"Enter name for variable:" popup (Cancel/OK); selecting the new row and
clicking "Edit" opens "Enter new value for variable:" (Cancel/OK) to set its
initial value. Both are real, immediate commits on OK.

Safety: calls `_pmcp_safety.assert_expected_coaching()` before any write.
Dry run by default; `--apply` to actually create. `--limit N` caps how many
variables get created/set in one run (required with `--apply`). `--only
NAME` restricts to one variable, for a first controlled test.

Default hyperparameter values below are reasonable starting points, not
spec-mandated - the spec deliberately calls these "hyperparameters" for the
team to tune. $hyperparameterMorningEndHour=11 matches the existing morning-
greeting rule's own window ("triggered between 6 and 11 am", confirmed in
an earlier probe). $hyperparameterSpiroGraceMinutes=180 is the spec's own
example value (3.1).

Run:
  PMCP_CDP=http://127.0.0.1:9222 .venv/bin/python create_variables.py
  PMCP_CDP=http://127.0.0.1:9222 .venv/bin/python create_variables.py --apply --limit 1 --only "..."
"""
from __future__ import annotations

import argparse
import asyncio
import os

from playwright.async_api import async_playwright

import _pmcp_safety as safety
import _variables_nav as V

CDP = os.environ.get("PMCP_CDP", "http://127.0.0.1:9222")

# name -> initial value (all values are typed as plain text into a single
# "Enter new value" field, matching every existing variable's own format,
# e.g. numbers with no quotes, "[]" for arrays).
VARIABLES: dict[str, str] = {
    # day-slot infrastructure (spec 2.3) - shared, not spirometry-only
    "$currentDaySlot": "morning",
    "$hyperparameterMorningEndHour": "11",
    "$hyperparameterMiddayEndHour": "17",
    "$hyperparameterEveningEndHour": "22",
    # spirometry redesign (spec 3.1)
    "$spiroWindowEnd": "0",
    "$spiroReminderStage": "0",
    "$spiroReminderEngaged": "0",
    "$hyperparameterSpiroGraceMinutes": "180",
}


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


async def all_variable_names(page) -> set[str]:
    """Delegates to _variables_nav.sweep_variables() (the incremental-scroll
    sweep fixed 2026-09-12/14). This function used to have its own
    jump-straight-to-bottom sweep, which looked converged (stable
    scrollHeight + row count) but was confirmed live to silently miss ~75%
    of rows on this exact table — see _variables_nav.py's module docstring.
    A false negative here wouldn't create real duplicate variables (PMCP's
    own "New" flow is the actual gate on that), but it would make
    create_one()'s own post-create existence check report false "not found
    after create" errors on variables that actually did get created —
    switched to the fixed sweep to stop that."""
    rows = await V.sweep_variables(page)
    return {r["Variable Name"] for r in rows}


async def scroll_table_to_row(page, name: str, max_steps: int = 45) -> bool:
    """The Variables table is server-paginated (see all_variable_names) -
    a row created just now, or any row named alphabetically deep in the
    list, is very likely NOT in the currently-rendered DOM window. Scroll
    incrementally (re-checking via a real Playwright locator each step,
    not JS-only) until the target row is actually queryable and clickable."""
    scroller = page.locator(".v-table .v-table-body-wrapper")
    await scroller.evaluate("(el) => { el.scrollTop = 0; }")
    await page.wait_for_timeout(300)
    row = page.locator(".v-table-body tr", has_text=name).first
    for _ in range(max_steps):
        if await row.count():
            return True
        try:
            await scroller.evaluate(
                "(el) => { el.scrollTop += Math.max(el.clientHeight * 0.8, 160); }")
        except Exception:  # noqa: BLE001
            return False
        await page.wait_for_timeout(300)
    return await row.count() > 0


async def _click_retry(page, locator, attempts: int = 4, timeout: int = 8000,
                        settle_ms: int = 1000) -> bool:
    """Retry a click a few times before giving up - the "element is not
    enabled" Vaadin quirk (documented repeatedly across this project) can
    persist for the full default 30s actionability wait, not just
    millisecond-scale flakiness. Confirmed live 2026-09-14: this exact
    function's clicks (all previously bare, no retry) crashed a Phase 4.1
    variable-creation run mid-way, leaving a stray "Enter name for
    variable:" popup open that then desynced the whole Vaadin session
    (see autochanges/2026-09-14-*)."""
    for attempt in range(attempts):
        try:
            await locator.click(timeout=timeout)
            return True
        except Exception:  # noqa: BLE001
            if attempt == attempts - 1:
                return False
            await page.wait_for_timeout(settle_ms)
    return False


async def create_one(page, name: str, value: str, apply: bool, existing: set[str]) -> str:
    if name in existing:
        return "already exists - skipped"
    if not apply:
        return f"would create with value {value!r} (dry run)"

    new_btn = page.locator(".v-button-caption", has_text="New").first
    if not await _click_retry(page, new_btn):
        return "ERROR: 'New' button stuck 'not enabled' - nothing changed"
    await page.wait_for_timeout(700)
    ta = page.locator(".v-window textarea, .v-window input[type=text]").first
    if not await _click_retry(page, ta):
        return "ERROR: name field stuck 'not enabled' - popup left open, close it by hand"
    await ta.fill(name)
    ok = page.locator(".v-window .v-button-caption", has_text="OK").last
    if not await _click_retry(page, ok):
        return "ERROR: name popup's OK stuck 'not enabled' - popup left open, close it by hand"
    await page.wait_for_timeout(1200)

    # select the new row (server-paginated table - scroll to find it) and
    # set its value. Confirmed live: clicking the <tr> only focuses it
    # (adds v-table-focus, NOT v-selected) and leaves the Edit button
    # disabled - must click a cell inside the row instead.
    if not await scroll_table_to_row(page, name):
        return "ERROR: created but row not found to set its value (scrolled full table)"
    row = page.locator(".v-table-body tr", has_text=name).first
    edit_btn = page.locator(".v-button-caption", has_text="Edit").first
    # the cell click occasionally doesn't register selection on the first
    # try (observed live, cause unconfirmed) - retry a few times, checking
    # v-selected rather than assuming one click always lands.
    selected = False
    for _ in range(4):
        await row.locator(".v-table-cell-wrapper").first.click()
        await page.wait_for_timeout(500)
        cls = await row.evaluate("(e) => e.className")
        if "v-selected" in cls:
            selected = True
            break
    if not selected:
        return "ERROR: row found but selection never registered (v-selected)"
    if not await _click_retry(page, edit_btn):
        return "ERROR: created, but 'Edit' stuck 'not enabled' - value not set, fix by hand"
    await page.wait_for_timeout(700)
    val_input = page.locator(".v-window textarea, .v-window input[type=text]").first
    if not await _click_retry(page, val_input):
        return "ERROR: created, but value field stuck 'not enabled' - popup left open, close by hand"
    await val_input.fill(value)
    ok2 = page.locator(".v-window .v-button-caption", has_text="OK").last
    if not await _click_retry(page, ok2):
        return "ERROR: created, but value popup's OK stuck 'not enabled' - popup left open, close by hand"
    await page.wait_for_timeout(1000)

    # Confirm via a targeted scroll-to-row, not a full re-sweep - the fixed
    # all_variable_names() takes ~2 minutes on this table (334 rows), which
    # would turn an N-variable run into N x ~2 minutes if called here per
    # variable (found live 2026-09-14 running Phase 4.1's medication
    # variables). scroll_table_to_row() is the same fast incremental-scroll
    # search already used to find the row for editing above.
    if await scroll_table_to_row(page, name):
        existing.add(name)
        return "created"
    return "ERROR: still not found after create (targeted row search)"


async def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="actually create (default: dry run)")
    ap.add_argument("--limit", type=int, help="max variables to create this run (required with --apply)")
    ap.add_argument("--only", help="restrict to one variable name")
    args = ap.parse_args()

    targets = [(n, v) for n, v in VARIABLES.items() if not args.only or n == args.only]
    if args.only and not targets:
        raise SystemExit(f"--only {args.only!r} does not match any VARIABLES entry")
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

        if not await open_variables_tab(page):
            raise SystemExit("could not open the Variables tab")

        print("sweeping existing variable names (virtualized table, can take a bit)...")
        existing = await all_variable_names(page)
        print(f"{len(existing)} existing variables found")

        for name, value in targets:
            result = await create_one(page, name, value, args.apply, existing)
            print(f"{'[APPLY]' if args.apply else '[dry-run]'} {name!r}: {result}")

        if not args.apply:
            print("\ndry run - pass --apply --limit N to actually create. Nothing was changed.")


if __name__ == "__main__":
    asyncio.run(main())
