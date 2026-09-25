# The reminder pattern

Every dialog that asks the patient to *do* something today (measure, inhale, prepare devices, fill in a questionnaire) is built from the same block. Spirometry was the first to use it; medication was the second.

## In plain words

1. **A window, not a moment.** The reminder first appears at the patient's chosen time (the *soft start*) or as soon as the way is clear. If other dialogs keep it waiting, it may still make its first appearance until its expiry (end of day, D4). The **window**, a grace period of currently 3 hours and never later than the end of its part of the day, limits the one re-ask.
2. **It steps aside, asks once more, then closes itself.** If ignored for 30 minutes it steps aside. It asks once more later inside the window, with its re-entry opener (D2). If that is ignored too, it says a short goodbye ("No worries, we'll check in again tomorrow") instead of lingering.
3. **One at a time.** At most one copy of a reminder is ever open. If the patient asks to be reminded later, the same reminder simply moves to the new time; no second one is created.
4. **It respects rank.** It only starts if nothing equally or more important is open ([priority.md](priority.md)). If it gets interrupted, the rules in [interruptions.md](interruptions.md) apply.
5. **Active answers are protected.** Once the patient has started answering, the reminder counts as rank 1 for up to an hour (D13), so it can't be yanked away mid-answer.

## Why a window

v01's reminders stayed open indefinitely. The window guarantees that a reminder the patient ignored gets out of the way, and in particular gives lower-ranked content its turn later in the day ([priority.md](priority.md#a-known-risk-and-what-keeps-it-in-check)).

---
### Implementation (as prototyped for spirometry on the sandbox; medication mirrors it per dose)

| Piece | Variable(s) |
|---|---|
| Soft start | `$spiroMesTime` (patient's chosen time) |
| Window end | `$spiroWindowEnd = min($spiroMesTime + $hyperparameterSpiroGraceMinutes/60, end of the next day-part)`; grace = 180 min |
| Done today | `$spiroMesDone` |
| Sent today | `$spiroReminderStage` (0 = not yet) |
| Actively answering | `$spiroReminderEngaged` |
| Day parts | `$currentDaySlot` from `$hyperparameterMorningEndHour` (11), `…MiddayEndHour` (17), `…EveningEndHour` (22) |

- **Daily reset (00:00, DAILY BASIS):** done, stage and engaged go back to 0; the window end is recomputed.
- **Firing (PERIODIC BASIS):** not done, now inside the window, not yet sent, nothing open. The last condition becomes the rank check from [interruptions.md](interruptions.md#implementation) in the workbench build.
- **Expiry:** set on the message itself ("minutes after sending until message is handled as unanswered"). PMCP has no built-in goodbye-on-expiry message, so the goodbye is its own follow-up step.

Medication uses `$myMedication_{doseTime,windowEnd,done,reminderStage,engaged}_i` for doses i = 1, 2, 3, also with a 180-minute grace. Build logs: `autochanges/2026-09-11…` to `2026-09-17…`.
