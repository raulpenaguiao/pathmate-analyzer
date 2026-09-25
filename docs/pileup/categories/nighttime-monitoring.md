# Nighttime asthma monitoring (night preparation)

**Rank 1** · **Comes back until:** end of day · **Status:** v01, next to build ([rollout.md](../rollout.md), step 2)

**Goal.** Before bed, the patient puts on the smartwatch, puts the phone on its charger and places it near the bed, so the night can be monitored. The smartwatch-battery check is part of this.

**What the patient sees.** "Good evening! 🌙 Quick reminder to set up your devices for nighttime asthma monitoring! 😴📲", then a short checklist.

**Timing.** Starts 10 minutes before the patient's bedtime. In v02 it will nag until bedtime plus a grace period.

**If interrupted.**
- *Before the checklist is confirmed:* it starts over.
- *After:* it doesn't come back.

**Open items.**
- Build it on the reminder pattern, with rank.
- Fold in the smartwatch-battery prompt.

---
*Implementation (today):* DAILY BASIS, unconditional. It is sent at `$timeToSendSleepMonitoringDialog = $userSetBedtime − 0.17` (hours). The sending rule's caption says "Send sleep quality dialog", but what it actually starts is "Prompt patient to prepare for nighttime monitoring".
