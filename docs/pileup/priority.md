# Priority: which dialog wins

Set by Raul, 2026-09-23/25. **A lower number means more important.**

| Rank | Category | Why here |
|---|---|---|
| 0 | Safety: offer to have medical staff contact the patient | Always wins; never interrupted, never dropped |
| 1 | [Spirometry](categories/spirometry.md), [medication](categories/medication.md), [nighttime monitoring](categories/nighttime-monitoring.md) (incl. smartwatch battery) | Daily clinical data; a missed day can't be recovered |
| 2 | [Asthma Control Questionnaire](categories/acq.md), [compliance coaching](categories/compliance-coaching.md) | Clinical measurement, and re-engagement of patients who slip |
| 3 | [Sleep quality inquiry](categories/sleep-quality.md) | Useful follow-up, only when the night data is missing or poor |
| 4 | [Educational content](categories/education.md) (incl. health literacy) | Important, but can move to another day |
| 5 | [Gamification](categories/gamification.md) | Motivation, not care |
| 6 | [Misc: FAQ, air quality, clinic visit reminders](categories/misc.md) | Informational |

**Outside the ladder** (confirmed by Raul, 2026-09-25):
- **Conversations the patient starts.** Nothing scheduled barges into them.
- **Onboarding.** It runs before any daily coaching starts.
- **Greetings.** They are openers inside other dialogs, not scheduled on their own.
- **The well-being check-in.** Not a priority, and never restarted.
- **Development/test dialogs.** Not part of production; most were already deleted in the Phase 2 prune.

## The collision rules

1. **Higher beats lower.** A dialog may interrupt an open dialog only if it is *strictly* more important.
2. **Equals wait.** Two dialogs of the same rank never interrupt each other; whichever started first finishes first. This matters most at rank 1, which holds several daily reminders.
3. **Lower waits, then checks again.** A less important dialog waits until the way is clear, then checks whether it is still relevant (its window or expiry) before starting.
4. **An active conversation is protected.** Once the patient has answered something in a dialog, that dialog counts as rank 1 until it ends, so a newly due reminder can't yank it away mid-answer. Only safety (rank 0) can still interrupt it.

## A known risk, and what keeps it in check

Putting the device reminders at rank 1 means that up to five of them a day (spirometry, three medication doses, night preparation) outrank all content. If they stayed open for hours, the questionnaire and education might rarely get a turn. This is why every rank-1 reminder only nags within a **short window** ([reminder-pattern.md](reminder-pattern.md)), and why the rollout's verification step explicitly checks that content still gets through ([rollout.md](rollout.md)).

---
### Implementation

PMCP has no priority setting, so rank is enforced by conditions in each dialog's firing rule. The only such condition live today, `$participantOpenQuestions==0` ("no question open at all"), cannot tell ranks apart. The replacement is described in [interruptions.md](interruptions.md#implementation): the currently open dialog's rank is kept in a variable, and each firing rule compares its own rank against it.
