# ALEX v02 — Anti-Pile-Up Redesign Spec

> **Archived 2026-09-25.** The current design is [`docs/pileup/`](../README.md). Where this spec disagrees with it (priority order, "delete when interrupted"), `docs/pileup/` wins. Kept for history and for the section numbers that older logs and code cite.

Companion to `Coaching_ALEX_v01_zum_Ausprobieren.html`. This is a design document for the PMCP Coach Editor, not an importable file — transcribe it into the Coaching's Rules / Micro Dialogs sections yourself.

> Imported into this repo 2026-09-11 from personal notes to become the tracked spec for the "Pile-up problem" workstream's implementation phase — see `TASKS.md`'s "ALEX v02 redesign" section and `README.md`'s workstream 2 detail. Content unchanged from the original except this note. One correction to keep in mind while implementing: this repo's own live exploration (`README.md`'s "priority-field correction") confirmed PMCP has **no native priority/tier field** — every "P0–P4" reference below is our own abstraction, implemented entirely through rule order, per-rule timeout, and guard variables, not a UI setting.

## 1. Diagnosis (recap)

Reported symptom: an unanswered morning reminder (e.g. "do your spirometry") resurfaces later in the day, displacing the content that was actually scheduled for that time (e.g. an evening dialog) instead of getting out of the way.

Root cause, found in the v01 file and confirmed against the PMCP v5.0 docs:

- All of ALEX's reminders (spirometry, medication, sleep-prep) are PMCP's default **"blocking question"** — they stay open indefinitely until answered, with no priority and no expiry.
- PMCP offers two ways to handle a new dialog interrupting an unanswered one: **"Reactivating Questions"** (deactivate, then resume it later — docs warn this *"demands sophisticated state management to avoid overwhelming users"*) or **"Deleting Questions"** (drop it on interrupt — recommended *"when dialogues follow a predictable, chronological sequence,"* which daily reminders are).
- v01 hand-builds the risky "Reactivating" model: it reads the native counter `$participantDeactivatedOpenQuestions` (17 reads, 0 writes — a PMCP system variable) and, via two generic "Transition message when interrupting dialog kicks in / has finished" micro-dialogs, explicitly resumes the old topic afterward ("*we had previously stopped somewhere else... let us resume the previous conversation*"). That resumption **is** the pile-up.
- *Checked 2026-09-23 against the v6.0 docs (`/best-practices/defining-the-conversational-coaching-flow`): v6.0 calls Reactivation the **preferred** option ("allows users to respond to all open questions at their own pace and reduces frustration") and Deletion the one that "risks frustrating users". So reactivation isn't wrong in itself. The v01 problem is reactivating with **no expiry and no priority**, which is exactly what the new interrupt design (2.0) adds. The docs don't say whether the open-question counters are per dialog or per participant.*
- The only cleanup is one blunt end-of-day sweep (`Clearing microdialogs of the day related to spirometry`, gated on `$timeDecimal >= bedtime`), not a relevance window per message.
- PMCP also documents a **time-out question** type (auto-expires) and a **priority hierarchy** ("a higher-priority dialogue cannot be interrupted by a lower-priority one") — v01 uses neither.

Fix direction: stop reactivating stale reminders; make them expire and get deleted instead, and rank scheduled content above nagging so it's never blocked. *(Ranking superseded 2026-09-23: device reminders now rank first, see 2.0.)*

## 2. Architecture principles

### 2.0 Priority ladder (2026-09-23, Raul): supersedes the P1/P2 split in 2.1

Raul set the coaching's priority by **category**. A category-by-category check of the 18 Sep export found three things:
- Only spirometry and medication run on the v02 pattern.
- ACQ, nighttime monitoring, education, gamification and the one compliance rule still fire with no guard.
- Sleep quality, compliance coaching and misc (FAQ, air quality, clinic visits) have content but **no working trigger**. The only compliance rule starts an empty dialog, so each of these needs a rule built, not just a guard added.

This ladder replaces 2.1's P1-vs-P2 ranking for everything between safety (P0) and dev/testing (P4). A lower number is higher priority.

| Rank | Category | Dialogs (Appendix A #) | Old tier |
|---|---|---|---|
| 0 | Safety escalation (unchanged) | #90 | P0 |
| 1 | Daily home spirometry | #8, #52, #53–55, #75 | P2 |
| 1 | Controller medication adherence | #11, #60–63, #67, #76 | P2 |
| 1 | Nighttime asthma monitoring (sleep-prep, incl. smartwatch battery check) | #10, #35 | P2 |
| 2 | Asthma Control Questionnaire | #12 | P1 (reminder-creating) |
| 2 | Compliance coaching | #18, #22, #51, #57, #59, #91–99, #103–106 | P1 |
| 3 | Sleep quality inquiry | #6, #58, #69 | P1 |
| 4 | Educational content | #14, #28, #36, #37, #41, #64, #77–86, #100–102 | P1 (#14/#64 reminder-creating) |
| 5 | Gamification | #0, #9, #56 | P1 |
| 6 | Misc (FAQ, air quality, clinic visit reminders) | #13, #15, #17, #65, #66 | P1 / P3 |

The collision rules from 2.1 stay the same, with "tier" read as "rank":

- A **strictly** higher rank may interrupt a lower rank.
- Equal ranks never interrupt each other; whichever opened first runs to its natural stop. This matters because rank 1 now holds three daily reminders.
- A lower rank waits, then re-checks its own window before it fires.

What changes:

1. **Device reminders now outrank content.** Spirometry, medication and sleep-prep beat ACQ, education and gamification. This is the flip that 2.1a originally rejected, because it risks starving content. The risk is still real: rank-1 reminders fire up to 5 times a day. They must therefore keep short grace windows (2.2b), so that a lower rank waiting behind one finds its own window still open. Watch this in the Phase 5 verification.
2. **2.1a's engagement promotion mostly becomes moot for rank 1**, since only rank 0 can interrupt it. It still matters for ranks 2–6. An engaged dialog, meaning the user has already answered something, is treated as rank 1 while engaged, so a newly due reminder can't yank it away mid-answer.
3. **Unranked, kept as before:** P3 user-pulled conversations (#19, #21, #87–89 — the user's own messages, which no scheduled dialog barges into), onboarding (#1, #3, #4, which runs before any daily rule, gated on `$onboardingDone`), and greetings (#5, #43–48, which are embedded as openers inside other dialogs rather than scheduled by themselves). *These placements are Mason's reading of the existing spec, not part of Raul's table. Confirm them.*
4. **Dialogs that weren't in the table** (Raul, 2026-09-23):
   - smartwatch battery (#35) is part of night preparation, so rank 1;
   - the well-being check-in and its feedback (#7, #49, #50) is not a priority and is **never restarted**, the same treatment as greetings;
   - health literacy (#16) has "the same priority as edu content and ACQ". Those two are ranks 4 and 2, so **which one it gets is still open**.

   `Sensor data updates` (#34) is backend-only, never user-facing, and needs no rank.

PMCP has no native priority field (see the header note), so rank is implemented the same way the tiers were: guard variables in each firing rule. The only guard live today, `$participantOpenQuestions==0`, is rank-blind; it blocks on *any* open question. A real rank comparison needs a per-dialog "open" flag or a shared `$currentOpenRank` variable that the firing rules can compare against. That's a design item for the interrupt rewrite, which is pending, see below.

> **Also pending: rewriting the interrupt handling.** Raul has decided that interrupted dialogs are *restarted* with a short resume line rather than deleted. The restart expires at end of day (spirometry, medication) or end of week (educational content, gamification). It applies to every dialog except onboarding, greetings and the well-being check-in, tracked with one three-state variable per dialog, `$<name>_resumeMode`: **0** = restart from the beginning (the default until a checkpoint is passed), **1** = don't restart at all (e.g. only "thanks" or feedback is left), **2** = resume from the checkpoint, meaning the dialog jumps to its post-checkpoint half. Each checkpoint in the dialog sets whichever value fits what comes after it. That overrides 2.1's "Deleting Question" rule and 2.2b step 4. This section will be rewritten once the last detail is confirmed (see `agents/mason/STATUS.md`).

### 2.1 Priority tiers

> *Rank ordering between P1 and P2 is superseded by 2.0 above. P0, P3 and P4 and the collision rules still apply.*

| Tier | Meaning | v01 examples | Count |
|---|---|---|---|
| P0 | Safety-critical. Always wins, never expires, never dropped. | `Offer to have medical staff contact patient` | 1 |
| P1 | Scheduled coaching/clinical content — arrives on its own due-date/time-slot. Outranks P2. A few P1 items *also* create a reminder (see 2.2b) but they still outrank device nags. | Greetings, ACQ, educational content, feedback/compliance messages, infocards | 63 |
| P2 | Reminders/nudges for a same-day behavioral task. Time-boxed, expires, never resumed once interrupted. | Spirometry, medication (×3 doses), sleep-prep, smartwatch battery, health-literacy prompt | 15 |
| P3 | User-initiated/reactive — pulled by the user's own message, not pushed by the scheduler. Can't be pre-empted by a P2 nag while active. | FAQ, "coach" free-text routing, settings changes | 6 |
| P4 | Internal/dev/testing. Not part of the production priority scheme at all — flagged for removal or archiving. | `PLAYGROUND`, `Attic`, the various `Testing...` dialogs, `Andreas Test` | 17 |

Plus 3 dialogs that are the pile-up mechanism itself (both `Transition message...` dialogs and `Clearing microdialogs of the day related to spirometry`, see 2.4) and 2 pure folder/organizational nodes with no content of their own (`Home Spirometry`, `System`).

Rules:
- Priority order for interruption: **P0 > P1 > P2 > P3** (P3 is "active user conversation," which nothing but P0 should barge into; P4 never runs in production).
- A **strictly** higher tier may interrupt a lower tier's open dialog. A dialog never interrupts another open dialog of the **same or higher** tier — whichever opened first runs to its natural stop (completion or expiry) before anything at its own tier gets a turn. This applies to P1-vs-P1 too: e.g. if ACQ is already open, a same-moment educational-content trigger simply waits, it doesn't reactivate-interrupt.
- A lower tier may never interrupt a higher tier's open dialog — it must wait, then re-check its own window before firing (see 2.2; if the window has closed by the time the higher-tier dialog finishes, the reminder simply doesn't fire).
- **Every dialog that "creates a reminder" (2.2b) is always a "Deleting Question."** If interrupted, it's discarded, never resumed — regardless of tier. This retires the `$participantDeactivatedOpenQuestions` recall pattern and both "Transition message..." micro-dialogs.
- See **2.1a** for the one exception to plain tier-ranking: a P2 reminder the user is actively engaged with is temporarily treated as P1 for interruption purposes, not just P2.

### 2.1a Engagement promotion (P2 → P1)

> *Under the 2.0 ladder, spirometry and medication are already rank 1, so the promotion below now applies to engaged dialogs of ranks 2–6 (engaged → treated as rank 1). The starvation argument that follows is the reason 2.0 insists on short grace windows for rank 1.*

Flipping spirometry/medication to outrank content outright was considered and rejected: device reminders fire 4×/day and can sit open for hours (their whole grace window), while ACQ/education fire only every few days — if reminders always won, content would rarely get a turn at all (same starvation failure as the original bug, aimed the other way). But a real problem remains in the plain tier ranking above: as written, an in-progress spirometry attempt (user mid-breath-test in the CLAID app) or a medication confirmation the user has already started answering is still just "P2," so a same-moment ACQ/education trigger could legally interrupt and delete it — cancelling a task the user is actively doing for a quiz. That's worth fixing without reopening the starvation problem.

Fix: split *idle* from *engaged*.

- Every reminder-creating P2 dialog gets a companion flag, e.g. `$spiroReminderEngaged` (0/1), flipped to **1** the moment the user takes any action inside it (answers the first decision point, taps the CLAID link, confirms a medication dose) — not merely receiving the initial ping.
- **While that flag is 1, the dialog is treated as P1**, not P2, for every interruption check in this document — including the "same tier never interrupts" rule in 2.1. So an engaged spirometry/medication dialog can no longer be bumped by ACQ or education (only P0 could interrupt it), but an *idle* one (sent, not yet responded to) still yields to P1 exactly as before.
- The flag resets to 0 when the dialog reaches its natural stop (success, decline-to-retry, or expiry), so the promotion only lasts for the duration of active engagement, not for the reminder's whole window.
- Mechanically, any rule that fires a P1 dialog must gate on "no dialog is currently open whose *effective* tier is ≥ P1" — i.e. the existing "no open P1 dialog" guard (already used for P2 firing in 3.2) generalizes to check engaged-P2 dialogs too, not just literal P1s.

### 2.2a "Creates a reminder" — a second, orthogonal axis

Tier answers *"who wins if two dialogs collide."* It doesn't answer *"does this dialog nag and expire."* Those turn out to be independent:

- **P2 dialogs** (spirometry, medication ×3, sleep-prep, smartwatch battery, health-literacy) always create a reminder — that's their whole purpose.
- **Three P1 dialogs also create one**, because v01's own rules already give them a same-day reschedule flag identical in shape to the P2 ones: **ACQ administration** (`$userRequestedNewTimeForACQ`), **educational-content prompt** (`$userRequestedNewTimeForEducationalContents`), and its dedicated **"Interaction with educational content and rescheduling"** dialog. They keep P1 *priority* (a stale spirometry nag still can't block them) but get the *same* time-boxed/delete-not-reactivate treatment for their own rescheduling, because v01's evidence shows they can go stale exactly the same way.
- Every other P1/P3 dialog does not create a reminder at all — it's fire-once content or user-pulled.

### 2.2b Time-boxed relevance windows (the general reminder rule)

This is the one rule every reminder-creating dialog (every P2, plus the three P1 exceptions above) follows:

1. It has an explicit **soft start** (when it may first fire — a user-set time, e.g. `$spiroMesTime`, or a computed due-date/time) and a **hard expiry** (`soft start + a grace-period hyperparameter`, clipped so it can never spill past the next `$currentDaySlot` boundary — see 2.3).
2. It fires as a PMCP **time-out question**, never the default blocking one.
3. On expiry it closes **itself** with a short built-in fallback message (e.g. "no worries, we'll try again tomorrow") — no separate cleanup dialog needed.
4. If interrupted by an equal-or-higher-priority dialog before it expires, it is **deleted**, never reactivated or resumed.
5. If the user explicitly asks to be reminded later, that only resets the reminder's own soft-start to the new time — it never creates a second, concurrent open reminder.
6. At most one instance of a given reminder is open at a time, gated by its own `$xDone` / `$xReminderStage` flag.

### 2.3 Day-slot variable

```
$currentDaySlot ∈ { morning, midday, evening, night }
```
Computed once per PERIODIC BASIS tick from `$systemHourOfDay` against three new hyperparameters (`$hyperparameterMorningEndHour`, `$hyperparameterMiddayEndHour`, `$hyperparameterEveningEndHour`). Every reminder's window-end is clipped to "no later than end of the *next* slot boundary after its soft start" — so a P2 reminder can never spill into a slot it wasn't meant for, without each feature re-deriving its own time math (v01 duplicates ad hoc `$timeDecimal` comparisons per feature; this centralizes it).

### 2.4 What gets removed

- Micro dialogs: `Transition message when interrupting dialog kicks in`, `Transition message when interrupting dialog has finished`, `Clearing microdialogs of the day related to spirometry`.
- Rule-side per-feature postponement bookkeeping: `$spiroMesNumberOfDelayedRemindersIssued`, `$spiroMesDelayedReminderActive`, `$spiroMesDelayedReminderSent`, `$lastMinuteSpirometry`, `$spiroMesTimeDelay`, `$mySpiro_userRequestedNewTimeForSpirometry` and the equivalent per-dose medication variables — all superseded by the time-out question's native expiry plus one small `ReminderStage` variable (see 3.1). Most of the 50-item spirometry dialog's branching existed to hand-rebuild what a native time-out + priority gives for free, so the new flow is expected to be roughly a fifth of the size.

## 3. Concrete redesign: Spirometry reminder

### 3.1 Variables

| Variable | Type | Purpose |
|---|---|---|
| `$spiroMesTime` | time (reused) | User-set preferred time — soft window start |
| `$spiroWindowEnd` | time (new) | `$spiroMesTime + $hyperparameterSpiroGraceMinutes`, clipped to end of next day-slot boundary |
| `$spiroMesDone` | 0/1 (reused) | Whether spirometry was completed today |
| `$spiroReminderStage` | 0/1/2 (new) | 0 = not yet sent, 1 = initial prompt sent, 2 = one escalation sent. Replaces the five bookkeeping variables listed in 2.4 |
| `$spiroReminderEngaged` | 0/1 (new) | 0 = idle (sent, unanswered) — interruptible by P1. 1 = user has responded to at least one step — promoted to effective P1 per 2.1a, only P0 can interrupt |
| `$hyperparameterSpiroGraceMinutes` | number (new) | How long the reminder stays valid before hard expiry, e.g. 180 |
| `$totalNumberOfConsecutiveDaysWithoutSpirometry` | number (reused) | Weekly compliance metric — unrelated to the pile-up bug, keep as-is |

### 3.2 Rules

**DAILY BASIS** (inside the existing onboarding-done branch, replacing the old reset block for this feature):
```
$spiroMesDone            → 0
$spiroReminderStage      → 0
$spiroReminderEngaged    → 0
$spiroWindowEnd          → min( $spiroMesTime + $hyperparameterSpiroGraceMinutes,
                                 end-of-slot-after($spiroMesTime) )
```

**PERIODIC BASIS**:
```
IF $spiroMesDone == 0
   AND now >= $spiroMesTime
   AND now <  $spiroWindowEnd
   AND $spiroReminderStage == 0
   AND no dialog open with effective tier >= P1   # i.e. no open P1, and no *engaged* P2
   → fire spirometry micro-dialog as P2 time-out question, expiry = $spiroWindowEnd
   → $spiroReminderStage = 1

IF $spiroMesDone == 0
   AND now >= $spiroWindowEnd
   AND $spiroReminderEngaged == 0                 # an engaged attempt is protected — let it finish even past window-end
   → let the time-out question close itself (no manual message needed —
     see 3.3 for the expiry message configured on the question itself)
```
No "ask if they still want to be reminded" sub-flow: if the user wants a later nudge, that's handled by the existing `USER INTENTION` mechanism (a free-text "remind me later" intent updates `$spiroMesTime` directly), not a branch inside this dialog.

### 3.3 Micro-dialog outline (≈10 items, down from 50)

1. **[Message, P2 time-out, expiry = `$spiroWindowEnd`]** "Quick reminder to check your lung function with spirometry today!" (push notification). *Time-out fallback message:* "No worries — we'll check in again tomorrow." (replaces the old separate "clearing" dialog's goodbye message). Still idle — interruptible by P1.
2. **[Decision Point]** "Do you have your spirometer handy?" (single phrasing; v01's six near-duplicate rewordings can be collapsed to one — rotate wording via the existing localization table if variety is wanted, not via six branch copies). **On the user's first answer here → `$spiroReminderEngaged = 1`** (per 2.1a, promoted to effective P1 from this point on).
3. **[Message]** "Please tap when ready!" → opens CLAID app (`show-link` command, unchanged from v01).
4. **[Decision Point]** wait for `$claidSpirometryCompleted`.
5. **[Message, success branch]** "Thanks for taking the time to do a spirometry measurement." → set `$spiroMesDone = 1`, `$spiroReminderEngaged = 0`, `$totalNumberOfConsecutiveDaysWithoutSpirometry = 0` → **Stop Dialog**.
6. **[Message, failure branch]** "Something didn't work out — want to try again, or watch a quick how-to video?" → offer retry (loops to step 3) or educational-content link → set `$spiroReminderEngaged = 0` → **Stop Dialog** either way.

## 4. Concrete redesign: Medication reminder (3 doses/day)

Same pattern, parametrized per dose `i ∈ {1,2,3}`:

| Variable | Type | Purpose |
|---|---|---|
| `$myMedication_doseTime_i` | time (reused, was `$userSetDesired...DoseOfControllerMedicationInhalationTime`) | Soft window start |
| `$myMedication_windowEnd_i` | time (new) | `doseTime_i + $hyperparameterMedicationGraceMinutes`, clipped to day-slot boundary |
| `$myMedication_done_i` | 0/1 (new, replaces the single shared `$myMedication_NumberOfInhalationsOfTheDayCompleted` counter with a per-dose flag) | Whether that dose was confirmed |
| `$myMedication_reminderStage_i` | 0/1 (new) | Replaces `$medicationNumberOfRegularRemindersIssued` |
| `$myMedication_engaged_i` | 0/1 (new) | Same promotion mechanism as `$spiroReminderEngaged` (2.1a) — flips to 1 on the user's first response to that dose's reminder |

Rules mirror 3.2 exactly (one instance per dose), including the `effective tier >= P1` guard and the engaged-flag set/reset. Dialog outline mirrors 3.3 but shorter — no CLAID handoff, just: reminder (idle) → "did you take it?" (first response sets `$myMedication_engaged_i = 1`) → confirmation, resets engaged to 0 → thanks / time-out fallback. ~5 items instead of the current per-dose flow. Being short-lived, the engaged-protection window for medication is brief in practice — but it still guarantees a dose confirmation the user has already started answering can't be yanked away mid-exchange for a quiz.

## 5. Migration notes — porting the pattern to the rest of ALEX

- **Sleep-prep / nighttime monitoring**: same treatment as spirometry — P2, window = `$userSetBedtime - 10min` → `$userSetBedtime + $hyperparameterSleepPrepGraceMinutes`, delete-not-reactivate.
- **ACQ administration** *(correction from the first pass of this doc — see 2.2a)*: keep **P1 priority** (a stale device reminder still can't hold it hostage), but it **does create a reminder** — v01's own PERIODIC BASIS rules already give it a same-day reschedule flag (`$userRequestedNewTimeForACQ`), so apply the same soft-start/hard-expiry/delete-not-reactivate treatment from 2.2b, just at P1 rank instead of P2. If the user misses it entirely for the day, let the existing next-due-date rule (`$dateOfNextACQ` math) carry it forward rather than re-showing it later the same day. Its firing rule needs the same "no dialog open with effective tier >= P1" guard as spirometry (2.1a) — so it won't barge into an *engaged* spirometry/medication dialog, only an idle one.
- **Educational-content nudges**: same correction — P1 priority, but reminder-creating (`$userRequestedNewTimeForEducationalContents`, and the dedicated "Interaction with educational content and rescheduling" dialog), and the same firing guard against engaged P2 dialogs. Note this dialog is currently a **stub** in v01 (name + comment only, no messages configured) — building it out is a prerequisite, not just a rewire.
- **Health literacy prompt**: treat as P2, same as spirometry — it asks the user to act now and has no special standing over the device reminders.
- **Delete outright**: `Transition message when interrupting dialog kicks in`, `Transition message when interrupting dialog has finished`, `Clearing microdialogs of the day related to spirometry` (its one useful line — the "give up for today" message — is folded into the time-out fallback message per reminder, per 3.3).
- **Prune before migrating anything**: the 17 P4 dev/testing dialogs (`PLAYGROUND`, `Attic`, `⚙️ Controls`, `Andreas Test`/`Test Andreas`, and the various `Testing...` entries) aren't part of the production flow at all — archive or delete them rather than porting them.
- **Build the stubs or drop the rules that reference them**: 8 dialogs in v01 exist as a name + design comment only, with zero configured content — `Goodbye 🚪`, `Adherence barriers dialog`, `Modification of reminder preferences`, `Escalation dialogues to address poor compliance`, `Prompt patient to watch/read/listen educational material`, `Feedback on compliance regarding daily spirometry`, `Status of weekly incentive`, `Feedback on compliance regarding nighttime monitoring`, `Feedback medication adherence`. Notably, the DAILY BASIS rule `🧐💬 If required, send feedback on poor compliance...` already fires *into* one of these empty stubs today — so that compliance-feedback path is currently a no-op in v01, independent of the pile-up bug.

## Appendix A: Full dialog classification (all 107)

Tier counts: **P0** 1 · **P1** 63 · **P2** 15 · **P3** 6 · **P4** 17 · retire 3 · folder/no-content 2.

`Yes*` = P1-ranked but reminder-creating (2.2a exception). Sub-steps marked `No` under P2 are absorbed into their parent reminder dialog in the v02 outline (3.3) rather than staying separate top-level dialogs.

| # | Dialog | Tier | Creates reminder? | Note |
|---|---|---|---|---|
| 0 | Initialize questionnaire game score | P1 | No | Onboarding — one-shot game-score init |
| 1 | START | P1 | No | Onboarding entry node |
| 2 | ☑️ Testing | P4 | – | Dev/testing |
| 3 | 🤝 Welcome | P1 | No | Onboarding |
| 4 | 👋 Hello | P1 | No | Onboarding |
| 5 | Goodbye 🚪 | P1 | No | STUB — comment only, no content configured |
| 6 | Inquire about last night's sleep | P1 | No | Scheduled morning content |
| 7 | Inquire about patient's well-being | P1 | No | Scheduled content |
| 8 | Prompt patient to conduct daily spirometry | P2 | **Yes** | Daily; window = `$spiroMesTime`→`+grace`, 1 escalation, expires |
| 9 | Introduction of weekly incentive | P1 | No | Monday-only, one-shot |
| 10 | Prompt patient to prepare for nighttime monitoring | P2 | **Yes** | Daily; window = bedtime−10min → bedtime+grace |
| 11 | Prompt patient to take controller medication | P2 | **Yes** | Generic trigger; superseded by per-dose #61/62/63 |
| 12 | Prompt patient to answer questions of the ACQ | P1 | **Yes\*** | Due-date scheduled, but has its own same-day reschedule flag (`$userRequestedNewTimeForACQ`) — P1 priority + P2-style expiry |
| 13 | Reminder quarterly clinic visits | P1 | Yes (light) | Quarterly cadence — low pileup risk, simple expiry, no escalation |
| 14 | Prompt patient to watch/read/listen educational material | P1 | **Yes\*** | STUB (no content yet). Same dual-mode as ACQ — reschedule flag `$userRequestedNewTimeForEducationalContents` |
| 15 | Information about local air quality (pollutants and allergens) | P1 | No | Informational, sensor/threshold-triggered |
| 16 | Prompt patient to answer health literacy questions | P2 | **Yes** | Asks user to act now; same pileup pattern as spirometry |
| 17 | Inform the patient about the list of FAQs | P3 | No | User-pulled (FAQ command) |
| 18 | Adherence barriers dialog | P1 | No | STUB — feeds compliance escalation ladder |
| 19 | General feedback | P3 | No | Reactive/user feedback |
| 20 | Attic | P4 | – | Explicitly dead ("Attic", disabled in Rules too) |
| 21 | Modification of reminder preferences | P3 | No | STUB — user-initiated settings change |
| 22 | Escalation dialogues to address poor compliance | P1 | No | STUB — escalation ladder |
| 23 | Transition message when interrupting dialog kicks in | RETIRE | – | Pile-up mechanism — delete in v02 |
| 24 | Transition message when interrupting dialog has finished | RETIRE | – | Pile-up mechanism — delete in v02 |
| 25 | Clearing microdialogs of the day related to spirometry | RETIRE | – | Blunt bedtime-only sweep — delete in v02 |
| 26 | Testing of gamification concept | P4 | – | Dev/testing |
| 27 | Testing infocards | P4 | – | Dev/testing |
| 28 | Dialogs presenting infocards | P1 | No | Content delivery |
| 29 | Testing Media Objects | P4 | – | Dev/testing |
| 30 | Testing questionnaires | P4 | – | Dev/testing |
| 31 | Testing of streak concept | P4 | – | Dev/testing |
| 32 | ⚙️ Controls | P4 | – | Dev/testing, empty stub |
| 33 | Testing of gamification concept II | P4 | – | Dev/testing |
| 34 | Sensor data updates | P1 | No | Backend/system-triggered, not user-facing nag |
| 35 | Prompt patient to check the smartwatch battery level and potentially recharge it | P2 | **Yes** | Device-task nag (battery check) |
| 36 | Sequence of educational materials for kids aged 10 to 14 | P1 | No | Content sequence |
| 37 | Sequence of educational materials for kids aged 15 to 19 | P1 | No | Content sequence |
| 38 | Testing REDCap data | P4 | – | Dev/testing |
| 39 | 🐞 Testing sensor data retrieval | P4 | – | Dev/testing |
| 40 | 🐞 Testing time line of scheduled periodic events | P4 | – | Dev/testing |
| 41 | Educational video on how to do spirometry | P1 | No | Content |
| 42 | PLAYGROUND | P4 | – | Dev/testing, empty stub |
| 43 | Timeless Greetings | P1 | No | Content |
| 44 | Daytime Greetings | P1 | No | Content |
| 45 | Evening Greetings | P1 | No | Content |
| 46 | Morning greetings | P1 | No | Content |
| 47 | Generic | P1 | No | Fallback content bucket |
| 48 | Patient coaching goodbye messages | P1 | No | Content |
| 49 | Compassionate feedback when patient is not doing so great | P1 | No | Content |
| 50 | Positive feedback when patient is doing well | P1 | No | Content |
| 51 | Feedback on compliance regarding daily spirometry | P1 | No | STUB |
| 52 | Medical Feedback lung function | P1 | No | Content |
| 53 | Quit spirometry dialog after successful spirometry procedure | P2 | No | Sub-step of #8 reminder flow (fold into it in v02) |
| 54 | Quit spirometry dialog after unsuccessful spirometry procedure | P2 | No | Sub-step of #8 |
| 55 | Quit spirometry dialog after too many spirometry reminders | P2 | No | Sub-step of #8 |
| 56 | Status of weekly incentive | P1 | No | STUB |
| 57 | Feedback on compliance regarding nighttime monitoring | P1 | No | STUB |
| 58 | Medical feedback sleep quality | P1 | No | Content |
| 59 | Feedback medication adherence | P1 | No | STUB |
| 60 | Quit medication reminders dialog after successful inhalation | P2 | No | Sub-step of #61-63 reminder flow |
| 61 | Prompt patient to take first dose of controller medication | P2 | **Yes** | Dose 1; window = doseTime→+grace |
| 62 | Prompt patient to take second dose of controller medication | P2 | **Yes** | Dose 2 |
| 63 | Prompt patient to take third dose of controller medication | P2 | **Yes** | Dose 3 |
| 64 | Interaction with educational content and rescheduling | P1 | **Yes\*** | This *is* the reschedule handler for educational content — dual-mode like #12/#14 |
| 65 | Extreme levels of allergens | P1 | No | Env-alert; escalate to P0 only if clinically urgent (flag for review) |
| 66 | Extreme levels of air pollutants | P1 | No | Env-alert; same note as #65 |
| 67 | Medication | P2 | **Yes** | Content-bearing "Medication" node — actual per-dose reminder content |
| 68 | Home Spirometry | — | – | Folder/organizational node, no content |
| 69 | Morning greetings + inquire about sleep | P1 | No | Content |
| 70 | System | — | – | Folder/organizational node, no content |
| 71 | Test dialog for debugging | P4 | – | Dev/testing |
| 72 | Testing questionnaires | P4 | – | Dev/testing |
| 73 | Andreas Test | P4 | – | Dev/testing |
| 74 | Test Andreas | P4 | – | Dev/testing |
| 75 | Spirometry | P2 | **Yes** | Folder/summary node for spirometry dialogs |
| 76 | Medication | P2 | **Yes** | Folder/summary node for medication dialogs |
| 77 | Age group 10-14, Infocard 1 | P1 | No | Infocard content |
| 78 | Age group 10-14, Infocard 2 | P1 | No | Infocard content |
| 79 | Age group 10-14, Infocard 3 | P1 | No | Infocard content |
| 80 | Age group 10-14, Infocard 4 | P1 | No | Infocard content |
| 81 | Age group 10-14, Infocard 5 | P1 | No | Infocard content |
| 82 | Age group 15-19, Infocard 1 | P1 | No | Infocard content |
| 83 | Age group 15-19, Infocard 2 | P1 | No | Infocard content |
| 84 | Age group 15-19, Infocard 3 | P1 | No | Infocard content |
| 85 | Age group 15-19, Infocard 4 | P1 | No | Infocard content |
| 86 | Age group 15-19, Infocard 5 | P1 | No | Infocard content |
| 87 | 📄 dataEdited | P3 | No | `personal-data-edited` intent handler |
| 88 | Offer assistance | P3 | No | User-pulled |
| 89 | Coaching | P3 | No | `coach` free-text intent handler |
| 90 | Offer to have medical staff contact patient | P0 | No | Safety escalation to human/medical staff |
| 91 | Good Compliance | P1 | No | Compliance-phase branch content |
| 92 | Poor Compliance | P1 | No | STUB (empty at this tree position) |
| 93 | EarlyPhase | P1 | No | Compliance-phase folder w/ content |
| 94 | IntermediatePhase | P1 | No | Compliance-phase folder w/ content |
| 95 | FinalPhase | P1 | No | Compliance-phase folder — feeds toward #90 on poor compliance |
| 96 | Good Compliance | P1 | No | Compliance-phase branch content |
| 97 | Poor Compliance | P1 | No | Compliance-phase branch content |
| 98 | Good Compliance | P1 | No | Compliance-phase branch content |
| 99 | Poor Compliance | P1 | No | STUB (empty at this tree position) |
| 100 | Introductory sentences for videos | P1 | No | Content |
| 101 | Introductory sentences for podcasts | P1 | No | Content |
| 102 | Introductory sentences for text | P1 | No | Content |
| 103 | One missed session | P1 | No | Compliance feedback content |
| 104 | Several missed sessions | P1 | No | Compliance feedback content |
| 105 | One missed dose | P1 | No | Compliance feedback content |
| 106 | Several missed doses | P1 | No | Compliance feedback content |

Notes on ambiguous rows: #91–99 are the Early/Intermediate/Final-phase × Good/Poor-compliance escalation ladder — the flattened report doesn't preserve exact folder nesting, so treat the grouping as approximate; two "Poor Compliance" leaves (#92, #99) are empty at their tree position even though others with the same name (#97) have real content. #67/#75/#76 ("Medication"/"Spirometry"/"Medication") are content-bearing nodes distinct from the "Prompt patient to..." dialogs — likely alternate entry points or menu nodes into the same reminder flows; worth checking directly in the Coach Editor which one is actually wired to the daily rules before you delete anything.

## 6. Open item to confirm in the Coach Editor UI — RESOLVED 2026-09-11

Confirmed live (`autochanges/2026-09-11-alex-v02-phase0-recon.md`). There is
no distinct "time-out question" message *type* — it's a combination of
fields hidden behind a message editor's collapsed **"Show additional
settings"** section:

- `Minutes after sending until message is handled as unanswered:` — the
  real expiry duration (quick-pick `1/5/10/30/60/infinite`). **This is a
  per-message field, independent of the per-rule "not answered" timeout**
  already in `rules_stage3_ALEX_v01.json` — v01 defaults both to 4h on the
  spirometry reminder probed, which is why the two are easy to conflate.
  Section 3's `$spiroWindowEnd`/expiry design should set *this* field, not
  (only) rely on the rule-level timeout.
- `This message blocks the micro dialog until answered/unanswered` — the
  literal "blocking question" flag. Uncheck it for every P2/reminder-class
  message per this spec.
- `This message deactivates and remembers all former open questions` +
  `This message recalls former deactivated questions from last
  deactivation` / `…from most recent still filled deactivation` — this
  *is* the reactivation pattern named in §1 as the pile-up root cause.
  Leave all three unchecked on every redesigned reminder.
- `This message clears the current dialog cascade (and remembered
  questions)` / `…clears all dialog cascades…` / `…will not be cleared on
  clear all` — the likely "delete, not reactivate" lever, but this was a
  read-only recon pass and toggling wasn't tested. **Confirm behaviour on
  one throwaway message before relying on it in Phase 3.**
- **No native "fallback message on expiry" field exists.** §3.3 step 1's
  "time-out fallback message" needs to be built as an explicit follow-up
  rule/message reacting to the unanswered state, not configured on the
  expiring message itself.

Also resolved: deleting a whole micro dialog (needed for §2.4/§5's prune
list) is the dialog-level toolbar's **`Delete Dialog`** button, a separate
toolbar from the per-row node toolbar `rgroup_apply.py` already uses — see
`README.md`'s portal-navigation notes.
