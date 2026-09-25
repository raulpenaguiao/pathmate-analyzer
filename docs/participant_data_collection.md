# What participant data to collect: first pass

Owner: Mirror. First draft 2026-09-25, for Raul to react to.
Status: **proposal**. Nothing here is built, and nothing touches live content.

## Why collect more

Today ALEX's variables are mostly *control state*: just enough to fire
the next reminder (`$spiroReminderStage`, `$myMedication_done_1`, …),
reset daily and then overwritten. To learn how a participant behaves over
time, and to fit the patient models for workstream 5's simulated
patients, we need a record of **what was offered, when, and what the
participant did with it**.

## What we already get for free

- **Every variable write is timestamped.** A participant export (`.pmcp`)
  keeps each variable's `formerVariableValues` history with timestamps.
  `app/participant_import.py` already turns it into a timeline. So
  "collecting" something mostly means *writing a variable at the right
  moment*. The history does the rest, and no new infrastructure is
  needed.
- Cascade completions appear in the same export.
- Measurements arrive from sensors (`$spirometerData`, `$smartInhalerData`,
  `$sleepData`, `$coughData`, `$aqiData`). ACQ answers and score are
  stored (`$acq_*`, `$acq_history`).

## Gaps, ranked by value

Checked against the 25 Sep ALEX export.

### 1. Ignored prompts leave no trace (highest value)
All 18 sending rules have a not-answered timeout, but **none has any
"does not answer" rules**. When a participant ignores a reminder, no
variable changes. We only see what they *did*, never what they
*skipped*. That's exactly the signal adherence modelling needs.
- **Proposal:** each sender's not-answered branch increments a counter,
  e.g. `$ignored_<topic>_count`, and sets `$lastIgnored_<topic> = $today`.
  Topics: spiro, medication 1/2/3, ACQ, education, nighttime.
- **Why:** P(ignore | topic, time of day, day of study) is the core
  parameter of a patient model. It also answers "is it pile-up or
  disengagement?" for the redesign.

### 2. Response latency isn't recorded
We know *that* a participant answered, but not *how long after the
prompt*. Answer history timestamps help only if we also know when the
prompt went out.
- **Proposal:** at dialog start, set `$promptSentAt_<topic> =
  $participantCurrentTimestamp`. The answer's own history timestamp then
  gives the latency.
- **Why:** response delay is the second core patient-model parameter.
  It maps directly to the stored patient-model field
  `notification_response_minutes`.

### 3. Deferrals and reschedules are overwritten, not counted
`$userRequestedNewTimeFor*` and `$newTimeFor*` are reset every run.
The history keeps them, but there's no per-topic count.
- **Proposal:** add `$deferCount_<topic>` (lifetime) alongside the
  existing flags.
- **Why:** it maps to `reschedule_acceptance_pct`, and it separates "busy
  now" from "not interested".

### 4. 31 of 312 questions don't store their answer
These question nodes have no result variable, so the answer is lost.
- **Proposal:** list them (Mirror can generate the list from the
  export), then decide one by one. Many may be "OK" acknowledgements that
  aren't worth storing.

### 5. Which message variant was shown
The r_ randomisation groups pick one wording, but nothing records which
one was picked.
- **Proposal:** find out first whether PMCP logs the picked variant
  anywhere. If not, consider a per-group `$variantShown_<group>` write.
  That's a lot of variables, so only do it if message-effect analysis is
  actually wanted.
- **Why:** without it, "which wording works better" can't be answered.

### 6. Engagement vs completion
There's no distinction between *opened the dialog*, *started the task*
and *finished the task* (e.g. spirometry started vs completed).
- **Proposal:** use a per-topic stage variable (0 = sent, 1 = opened,
  2 = started, 3 = done) instead of just `done`.
- **Why:** it maps to `completion_after_engagement_pct`.

## What this would give workstream 5

From gaps 1–3 and 6, each stored patient-model field could be *estimated
from real participants* instead of guessed:

| patient-model field | estimated from |
| --- | --- |
| `adherence_*_pct` | done vs ignored counts per topic |
| `notification_response_minutes` | answer timestamp − `$promptSentAt_*` |
| `reschedule_acceptance_pct` | `$deferCount_*` vs later completion |
| `completion_after_engagement_pct` | stage transitions |
| `sleep_start/end` | `$userSetBedtime` plus when prompts are answered |

## Open questions for Raul

1. Is any of this already logged on the PMCP/CLAID side (push opened,
   variant shown), so we shouldn't duplicate it in variables?
2. Are there privacy or ethics limits on logging behaviour at this
   granularity in the study?
3. Scope: ALEX v02 content only, or retrofit v01 as well?
4. Who would build it? This is live-content work (Mason's redesign
   area, possibly with Loom's pipeline), not engine work.
