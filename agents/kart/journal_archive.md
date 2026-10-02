# Agent journal archive (Kart)

Every digest Kart has written, newest first. `journal_latest.md` holds only the newest one; each new digest is also appended here.

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
- **Big finding:** the 15 v02 medication rules in alex-sandbox sit outside
  the 4 execution sections. They were misplaced during the September
  build. **They probably never fired.** Moving them is on Mason's fix-up
  list, and it's also question 1 to Simone.
- **Task 2 (your CSV → alex-sandbox) is partly applied: 57 of 793
  variants.** It stopped cleanly on a toolbar issue in the spirometry
  dialog. Warden reviewed the cause and the fix. Loom is fully idle until
  your go.
- **The richer exporter has NOT been tested yet:**
  - The overnight run ended PARTIAL, because the machine slept and the
    session expired.
  - The 11:05 run failed at login.
  - Warden's own login and export ran as separate commands about 1 h
    apart, so the session timed out. **Loom was not the cause**
    (Warden's correction). Login, open and export now run as one command.

  Warden is retrying.
- **The advisor account is built** (Smith `2543058`): Users page,
  per-use API key field, nothing stored on the server. You deploy it.
- **The masculine pass is done** (rule-based): 5 changes in alex-live, 3
  in alex-sandbox. The Sonnet pass for alex-live is planned and on hold.

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

---

# Agent journal: 2026-09-30 00:55 → 2026-10-01 ~08:00

**Last digest: 2026-10-01 08:00.** The next one is due by 2026-10-02
08:00, or on Kart's first wake after that time.

Compiled by Kart from every `agents/*/STATUS.md`, the mail, `TASKS.md` and
the git log.

## At a glance

- **Your API key is now manager-only.** That's a new RULES.md rule. Warden's
  gate (`ed6ae85`) makes `rgroup_expand.py` refuse to run inside any agent
  session. It's a speed bump, since the key stays in `.env`. Your
  Anthropic spend cap is the hard limit.
- **The alex-live r_ CSVs are finished.** 1312 of 1314 variants passed
  (`rgroups_generated_260930123725.csv`). The last resumes went through
  after the cap reset.
- **The exporter got sturdier.** It no longer resizes the window, and it
  can't pass silently any more: your test caught a run that read 0 of 6
  senders and still said ok. Your 14:31 alex-live re-run passed: 98
  dialogs, 37/37 senders, 0 retries.
- **New duplicate checker for r_ wordings** (Loom). It's offline, uses no
  API, and only reports. It found one real bug: Timeless Greetings row 2
  has **no Romanian in either coaching**. Mason drafted "Salut,
  $participantName! 🤗", which needs a native speaker's check.
- **`multiSubmit` = false is now part of the plan** (Mason). It's in the
  build steps, the rollout and One Question at a Time v11. Catch: the ACQ
  needs a unique questionnaire id per round.
- **Task 2 (writing the 802 variants into alex-sandbox) is postponed** on
  your call: you're making the CSVs yourself first.
- **The mailbox listener is now `agents/waitmail.sh`** (your call, 10-01).
  It's a background command with no time limit, so there are no more
  half-hourly "restarted the listener" lines.
- **New page: Agent Journal Archive**
  (https://claude.ai/artifact/7NezBkmyqQHC1uhYjcwQK4). It holds every
  digest, and Kart republishes it with each new one.

**Waiting on you:**
1. **Your CSVs for task 2.** Then Loom applies them, Warden re-exports,
   and Loom publishes the comparison page.
2. **Smith's advisor-account proposal:** the deployed portal's URL, and the
   advisor's rights. Kart suggests read-only, since step 3 of the r_ tab
   spends API credit.
3. **The Simone email:** Herald is waiting for your screenshot, description
   and goal.
4. **Mason's questions:**
   - Retrofit the alex-sandbox spirometry/medication prototype, or rebuild
     it?
   - Data-collection Q1/Q2.
   - Should the advisor email ask PathMate "in parallel", or "only if
     inconclusive"?
5. **Phase A (pile-up platform tests) needs a browser slot on sandbox.**
   Warden held the browser until your exporter sign-off. Your 14:31
   re-run passed, so Warden can now give Mason a slot.
6. **Native-speaker check** of the new Romanian greeting.

---

## Kart: planning and tracking
**Done**
- 09-30 digest. Built the Journal Archive page plus its build script.
- Took your 6 follow-ups and routed each to its owner after talking them
  through with you: the API gate, the dupcheck, multiSubmit in the plan,
  the Simone email, the advisor account, and the chat backlog.
- Tracked everything in TASKS.md and pushed throughout.
- Today: switched to `waitmail.sh` and committed Mirror's listener files
  (`d44cd46`).

**Next:** chase the answers above. Bring the Progress Tree up to date with
this week.

## Warden: browser access and safeguards
**Done**
- **Fixed-window export.** Collapsed menus open through the overflow
  button, on hover (`b431973`, `97893b0`).
- **Loud failures:** a sender that can't be read now fails the run and
  takes a snapshot. The baseline only updates from a passing run
  (`ef8f83a`, `3a88447`).
- **Jump targets:** command messages are matched, and an empty dropdown
  counts as "no jump" (`a911cd1`).
- **API gate** (`ed6ae85`, `tools/_agent_guard.py`).
- The `.env` login works again. Yesterday's rejection was temporary.

**Next:** give Mason a sandbox slot for Phase A, and do the AFTER export
once task 2 runs.

## Loom: r_ randomisation groups
**Done**
- alex-live CSVs: 1312/1314 OK, 0 failed, 2 duplicates in
  r_EveningGreetings.
- Fixed thinking-token headroom (`c88d9bf`). Every r_ step now takes its
  input file explicitly, with no "latest file" guessing (`2703975`).
- **Dupcheck** (`2703975`, `5ace42a`, `43acb02`):
  - A pool is a run of consecutive rows.
  - Pairs whose rows have different send conditions are labelled as such.
  - It flags Romanian slots that hold English.
- Made a masculine copy of the alex-sandbox table for you. Only 3 ro-RO
  cells had gender alternations.
- Checked Herald's Wording Pools v5.

**Rule:** no more API runs by Loom.

## Mason: pile-up redesign
**Done**
- multiSubmit=false is in the plan (`962f429`).
- Put the dupcheck finds on the build fix list, and corrected row 2 to
  "needs real Romanian" (`eba8a25`).

**Waiting:** the 3 questions above, and the sandbox browser slot for
Phase A. Phase A doesn't depend on the retrofit-or-rebuild answer.

## Herald: advisor materials
**Done**
- **Wording Pools v5:** final alex-live numbers, plus a "See it run"
  section. Loom checked it. Portal screenshots from Smith are pending.
- Asked you for the Simone email inputs. No draft until all three arrive.

**In progress:** adding multiSubmit to Coming Back with Context, with
Mason's wording.

## Mirror: chat simulation engine
- No new work. Workstream 5 and the export study are still blocked on the
  chat test, which is now on the backlog and not a priority.
- Set up the new `waitmail.sh` listener for everyone, which you approved.

## Smith: portal
- Sent the advisor-account proposal (details in TASKS.md). Smith is
  waiting for your answers.
- **Note:** `app/` has uncommitted changes, +142 lines in 6 files.
  Smith's STATUS hasn't been updated since 09-25, so Kart is asking Smith
  what they are.

---

# Agent journal: 2026-09-29 00:20 → 2026-09-30 ~00:55

**Last digest: 2026-09-30 00:55.** The next one is due by 2026-10-01
00:55, or on Kart's first wake after that time.

Compiled by Kart from every `agents/*/STATUS.md`, the mail, `TASKS.md` and
the git log. A busy day: there are about 30 commits.

## At a glance

- **New coaching names (RULES.md, your rule).** Warden's write guard now
  refuses alex-live, and the pile-up fix gets built in alex-sandbox,
  with tests in sandbox. There is no separate workbench any more.

  | Short name | Coaching | Rule |
  |---|---|---|
  | alex-live | `ALEX v01 zum Ausprobieren 2` | export only, never changed |
  | alex-sandbox | `ALEX v01 zum Ausprobieren` | the pile-up target, free to change |
  | sandbox | `Minimal Coaching for Development 2 for Raul` | free to change |

- **Both clean exports are done:**
  - **alex-sandbox:** `..._20260929-111706.json`. Coherence OK, 0 warnings,
    all 14 jump targets resolved.
  - **alex-live:** your run, `..._ausprobieren-2_20260929-162548.json`.
    Coherence OK, 98 dialogs, 37 senders; 4 of 26 jump targets are still
    ambiguous.
- **The alex-live r_ CSVs are half done.** Report and requests are done:
  138 groups, 175 pools, 159 thin, 1314 variants. Expand stopped at pool 37
  because your **Anthropic API spend cap** was hit. It resets
  2026-10-01 00:00 UTC.
- **alex-sandbox r_ CSV done:** 802 of 804 variants generated. The apply
  (task 2) hasn't started.
- **Advisor pages ready:** Coming Back with Context v4 (pile-up, with the
  "What the PathMate docs say" section), and the r_ tool explainer v2.
- **PMCP docs knowledge base:** `docs/pmcp-docs/` holds all 49 v6.0 pages.
- **Mailbox listener** now runs through the Monitor tool for every agent
  (RULES 5 and the wake prompt).
- **Repo:** 11 commits since 16:56 are not pushed yet. Kart pushes them
  with this digest.

**Waiting on you, most urgent first:**
1. **The API spend cap:** raise it in the Anthropic console, or let it
   reset at 00:00 UTC on Oct 1. Then Loom resumes expand (122 pools, 1028
   variants).
2. **The PMCP `.env` login** has been rejected since ~13:10. Your
   hand-login worked for the export, but unattended runs, including Loom's
   task-2 apply, need working credentials.
3. **Confirm the 09-25 write freeze is lifted for alex-sandbox.** That
   unblocks Loom's 802-variant apply and Mason's Phase A. Mason also asks:
   retrofit the spirometry/medication prototype in alex-sandbox, or
   rebuild it?
4. **The chat test with Smith (EngineV1).** It unblocks Mirror's export
   study, which you called the most important part, and workstream 5.
5. **Participant data collection:** 4 open questions with Mason.

---

## Kart: planning and tracking
**Done**
- Wrote the 09-29 digest.
- Progress Tree v15 → v16: completed steps fold into a "✓ N completed"
  line, and old banners moved into History.
- Routed your two tasks (the clean export, and the r_ apply with a
  before/after diff). Then routed tasks 3–4 once alex-live access came.
- Pushed `94fb007`, `9d4c79f`, `2e39e58`, `415289c`, `669b02d` and
  `cba01f2`.
- Routed the `$particpantName` typo to Mason. Tracked the docs KB and
  Mirror's export study.
- Armed the mailbox listener. It's now step 4 of my wake-up sequence.

**Next:** push the pending commits. Chase expand once the cap is lifted.
Add today's changes to the Progress Tree.

## Warden: browser access and safeguards
**Done**
- **The alex-sandbox BEFORE export.** Jump targets went from 4/14 to 14/14
  resolved (`b3e0971`). Tooltips are click-through, and there's a headless
  mode (`b64b345`).
- **The coaching guard:** exact coaching-row matching, and alex-live
  refused (`2f89222`).
- **Per-coaching baselines** (`935d7a8`), with the alex-live baseline in
  `c73600d`.
- **`--allow-noop-resaves`** (`461fc75`), so you can run a full alex-live
  export by hand.
- **Screen-sleep fixes:** your first 4 alex-live runs died because the
  screen went to sleep. Warden added a pause-and-resume guard (`2baf7ee`)
  and a systemd-inhibit wrapper.

**Open**
- 4 ambiguous jump targets (3 kinds, fixes queued).
- A root fix for the black 12000px window: emulate the wide viewport
  instead.
- A read-only close for editor modals.
- `multiSubmit` (unblocked, but needs your OK before any write).

## Loom: r_ randomisation groups
**Done**
- alex-sandbox expand: `rgroups_generated_260929093415.csv`, 802/804 OK.
- Added an abort guard and `--resume` (`94fb007`). `--csv` pins the file
  (`2e1ef85`). The "usage limits" error now aborts cleanly (`ff2993a`).
- alex-live steps 1–2, plus 37 pools of expand
  (`rgroups_generated_260929170725.csv`).
  - Compared with alex-sandbox: +53 groups, mostly weekly-incentive weeks
    and morning greetings.
  - −4 groups: GoodOverallCompliance_Stage1-3 and
    NighttimeMonitoring_Stage3_Push.
  - An "Attic" dialog holds 3 groups.

**Blocked**
- alex-live expand: the spend cap.
- Task 2 apply: the login, and the freeze confirmation.

**Note:** the 6 new Stage3 rows would inherit the one-line Yes/No bug.
Mason says there's no sandbox fix for it.

## Mason: pile-up redesign
**Done**
- Checked Coming Back with Context v1–v4, plus your advisor question on
  what the docs say about pile-up.
- The PMCP docs knowledge base (`a2cb347`).
- Moved `docs/pileup` to the alex-sandbox/sandbox target. The build steps
  carry the greeting-typo fix (`c50f431`), and the A1/A3 tests end with a
  sandbox export for Mirror (`a21d6ab`).
- Took over `docs/participant_data_collection.md` from Mirror.

**Waiting on you:** the freeze confirmation, retrofit vs rebuild, and the
4 data-collection questions.

## Herald: advisor materials
**Done**
- **Coming Back with Context v4:**
  https://claude.ai/artifact/V27fFmmiLLb1apZs4zAxUh
- **r_ tool explainer v2:** https://claude.ai/artifact/JmLGKdfsXxkn8zeyBPK3Y5
- Both are checked (by Mason and Loom) and ready for you.
- Drafts now live in `agents/herald/context/drafts/`, so a restart can't
  lose them.

**Next:** refresh the r_ page after the task 2 apply and diff, and update
its status row for the new coaching names.

## Mirror: chat simulation engine
**Done**
- Typed-input answers and per-language multilingual variables, from your
  chat test (`dbfc05d`).
- Same-pass variable visibility as a switchable assumption, for pile-up
  test A2 (`cfa2c7e`).
- Scoped the **export study**:
  - It extends our `.json`, not PMCP's `.html` Report.
  - Warden reads all the new fields in one batched live pass.
  - Fields so far: the cascade-clearing flag, stop-intervention,
    questionnaire bindings, empty messageGroups, does-not-answer rules.
- Handed the data-collection doc to Mason.

**Blocked:** the EngineV1 chat test.

## Smith: portal
No new entries since 09-25. Smith is waiting for your chat test. The
demo portal can be relaunched on request.


---

# Agent journal: 2026-09-25 ~08:45 → 2026-09-29 ~00:20

**Last digest: 2026-09-29 00:20.** The next one is due by 2026-09-30
00:20, or on Kart's first wake after that time.

Compiled by Kart from every `agents/*/STATUS.md`, the mail, `TASKS.md` and
the git log. Almost everything happened on 09-25. The weekend was quiet
until tonight (09-29 ~00:00), when Warden, Loom and Mason woke up again.

## At a glance

- **Your 09-25 decisions are in force.** There are **no live PMCP writes**
  until you set up the workbench coaching, so the live-write queue
  (spirometry Yes/No fix, Loom's Stage3 wordings) is dropped. Owners:
  Mirror has workstream 5 and "what info to collect"; Warden has
  `multiSubmit`.
- **The pile-up strategy is settled** (you and Mason, 09-25 ~13:40). D1–D13
  and D12b are all answered in `docs/pileup/decisions.md` + `rollout.md`.
  The defining change: an interrupted dialog restarts from the top with a
  re-entry opener. First release: spirometry, medication, night prep, ACQ,
  education, gamification. **Nothing is live.** Everything gets rebuilt on
  the workbench.
- **Clean export delivered** (Warden, 09-25 16:30):
  `..._20260925-161248.json`, coherence OK, 0 stale tables, 0 unresolved
  dialogs. A follow-up run to clear the last log noise is going now.
- **r_ rerun for the advisor CSV is blocked:** the API key in `.env`
  returns **401 Unauthorized** (Loom, tonight). Steps 1–2 are done on the
  clean export.
- **Repo:** the 09-25 commit round and push are done. `main` is now 2
  commits ahead of origin (`6e9c5b4` Mason's RO seeds, `af5e637` Warden's
  sweep fix). Several agents' STATUS/context edits and
  `tools/rgroups-table/rgroups_table.csv` are uncommitted.

**Waiting on you, most urgent first:**
1. **A valid `ANTHROPIC_API_KEY` in `.env`.** This blocks Loom's step 3
   (expand), which blocks the advisor CSV and Herald's r_ explainer. Both
   were due 09-25.
2. **The workbench coaching** (plus an export of it). This blocks the
   whole pile-up rollout (Mason's Phase A platform tests onward) and every
   live write.
3. **Chat test with Smith.** It unblocks workstream 5 (Mirror). The
   09-25 demo portal on :8010 died with the old session, and Smith can
   relaunch it on request.
4. **Advisor questions from the pile-up strategy:** compliance thresholds
   M/K (placeholder 2), the ACQ interval (14 days assumed; the sandbox has
   1), and confirming the 5 h spirometry-after-medication gap.
5. **Mirror's `docs/participant_data_collection.md`** has 4 open questions
   for you, including privacy limits and who builds it.
6. **The ro-RO duplicate** ("within reach" = "nearby", and "handy" is
   near-identical) is in the existing v01 content. It's flagged for the
   advisor.
7. **Your live portal (:8000)** still has the stale 09-14 bundle
   attached. Swap in `..._20260925-161248.json`.

---

## Kart: planning and tracking

**Done**
- Finished the 09-25 commit round: all 6 agents committed their own
  files, Loom pushed `b35d0a1`, and I pushed the rest (`main` = origin at
  09-25 ~10:15).
- Recorded in `TASKS.md`:
  - your 09-25 decisions (no live writes, the day's priorities, owners)
  - Warden's clean-export progress
  - the settled pile-up strategy, first-release scope and rollout
- Mailed all agents the plain `checkmail.sh`/`mail.sh` rule. It is now
  RULES.md 6b (`722e9e4`), so it survives restarts.
- Tonight: pulled (already up to date) and archived Warden's
  clean-export mail.

**Open / next**
- Tonight: synced the Progress Tree to v15 (52 done / 4 in progress / 20
  not started, 76 total) with the settled strategy, first-release scope,
  the clean export, r_ progress and the new owners.
- Mailed Herald that both advisor drafts may have been lost with the old
  session's scratchpad.
- Push the 2 local commits once you OK it (the 09-25 push was a one-off).

## Warden: browser access and safeguards

**Done**
- **Clean export**, your top priority for 09-25:
  `data/exports/coaching_alex-v01-zum-ausprobieren_20260925-161248.json`.
  Coherence OK, no stale tables, no missing rows or mismatches, 0
  unresolved dialogs.
- Fixes behind it:
  - stale-table root cause (`5a8c461`)
  - menu-click retries; dropped folders now fail loudly (`2819ff4`)
  - opt-in live jump-target resolver `--resolve-jumps` (`4bd935a`)
  - tonight: scrolling the virtualized dialog table, and capping the
    re-widen at 16000px (`af5e637`)

**In progress**
- An export run with `--resolve-jumps --update-baseline` to clear what's
  left in the log: 14 ambiguous jump targets and 7 baseline-drift
  warnings. Warden holds the browser; there is no queue.

**Blocked**
- `multiSubmit`: waits for access to the real ALEX coaching.

## Loom: r_ randomisation groups

**Done**
- Pushed `b35d0a1` (restore mode, safer matching, the widen-order fix).
- Committed `e23355e`: expand now rejects duplicate wordings, and apply
  claims the shared browser lock.
- Tonight, on the clean export:
  - Step 1 (report): 89 r_ groups (95 including r1-3 and the weekly
    incentive groups, which matches Warden's count), 424 messages, 117
    pools, 102 thin.
  - Step 2 (prepare): 102 API calls, 804 variants.

**Blocked**
- **Step 3 (expand): every call gets HTTP 401.** Loom stopped after ~60
  failures; no output was written. It needs a valid key, then:
  `.venv/bin/python tools/rgroups-table/rgroup_expand.py --limit 102`.

**Next:** check the expand output, send Herald the facts for the advisor
artifact, and report to Kart. Apply stays dry-run only.

## Mason: pile-up redesign

**Done (09-25)**
- Folded all your answers into `docs/pileup/`:
  - D1–D13 and D12b are answered
  - planning ahead (onboarding schedule check, 30-min gap, no spirometry
    within 5 h after medication)
  - active-answer protection is capped at 1 h
  - the "nothing is live, sandbox prototypes only" reframe
- Wrote gender-free RO seed text for each re-entry opener, so Loom's
  `r_ReEntry_<Dialog>` groups have a ro-RO anchor.
- Handed One Question at a Time over as Mason's dev page (v10). Sent
  Herald the GO for the advisor-facing pile-up artifact.

**Waiting**
- Herald's draft to review. Nothing has arrived since the GO on 09-25
  13:41.
- The workbench coaching, before Phase A.

**Next:** idle until one of those two arrives.

## Herald: advisor materials

**Done (09-25)**
- Rebuilt from `docs/pileup/`: The Interrupt Contract v3, Watching It
  Write Itself v2, One Question at a Time v6. One Question at a Time then
  became Mason's page.
- The PMCP-docs accuracy pass was dropped, on your call.

**Open**
- The **r_ tool explainer** (due 09-25) and the **advisor pile-up
  artifact** (unblocked 09-25) are both drafts. Neither is published.
- **Risk:** both drafts were in the old session's scratchpad, which is
  session-specific, so they may be lost after the restart. Herald hasn't
  woken since.
- The r_ explainer also needs Loom's final numbers, which wait on the
  API key.

## Mirror: chat simulation engine

**Done**
- Took over the two owners you assigned: workstream 5 (blocked until
  you've tested the chat) and "what info to collect". First pass
  committed as `docs/participant_data_collection.md`:
  - PMCP already timestamps every variable write, so collecting data
    means writing variables at the right moment.
  - Biggest gap: 18 senders time out, and none has a "does not answer"
    branch.
  - It maps each gap to a patient-model field.

**Open:** 4 questions for you in that doc. Workstream 5 waits on your
chat test.

## Smith: portal

**Done**
- Committed `604855d` + `58b7bb9`.
- Ran a demo portal for you on :8010 with the 09-25 export. It re-ran the
  medication Yes/No and ACQ walks with 0 errors.

**Open**
- The demo instance is down (it died with the old session). Smith can
  relaunch it on request, ideally with the clean `161248` export.
- The stale 09-14 bundle is still on your :8000 portal.

**Next:** idle until your chat test.


---

# Agent journal: 2026-09-23 ~14:45 → 2026-09-25 ~08:45

**Last digest: 2026-09-25 08:45.** The next one is due by 2026-09-26
08:45, or on Kart's first wake after that time.

Covers the time since the last agent-wide restart (2026-09-23 afternoon).
Compiled by Kart from every `agents/*/STATUS.md`, the mail, and the git
log. The next digest will cover what happened after this one.

## At a glance

- **Chat simulator (Stage 4) is finished, Phases A–F.** Browser acceptance
  walks pass for medication Yes/No and for ACQ through to its score. Only
  workstream 5 (patient behaviour) is left, and it has no owner.
- **Pile-up redesign:** the docs have been restructured into `docs/pileup/`,
  with the new category ranking, the restart-with-resume design and a
  rollout order. Nothing new is live yet. The next live step is a fix for a
  button bug in the spirometry dialog.
- **r_ Stage3 pool:** 2 of 6 wordings are live and verified. A bug that
  would have wrongly skipped 3 of the remaining 4 is fixed. Adding them
  needs your OK.
- **Export tooling:** there's a fresh full ALEX export
  (`..._20260925-093313.json`) and a much stricter coherence check.
- **Repo:** everyone committed their own files this morning. Loom is the
  only one left. Kart pushes once Loom has committed.

**Waiting on you, most urgent first:**
1. **OK the live writes.** Warden's browser queue is:
   - Mason fixes the spirometry v02 "Yes:1 No:0" one-line options. These
     are live and broken on devices right now.
   - Loom adds the 4 Stage3 wordings.
   - Warden re-exports to verify.
2. **Loom's content flag:** "within reach" and "nearby" have **identical
   ro-RO text**, so Romanian users would see the same wording twice. Keep
   both, or reword one?
3. **Mason's two "proposed" expiry rules** (details under Mason).
4. **Owners:**
   - workstream 5, patient behaviour (the last open Stage 4 item)
   - "what info to collect"
   - questionnaire `multiSubmit`
5. **Scope:** are ranks 3–6 (sleep quality, education/health literacy,
   gamification, misc) in scope for v02? Three of them need trigger rules
   built from scratch.
6. **Your live portal (:8000)** has a stale 09-14 bundle attached. Swap in
   today's export using Detach + Attach on the Statistics tab. Smith and
   Warden haven't touched it.
7. **Herald asks:** should the advisor artifacts get a check against the
   PMCP v6.0 docs? That would be scope expansion.
8. **Mail rule:** should the "read mail only with `checkmail.sh --read`"
   rule go into RULES.md, so it survives restarts? It has only been
   mailed so far.

---

## Kart: planning and tracking

**Done**
- Kept `TASKS.md` and the Progress Tree (v12: 50 done / 3 in progress /
  22 not started, 75 total) in line through every change below.
- Decided Phase F on your delegation: engine-only seam, no patient
  behaviour. Mirror shipped it (`87e5e11`).
- Relabelled the pile-up items with the new category ranks, added a
  tracked item for the 4 categories with no phase, and added Mason's
  rollout order.
- Replaced `md-NNN` ids with dialog paths in the trackers (your uid rule).
- Deleted `docs/coaching_categories_table.md` on your instruction.
- Ran this morning's commit round. My commits: `4d77620` (shared agent
  infrastructure), `d9b1570` and `21c8363` (TASKS.md).

**Went wrong, now fixed:** I sat on 12+ unread mails for about 20 hours
after you declined one mail command, asking you every 30 minutes instead
of reading them. The real cause: `mv` and shell loops aren't on the
allow-list, but `agents/checkmail.sh … --read` is. I now use only that,
and I've saved it as a rule for myself.

**Open / next**
- Push, once Loom commits.
- **Done on your instruction (09-25 08:57):** mailed all 6 agents the rule
  to read mail only with `checkmail.sh --read`, send it only with plain
  `mail.sh`, never use loops, `mv` or chains, and never ask you before
  reading mail. It isn't in RULES.md yet; say if you want it added there
  so it survives restarts.

## Mirror: chat simulation engine

**Done**
- Stage 4 Phases C–F are done and committed (`44cbf2f` … `87e5e11`). 98
  tests pass.
- Fidelity fixes, checked against the PMCP 6.0 docs:
  - answer options are label:value (they were inverted)
  - decision rules run as a tree
  - jump-to-message targets
  - cascades return to the calling dialog
  - questionnaire buttons
  - `{#d}` dates
  - sims start from the export's variable defaults
  - system variables are simulated
- Added a model fingerprint so a saved chat can't be continued on a
  changed export.
- Confirmed today's fresh export runs in the engine without patching.

**Open, waiting on you**
- **Owner for workstream 5.**
- Unverified assumptions to confirm:
  - `$participantParticipationInDays` timing (your chosen assumption)
  - suppressed senders retry later
  - the send-hour fallback when the variable is -99
  - `leaveDecisionPoint` is ignored
- Data gaps the engine can't fix:
  - 14 of 49 jump targets need a live pass
  - questionnaire→variable bindings aren't exported
  - `$participantDeactivatedOpenQuestions` is undocumented
  - 4 senders have empty target dialogs
- Worth knowing for new content: Mason authored the v02 medication
  dialogs flat, so a gate placed next to their assignments doesn't guard
  them.

**Next:** nothing queued until workstream 5 has an owner.

## Smith: portal

**Done**
- A live-browser QA pass of all the portal tabs, which fixed 2 UI bugs:
  - Chat variable inputs were 1 character wide.
  - The sticky tab bar hid the tab labels on phones.
- Phase E portal side:
  - chat routes use the bundle engine
  - auto-periodic toggle, timeout countdown, event bubbles
  - questionnaire aid
  - stale-chat guard
  - attaching a new bundle clears the old rgroups CSVs
- Found the engine bugs Mirror then fixed.
- Committed `604855d` (app/) and `58b7bb9`.

**Open, waiting on you**
- The stale bundle on your live portal (see "At a glance").
- Found the spirometry v02 one-line Yes/No bug. It's queued for Mason.
- Randomisation Groups step 3 (the LLM call) still needs you and an API
  key to test in a real browser.
- `open-component` behaviour on a real device isn't verified.

**Next:** nothing blocking.

## Warden: browser access and safeguards

**Done**
- Took this morning's fresh full ALEX export (0 dialog errors).
- Root-caused your failed export: the edit-view wait gave up after 2s and
  now polls for 20s.
- The login check was fooled by the "Session expired!" banner. Fixed in
  three places.
- New `_run_diag.py`: run logs, a stall heartbeat, and failure
  screenshots.
- The coherence check now **fails** on missing rows and on per-dialog
  count mismatches, naming the dialogs.
- The export now includes:
  - jump-to-message targets and rule nesting (`0686367`)
  - `path` / `dialogPath` fields (your uid rule)
  - a partial-export guard
- Diagnosed the 09-23 session drops as plain expiry, not a lock.
- Browser lock (`431553f`).
- Commits: `cb0a10c`, `f2fc2ad`, `f2c040c`, `431553f`.

**Browser queue:** Mason (spirometry Yes/No fix), then Loom (Stage3),
then Warden (the stale-table sweep fix, then a re-export).

**Open**
- 3 dialogs in the fresh export read a stale table (Quit spirometry,
  Infocard 3, Offer assistance). Warden is fixing the sweep.

## Loom: r_ randomisation groups

**Done**
- Stage3 pool, verified from the fresh export: the canonical row plus
  "within reach" are tagged and adjacent, with no duplicates.
  Stage1_Push was done earlier.
- Fixed 3 `rgroup_apply.py` bugs:
  - the widen-before-tab-switch order
  - `PMCP_WIDE`
  - **the duplicate check used the first 18 characters of en-GB**, so
    sibling wordings collided. That would have wrongly skipped 3 of the
    4 remaining variants. It's now an exact match, tested offline against
    every grid cell.
- All of this is **uncommitted**, and Loom hasn't replied to the commit
  round yet.

**Waiting on you**
- OK to add the last 4 wordings: "close by", "with you", "access to",
  "nearby".
- The identical ro-RO text flag (see "At a glance").

**Next:** the Stage3 write once you OK it and it's Loom's turn in the
browser queue.

## Mason: pile-up redesign

**Done**
- Restructured the docs into `docs/pileup/` (committed `3da9a52`):
  - `README.md`, `problem.md`, `priority.md`
  - `interruptions.md`: the full restart-with-resume design
  - `reminder-pattern.md`
  - `rollout.md`
  - 9 category pages
  - the old spec moved to `archive/`, with stubs left at the old paths
- Your Decision 1 is written in: an interrupted dialog expires (end of
  day or end of week) instead of having a restart cap.
- Rollout order:
  0. three platform tests
  1. spirometry/medication retrofit
  2. sleep-prep
  3. ACQ + compliance
  4. ranks 3–6
  5. a full check, including a starvation test
- Health literacy is now rank 4, with education.

**Waiting on you (marked "proposed" in the docs)**
1. Expiry for the categories you didn't name:
   - end of day: nighttime, compliance, sleep quality, air quality
   - end of week: ACQ, FAQ, clinic
2. A reminder's short nag window stays as it is. End of day/week governs
   only how long an *interrupted* dialog may come back.

**Next**
- The live spirometry Yes/No fix. The script is ready and dry-run by
  default; it's first in the browser queue and needs your OK.
- Then step 0's three platform tests, which need Warden browser slots.

## Herald: advisor materials

**Done**
- **One Question at a Time** is now at v5. The caveat reads: one pool
  fully restored, the other randomising with 2 of 6 wordings. It's based
  on Loom's verification from the fresh export.
- Applied the uid rule; the only hit was in Kart's tree, which Kart fixed.
- Committed `8712dc6`.

- **Synced 3 artifacts to Mason's `docs/pileup/` (09-25 ~08:57):**
  - The Interrupt Contract v3, rewritten
  - Watching It Write Itself v2
  - One Question at a Time v6
  This replaces the outdated ladder and the deleted Phase 2 dialogs.

**Waiting on you**
- Go-ahead for a PMCP-docs accuracy pass over the 6 advisor artifacts.

**Next:** drop the caveat entirely once Loom adds the last 4 wordings.


---

