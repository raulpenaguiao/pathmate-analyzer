# Asthma Control Questionnaire (ACQ)

**Rank 2** · **Comes back until:** end of week · **Status:** v01 ([rollout.md](../rollout.md), step 3)

**Goal.** The patient fills in the ACQ every two weeks. The questionnaire itself is a survey; this dialog is the reminder that leads to it.

**What the patient sees.** A rotating reminder, for example: "Hey there! ⏰ It's time to check in on your asthma with the questionnaire. Let's see how you're doing! 💨" The patient can ask for another time.

**If interrupted.**
- *Before the patient decides:* it starts over.
- *After the patient picked a new time:* it continues at that time.
- *After the survey:* it doesn't come back.

**Open items.** Reminder pattern, rank. **Ask the advisor:** the sandbox has `$hyperparameterNumberOfDaysBetweenACQs = 1`, which looks like a test value, since the dialog says biweekly. Use 14 on the workbench unless told otherwise.

---
*Implementation (today):* DAILY BASIS, when `$today == $dateOfNextACQ`, sent at `$userSetTimeOfTheDayForACQ`. The next date advances by `$hyperparameterNumberOfDaysBetweenACQs`. Rescheduling runs from PERIODIC BASIS via `$userRequestedNewTimeForACQ` / `$newTimeForACQ`. No open-question check.
