# Asthma Control Questionnaire (ACQ)

**Rank 2** · **Comes back until:** end of week *(proposed)* · **Status:** v01 ([rollout.md](../rollout.md), step 3)

**Goal.** The patient fills in the ACQ every two weeks. The questionnaire itself is a survey; this dialog is the reminder that leads to it.

**What the patient sees.** A rotating reminder, for example: "Hey there! ⏰ It's time to check in on your asthma with the questionnaire. Let's see how you're doing! 💨" The patient can ask for another time.

**If interrupted.**
- *Before the patient decides:* it starts over.
- *After the patient picked a new time:* it continues at that time.
- *After the survey:* it doesn't come back.

**Open items.** Reminder pattern, rank.

---
*Implementation (today):* DAILY BASIS, when `$today == $dateOfNextACQ`, sent at `$userSetTimeOfTheDayForACQ`. The next date advances by `$hyperparameterNumberOfDaysBetweenACQs`. Rescheduling runs from PERIODIC BASIS via `$userRequestedNewTimeForACQ` / `$newTimeForACQ`. No open-question check.
