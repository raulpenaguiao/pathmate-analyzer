# Rollout: what's live, what's next

Detailed task tracking lives in `TASKS.md` (owned by Kart). This page is the design-level order and the reasoning behind it.

## Where we are (2026-09-25)

| Category | Rank | State |
|---|---|---|
| Spirometry | 1 | **Live** on the reminder pattern, but still with the old "delete when interrupted" rule and a rank-blind "nothing open" check. Known bug: the "Do you have your spirometer handy?" buttons render as raw text; the fix is queued. |
| Medication (3 doses) | 1 | **Live**, same as spirometry |
| Everything else | 2–6 | Still v01: no window, no rank. Sleep quality, compliance coaching and misc also have **no working trigger at all**. |

## First release scope (Raul, D6)

Everything with a working trigger today:
- **Rank 1:** spirometry, medication, night preparation
- **Rank 2:** ACQ
- **Rank 4:** educational content
- **Rank 5:** gamification

The shared infrastructure and planning ahead are included too.

**Later**, once each has a trigger: compliance coaching (needs D7), sleep quality, health literacy, and misc (FAQ, air quality, clinic).

## Order

**Step 0: three quick platform tests** (sandbox coaching, one browser session via Warden). These settle the unverified points in [interruptions.md](interruptions.md#not-yet-verified-needs-one-test-on-the-sandbox-coaching-booked-through-warden). They must come first, because the design depends on them.

**Step 1: retrofit spirometry and medication** to the new interrupt design:
1. Add the shared markers (`$openDialogName`, `$openDialogRank`, `$openDialogStaleAt`) and each dialog's `…_resumeMode`.
2. Firing rules: swap the "nothing open" check for the rank check, and set the markers when the dialog starts.
3. Dialogs:
   - Add the dialog's re-entry opener (the context for a returning patient) and the checkpoint.
   - **Spirometry:** once measured → don't come back.
   - **Medication:** once the dose is answered → don't come back. Neither needs the "continue" state, so neither needs splitting.
   - At the end, clear the markers. On the first message, turn on the clear setting.
4. Add the ignored-dialog cleanup rules, plus the daily reset of the new variables.
5. Fix the latent issue Mirror found in the medication dialogs: the "is actively answering" flag isn't guarded by its answer check.
6. Verify with a fresh export, Mirror's chat simulator, and a real-device test on the sandbox.

**Step 1b: planning ahead for spirometry and medication** ([planning-ahead.md](planning-ahead.md)): the onboarding schedule check, postponement validation, the `$lastDoseTakenAt` safety gate, and spirometry ordered above medication. This is done together with step 1, since it touches the same dialogs. The onboarding check grows as each later category is added.

**Step 2: nighttime monitoring (sleep-prep)**, rank 1, end of day. The smartwatch-battery prompt folds into it. Window: 10 min before bedtime → bedtime + grace.

**Step 3: ACQ** (rank 2). The reminder pattern plus rank. It already has a reschedule flag; it needs the "continue" split.

**Step 4: educational content (rank 4), then gamification (rank 5).** Education needs the "continue" split, and an idle timeout long enough for its longest video (D13 note). Gamification's weekly-status dialog is an empty stub; build it, or ship only the Monday announcement.

**Step 5: first-release check.** Every first-release dialog is ranked; the onboarding schedule check covers all their times. Simulate a busy day to confirm that rank-1 reminders don't starve the ACQ, education or gamification ([priority.md](priority.md#a-known-risk-and-what-keeps-it-in-check)).

**Later releases, in rank order:**
- Compliance coaching (rank 2): needs D7, a real trigger, and wiring to its existing content.
- Sleep quality (rank 3): needs a trigger on "night data missing or poor".
- Health literacy (rank 4): no trigger today.
- Misc (rank 6): the FAQ and air-quality dialogs still use v01's recall setting and must be rebuilt without it.

Then a **full check**: every dialog ranked or explicitly outside the ladder, and no v01 recall settings left.

Why this order: the design is proven on the two dialogs already live before it's copied, and after that each step follows rank. The most clinically important pieces are therefore protected first.
