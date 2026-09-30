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
