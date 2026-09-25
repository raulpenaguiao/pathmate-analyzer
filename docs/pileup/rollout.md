# Rollout: what's live, what's next

Detailed task tracking lives in `TASKS.md` (owned by Kart). This page is the design-level order and the reasoning behind it.

## Where we are (2026-09-25)

| Category | Rank | State |
|---|---|---|
| Spirometry | 1 | **Live** on the reminder pattern, but still with the old "delete when interrupted" rule and a rank-blind "nothing open" check. Known bug: the "Do you have your spirometer handy?" buttons render as raw text; the fix is queued. |
| Medication (3 doses) | 1 | **Live**, same as spirometry |
| Everything else | 2–6 | Still v01: no window, no rank. Sleep quality, compliance coaching and misc also have **no working trigger at all**. |

## Order

**Step 0: three quick platform tests** (sandbox coaching, one browser session via Warden). These settle the unverified points in [interruptions.md](interruptions.md#not-yet-verified-needs-one-test-on-the-sandbox-coaching-booked-through-warden). They must come first, because the design depends on them.

**Step 1: retrofit spirometry and medication** to the new interrupt design:
1. Add the shared markers (`$openDialogName`, `$openDialogRank`, `$openDialogSince`) and each dialog's `…_resumeMode`.
2. Firing rules: swap the "nothing open" check for the rank check, and set the markers when the dialog starts.
3. Dialogs:
   - Add the opening "pick up where we left off" step and the checkpoint.
   - **Spirometry:** once measured → don't come back.
   - **Medication:** once the dose is answered → don't come back. Neither needs the "continue" state, so neither needs splitting.
   - At the end, clear the markers. On the first message, turn on the clear setting.
4. Add the ignored-dialog cleanup rules, plus the daily reset of the new variables.
5. Fix the latent issue Mirror found in the medication dialogs: the "is actively answering" flag isn't guarded by its answer check.
6. Verify with a fresh export, Mirror's chat simulator, and a real-device test on the sandbox.

**Step 2: nighttime monitoring (sleep-prep)**, rank 1, end of day. The smartwatch-battery prompt folds into it. Window: 10 min before bedtime → bedtime + grace.

**Step 3: rank 2.**
- ACQ: pattern plus rank; it already has a reschedule flag.
- Compliance coaching: the rule exists but points at an empty dialog, so this needs a real trigger and content wiring.

**Step 4: ranks 3–6 in order.**
- Sleep quality: needs a trigger on "night data missing or poor".
- Education plus health literacy.
- Gamification: the weekly-status dialog is an empty stub.
- Misc: the FAQ and air-quality dialogs still use v01's recall setting and must be rebuilt without it.

**Step 5: full check.** Every dialog is ranked or explicitly outside the ladder; no v01 recall settings remain. Simulate a busy day to confirm that rank-1 reminders don't starve lower-ranked content ([priority.md](priority.md#a-known-risk-and-what-keeps-it-in-check)).

Why this order: the design is proven on the two dialogs already live before it's copied, and after that each step follows rank. The most clinically important pieces are therefore protected first.
