# The pile-up problem and its fix

**The problem, in one sentence:** ALEX's reminders never expire and have no priority. An unanswered morning reminder keeps coming back later in the day and pushes aside whatever was actually scheduled for that time.

**The fix, in three rules:**

1. **Every dialog has a rank.** A more important dialog may interrupt a less important one, never the other way round. Two dialogs of the same rank never interrupt each other. → [priority.md](priority.md)
2. **An interrupted dialog comes back, but not forever.** When the interruption is over, it restarts with a short "let's pick up where we left off", until it expires at the end of the day or the end of the week. Dialogs that are effectively finished don't come back at all. → [interruptions.md](interruptions.md)
3. **Reminders have a time window.** A reminder only nags within a window around its scheduled time, then gives up for the day. → [reminder-pattern.md](reminder-pattern.md)

## Pages

| Page | What it answers |
|---|---|
| [problem.md](problem.md) | What exactly goes wrong in ALEX v01, and why |
| [priority.md](priority.md) | Which dialog wins when two collide |
| [interruptions.md](interruptions.md) | What happens to the one that lost |
| [reminder-pattern.md](reminder-pattern.md) | The building block every reminder uses |
| [walkthrough.md](walkthrough.md) | One patient's day, showing every rule in action |
| [decisions.md](decisions.md) | **Open questions for Raul**, each with options and a recommendation |
| [build-steps.md](build-steps.md) | Step-by-step build instructions for the workbench coaching |
| [rollout.md](rollout.md) | What is live, what is next, in what order |
| [categories/](categories/) | One page per coaching category: goal, what the patient sees, rank, status |
| [archive/](archive/) | The original long spec and the v01 analysis, kept for reference |

## Status at a glance (2026-09-25)

- **Live on the new pattern:** spirometry, medication. Both use the old "delete when interrupted" rule, which still needs updating to the restart design.
- **Designed, not built:** everything else. See [rollout.md](rollout.md).

A note on words: PMCP (the platform ALEX runs on) has no built-in priority setting. "Rank" here is our own design, and it is built out of ordinary rule conditions and variables.
