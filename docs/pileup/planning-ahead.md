# Planning ahead: avoid pile-ups before they happen

Raul, 2026-09-25. Ranks and re-entry openers handle collisions when they happen. Planning ahead makes them rarer in the first place. It is the **first line of defence**: every collision it prevents is one interruption, and one re-entry, the patient never has to deal with.

## Two ideas

**1. Check the schedule at onboarding.** Onboarding already asks for every time: bedtime, spirometry, each medication dose, the ACQ, the weekly feedback and the weekly incentive announcement. Once they're in, ALEX looks at the whole day. Where reminders are packed too tightly, it suggests a concrete adjustment **before the first day starts**.

**2. Respect spacing rules whenever something is postponed.** When the patient says "remind me later", the new time must still fit the day. One clinical rule matters most:

> **Spirometry not within 5 hours after controller medication** (rule of thumb, Raul). Spirometry *before* medication is fine.

## The spacing rules

| Rule | Value | Where it applies |
|---|---|---|
| Minimum gap between any two scheduled reminders | 60 min *(D10, proposed)* | onboarding, and any later change of preferred times |
| Spirometry not within **5 h after** a medication dose | 5 h (`$hyperparameterSpiroAfterMedHours`) | onboarding, postponing spirometry, postponing a dose, and at firing time |
| When spirometry and a dose are due together, **spirometry goes first** | — | tie-break between the two rank-1 reminders |

The 60-minute gap is chosen so that an ignored reminder (which steps aside after 30 minutes, D1) can never delay the next scheduled one.

## What the patient sees

**At onboarding.** The patient chose spirometry at 11:00 and medication at 08:00 and 20:00.
> ALEX: One small thing about your schedule. Spirometry works best *before* your medication, or at least 5 hours after it. 11:00 is only 3 hours after your morning dose. Would 07:00 work for your spirometry instead?  **[07:00 is fine] [Keep 11:00] [Choose another time]**

**On postponing spirometry.** The patient taps "remind me later" at 07:40 and picks 09:00, but their dose is at 08:00.
> ALEX: At 09:00 your spirometry would come just after your medication, which can affect the result. We can do it right now, before your dose, or I can remind you at 13:00. Which do you prefer?

**On postponing a dose when spirometry hasn't been done yet.** It's 07:50, spirometry is due at 08:15, and the patient wants to take the dose now instead of at 08:30.
> ALEX: Before you take it: your spirometry isn't done yet today. If you'd like, let's do it now, since after your medication it has to wait about 5 hours.  *(behaviour: D12)*

**The patient has the final say** *(D11)*. If they keep a tight or clinically awkward time, ALEX respects it. The firing-time safety net below still stops spirometry from asking inside a post-dose window.

---

## Implementation

**Evidence that the platform supports this:** onboarding's time questions already carry bounds taken from variables. Examples: the first dose's picker has `max:$pseudoBedTime`, the second dose's has `min:$lowerBoundForTimeOfNextContr…`, and every "When would you like to be reminded again?" picker has `min:$…lowerBoundFor…` / `max:$userSetBedtime` (25 Sep export, dialogs "🤝 Welcome", ACQ, education, and the v01 spirometry and medication dialogs). A picker takes **one** min–max range. A forbidden window in the *middle* of the day (e.g. 08:00–13:00 after a dose) therefore can't be expressed as a bound. It needs a check right after the answer.

**P1. Onboarding schedule check.** A new step at the end of "🤝 Welcome", after all times are collected. It uses decision-point branches:
- for each pair of reminder times closer than the minimum gap, set `$scheduleConflict = 1` and compute a suggested time (the nearest time that satisfies every rule);
- if `$userSetDesiredSpirometryTime` falls inside `(doseTime_i, doseTime_i + 5)` for any dose i, set the spirometry conflict and suggest `doseTime_1 − 1` (an hour before the first dose, respecting the minimum gap) or `doseTime_i + 5`, whichever is valid and before bedtime;
- if there's a conflict, ask the confirm question shown above. The answer overwrites the time or keeps it.

**P2. The same check whenever preferred times change later.** This covers the `personal-data-edited` intent and the "Modification of reminder preferences" dialog, which is still a stub.

**P3. Postponement validation.** After each "remind me later" time answer:
- for spirometry: if the new time falls in a post-dose window, explain and offer the two nearest valid times;
- for a dose: if spirometry is not yet done today and the new dose time is before the spirometry time, offer spirometry first (D12).

**P4. Firing-time safety net.** When a dose is confirmed, record `$lastDoseTakenAt = $timeDecimal`. Reset it daily. Add one gate to the spirometry firing rule: `$timeDecimal ≥ $lastDoseTakenAt + $hyperparameterSpiroAfterMedHours`. This protects spirometry even when a dose is taken at an unexpected time.

**P5. Tie-break.** In the PERIODIC rule order, the spirometry firing rule sits **above** the medication firing rules. When both are due in the same pass, spirometry starts first.

**Unverified:** whether a time picker's min/max accepts an expression, or only a single variable. Precedent only shows single variables (`$lowerBoundFor…`), so bounds are computed into variables first. That also works if expressions turn out to be supported.
