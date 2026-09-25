# Decisions

All design decisions for the first release are answered (Raul, 2026-09-25). The design pages reflect them. Open items for the advisor are listed at the bottom.

## Behaviour

| # | Decision |
|---|---|
| D1 | An unanswered question blocks others for at most **30 minutes**, then counts as ignored and steps aside. |
| D2 | An ignored reminder gets **one re-ask**, no sooner than 30 min later, through its re-entry opener. Ignored again → done for the day/week. |
| D3 | **Expiry:** end of day for spirometry, medication, night preparation, compliance coaching, sleep quality, air quality; end of week for the ACQ, education, gamification, FAQ, clinic-visit reminder. |
| D4 | A reminder that other dialogs kept waiting past its window **may still start later, up to the end of the day** (its expiry). The window only limits the re-ask. Known risk: a morning reminder can first appear late in the day. Planning ahead (D10, D11) is what keeps this rare. |
| D5 | **Strict waiting:** equal ranks never interrupt each other. |
| D13 | Active-answer protection lasts **1 hour** from the first answer, then the dialog drops back to its own rank. |

## Planning ahead

| # | Decision |
|---|---|
| D10 | Minimum gap between scheduled reminders: **30 minutes.** With D1 = 30 min, an ignored reminder can delay the next one by at most about 30 minutes. |
| D11 | When onboarding finds a conflict, **ALEX shifts the time automatically and tells the patient**, who can change it back. |
| D12 | A dose due or taken before spirometry is done → **ALEX offers spirometry first.** If declined, spirometry waits 5 h after the dose (if still before bedtime), otherwise it's skipped for the day. |
| D12b | "No spirometry within 5 h after medication" is **advice**, not a hard constraint. ALEX explains, but if the patient insists on a time, spirometry may fire there. |

## Scope and content

| # | Decision |
|---|---|
| D6 | **First release:** spirometry, medication, night preparation (rank 1); ACQ (rank 2); education (rank 4); gamification (rank 5). Later: compliance coaching, sleep quality, health literacy, misc. |
| D7 | Compliance thresholds come from the **clinical team**. Values used until then: see below. |
| D8 | Re-entry openers approved; each is an `r_ReEntry_<Dialog>` group, and Loom's pipeline generates EN + RO variants. |
| D9 | The spirometry Yes/No options are entered correctly (two lines) in the workbench build. |

Earlier decisions: the ladder (0 safety; 1 spirometry / medication / night prep; 2 ACQ / compliance; 3 sleep quality; 4 education and health literacy; 5 gamification; 6 misc); what sits outside it (patient-started conversations, onboarding, greetings, the well-being check-in); **the defining change** (interrupted dialogs come back from the beginning, with a re-entry opener that gives context); planning ahead.

## To ask the advisor / clinical team

| Item | Value in use | Source |
|---|---|---|
| **N**: consecutive days without spirometry before compliance feedback | **2** | in the export: `$hyperparameterToleranceForNumberOfConsecutiveDaysWithoutSpirometry = 2` |
| **M**: missed medication doses in the last 3 days before feedback | **2** *(placeholder)* | not in the export. Mason's default: **ask the advisor** |
| **K**: missed night-monitoring nights in the last 7 days before feedback | **2** *(placeholder)* | not in the export. Mason's default: **ask the advisor** |
| Days between ACQs | **14** *(to confirm)* | the export has `$hyperparameterNumberOfDaysBetweenACQs = 1`, which looks like a sandbox test value; the dialog text says "biweekly". **Ask the advisor.** |
| Spirometry after medication | **5 h** | Raul's rule of thumb. Confirm the number, and that it is advice rather than a hard rule (D12b). |

Compliance coaching isn't in the first release (D6), so none of N, M or K blocks the build.
