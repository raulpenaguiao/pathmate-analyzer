# The reminder pattern

Every dialog that asks the patient to *do* something today (measure, inhale, prepare devices, fill in a questionnaire) is built from the same block. Spirometry was the first to use it; medication was the second.

## In plain words

1. **A window, not a moment.** The reminder may first appear at the patient's chosen time (the *soft start*). It stops nagging after a set grace period, currently 3 hours for both spirometry and medication, and never later than the end of the part of the day it belongs to (morning / midday / evening / night).
2. **It closes itself.** When the window ends unanswered, the reminder says a short goodbye ("No worries, we'll check in again tomorrow") instead of lingering.
3. **One at a time.** At most one copy of a reminder is ever open. If the patient asks to be reminded later, the same reminder simply moves to the new time; no second one is created.
4. **It respects rank.** It only starts if nothing equally or more important is open ([priority.md](priority.md)). If it gets interrupted, the rules in [interruptions.md](interruptions.md) apply.
5. **Active answers are protected.** Once the patient has started answering, the reminder counts as rank 1 until it ends, so it can't be yanked away mid-answer.

## Why a window

v01's reminders stayed open indefinitely. The window guarantees that a reminder the patient ignored gets out of the way, and in particular gives lower-ranked content its turn later in the day ([priority.md](priority.md#a-known-risk-and-what-keeps-it-in-check)).

---
### Implementation (as built for spirometry; medication mirrors it per dose)

| Piece | Variable(s) |
|---|---|
| Soft start | `$spiroMesTime` (patient's chosen time) |
| Window end | `$spiroWindowEnd = min($spiroMesTime + $hyperparameterSpiroGraceMinutes/60, end of the next day-part)`; grace = 180 min |
| Done today | `$spiroMesDone` |
| Sent today | `$spiroReminderStage` (0 = not yet) |
| Actively answering | `$spiroReminderEngaged` |
| Day parts | `$currentDaySlot` from `$hyperparameterMorningEndHour` (11), `…MiddayEndHour` (17), `…EveningEndHour` (22) |

- **Daily reset (00:00, DAILY BASIS):** done, stage and engaged go back to 0; the window end is recomputed.
- **Firing (PERIODIC BASIS):** not done, now inside the window, not yet sent, nothing open. The last condition becomes the rank check from [interruptions.md](interruptions.md#implementation) in the retrofit.
- **Expiry:** set on the message itself ("minutes after sending until message is handled as unanswered"). PMCP has no built-in goodbye-on-expiry message, so the goodbye is its own follow-up step.

Medication uses `$myMedication_{doseTime,windowEnd,done,reminderStage,engaged}_i` for doses i = 1, 2, 3, also with a 180-minute grace. Build logs: `autochanges/2026-09-11…` to `2026-09-17…`.
