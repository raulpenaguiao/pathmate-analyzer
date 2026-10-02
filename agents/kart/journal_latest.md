# Agent journal: 2026-10-01 08:00 → 2026-10-02 ~11:20

**Last digest: 2026-10-02 11:20.** The next one is due by 2026-10-03
11:20, or on Kart's first wake after that time.

Compiled by Kart from every `agents/*/STATUS.md`, the mail, `TASKS.md`, the
git log (58 commits) and direct checks of the browser lock, running
processes and exports.

## At a glance

- **New top priority (your call, 10-01 afternoon): PMCP editor
  documentation and a richer export.** The plan is in place:
  - Mirror owns the export coverage map.
  - Warden owns the annotated screenshots and the exporter.
  - Mason owns the meanings and the documentation page.
  - Herald owns the Simone email.
- **Documentation v1:** "PMCP editor: what every setting does"
  (https://claude.ai/code/artifact/27405faa-5de0-4e32-a865-c5de349ef0cb).
  It has 20 red-box questions and all 50 rule comparison operators.
- **The Simone email is ready** (Herald v10, 22 questions, with screenshot
  attachments). **You send it.**
- **Finding, CORRECTED 10-02 (Mason):** the 15 top-level rules in alex-sandbox
  are **stray copies**. The real medication chains sit correctly under
  PERIODIC BASIS, so the reminders can fire. The strays should be
  **deleted**, and 2 of them have "Send message" ticked. Whether PMCP runs
  top-level rules at all is still question 1 to Simone.
- **Task 2 (your CSV → alex-sandbox) is partly applied: 57 of 793
  variants.** It stopped cleanly on a toolbar issue in the spirometry
  dialog. Warden reviewed the cause and the fix. Loom is fully idle until
  your go.
- **The richer exporter: test PASSED 10-02 11:37** (`20261002-111732`: 90/90,
  14/14 jumps, 21/21 senders, new fields plausible). Before that:
  - The overnight run ended PARTIAL, because the machine slept and the
    session expired.
  - The 11:05 run failed at login.
  - Warden's own login and export ran as separate commands about 1 h
    apart, so the session timed out. **Loom was not the cause**
    (Warden's correction). Login, open and export now run as one command.

  Warden is retrying.
- **The advisor account is built** (Smith `2543058`): Users page,
  per-use API key field, nothing stored on the server. You deploy it.
- **The masculine pass is done** (rule-based, **offline only**). It
  produced CSVs proposing 5 changes for alex-live texts and 3 for
  alex-sandbox. **Nothing was written to either coaching**; alex-live is
  verified unchanged. The Sonnet pass for alex-live (also CSV-only) is
  planned and on hold.

**Waiting on you:**
1. **Send the Simone email.**
2. **The new rule Warden proposes:** any PMCP login needs the browser
   lock. Kart recommends adding it to RULES.md.
3. **When to resume Loom:** the rest of task 2 (736 variants), then the
   masculine CSV.
4. **Deploy the advisor account:** release tag, then Users → create
   "advisor".

---

## Kart: planning and tracking
**Done**
- 10-01 digest and archive. Switched to `waitmail.sh`.
- Routed:
  - the decisions on Mason's brief (fix up, ask PathMate now, no hold)
  - the masculine task
  - the documentation project (copied your notes and screenshots into
    `docs/pmcp-ui/raul-2026-10-01/`)
  - task 2 (go, hold, partial)
  - the exporter test
- Traced your CSV to alex-sandbox.

**Went wrong:** I reported Loom as "on hold" from its own mail. My hold
mail had allowed "small fixes", so Loom kept committing, and later logged
into PMCP, per Warden; Warden has since withdrawn that. **Now:** I verify with processes, the lock and git before
reporting, and "hold" means no work at all, including no PMCP login.

## Warden: browser access and safeguards
**Done**
- Annotated screenshots of every editor (`docs/pmcp-ui/screens/`). The 15
  out-of-section rules are now exported with a warning. "Leaves" now
  means something.
- **Exporter:**
  - sender disabled state
  - the raw dialog target
  - 2 scraper fixes
  - the change list (`d8f3416`)
  - the menu-click fix (`045481e`)
- Your 13:45 alex-live export passed: 37/37 senders, 24/25 jumps.
- Reviewed Loom's apply stop.

**Open:** the exporter test run (retrying now), then the §6 message
settings.

## Mason: pile-up redesign
**Done**
- The decision brief, the rule-modal explainer, and the editor
  documentation v1 (Confirmed / Inferred / Unknown).
- The medication misplacement diagnosis.
- Fix-up checklist items: the typo, the RO slot bug, multiSubmit, moving
  the 15 rules.

**Next:** iterate on your comments, and add Warden's screens and Mirror's
map.

## Mirror: chat simulation engine
**Done**
- **The coverage map** (`docs/pmcp-ui/coverage-map.md`): the §6 export
  spec (14 items) and the §7 unknowns (13).
- Found 2 scraper bugs, which Warden has fixed.

**Next:** a per-dialog questions sheet, and checking the exporter test
against §6.

## Herald: advisor materials
**Done**
- Coming Back with Context v6 (multiSubmit), and Wording Pools v7 (with
  screenshots).
- The PathMate/Simone email v10.

**Waiting:** you send it, and then Herald marks the red boxes "Asked
PathMate".

## Loom: r_ randomisation groups
**Done**
- The masculine tool and its reports.
- The dupcheck ro-holds-English check.
- The skip-missing and skip-pool logic (`952372f`, `7359cac`).
- 2 apply bug fixes, plus the selection check (`c945781`).
- **Task 2:** 57 variants applied cleanly, then a clean stop.

**Now:** idle (verified). Told not to log in to PMCP.

## Smith: portal
**Done**
- The Chat-tab work (`6c0f1ca`).
- The advisor account (`2543058`).
- Portal screenshots for Herald.
