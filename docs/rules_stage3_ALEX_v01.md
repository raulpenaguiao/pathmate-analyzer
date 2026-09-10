# Stage 3 — rule-level timing & routing (ALEX v01)

Captured 2026-09-10 from the live PMCP editor's **Rules** tab
(`tools/coaching-bundle-export/probe_rules_tree.py, live PMCP Rules-tab .v-tree + Edit-rule modals`).

Machine-readable: `tools/coaching-bundle-export/rules_stage3_ALEX_v01.json`.

## What this is

The Report-HTML export and `coaching.bundle.v2.json` reconstruct a
coaching's *content* but not its *timing behaviour*. Timing lives on the
**rule** that starts a dialog, in its "Edit rule:" modal — not on the
message. This is that data for every one of the coaching's **25
message/dialog-sending rules** (the `message-icon-small.png` rows of the
Rules `.v-tree`; the other 97 nodes are condition/calculation rules).

## "Edit rule:" modal schema

| Field | Notes |
|---|---|
| Comment | rule label |
| Rule [x] / operator / Comparison term [y] | the condition; `(no value set)` + `calculate value but result is always true` on most senders (they fire whenever their parent condition-chain matches) |
| Store rule result to variable | usually unset on senders |
| **Send message if rule result is TRUE** | action checkbox — dispatch a single message via a *message group* |
| **Start micro dialog if rule result is TRUE** | action checkbox — launch a *micro dialog* |
| **Mark case as solved (unexpected message) and stop the current rule execution run** | action checkbox — **all 25 senders: false** |
| **Stop current rule execution run and finish coaching for this participant** | action checkbox — **all 25 senders: false** |
| Message group to send messages from | target when *Send message* is checked |
| Micro dialog to start | target when *Start micro dialog* is checked; a `" > "`-joined dialog path |
| Hour to send message (24h, 0 = immediately) | **a `$variable`**, not a literal — user-preference time or a reschedule new-time var. Empty = immediate. |
| Minutes after sending until message is handled as not answered | **default 4h** on every dialog sender; 19 min on the one message sender |
| Rules if participant DOES answer / DOES NOT answer | nested rule sub-trees; empty on 24 of 25 |

## The 25 sending rules

