# A day with the new rules

One patient, one ordinary Wednesday, showing every rule from [priority.md](priority.md) and [interruptions.md](interruptions.md) in action. The timings use the defaults recommended in [decisions.md](decisions.md). Where a moment depends on an open decision, it says so.

**The patient's settings:** spirometry at 08:00; controller medication twice a day, 08:30 and 20:30 (no third dose); bedtime 22:00. The ACQ is due today at 18:00. Educational content is due this week, today at 17:00.

## Before the first day: planning ahead

At onboarding the patient chose spirometry at 11:00 and medication at 08:30. ALEX's schedule check flagged it: 11:00 is only 2½ hours after the dose, and spirometry needs 5 hours after medication.
> ALEX: One small thing about your schedule. Spirometry works best *before* your medication, or at least 5 hours after it. Would 07:30 work for your spirometry instead?
> Patient: 07:30 is too early for me. **08:00?**

08:00 is before the dose, so it satisfies the 5-hour rule, although it's only 30 minutes before medication. The patient has the final say (D11), so 08:00 it is. The day below shows what that costs: an ignored 08:00 spirometry question, and a dose that has to wait for it.

## Morning

**08:00 · Spirometry asks** (rank 1). Nothing else is open, so it starts.
> ALEX: Quick reminder to check your lung function with spirometry today!
> ALEX: Do you have your spirometer handy?  **[Yes] [No]**

The patient is making breakfast and doesn't answer.

**08:30 · Medication dose 1 is due** (rank 1), but spirometry, also rank 1, is still open. Equal ranks don't interrupt, so medication waits.

**08:30 · Spirometry counts as ignored.** It has gone unanswered for 30 minutes (D1), so it steps aside. It isn't finished, though: it has one re-ask left (D2).

**08:31 · Medication dose 1 is next, but spirometry isn't done yet.** Spirometry isn't allowed for 5 hours after a dose, so ALEX first offers spirometry *(planning ahead, D12)*:
> ALEX: Earlier today I reminded you about your spirometry measurement. We didn't get to it, so let's start again from the top. After your medication it has to wait about 5 hours; would you like to do it now?  **[Yes, now] [Later]**
> Patient: **Yes, now**

This offer comes from the medication reminder itself (D12, still open), so the usual 30-minute spacing before a re-ask doesn't apply. It uses up spirometry's one re-ask, and it comes through the re-entry opener: the patient is told what this is and why it's back. The patient measures, and spirometry is done for the day. *(Without D12, spirometry's re-ask would come no sooner than 09:00, and the 5-hour post-dose rule would then hold it until 13:40, after its window closes at 11:00. Spirometry would be missed for the day. This is the strongest argument for D12 = A.)*

**08:40 · Medication dose 1 asks.**
> ALEX: Quick reminder: it's time for your medication!
> ALEX: Did you take your medication?  **[Yes] [No]**
> Patient: **Yes**

The dose is recorded. That was the checkpoint, so medication dose 1 won't come back today.

## Afternoon

**17:00 · Educational content asks** (rank 4, due this week).
> ALEX: Is this a good time point to interact with educational material related to asthma? 🧐📖
> Patient: **Yes**

The patient has now answered, so the dialog counts as rank 1, and nothing except safety may interrupt the video. The protection lasts up to one hour from this answer, until 18:00 *(D13)*. After that the dialog would drop back to rank 4. At 17:12 the video ends and the dialog closes normally, well inside the hour. Done for the week.

## Evening: an interruption and a comeback

**18:00 · The ACQ asks** (rank 2).
> ALEX: Hey there! ⏰ It's time to check in on your asthma with the questionnaire.

The patient sees it but doesn't open it yet.

**20:30 · Medication dose 2 is due** (rank 1). The ACQ is open but *idle* (not answered), and 1 is more important than 2, so medication interrupts. The ACQ's open question is cleared.
> ALEX: Quick reminder: it's time for your medication!
> ALEX: Did you take your medication?  **[Yes] [No]**
> Patient: **Yes**

**20:31 · The ACQ comes back.** Nothing is open any more, it's before the ACQ's expiry, and it had been shown but not finished.
> ALEX: Earlier I asked you to fill in your asthma questionnaire (ACQ), and we got interrupted. Here it is again.
> ALEX: It's time to check in on your asthma with the questionnaire…

This is the defining change. v01 would have re-surfaced the ACQ's bare question with no framing. Here the ACQ **starts over**, and the opener first tells the patient what this is and why it's back. The patient opens the survey at 21:40 and is still answering at 21:50.

**21:50 · Night preparation is due** (rank 1, 10 minutes before bedtime). The ACQ is being *actively answered*, so it counts as rank 1 as well. Equal ranks wait, and night preparation waits.

**21:56 · The ACQ is finished**, then night preparation asks.
> ALEX: Good evening! 🌙 Quick reminder to set up your devices for nighttime asthma monitoring! 😴📲

The patient ticks the checklist. Done.

## Midnight: expiry

**00:00 · Daily reset.** Spirometry and medication reset for the new day. Had the ACQ been left unfinished, it could have kept coming back until the end of the week *(D3)*. Education is done for this week, so it won't ask again before next week's due date.

## What this day shows

| Rule | Where you saw it |
|---|---|
| Higher beats lower | 20:30: medication interrupts an idle ACQ |
| Equals wait | 08:30: medication waits for spirometry. 21:50: night prep waits for the actively answered ACQ |
| Active answers are protected | 17:00 education, 21:50 ACQ |
| **Interrupted → comes back from the beginning, with context** | 20:31: the ACQ's re-entry opener |
| Checkpoint → doesn't come back | 08:40 medication, 17:12 education |
| Ignored → steps aside, then one re-ask with context | 08:30 → 08:31 spirometry |
| Expiry | 00:00 reset |
| Planning ahead | onboarding: spirometry moved before the dose; 08:31: spirometry offered before the dose |

**Compared with v01:** in v01, the ignored 08:00 spirometry question would still have been sitting open at 18:00 and 20:30. The v01 transition dialogs would have parked it and resumed it afterwards ("we had previously stopped somewhere else…"). The patient would have met a morning question in the evening, mid-conversation, with nothing saying what it was about or where to pick up.
