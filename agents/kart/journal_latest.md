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
