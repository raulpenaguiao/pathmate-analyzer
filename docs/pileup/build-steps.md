# Build steps

How to build the design in the PMCP editor, step by step. Written for the **new test-workbench coaching** Raul is setting up. **No writes happen before that coaching exists.** Every live step goes through Warden's browser lock.

Notation: *rule node* = a node in the Rules tree. Nested nodes act as AND: a child only runs if its parent was true (confirmed live, see the pile-up findings in the archive). An *assignment* is a node with the operator "calculate value (or create text) but result is always true" and a result variable.

---

## Phase A: platform tests (one browser session, on the workbench)

The design depends on three behaviours the PMCP docs don't describe. Each test is small and throwaway.

| # | Question | Setup | Pass means | If it fails |
|---|---|---|---|---|
| A1 | Does "clears the current dialog cascade" on dialog B's first message remove dialog A's open, unanswered question? | Test dialog A asks a Yes/No question. Test dialog B's first message has the clear setting. Start A, don't answer, then start B. Finish B. | A's question is gone and does not reappear by itself | Use PMCP's own recall instead and design around it (bigger change; back to Raul) |
| A2 | Does a variable set by one PERIODIC rule show up in a later rule in the same pass? | Rule 1 sets `$t=1`; rule 2 (below it) fires a test message only if `$t==1`. Reset `$t=0` daily. | The message fires on the same pass | Add a "one start per pass" flag, or rely on rank-order spacing (note it in interruptions.md) |
| A3 | Do a sending rule's "does not answer" follow-up rules run when its question times out? | Test sender with a 1-minute timeout and one "does not answer" rule setting `$u=1`. Let it time out. | `$u == 1` in the participant's variables | Use the time-based cleanup rule (B5), which is the design default anyway |

