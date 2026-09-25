# Interruptions: what happens to the dialog that lost

Decided by Raul, 2026-09-23. Replaces the original spec's "delete it and never bring it back".

## The idea

When a more important dialog interrupts a less important one, the interrupted dialog **comes back** once the interruption is over. It opens with one short line, *"Let's pick up where we left off"*, and then either starts over or continues, depending on how far the patient had got. It stops coming back at its **expiry**: the end of the day for daily tasks, the end of the week for weekly ones.

Two things make this different from the v01 pile-up. First, a dialog only comes back when nothing equally or more important is open ([priority.md](priority.md)). Second, it can never come back after its expiry.

## How far the patient got: three states

Each dialog is marked at **checkpoints**, points where the conversation reaches a meaningful milestone. The mark decides what happens if it's interrupted later.

| State | Meaning | Example |
|---|---|---|
| **Start over** (default) | No checkpoint passed yet. On return, the dialog restarts from the beginning. | Spirometry reminder interrupted before the patient said they have the spirometer |
| **Don't come back** | The part that matters is done; what's left isn't worth returning for. | Spirometry already measured; only the "thanks" and optional feedback were left |
| **Continue** | A real chunk is done *and* a real chunk is left. On return, skip what's done. | ACQ reminder answered and a new time chosen, but the questionnaire itself is still pending |

Most short reminders only ever need the first two states. **Continue** only earns its place where there is substantial content after the checkpoint.

## Ignored is not the same as interrupted

If the patient simply **doesn't answer** and the dialog times out, it is *not* brought back. It is treated as given up for today (or this week). Otherwise an ignored reminder would come back again and again, which is exactly the pile-up.

## Expiry per category

| Expiry | Categories |
|---|---|
| **End of day** | Spirometry, medication *(Raul)*; nighttime monitoring, compliance coaching, sleep quality, air-quality warnings *(proposed)* |
| **End of week** | Educational content incl. health literacy, gamification *(Raul)*; ACQ, FAQ, clinic-visit reminder *(proposed)* |

The *proposed* rows are Mason's defaults, following the same logic (daily task → day, weekly/occasional → week). **Raul to confirm.**

## Reminders keep their short window

A reminder's own nagging still stops after its short window (e.g. 3 hours after the scheduled spirometry time, see [reminder-pattern.md](reminder-pattern.md)). The end-of-day/week expiry only governs how long an **interrupted** dialog may come back. *(Mason's default; Raul to confirm.)*

---
## Implementation

### Variables

Two shared markers record which dialog is open right now:

| Variable | Value when nothing is open | Set when |
|---|---|---|
| `$openDialogName` | `""` | a ranked dialog starts (its own name); cleared when it ends |
| `$openDialogRank` | `99` | a ranked dialog starts (its rank); set to `1` while the patient is actively answering (the protection rule in [priority.md](priority.md)); `99` when it ends |
| `$openDialogStaleAt` | `0` | a ranked dialog starts, and again on every answer: `$timeDecimal` + the idle time. After this, an unanswered dialog counts as ignored. |

Each ranked dialog X has its own:

| Variable | Meaning |
|---|---|
| `$X_started` | 0/1. Has X been shown today (or this week)? Decides whether the "pick up where we left off" line is said. The reminders already have this as `$…ReminderStage ≥ 1`. |
| `$X_resumeMode` | 0 = start over, 1 = don't come back, 2 = continue. Set by X's checkpoints; 1 also when X ends normally or is ignored. |

### Firing rule for dialog X (rank r)

```
X is due (its own schedule; for reminders: inside the reminder window on the first showing)
AND $X_resumeMode != 1
AND $openDialogName != "X"                 # not already open
AND r < $openDialogRank                    # strictly more important than whatever is open (99 = nothing open)
→ start X    # X's opening step then sets $openDialogName = "X", $openDialogRank = r, $openDialogStaleAt
             # (see build-steps.md C3)
```

PERIODIC rules are ordered by rank, so when several dialogs are waiting, the most important one is tried first.

### Inside dialog X

1. **Opening decision point:** if `$X_started == 1`, say "Let's pick up where we left off". If `$X_resumeMode == 2`, jump to "X, part 2". Then set `$X_started = 1`.
2. **Checkpoints** set `$X_resumeMode` to 1 or 2.
3. **Normal end:** `$X_resumeMode = 1`, `$openDialogName = ""`, `$openDialogRank = 99`.
4. **The first message** of every ranked dialog clears whatever it interrupted ("clears the current dialog cascade" setting). The interrupted dialog then returns only through its own firing rule, never through PMCP's built-in recall, which has no expiry.

"Continue" (state 2) needs X to be split into two dialogs at the checkpoint. PMCP's "jump" can only target a whole micro dialog, not a point inside one ("Jumping to another micro dialogue" on the PMCP v6.0 micro-dialogs page).

### Ignored dialogs, and expiry

- **Ignored:** one cleanup rule per dialog. If `$openDialogName == "X"` and `$timeDecimal > $openDialogStaleAt`, then set `$X_resumeMode = 1` and clear both markers. This also stops a forgotten marker from blocking every lower-ranked dialog.
- **Expiry** is simply the reset point. The DAILY BASIS reset at 00:00 sets `$X_started = 0` and `$X_resumeMode = 0` for end-of-day dialogs. A Monday-only reset (`$systemDayInWeek == 1`) does the same for end-of-week dialogs.

### Not yet verified (needs one test on the sandbox coaching, booked through Warden)

1. **The clear setting's effect.** The "clears the current dialog cascade" message setting is confirmed writable (Phase 3.1 log). What it *does* to an open question from another dialog has not been tested, and the PMCP docs don't describe it.
2. **Within-pass visibility.** When one rule sets `$openDialogRank` during a PERIODIC pass, do later rules in the same pass see the new value? If not, two dialogs could start in the same pass.
3. **Cleanup via "does not answer" rules.** The sending rules' "does not answer" follow-up rules might be a simpler way to catch ignored dialogs. They appear in the export but are undocumented.
