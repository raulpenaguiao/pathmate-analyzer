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
