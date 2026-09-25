# Pile-up findings — ALEX v01 zum Ausprobieren (2a/2b)

> **Archived 2026-09-25.** Findings from the 14 Sep export; the summary is in [`docs/pileup/problem.md`](../problem.md). The "Phase 4" table below predates the new priority ladder.

Deliverable for TASKS.md's "Pile-up problem" 2a ("read the live Rules tab's
order and timeouts by hand, write a findings doc naming specific rules to
reorder or re-delay") and 2b ("rigorous pass — cross-check tree order
against timeouts to name the actual collisions"). Done 2026-09-14 as a
data-driven analysis of the live Rules tab, captured via
`export_coaching.sh` (`data/exports/coaching_alex-v01-zum-ausprobieren_20260914-094837.json`)
rather than read by eye — the export is a faithful, complete machine
reading of the exact same live tree, and Stage 4 Phase 0 (2026-09-14) means
every rule's condition is already parsed into structured form, which makes
a systematic cross-check practical in a way hand-reading isn't. No live
writes made — this is 2a/2b's diagnostic pass; any resulting reordering
happens as part of Phase 4.

## Method and a real limitation

Every one of this coaching's 21 sending rules' `sendHourVariable` resolves
to **`-99`** against the live Variables tab (captured the same day) — this
sandbox has no live participant with real preference data filled in, and
`-99` is PMCP's own "unset" sentinel here (several senders gate explicitly
on `!= -99` before firing). **This means no *literal* same-time collision
can be observed for a real participant right now** — the analysis below is
structural (rule logic and tree shape), not "these two rules fire at the
same clock minute today." It answers "could these collide for *some*
participant's preference settings," which is what actually matters for a
platform used by many participants with different chosen times.

Two platform facts this analysis leans on, both already confirmed
elsewhere in this project (not re-derived here):
- **DAILY BASIS evaluates once at 00:00 and freezes for the day; PERIODIC
  BASIS re-evaluates continuously** (documented explicitly — see
  `autochanges/2026-09-11-alex-v02-phase3.3-periodic-firing-rule.md`).
  Confirmed live in this export too: PERIODIC BASIS senders gate on
  `"🚀 Only perform if daily rules have been already performed"`, and DAILY
  BASIS's own last rule (`r-067`, `"Remember that the rules on 'Daily
  Basis' were already performed today"`) sets the flag that guard checks —
  so this isn't hidden platform magic, it's a plain variable flag written
  and read like everything else.
