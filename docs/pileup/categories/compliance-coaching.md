# Compliance coaching

**Rank 2** · **Comes back until:** end of day · **Status:** content exists but is not wired up

**Goal.** Re-engage patients who start missing measurements or doses, with praise when they're consistent. In extreme cases, escalate to parents or caregivers by SMS or email.

**What the patient sees (content already written).**
- "I noticed you missed a spirometry session. It's okay—let's work together to get back on track!"
- Similar messages for missed doses and missed nights.
- "Great job staying consistent…" praise variants.

**What's broken.**
- The only rule (too many days without spirometry) starts an **empty** dialog, so nothing is sent.
- Medication and nighttime compliance have no rule at all.
- The escalation and adherence-barriers dialogs are empty shells.

**Open items.** Design the triggers (which thresholds, how often), wire them to the existing content, then apply the pattern and rank.

---
*Implementation (today):* DAILY BASIS, `$totalNumberOfConsecutiveDaysWithoutSpirometry > $hyperparameterToleranceFor…WithoutSpirometry`, sent at `$userSetTimeOfTheDayForFeedbackIfRequired`, target dialog empty. The content lives under the "Feedback on compliance regarding …" / "Feedback medication adherence" folders (Good / Poor compliance → one missed / several missed).
