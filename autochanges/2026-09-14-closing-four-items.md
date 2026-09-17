# Closing four items: sweep_table bug, pile-up 2a/2b, Raw-tab display, export-tool "Later" items

2026-09-14. User picked four items from the backlog surfaced the day before
to close in one sitting, explicitly asking that everything else be left
"very well documented" instead. This log covers all four plus one new
finding surfaced along the way. See `TASKS.md` for the item-by-item
checkbox state — this is the narrative version.

## 1. `sweep_table()` over-read bug

Investigated the `[51, 7]` delta flagged (but deliberately not accepted)
while regenerating the coherence baseline the day before. The original
hypothesis — stale `scrollHeight` inherited from the much-larger PARENT
dialog navigated away from — turned out to be wrong on inspection: the
real preceding dialog in the actual sweep order is only 6 rows, and a
faithful live repro (full `sweep_table()` scroll-through of the 51-row
parent, then navigate to the child) did not reproduce it — resolved
cleanly to 7 every time. Cross-checking the SAME dialog at the SAME index
in the previous day's otherwise-identical export showed it swept correctly
that day. Conclusion: a genuine intermittent Vaadin timing race, not a
deterministic trigger.

Since it isn't reliably reproducible on demand, fixed the symptom instead:
`_menu_nav.py::sweep_table()` now trims any trailing run of fully-blank
captured rows before returning `total` (`_trim_trailing_blanks()`) — a
real PMCP row always has content in at least one column. Verified against
the actual bad data (51 → 15, exactly the 36 blank rows removed) and
against 3 known-good dialogs (untouched, no regression). Live re-sweep of
the same dialog: `total=7`, matching the Report HTML.

## 2. Pile-up problem 2a/2b

Findings doc: `docs/pileup_findings_ALEX_v01.md`. Done as a data-driven
read of a fresh `export_coaching.sh` capture (Stage 4 Phase 0's now-
structured rule expressions made a systematic cross-check practical)
rather than eyeballing the live Rules tab by hand — 2a's own deliverable
framing ("read the live Rules tab... by hand") is satisfied by a faithful
machine reading of the identical live tree.

Headline finding: only the already-redesigned spirometry rule (`r-113`,
this project's Phase 3) guards against pile-up — it checks
`$participantOpenQuestions==0` before firing. None of the 8 other
DAILY-BASIS reminder senders (medication ×3, sleep-prep, ACQ, educational
content, weekly incentive, poor-compliance feedback) have any equivalent
guard, and DAILY BASIS evaluates every sibling regardless of earlier
results (confirmed: no sender sets the stop-the-run checkbox) — so any
participant whose preference times/due-dates line up is structurally
exposed to the exact pattern Phase 3 just fixed for spirometry. Directly
scopes Phase 4. Separately found a likely real bug unrelated to pile-up:
the dose-2 medication reminder (`r-063`) is nested as a Rules-tree CHILD
of the dose-3 reminder (`r-062`) — confirmed via raw tree structure, not
just caption text — so a 2-dose/day participant (who never sets a dose-3
time) would never get their dose-2 reminder. No live edits made (2a/2b is
diagnostic); both findings feed Phase 4.1.

## 3. Portal Raw tab didn't display `coaching.json`

Root cause: the tab's iframe/download link only ever pointed at the HTML
file — there was no code path for the bundle at all. Added
`GET /coachings/<id>/bundle/raw` and `.../bundle/download`
(`app/routes.py`); the Raw tab now shows an "HTML export / coaching.json"
toggle when a bundle is attached (`app/static/coaching_tabs.js`,
`app/static/style.css`, `app/templates/coaching_view.html`). Verified live
against a spare portal instance on a different port (to avoid touching the
user's own running instance mid-test): toggle renders, `bundle/raw`
returns real JSON with the right content-type, `bundle/download` serves it
named `coaching.json`.

## 4. Export-tool "Later" items

**Auto-fetch the Report HTML** (`_report_fetch.py`, new phase 0 in
`export_coaching.py`). The interesting discovery: clicking "Report" on the
Coachings list does NOT navigate or open a popup — confirmed live,
`context.expect_page()` times out and `context.pages` never grows. It's a
native Chrome file download, invisible to ordinary Playwright page/popup
tracking. Getting it required `Page.setDownloadBehavior` +
`Browser.setDownloadBehavior` via CDP, pointed at a script-controlled
directory, set before the click. Verified live: fetched file matched the
reference file's exact byte size (1,215,736 bytes); a full run then
successfully used the auto-fetched file for phase 3 enrich ("enriched 72
dialogs, 15 empty, 0 unresolved (of 87)") with zero manual steps.
`--report FILE` still works (skips the fetch); new `--no-report` skips it
outright.

**`--with-rgroups` on `export_coaching.sh`**: runs
`rgroup_report.py OUT.json --md` against the run's own output right after
a successful export — one run now gives `coaching.json` *and* an
up-to-date `rgroups_table.csv` + `rgroups_report.md`. Implemented as
shell-side orchestration (parses the export's own `wrote <path>` log line)
rather than touching the Python side. Verified live: produced a real
416-row CSV and a markdown summary with correct live counts (89 groups,
412 messages, 968 nodes, 65 dialogs).

**UI-structure self-check (the third "Later" item)**: NOT implemented this
pass — it's explicitly bigger in scope than the other two ("Idea:", not a
scoped task, would mean retrofitting assertions across most navigation
helpers in the project). Left well-documented in TASKS.md instead, per the
user's own instruction for anything not fully closed — including a fresh,
concrete illustration found by accident while verifying the two items
above (see next section).

## Bonus finding: `click_expander()` silently mis-classifies a timeout as
"this is a leaf"

While live-testing auto-fetch + `--with-rgroups` together, hit an unusually
bad flakiness patch in the (pre-existing, unrelated) Rules-tree expansion
logic: dozens of consecutive `click_expander()` calls timed out. Root
cause of the DAMAGE (not the flakiness itself, which is the same class of
Vaadin timing issue documented repeatedly this project): `click_expander()`
catches any exception and returns `False`, and `expand_all()` treats
`False` as "confirmed leaf" rather than "unknown, retry" — so a node that
merely timed out gets permanently excluded from the tree for that run,
with no error. The run "succeeded" (exit code path reached "wrote ...")
but with only 58 of ~125 real rules captured (46%), and all 8 sender-modal
reads then failed too (stale tree indices from the truncated structure).

**Only caught because the coherence check has a baseline to compare
against** — `ruleTreeNodes: 58 vs baseline 125 (down 54%)`,
`sendingRules: 0 vs baseline 21 (down 100%)`, exit code 1. Without that
baseline, this would have been a silently-corrupted `coaching.json` with
exit code 0 — exactly the scenario the coherence check exists to catch,
and exactly the "wrong but successful" failure class the UI-self-check
"Later" item above is about. Not fixed this pass (out of the four
selected items) — logged in TASKS.md as a concrete first-application
candidate for that item, with the specific fix already scoped (distinguish
"confirmed not expandable" from "timed out" in `click_expander`, don't
conflate them).

## Verification summary

- 48/48 tests pass throughout (checked after each code change, not just
  once at the end).
- Every touched Python file syntax-checked via `ast.parse`; the shell
  script via `bash -n`.
- Every fix verified against real, live, or previously-captured data before
  being called done — no claim in this log or in TASKS.md rests on
  "should work" without a corresponding check.
