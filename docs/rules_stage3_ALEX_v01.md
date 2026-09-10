# Stage 3 — rule tree + per-rule timing & routing (ALEX v01)

Captured 2026-09-10 from the live PMCP editor's **Rules** tab.
Machine-readable: `tools/coaching-bundle-export/rules_stage3_ALEX_v01.json`
(same schema `export_rules.py` emits as `coaching.rules.json` / merges into
`coaching.bundle.v3.json`). Session log:
`autochanges/2026-09-10-rules-tree-stage3-sweep.md`.

**117 rule-tree nodes** — 92 condition/calc rules, 25 message/dialog senders (all 25 captured). Sections: DAILY BASIS, PERIODIC BASIS, USER INTENTION (UNEXPECTED MESSAGE is empty).

## "Edit rule:" modal schema (senders)

| Field | Notes |
|---|---|
| `actions[]` | which TRUE-result checkboxes are set: `send_message`, `start_micro_dialog`, `mark_solved_stop_run`, `stop_run_finish_coaching`. **No sender sets the last two** — senders never cut the run; the guard rules above them do. |
| `microDialogToStart` / `microDialogPath[]` | target when `start_micro_dialog` — a `" > "`-joined dialog path |
| `messageGroup` | target when `send_message` |
| `sendHourVariable` | **a `$variable`** (user-preference time or reschedule new-time), not a literal. `null` = immediate / event-driven. Actual scheduling is in the rule's condition chain. |
| `notAnsweredTimeoutMinutes` | **240 (4h)** on every dialog sender; 19 on the one `send_message` rule |
| `doesAnswerRules` / `doesNotAnswerRules` | nested rule captions; empty on 24 of 25 |

## The 25 sending rules

