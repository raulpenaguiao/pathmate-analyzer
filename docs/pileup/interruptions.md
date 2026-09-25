# Interruptions: what happens to the dialog that lost

Decided by Raul, 2026-09-23. Replaces the original spec's "delete it and never bring it back".

## The idea: come back with context

This is **the defining architecture change of v02** (Raul, 2026-09-25).

When a more important dialog interrupts a less important one, the interrupted dialog **comes back** once the interruption is over. In v01, it came back at the exact question where it stopped, with at most one generic line. The patient, sometimes hours later, had to work out what was being asked and why.

In v02 a returning dialog takes a separate path, the **re-entry path**. That path is designed on the assumption that the patient has lost the thread:

1. **A re-entry opener, specific to the dialog.** It says what the conversation is about and why it's back. It is not a generic "let's pick up where we left off".
2. **Then the dialog from the beginning.** Its first question is worded so that it stands on its own.
3. **Only if a real part is already done ("continue", below) does it skip ahead.** Even then the opener says what's already done, and never drops the patient into a bare mid-dialog question.

| Dialog | Re-entry opener, EN seed | RO seed (informal *tu*) |
|---|---|---|
| Spirometry | "Earlier today I reminded you about your spirometry measurement, and we got interrupted. Let's start again from the top." | "Mai devreme ți-am amintit de măsurarea spirometriei și am fost întrerupți. Hai să o luăm de la început." |
| Medication dose | "A little while ago I asked about your medication dose, before something else came up. Let's go back to it." | "Acum puțin timp te-am întrebat despre doza ta de medicament, înainte să intervină altceva. Hai să revenim la ea." |
| Night preparation | "Before we got side-tracked, I wanted to help you get your devices ready for tonight's monitoring." | "Înainte să ne abatem de la subiect, voiam să te ajut să-ți pregătești dispozitivele pentru monitorizarea de la noapte." |
| ACQ | "Earlier I asked you to fill in your asthma questionnaire (ACQ), and we got interrupted. Here it is again." | "Mai devreme te-am rugat să completezi chestionarul despre astm (ACQ) și am fost întrerupți. Iată-l din nou." |
| ACQ, after a new time was picked *(continue)* | "You asked me to remind you about your asthma questionnaire at this time. Here it is." | "Mi-ai cerut să-ți amintesc de chestionarul despre astm la ora asta. Iată-l." |
| Educational content | "Before we were interrupted, I wanted to share some material about asthma with you." | "Înainte să fim întrerupți, voiam să-ți arăt niște materiale despre astm." |

Approved by Raul (D8). Each opener is built as an `r_` randomisation group named `r_ReEntry_<Dialog>` (e.g. `r_ReEntry_Spirometry`). Loom's r_ pipeline then generates further variants in English and Romanian automatically, so a returning patient doesn't see the identical line every time. The Romanian seeds are Mason's drafts. They anchor the pipeline's style and register; a native speaker should review the generated set.

Two further rules keep comebacks from piling up. A dialog only comes back when nothing equally or more important is open ([priority.md](priority.md)), and it never comes back after its expiry.

## How far the patient got: three states

Each dialog is marked at **checkpoints**, points where the conversation reaches a meaningful milestone. The mark decides what happens if it's interrupted later.

| State | Meaning | Example |
|---|---|---|
| **Start over** (default) | No checkpoint passed yet. On return, the dialog restarts from the beginning. | Spirometry reminder interrupted before the patient said they have the spirometer |
| **Don't come back** | The part that matters is done; what's left isn't worth returning for. | Spirometry already measured; only the "thanks" and optional feedback were left |
| **Continue** | A real chunk is done *and* a real chunk is left. On return, skip what's done. | ACQ reminder answered and a new time chosen, but the questionnaire itself is still pending |

Most short reminders only ever need the first two states. **Continue** only earns its place where there is substantial content after the checkpoint.

## Ignored is not the same as interrupted

If the patient simply **doesn't answer**, the dialog steps aside after 30 minutes (D1), so it never blocks anything for long. It then gets **exactly one re-ask** (D2), no sooner than 30 minutes later and still inside its window. Because the patient has already seen it once, the re-ask comes through the re-entry opener. If that is ignored too, it is done for today (or this week). Interrupted dialogs, by contrast, keep coming back until their expiry: the patient didn't choose to leave them.

## Expiry per category

| Expiry | Categories |
|---|---|
| **End of day** | Spirometry, medication *(Raul)*; nighttime monitoring, compliance coaching, sleep quality, air-quality warnings *(Raul, D3)* |
| **End of week** | Educational content incl. health literacy, gamification *(Raul)*; ACQ, FAQ, clinic-visit reminder *(Raul, D3)* |

Rule of thumb: a daily task expires at the end of the day, a weekly or occasional one at the end of the week.

## Reminders keep their short window

Each reminder has two timers. The **window** (e.g. 3 h after the scheduled spirometry time, see [reminder-pattern.md](reminder-pattern.md)) is how late it may still make its *first* appearance. The **expiry** (end of day or week) is how long it may *come back after an interruption*. A reminder kept waiting by other dialogs until its window closes, never having started, is skipped for today *(D4, Mason's recommendation)*.

---
## Implementation

### Variables

Two shared markers record which dialog is open right now:

| Variable | Value when nothing is open | Set when |
|---|---|---|
| `$openDialogName` | `""` | a ranked dialog starts (its own name); cleared when it ends |
| `$openDialogRank` | `99` | a ranked dialog starts (its rank); set to `1` while the patient is actively answering (the protection rule in [priority.md](priority.md)); `99` when it ends |
| `$openDialogOwnRank` | `99` | a ranked dialog starts (its own rank). The demote rule uses it to drop the dialog back once protection runs out. |
| `$openDialogProtectedUntil` | `0` | the patient's first answer: `$timeDecimal` + the protection time (1 h, D13) |
| `$openDialogStaleAt` | `0` | a ranked dialog starts, and again on every answer: `$timeDecimal` + the idle time. After this, an unanswered dialog counts as ignored. |

Each ranked dialog X has its own:

| Variable | Meaning |
|---|---|
| `$X_started` | 0/1. Has X been shown today (or this week)? Decides whether the dialog takes the re-entry path. The reminders already have this as `$…ReminderStage ≥ 1`. |
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

1. **Opening decision point:** if `$X_started == 1`, go to the dialog's **re-entry opener** (its own message rows, then back to the first question). If `$X_resumeMode == 2`, jump to "X, part 2", whose own re-entry opener says what's already done. Then set `$X_started = 1`.
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
