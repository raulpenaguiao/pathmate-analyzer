# Misc: FAQ, air quality, clinic visits

**Rank 6** · **Comes back until:** FAQ and clinic end of week, air quality end of day · **Status:** content exists but nothing triggers it

| Item | Goal | What the patient sees |
|---|---|---|
| FAQ | Point to the in-app FAQ list, in the first 2 weeks and then every 3 months | "Got questions about asthma? 🤔 We've got answers! Check out the FAQ list…" (go now / remind me later) |
| Air quality | Warn on days when allergens or pollutants are extremely high | "Warning! ⚠️ Today's air quality isn't great—allergens [pollutants] are high…" |
| Clinic visits | Remind the patient of the four clinic visits in the study year | "Hey! Just a reminder, your doctor's appointment is coming up on [date] at [time] at [address]. 🩺" |

**What's broken.**
- No rule starts any of the three.
- The FAQ and air-quality dialogs open with PMCP's "park and recall old questions" setting, the v01 mechanism behind the pile-up ([problem.md](../problem.md)). It must be removed before they're wired up.

**Open items.** Triggers (sensor thresholds for air quality, dates for the clinic), then pattern and rank.
