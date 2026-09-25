# Gamification

**Rank 5** · **Comes back until:** end of week · **Status:** v01, partly unbuilt

**Goal.** Motivate the patient to complete their daily routines with a weekly incentive: a prize draw or a "Streak Week".

**What the patient sees (Mondays).**
- "Today is the first day of the week. I will closely assist you throughout the week…"
- "I'm giving you the chance to win … The drawing will take place next Sunday evening."
- Or: "This week is special — it's Streak Week ✨…"

**What's broken.** "Status of weekly incentive" is an empty shell, so the patient never hears how they're doing or who won.

**Open items.** Build the weekly status and result messages; then pattern and rank.

---
*Implementation (today):* DAILY BASIS, `$systemDayInWeek == 1`, sent at `$userSetTimeOfTheDayForWeeklyIncentiveAnnouncement`. Dialog: "Introduction of weekly incentive".