| Section | Rule | Action | Sends → | Send hour | Timeout |
|---|---|---|---|---|---|
| DAILY BASIS | 🧐💬 If required, send feedback on poor compliance with lung functio | dialog | Prompt patient to conduct daily spirometry > Feedback on compliance re | `$userSetTimeOfTheDayForFeedbackIfRequired` | 240m |
| DAILY BASIS | 💰 Introduce weekly incentive: $systemDayInWeek calculated value eq | dialog | Introduction of weekly incentive | `$userSetTimeOfTheDayForWeeklyIncentiveAnnouncement` | 240m |
| DAILY BASIS | 🌬️ Send regular pushed reminder for spirometry measurement (temp.  | message | msg: Test (expects NO answer) | `$userSetDesiredSpirometryTime` | 19m |
| DAILY BASIS | 🌬️ Send regular reminder for spirometry measurement: calculate val | dialog | Prompt patient to conduct daily spirometry | `$userSetDesiredSpirometryTime` | 240m |
| DAILY BASIS | Send sleep quality dialog: calculate value but result is always tr | dialog | Prompt patient to prepare for nighttime monitoring | `$timeToSendSleepMonitoringDialog` | 240m |
| DAILY BASIS | 💊 Send regular reminder for first of the day controller medication | dialog | Prompt patient to take controller medication > Prompt patient to take  | `$userSetDesiredFirstDoseOfControllerMedicationInhalationTime` | 240m |
| DAILY BASIS | 👩‍🏫📚 Prompt user to interact with educational material: $today tex | dialog | Prompt patient to watch/read/listen educational material > Interaction | `$userSetTimeOfTheDayForWeeklyFeedback` | 240m |
| DAILY BASIS | 💊 Send regular reminder for third of the day controller medication | dialog | Prompt patient to take controller medication > Prompt patient to take  | `$userSetDesiredThirdDoseOfControllerMedicationInhalationTime` | 240m |
| DAILY BASIS | 💊 Send regular reminder for second of the day controller medicatio | dialog | Prompt patient to take controller medication > Prompt patient to take  | `$userSetDesiredSecondDoseOfControllerMedicationInhalationTime` | 240m |
| DAILY BASIS | 📋✏️ Prompt user to fill out ACQ: $today text value equals $dateOfN | dialog | Prompt patient to answer questions of the ACQ | `$userSetTimeOfTheDayForACQ` | 240m |
| DAILY BASIS | 🐞 Test sensor data retrieval: $userSetTimeOfTheDayForFeedbackIfReq | dialog | 🐞 Testing sensor data retrieval | `$userSetTimeOfTheDayForFeedbackIfRequired` | 240m |
| DAILY BASIS | 🐞 Test time line of scheduled periodic events: $userSetTimeOfTheDa | dialog | 🐞 Testing time line of scheduled periodic events | `$userSetTimeOfTheDayForFeedbackIfRequired` | 240m |
| DAILY BASIS | 🐞 Send test dialog if debug mode is activated: $debugMode calculat | dialog | Attic > Test dialog for debugging | — | 240m |
| PERIODIC BASIS | 🌬️ If still in time, send repeated reminder for spirometry measure | dialog | Prompt patient to conduct daily spirometry | `$spiroMesTime` | 240m |
| PERIODIC BASIS | --- calculated value equals --- | dialog | START | — | 240m |
| PERIODIC BASIS | Check if reminder for delayed spiro measurement time is due: calcu | dialog | Prompt patient to conduct daily spirometry | `$spiroMesTimeDelay` | 240m |
| PERIODIC BASIS | Trigger sensor data updates: $triggerSensorDataUpdate calculated v | dialog | Sensor data updates | — | 240m |
| PERIODIC BASIS | 👩‍🏫📚 Rescheduled prompting of user to interact with educational ma | dialog | Prompt patient to watch/read/listen educational material > Interaction | `$newTimeForInteractingWithEducationalMaterial` | 240m |
| PERIODIC BASIS | 📋✏️ Rescheduled prompting of user to fill out ACQ: calculate value | dialog | Prompt patient to answer questions of the ACQ | `$newTimeForACQ` | 240m |
| PERIODIC BASIS | 💊 Rescheduled reminder to inhale first medication dose: calculate  | dialog | Prompt patient to take controller medication > Prompt patient to take  | `$myFirstMedication_newTimeForFirstMedication` | 240m |
| PERIODIC BASIS | 💊 Rescheduled reminder to inhale second medication dose: calculate | dialog | Prompt patient to take controller medication > Prompt patient to take  | `$mySecondMedication_newTimeForSecondMedication` | 240m |
| PERIODIC BASIS | 💊 Rescheduled reminder to inhale third medication dose: calculate  | dialog | Prompt patient to take controller medication > Prompt patient to take  | `$myThirdMedication_newTimeForThirdMedication` | 240m |
| PERIODIC BASIS | 🌬️ Rescheduled reminder to perform spirometry: calculate value but | dialog | Prompt patient to conduct daily spirometry | `$mySpiro_newTimeForSpirometry` | 240m |
| USER INTENTION | $phaseGoPerformed calculated value equals 0 | dialog | START | — | 240m |
| USER INTENTION | ✏️ Personal data edited: $participantIntention text value equals p | dialog | ⚙️ Controls > 📄 dataEdited | — | 240m |

## Rule-tree skeleton

`ruleTree[]` in the JSON: every rule in tree order with `uid`, `section`,
`depth`, `parentUid`, `kind` (`condition` / `sender`), and `caption`. This
is the execution order — pile-up analysis (workstream 2b) reads it together
with the sender timeouts above.

## Notes

- **Reschedule pairs** (PERIODIC BASIS): six `Check whether
  $…_userRequestedNewTime = 1` → (reset flag) + (re-send with the new-time
  var) handlers — education, ACQ, med 1/2/3, spirometry.
- **UNEXPECTED MESSAGE empty**; all inbound handling is under USER INTENTION.
- **Pile-up / interruption** is emergent from condition-rule order + these
  per-rule timeouts, per the Rules-tab Info panel. No P0–P3 tier system.
