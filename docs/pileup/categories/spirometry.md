# Daily home spirometry

**Rank 1** · **Comes back until:** end of day · **Status:** live on the reminder pattern; interrupt retrofit pending

**Goal.** The patient does their daily lung-function measurement with the home spirometer.

**What the patient sees.** "Quick reminder to check your lung function with spirometry today!" → "Do you have your spirometer handy?" (Yes/No) → a link that opens the CLAID app → thanks, or on failure a retry or a how-to video.

**Timing.** From the patient's chosen time, the reminder nags for up to 3 hours, and never past the end of that part of the day.

**Spacing.** Never within 5 hours after a medication dose; before the dose is fine. When both are due together, spirometry goes first ([planning-ahead.md](../planning-ahead.md)).

**If interrupted.**
- *Before the measurement:* it comes back and starts over.
- *After the measurement:* it doesn't come back. Only "thanks" or feedback was left.

**Open items.**
- The Yes/No answer buttons render as raw text ("Yes:1 No:0"). The fix is queued.
- Interrupt retrofit ([rollout.md](../rollout.md), step 1).

---
*Implementation:* dialog "Prompt patient to conduct daily spirometry / … (v02)". The PERIODIC firing rule has five gates (`$spiroMesDone`, window start/end, `$spiroReminderStage`, `$participantOpenQuestions==0`). Variables: [reminder-pattern.md](../reminder-pattern.md#implementation).
