# The pile-up problem and its fix

**The problem, in one sentence:** when ALEX brings an interrupted dialog back, it drops the patient back into the middle of it, sometimes hours later, with no context about what was being asked or why.

**The defining change in v02:** an interrupted dialog comes back **from the beginning**, through a **re-entry opener** written for that dialog. The opener tells the patient what this is about and why it's back, and never assumes they remember. → [interruptions.md](interruptions.md)

**Planning ahead, the first line of defence:** at onboarding ALEX checks the whole day's schedule and suggests spacing where reminders are packed too tightly. Every postponement respects the spacing rules, including *no spirometry within 5 hours after medication*. → [planning-ahead.md](planning-ahead.md)

**Three mechanisms v01 already has, organized better:**

1. **Priority, made explicit.** Every dialog has a rank. A more important dialog may interrupt a less important one, never the other way round, and equal ranks don't interrupt each other. → [priority.md](priority.md)
2. **Comebacks that expire.** An interrupted dialog keeps coming back only until the end of the day or week. Dialogs that are effectively finished don't come back at all. → [interruptions.md](interruptions.md)
3. **Reminder windows.** A reminder only asks within a window around its scheduled time, then gives up for the day. → [reminder-pattern.md](reminder-pattern.md)

## Pages

| Page | What it answers |
|---|---|
| [problem.md](problem.md) | What exactly goes wrong in ALEX v01, and why |
| [priority.md](priority.md) | Which dialog wins when two collide |
| [interruptions.md](interruptions.md) | What happens to the one that lost |
| [reminder-pattern.md](reminder-pattern.md) | The building block every reminder uses |
| [planning-ahead.md](planning-ahead.md) | Spacing the schedule at onboarding and on postponement, so collisions don't happen |
| [walkthrough.md](walkthrough.md) | One patient's day, showing every rule in action |
| [decisions.md](decisions.md) | **Open questions for Raul**, each with options and a recommendation |
| [build-steps.md](build-steps.md) | Step-by-step build instructions for the workbench coaching |
| [rollout.md](rollout.md) | Where things stand, what is next, in what order |
| [categories/](categories/) | One page per coaching category: goal, what the patient sees, rank, status |
| [archive/](archive/) | The original long spec and the v01 analysis, kept for reference |

## Status at a glance (2026-09-25)

- **Nothing is live.** Spirometry and medication were prototyped on the **sandbox** coaching, which will be reset. They get rebuilt on the new workbench coaching, with the restart design, from the start.
- **Designed, not built:** everything else. See [rollout.md](rollout.md).

A note on words: PMCP (the platform ALEX runs on) has no built-in priority setting. "Rank" here is our own design, and it is built out of ordinary rule conditions and variables.
