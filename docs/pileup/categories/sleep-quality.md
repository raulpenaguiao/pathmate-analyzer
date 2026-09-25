# Sleep quality inquiry

**Rank 3** · **Comes back until:** end of day · **Status:** content exists but nothing triggers it

**Goal.** Ask about last night's sleep, **only** when the night's monitoring data is missing or shows very poor sleep.

**What the patient sees (content already written).**
- "How did you sleep?" and follow-up questions.
- A related offer: "Thanks for enabling nighttime asthma monitoring last night! … Would you like to know more about the quality of your sleep last night?"

**What's broken.** No rule starts either dialog, and the "missing or poor data" condition isn't implemented anywhere.

**Open items.** Define "poor" from the sensor data, add the trigger, then apply the pattern and rank.

---
*Implementation:* dialogs "Inquire about last night's sleep" and "Prompt patient to prepare for nighttime monitoring / Medical feedback sleep quality".
