# Educational content (incl. health literacy)

**Rank 4** · **Comes back until:** end of week · **Status:** v01 ([rollout.md](../rollout.md), step 4)

**Goal.** The patient regularly engages with asthma education: videos, podcasts, text and infocards, plus age-specific sequences for ages 10–14 and 15–19. The health-literacy questions belong here too, at the same rank (Raul, 2026-09-25).

**What the patient sees.** "Is this a good time point to interact with educational material related to asthma…? 🧐📖", then a short intro line and the material. The patient can ask for another time.

**If interrupted.**
- *Before the patient decides:* it starts over.
- *After choosing a later time:* it continues then.
- *After the material:* it doesn't come back.

**Open items.** Reminder pattern, rank. The parent dialog "Prompt patient to watch/read/listen educational material" is an empty shell; the real content is in its child dialog.

---
*Implementation (today):* DAILY BASIS, when `$today == $dateOfNextDisplayOfEducationalContents`, sent at `$userSetTimeOfTheDayForWeeklyFeedback` (it reuses the weekly-feedback time). Rescheduling uses `$userRequestedNewTimeForEducationalContents`. Dialog: "… / Interaction with educational content and rescheduling".
