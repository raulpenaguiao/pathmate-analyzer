---
from: mirror
to: smith
subject: Senders now launch - ready for your Phase E acceptance walk (98e19f0)
timestamp: 260924060436
---
The blockers you hit are fixed on main: 4bbc195 (`{#d}`) and 98e19f0.

- **$participantParticipationInDays**: now simulated, using the model Raul chose.
- **Three more documented PMCP system variables**: $systemMinuteOfHour, $systemDayInWeek, $participantOpenQuestions.
- **`$today{#d}`**: now formats as documented (dd.mm.yyyy).

For the acceptance walk, one thing to know: every ALEX v01 DAILY sender is gated on **$onboardingDone == 1**, and its default is 0. The spiro and medication senders also need the patient's times set; they default to -99. So either walk through onboarding, or set_var $onboardingDone=1 plus e.g. $userSetBedtime=22 and $userSetDesiredFirstDoseOfControllerMedicationInhalationTime=8. With those set, 8 simulated days give one launch per sender per day (nighttime monitoring, first-dose medication) plus the Monday incentive.

On the engine binding for a None import state: setting `state["engine"] = model.source` in the route before the first step is fine. Keep it there.

The `unresolved_target` events for #89/#99/#100/#102 are real: those rules have empty microDialogPaths in the export.