| # | Section | Rule | Action | Sends → | Send hour | Not-answered |
|--:|---|---|---|---|---|---|
| 0 | DAILY BASIS | 🧐💬 If required, send feedback on poor compliance with lung function mo | dialog | Prompt patient to conduct daily spirometry > Feedback on compliance regarding da | `$userSetTimeOfTheDayForFeedbackIfRequired` | 4 hours |
| 1 | DAILY BASIS | 💰 Introduce weekly incentive: $systemDayInWeek calculated value equals | dialog | Introduction of weekly incentive | `$userSetTimeOfTheDayForWeeklyIncentiveAnnouncement` | 4 hours |
| 2 | DAILY BASIS | 🌬️ Send regular pushed reminder for spirometry measurement (temp. disa | message | msg group: Test (expects NO answer) | `$userSetDesiredSpirometryTime` | 19 minutes |
| 3 | DAILY BASIS | 🌬️ Send regular reminder for spirometry measurement: calculate value b | dialog | Prompt patient to conduct daily spirometry | `$userSetDesiredSpirometryTime` | 4 hours |
| 4 | DAILY BASIS | Send sleep quality dialog: calculate value but result is always true | dialog | Prompt patient to prepare for nighttime monitoring | `$timeToSendSleepMonitoringDialog` | 4 hours |
| 5 | DAILY BASIS | 💊 Send regular reminder for first of the day controller medication inh | dialog | Prompt patient to take controller medication > Prompt patient to take first dose | `$userSetDesiredFirstDoseOfControllerMedicationInhalationTime` | 4 hours |
| 6 | DAILY BASIS | 👩‍🏫📚 Prompt user to interact with educational material: $today text va | dialog | Prompt patient to watch/read/listen educational material > Interaction with educ | `$userSetTimeOfTheDayForWeeklyFeedback` | 4 hours |
| 7 | DAILY BASIS | 💊 Send regular reminder for third of the day controller medication inh | dialog | Prompt patient to take controller medication > Prompt patient to take third dose | `$userSetDesiredThirdDoseOfControllerMedicationInhalationTime` | 4 hours |
| 8 | DAILY BASIS | 💊 Send regular reminder for second of the day controller medication in | dialog | Prompt patient to take controller medication > Prompt patient to take second dos | `$userSetDesiredSecondDoseOfControllerMedicationInhalationTime` | 4 hours |
| 9 | DAILY BASIS | 📋✏️ Prompt user to fill out ACQ: $today text value equals $dateOfNextA | dialog | Prompt patient to answer questions of the ACQ | `$userSetTimeOfTheDayForACQ` | 4 hours |
| 10 | DAILY BASIS | 🐞 Test sensor data retrieval: $userSetTimeOfTheDayForFeedbackIfRequire | dialog | 🐞 Testing sensor data retrieval | `$userSetTimeOfTheDayForFeedbackIfRequired` | 4 hours |
| 11 | DAILY BASIS | 🐞 Test time line of scheduled periodic events: $userSetTimeOfTheDayFor | dialog | 🐞 Testing time line of scheduled periodic events | `$userSetTimeOfTheDayForFeedbackIfRequired` | 4 hours |
| 12 | DAILY BASIS | 🐞 Send test dialog if debug mode is activated: $debugMode calculated v | dialog | Attic > Test dialog for debugging | `—` | 4 hours |
| 13 | PERIODIC BASIS | 🌬️ If still in time, send repeated reminder for spirometry measurement | dialog | Prompt patient to conduct daily spirometry | `$spiroMesTime` | 4 hours |
| 14 | PERIODIC BASIS | --- calculated value equals --- | dialog | START | `—` | 4 hours |
| 15 | PERIODIC BASIS | Check if reminder for delayed spiro measurement time is due: calculate | dialog | Prompt patient to conduct daily spirometry | `$spiroMesTimeDelay` | 4 hours |
| 16 | PERIODIC BASIS | Trigger sensor data updates: $triggerSensorDataUpdate calculated value | dialog | Sensor data updates | `—` | 4 hours |
| 17 | PERIODIC BASIS | 👩‍🏫📚 Rescheduled prompting of user to interact with educational materi | dialog | Prompt patient to watch/read/listen educational material > Interaction with educ | `$newTimeForInteractingWithEducationalMaterial` | 4 hours |
| 18 | PERIODIC BASIS | 📋✏️ Rescheduled prompting of user to fill out ACQ: calculate value but | dialog | Prompt patient to answer questions of the ACQ | `$newTimeForACQ` | 4 hours |
| 19 | PERIODIC BASIS | 💊 Rescheduled reminder to inhale first medication dose: calculate valu | dialog | Prompt patient to take controller medication > Prompt patient to take first dose | `$myFirstMedication_newTimeForFirstMedication` | 4 hours |
| 20 | PERIODIC BASIS | 💊 Rescheduled reminder to inhale second medication dose: calculate val | dialog | Prompt patient to take controller medication > Prompt patient to take second dos | `$mySecondMedication_newTimeForSecondMedication` | 4 hours |
| 21 | PERIODIC BASIS | 💊 Rescheduled reminder to inhale third medication dose: calculate valu | dialog | Prompt patient to take controller medication > Prompt patient to take third dose | `$myThirdMedication_newTimeForThirdMedication` | 4 hours |
| 22 | PERIODIC BASIS | 🌬️ Rescheduled reminder to perform spirometry: calculate value but res | dialog | Prompt patient to conduct daily spirometry | `$mySpiro_newTimeForSpirometry` | 4 hours |
| 23 | USER INTENTION | $phaseGoPerformed calculated value equals 0 | dialog | START | `—` | 4 hours |
| 24 | USER INTENTION | ✏️ Personal data edited: $participantIntention text value equals perso | dialog | ⚙️ Controls > 📄 dataEdited | `—` | 4 hours |

## Notes

- **Scheduling is in the condition, not this field.** `Hour to send`
  binds to a variable; *whether* a rule fires today is decided by the
  condition chain above it (`$today text value equals $dateOfNextACQ`,
  `$systemHourOfDay calculated value is bigger than 3`, …).
- **Reschedule pairs.** PERIODIC BASIS has six
  `Check whether $…_userRequestedNewTime = 1` → (reset flag) + (re-send
  with the new-time var) handlers, one each for education, ACQ, med 1/2/3,
  spirometry.
- **UNEXPECTED MESSAGE is empty.** All inbound handling is under USER
  INTENTION (`go` / `coach` / `language` / personal-data-edited).
- **Pile-up / interruption** is emergent from condition-rule order +
  these per-rule timeouts, exactly as the Rules tab Info panel states.
  No sender sets a stop/solve checkbox, so senders never cut the run;
  the guard rules above them do.