Log each result in `autochanges/`, then update [interruptions.md](interruptions.md#not-yet-verified-needs-one-test-on-the-sandbox-coaching-booked-through-warden).

---

## Phase B: shared infrastructure (once per coaching)

**B1. Variables**

| Variable | Type | Default | Meaning |
|---|---|---|---|
| `$openDialogName` | text | `""` | the ranked dialog currently open |
| `$openDialogRank` | number | `99` | its rank (99 = nothing open) |
| `$openDialogStaleAt` | number | `0` | `$timeDecimal` after which an unanswered open dialog counts as ignored |
| `$hyperparameterIdleMinutes` | number | `30` *(D1)* | how long an unanswered question may block others |

**B2. Daily reset.** In the DAILY BASIS reset block, add assignments that reset the three markers to their defaults. Anything open at midnight is over.

**B3. Weekly reset rule.** A DAILY BASIS rule `$systemDayInWeek == 1` with child assignments. Each end-of-week dialog adds its own resets here (C6).

---

## Phase C: the recipe for one ranked dialog X (rank r)

Do these for each dialog, in the order from [rollout.md](rollout.md). Category-specific values are in the table under Phase D.

**C1. Variables:** `$X_started` (number, 0) and `$X_resumeMode` (number, 0). Reminders reuse their existing `…ReminderStage` as `started`.

**C2. Firing rule** (PERIODIC BASIS; place it in rank order among the other firing rules). Nested gates, top to bottom:
1. X's own "is due" conditions: date, time, the reminder window on the first showing. These are the existing gates, e.g. spirometry's gates 1–4.
2. `$X_resumeMode` *not equal* `1`
3. `$openDialogName` *text value not equal* `X`
4. `$openDialogRank` *is bigger than* `r`. This replaces the old `$participantOpenQuestions == 0` gate.
5. Sender: start dialog X. Keep the rule's own "not answered" timeout at least as long as `$hyperparameterIdleMinutes`.

**C3. Opening decision point** (new first row of dialog X), flat branches in this order:
1. If `$X_started == 1`: jump to the **re-entry opener**, one or two plain message rows written for this dialog (wording in [interruptions.md](interruptions.md#the-idea-come-back-with-context), D8), which then continue into the dialog's first question.
2. If `$X_resumeMode == 2`: jump to dialog "X, part 2". Only for dialogs that have one (C5).
3. Assign `$X_started = 1`.
4. Assign `$openDialogName = "X"` (create text), `$openDialogRank = r`, `$openDialogStaleAt = $timeDecimal + $hyperparameterIdleMinutes/60`.

**C4. The first visible message** has "clears the current dialog cascade" **on**, and has "expects an answer" **off** (the two are mutually exclusive in PMCP; Phase 3.4 log). "Deactivates and remembers" and both "recalls…" settings stay **off**.

**C5. Checkpoints.** At each checkpoint, add an assignment for `$X_resumeMode` (1 or 2, per the table). Where the table says "split", move everything after the checkpoint into a new dialog "X, part 2". The checkpoint then jumps there, and part 2 gets its own opening decision point (C3).

**C6. Engaged and end.**
- On the patient's first answer, assign `$openDialogRank = 1` (active-answer protection).
- On **every** answer, re-assign `$openDialogStaleAt = $timeDecimal + $hyperparameterIdleMinutes/60`. An active conversation never counts as ignored, but one the patient walks away from mid-way clears after the idle time instead of blocking everything until midnight.
- At every normal stop: assign `$X_resumeMode = 1`, `$openDialogName = ""`, `$openDialogRank = 99`.
- Put the condition and its assignments as **children** of the answer check, not beside it. Flat siblings are OR'd; this is the latent issue Mirror found in the medication dialogs.

**C7. Ignored-dialog cleanup** (PERIODIC BASIS, above the firing rules):
`$openDialogName == "X"` AND `$timeDecimal is bigger than $openDialogStaleAt` → assign `$X_resumeMode = 1`, `$openDialogName = ""`, `$openDialogRank = 99`.
*(With D2 = "one re-ask": for reminders, set `…ReminderStage = 2` instead of resumeMode 1, and allow one more firing while stage < 2.)*

**C8. Expiry resets.** End-of-day dialogs: add `$X_started = 0` and `$X_resumeMode = 0` to the daily reset (B2). End-of-week dialogs: add them to the weekly reset (B3).

**C9. Verify** before moving to the next dialog:
- A fresh export shows every node above. Check by dialog path, never by uid.
- Mirror's chat simulator runs these scenarios: the dialog alone; interrupted while idle by a rank-1 dialog; ignored; answered then interrupted (it must not be interrupted).
- A real-device run on the workbench participant.
- A log in `autochanges/`.

---

## Phase D: per-category values

| Dialog | r | Due / window | Checkpoint → resumeMode | Split? | Expiry |
|---|---|---|---|---|---|
| Spirometry | 1 | `$spiroMesTime` → +180 min | measurement done → 1 | no | day |
| Medication dose i (×3) | 1 | `doseTime_i` → +180 min | dose answered → 1 | no | day |
| Night preparation (incl. battery) | 1 | bedtime − 10 min → bedtime + grace (D-value needed) | checklist confirmed → 1 | no | day* |
| ACQ | 2 | `$today == $dateOfNextACQ` | new time chosen → 2; survey done → 1 | **yes** | week* |
| Compliance coaching | 2 | trigger to design (D7) | message delivered → 1 | no | day* |
| Sleep quality | 3 | night data missing/poor (trigger to design) | answered → 1 | no | day* |
| Education + health literacy | 4 | `$today == $dateOfNextDisplayOfEducationalContents` | new time chosen → 2; material done → 1 | **yes** | week |
| Gamification | 5 | Monday | announcement delivered → 1 | no | week |
| FAQ / air quality / clinic | 6 | triggers to design | delivered → 1 | no | week / day / week* |

\* proposed, see [decisions.md](decisions.md) D3.

## Also carried into the workbench build

- **Spirometry Yes/No buttons.** Rows 3–6 of the v02 dialog store answer options on one line (`Yes:1 No:0`). Enter them as two lines (`Yes:1` newline `No:0`) when building on the workbench. The fix on the old sandbox was dropped (never applied).
- **Remove v01's recall setting** from the FAQ and air-quality dialogs before wiring them up.
