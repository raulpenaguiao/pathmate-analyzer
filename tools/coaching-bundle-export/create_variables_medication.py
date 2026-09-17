"""ALEX v02 redesign, Phase 4.1.1 (docs/ALEX_v02_redesign_spec.md §4):
create the new medication-reminder variables, parametrized per dose
i in {1,2,3}, mirroring Phase 3.1's spirometry variables. Reuses existing
$userSetDesired{First,Second,Third}DoseOfControllerMedicationInhalationTime
as doseTime_i - NOT recreated here.

Mechanics identical to create_variables.py (Phase 3.1) - reused directly
rather than duplicated. Safety: _pmcp_safety.assert_expected_coaching()
before any write. Dry run by default; --apply --limit N to actually create.

Run:
  PMCP_CDP=http://127.0.0.1:9222 .venv/bin/python create_variables_medication.py
  PMCP_CDP=http://127.0.0.1:9222 .venv/bin/python create_variables_medication.py --apply --limit 13
"""
from __future__ import annotations

import argparse
import asyncio
import os

from playwright.async_api import async_playwright

import _pmcp_safety as safety
from create_variables import (
    all_variable_names,
    create_one,
    open_variables_tab,
)

CDP = os.environ.get("PMCP_CDP", "http://127.0.0.1:9222")

# name -> initial value. $hyperparameterMedicationGraceMinutes mirrors
# spirometry's own $hyperparameterSpiroGraceMinutes=180 (the spec's example
# value there; medication doesn't specify one, reusing the same default is
# a reasonable starting point for the team to tune, same framing as 3.1).
VARIABLES: dict[str, str] = {
    "$hyperparameterMedicationGraceMinutes": "180",
    "$myMedication_windowEnd_1": "0",
    "$myMedication_done_1": "0",
    "$myMedication_reminderStage_1": "0",
    "$myMedication_engaged_1": "0",
    "$myMedication_windowEnd_2": "0",
    "$myMedication_done_2": "0",
    "$myMedication_reminderStage_2": "0",
    "$myMedication_engaged_2": "0",
    "$myMedication_windowEnd_3": "0",
    "$myMedication_done_3": "0",
    "$myMedication_reminderStage_3": "0",
    "$myMedication_engaged_3": "0",
}


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
