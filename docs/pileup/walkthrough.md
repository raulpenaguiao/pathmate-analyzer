# A day with the new rules

One patient, one ordinary Wednesday, showing every rule from [priority.md](priority.md) and [interruptions.md](interruptions.md) in action. The timings use the defaults recommended in [decisions.md](decisions.md). Where a moment depends on an open decision, it says so.

**The patient's settings:** spirometry at 08:00; controller medication twice a day, 08:30 and 20:30 (no third dose); bedtime 22:00. The ACQ is due today at 18:00. Educational content is due this week, today at 17:00.

## Morning

**08:00 · Spirometry asks** (rank 1). Nothing else is open, so it starts.
> ALEX: Quick reminder to check your lung function with spirometry today!
> ALEX: Do you have your spirometer handy?  **[Yes] [No]**

The patient is making breakfast and doesn't answer.

**08:30 · Medication dose 1 is due** (rank 1), but spirometry, also rank 1, is still open. Equal ranks don't interrupt, so medication waits.

**08:30 · Spirometry counts as ignored.** It has gone unanswered for 30 minutes *(D1)*, so it closes quietly. Ignored is not interrupted: spirometry does **not** come back with "let's pick up where we left off". *(Whether it may ask once more before its window closes at 11:00 is D2.)*

**08:31 · Medication dose 1 asks.** The way is clear and it is still inside its window (08:30–11:30).
> ALEX: Quick reminder: it's time for your medication!
> ALEX: Did you take your medication?  **[Yes] [No]**
> Patient: **Yes**

The dose is recorded. That was the checkpoint, so medication dose 1 won't come back today.

## Afternoon

**17:00 · Educational content asks** (rank 4, due this week).
> ALEX: Is this a good time point to interact with educational material related to asthma? 🧐📖
> Patient: **Yes**

The patient has now answered, so the dialog counts as rank 1 until it ends, and nothing except safety may interrupt the video. At 17:12 the video ends and the dialog closes normally. Done for the week.

## Evening: an interruption and a comeback

**18:00 · The ACQ asks** (rank 2).
> ALEX: Hey there! ⏰ It's time to check in on your asthma with the questionnaire.

The patient sees it but doesn't open it yet.

**20:30 · Medication dose 2 is due** (rank 1). The ACQ is open but *idle* (not answered), and 1 is more important than 2, so medication interrupts. The ACQ's open question is cleared.
> ALEX: Quick reminder: it's time for your medication!
> ALEX: Did you take your medication?  **[Yes] [No]**
> Patient: **Yes**

**20:31 · The ACQ comes back.** Nothing is open any more, it's before the ACQ's expiry, and it had been shown but not finished.
> ALEX: Let's pick up where we left off.
> ALEX: It's time to check in on your asthma with the questionnaire…

No checkpoint had been passed, so it **starts over**. The patient opens the survey at 21:40 and is still answering at 21:50.

**21:50 · Night preparation is due** (rank 1, 10 minutes before bedtime). The ACQ is being *actively answered*, so it counts as rank 1 as well. Equal ranks wait, and night preparation waits.

**21:56 · The ACQ is finished**, then night preparation asks.
> ALEX: Good evening! 🌙 Quick reminder to set up your devices for nighttime asthma monitoring! 😴📲

The patient ticks the checklist. Done.

## Midnight: expiry

**00:00 · Daily reset.** Spirometry and medication reset for the new day. Had the ACQ been left unfinished, it could have kept coming back until the end of the week *(proposed expiry, D3)*. Education is done for this week, so it won't ask again before next week's due date.

## What this day shows

| Rule | Where you saw it |
|---|---|
| Higher beats lower | 20:30: medication interrupts an idle ACQ |
| Equals wait | 08:30: medication waits for spirometry. 21:50: night prep waits for the actively answered ACQ |
| Active answers are protected | 17:00 education, 21:50 ACQ |
| Interrupted → comes back, starts over | 20:31: "Let's pick up where we left off" |
| Checkpoint → doesn't come back | 08:31 medication, 17:12 education |
| Ignored → doesn't come back | 08:30 spirometry |
| Expiry | 00:00 reset |

**Compared with v01:** in v01, the ignored 08:00 spirometry question would still have been sitting open at 18:00 and 20:30. The v01 transition dialogs would have parked it and resumed it afterwards ("we had previously stopped somewhere else…"). The patient would have met a morning reminder in the evening, which is the pile-up.
