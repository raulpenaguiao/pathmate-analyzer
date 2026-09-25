# Decisions for Raul

Each question has options and Mason's recommendation (**★**). Answering "D1: A" is enough. Answered items move into the design pages and disappear from here.

## Behaviour

**D1. How long may an unanswered question block everything else?**
The walk-through showed why this matters: at 08:30 medication had to wait behind an ignored spirometry question.
- **A ★ 30 minutes.** After that the question counts as ignored and steps aside.
- B 60 minutes.
- C The reminder's whole window (3 h). Simplest, but one ignored reminder then blocks every other rank-1 reminder for hours.

**D2. After a reminder has been ignored, may it ask once more before its window ends?**
- **A ★ No.** One ask per window. Least nagging, simplest to build.
- B Yes, once. Better adherence, but it's an extra message, and the original spec's "one escalation" was never built.

**D3. Expiry for the categories you didn't name.**
The rule of thumb: a daily task expires at the end of the day, a weekly or occasional one at the end of the week.

| Category | ★ Proposed |
|---|---|
| Nighttime monitoring | end of day |
| Compliance coaching | end of day |
| Sleep quality | end of day |
| Air-quality warning | end of day |
| ACQ | end of week |
| FAQ | end of week |
| Clinic-visit reminder | end of week |

Accept the whole table, or name the exceptions.

**D4. Does the reminder window stay?**
- **A ★ Yes.** A reminder stops nagging after its window (3 h), and end of day/week only limits how long an *interrupted* dialog may come back.
- B No. Interrupted *or* ignored, a dialog may return until its expiry. (Risk: this brings the pile-up back in a milder form.)

**D5. Two reminders of the same rank: strict waiting?**
- **A ★ Strict.** Equal ranks never interrupt each other. With D1 = 30 min, the worst case is a 30-minute delay.
- B An idle rank-1 reminder may be interrupted by another rank-1 reminder. Faster, but two morning reminders can then bounce each other.

**D10. Minimum gap between scheduled reminders** (checked at onboarding, [planning-ahead.md](planning-ahead.md)).
- A 30 minutes.
- **B ★ 60 minutes.** With D1 = 30 min, an ignored reminder can never delay the next scheduled one.
- C 90 minutes.

**D11. When the onboarding check finds a conflict, who decides?**
- **A ★ ALEX suggests a concrete time, and the patient accepts or keeps their own.** The spirometry-after-medication gate still protects the measurement at firing time.
- B ALEX shifts the time automatically and tells the patient.

**D12. A dose is moved (or taken) before spirometry is done that day.** What happens to spirometry?
- **A ★ Offer spirometry first** ("let's do it now, before your medication"). If the patient declines, spirometry waits until 5 h after the dose, if that's still before bedtime; otherwise it's skipped for the day.
- B Spirometry simply waits 5 h after the dose; no offer.
- C Clinical input needed. Is the 5 h rule a hard constraint, or advice?

## Scope

**D6. What goes into the first v02 release on the workbench?**
- A Rank 1 only: spirometry, medication, night preparation, plus the shared infrastructure.
- **B ★ Rank 1 plus the ACQ.** It proves the "continue" state (the ACQ needs a split) on a real clinical measure. Compliance coaching waits for D7.
- C Everything with a working trigger today (ranks 1, 2, 4, 5). Sleep quality, compliance and misc have no trigger yet.

**D7. Compliance-coaching triggers need clinical thresholds.** Who sets them?
Today only one exists: "more than N consecutive days without spirometry", with N as a hyperparameter. Proposed shape, values to be decided:
- missed spirometry: > N days in a row (existing);
- missed medication: ≥ M doses in the last 3 days;
- missed night monitoring: ≥ K nights in the last week.

Question: will you or the clinical team supply N, M and K?

## Content

**D8. The re-entry openers.** Each returning dialog gets its own opener, which says what the dialog is about and why it's back. Drafts for each dialog are in [interruptions.md](interruptions.md#the-idea-come-back-with-context).
- **A ★ Approve the drafts**, then write the rest per category as each is built; Romanian by a native speaker.
- B Reword (tell me which).
- C One generic line for all dialogs. *Not recommended: this is v01's missing-context flaw again.*

**D9. The spirometry Yes/No buttons.** On the old sandbox they show raw text, and the live fix was dropped. ★ Fix it as part of the workbench build ([build-steps.md](build-steps.md#also-carried-into-the-workbench-build)). Nothing to do before then.

## Already decided (for reference)

- **Planning ahead:** check the schedule at onboarding for tight packing; respect spacing on postponement; **spirometry not within 5 h after medication** (rule of thumb); spirometry is fine before medication.

- **The ladder:** 0 safety; 1 spirometry / medication / night prep; 2 ACQ / compliance; 3 sleep quality; 4 education and health literacy; 5 gamification; 6 misc.
- **Outside the ladder:** patient-started conversations, onboarding, greetings, the well-being check-in (never restarted).
- **The defining change:** interrupted dialogs come back **from the beginning, with a re-entry opener that gives context**, and never assume the patient remembers. Three states: start over / don't come back / continue.
- **Expiry:** spirometry and medication at the end of the day; education and gamification at the end of the week.