- **No sender in this coaching sets the "mark solved / stop the rule run"
  checkbox** (confirmed live 2026-09-10, `README.md`'s "priority-field
  correction") — so a sender firing does **not** stop evaluation of its
  siblings. Every DAILY BASIS sender genuinely gets evaluated every day,
  regardless of what fired before it in the list.

## Finding 1 (the main one): only the already-redesigned spirometry rule
guards against pile-up — nothing else does

`r-113`, the PERIODIC spirometry firing rule built in this session's Phase
3 (`docs/ALEX_v02_redesign_spec.md` §3.2/3.3), has a 5-gate chain, and gate
5 is:

> **`PERIODIC spiro fire, Gate 5: participantOpenQuestions==0 (ALEX v02
> spec 2.1a guard): $participantOpenQuestions calculated value equals 0`**

This is a real, confirmed PMCP system variable (established earlier this
engagement) — it's the actual **mutual-exclusion guard**: the redesigned
spirometry reminder refuses to fire while any other question is already
open. This is *the* mechanism the v02 redesign added to solve pile-up for
this one dialog.

**No other sender in the coaching has an equivalent guard.** The 8 other
DAILY-BASIS reminder/nudge senders — all still on the original v01 pattern
— gate on nothing more than "onboarding done" (and, for two of them, one
extra always-true wrapper node that adds no real condition):

| uid | sends | own condition | notAnsweredTimeout | `participantOpenQuestions` guard? |
|---|---|---|---|---|
| r-052 | poor lung-function compliance feedback | `$totalNumberOfConsecutiveDaysWithoutSpirometry > $hyperparameterTolerance...` | 240 min | **no** |
| r-053 | weekly incentive intro | `$systemDayInWeek == 1` | 240 min | **no** |
| r-057 | sleep-quality dialog | unconditional (`always true`) | 240 min | **no** |
| r-058 | medication dose 1 reminder | `$userSetDesiredFirstDose...Time != -99` | 240 min | **no** |
| r-061 | educational-material prompt | `$today == $dateOfNextDisplayOfEducationalContents` | 240 min | **no** |
| r-062 | medication dose 3 reminder | `$userSetDesiredThirdDose...Time != -99` | 240 min | **no** |
| r-063 | medication dose 2 reminder | `$userSetDesiredSecondDose...Time != -99` **+ inherits r-062's condition, see Finding 2** | 240 min | **no** |
| r-064 | ACQ prompt | `$today == $dateOfNextACQ` | 240 min | **no** |

Because none of these check `$participantOpenQuestions` (or any other
mutual-exclusion signal) and DAILY BASIS evaluates every sibling
regardless of earlier results (see Method), **any participant whose
preference times or due-dates happen to line up on the same day** — e.g. a
weekly-incentive Monday that's also an ACQ due-date, or a medication time
that coincides with the sleep-quality prompt — has multiple senders
simultaneously eligible at the same 00:00 pass with nothing in the rule
logic to stage or suppress the extras. Whatever actually happens on the
live platform when two `start_micro_dialog` actions fire in the same pass
is exactly the open mechanism question this whole workstream exists to
route around — Phase 3's answer was "don't let it happen — gate on
`participantOpenQuestions`" — and that fix has not yet been propagated to
any of these 8.

**This is precisely Phase 4's job** (TASKS.md, `docs/ALEX_v02_redesign_spec.md`
§4-5) — propagate the P2-timeout-question + `participantOpenQuestions`
guard pattern to medication (4.1), sleep-prep (4.2), ACQ (4.3), educational
content (4.4). `r-052` (poor-compliance feedback) and `r-053` (weekly
incentive) aren't explicitly named in the current 4.1-4.6 breakdown — worth
adding when Phase 4 is scoped in detail (flagging for Phase 5's "full
sweep against spec Appendix A").

## Finding 2: medication dose 2's reminder is nested under dose 3's — very
likely an existing bug, not a design choice

Confirmed via the raw tree structure (not just the caption text):

```
r-062  [SENDER] depth=2 parentUid=r-002   "third dose" reminder
  r-063  [SENDER] depth=3 parentUid=r-062  "second dose" reminder
```

Nesting is AND semantics in this tree (confirmed repeatedly this
engagement — a child only evaluates if its parent was also true). r-062's
own condition is `$userSetDesiredThirdDoseOfControllerMedicationInhalationTime
!= -99`. Because r-063 is r-062's child, **the second-dose reminder can
only ever fire if the participant has ALSO set a preferred time for a
third dose** — on top of r-063's own, separate condition
(`$userSetDesiredSecondDose...Time != -99`). r-058 (dose 1) and r-062
(dose 3) are both plain top-level siblings under r-002 with no such
cross-dependency.

**Practical impact**: a participant taking only 2 doses/day (who
legitimately never sets a dose-3 time, leaving it at `-99`) would never
receive their dose-2 reminder at all — not a pile-up/ordering issue, a
correctness bug. There's no sign this was deliberate (no comment, guard
rule, or spec text suggests dose 2 should depend on dose 3), and it looks
like a mis-drop during v01's original authoring.

**Fix, directly actionable, no redesign needed**: in the Rules tab, drag
`r-063` out from under `r-062` to sit as a sibling at the same depth (next
to r-058/r-062/r-064, under r-002) — exactly the "drag-and-drop in the same
tab" mechanism `README.md` already points to for 2a-class findings. Not
done as part of this pass (2a/2b is diagnostic; TASKS.md's "Pile-up
problem" section frames live edits as a deliberate follow-up, and this
specific fix should probably land together with Phase 4.1's medication
redesign rather than as an isolated live edit, so it gets covered by the
same before/after verification sweep).

## Finding 3: the uniform 240-minute timeout isn't itself a pile-up cause,
but it's worth knowing it's completely uniform

Every one of this coaching's 21 sending rules — old-pattern and the new
spirometry one alike — uses the identical 4-hour (240 min) not-answered
timeout (matches `README.md`'s earlier finding: "4h default on every
dialog sender"). This isn't a bug, but it does mean there is currently **no
per-reminder tuning** of how long a question can sit open before expiring
— a P2 nudge (spirometry, ACQ, educational) and a higher-stakes P1 item
(medication) share the same window. Not a 2a/2b finding in the "name a
collision" sense, but worth carrying into Phase 4/5: if medication ends up
wanting a shorter timeout than a weekly incentive announcement, that's a
per-rule field already available (confirmed writable in Phase 1 tooling),
just never differentiated in v01.

## Summary table for Phase 4 planning

| Area | Current guard | Phase | Status |
|---|---|---|---|
| Spirometry | `participantOpenQuestions==0` + day-slot gating | 3 | **done** (this session) |
| Medication ×3 doses | none; dose 2 additionally mis-nested under dose 3 | 4.1 | not started — see Findings 1 & 2 |
| Sleep-prep | none | 4.2 | not started — see Finding 1 |
| ACQ | none | 4.3 | not started — see Finding 1 |
| Educational content | none | 4.4 | not started — see Finding 1 |
| Weekly incentive (r-053) | none | not in current 4.1-4.6 list | flag for Phase 5 scope sweep |
| Poor-compliance feedback (r-052) | none | not in current 4.1-4.6 list | flag for Phase 5 scope sweep |
