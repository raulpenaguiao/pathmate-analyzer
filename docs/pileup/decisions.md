# Decisions for Raul

Each open question has options and Mason's recommendation (**★**). Answering "D4: A" is enough. Answered items move to the bottom of this page and into the design pages.

## Open

**D4. A reminder that never got its turn within its window: what happens after the window closes?**
Each reminder has two timers. The *window* is how late it may still make its **first** appearance: spirometry at 08:00 with a 3 h window may start until 11:00. The *expiry* is how long it may **come back after an interruption** (end of day). D4 is only about a reminder that other dialogs kept waiting until its window closed, so it **never started**. Interrupted reminders come back until expiry either way; ignored ones get their one re-ask (D2) and then stop.
- **A ★ Skip it for today.** Nothing is sent, and tomorrow starts fresh. A morning reminder never first appears in the evening.
- B It may still start later, until the end of the day. No day is lost, but a morning spirometry prompt could land at 19:00 and push aside evening content (the v01 symptom).

**D7. Compliance-coaching thresholds: who sets them?** (Not needed for the first release, see D6.)
Today only one trigger exists: "more than N consecutive days without spirometry", with N as a hyperparameter. Proposed shape, values to be decided:
- missed spirometry: > N days in a row (existing);
- missed medication: ≥ M doses in the last 3 days;
- missed night monitoring: ≥ K nights in the last week.

Will you or the clinical team supply N, M and K?

**D10. Minimum gap between scheduled reminders** (checked at onboarding, [planning-ahead.md](planning-ahead.md)).
- A 30 minutes.
- **B ★ 60 minutes.** With D1 = 30 min, an ignored reminder never delays the next scheduled one.
- C 90 minutes.

**D11. When the onboarding check finds a conflict, who decides?**
- **A ★ ALEX suggests a concrete time; the patient accepts it or keeps their own.** The spirometry-after-medication gate still protects the measurement at firing time.
- B ALEX shifts the time automatically and tells the patient.

**D12. A dose is moved (or taken) before spirometry is done that day. What happens to spirometry?**
- **A ★ Offer spirometry first** ("let's do it now, before your medication"). If the patient declines, spirometry waits until 5 h after the dose, if that's still before bedtime; otherwise it's skipped for the day.
- B Spirometry simply waits 5 h after the dose, with no offer.

**D12b. Is "no spirometry within 5 h after medication" a hard clinical constraint, or advice the patient may override?**
- A Hard: the firing gate always holds spirometry back.
- B Advice: ALEX explains, but if the patient insists on a time, spirometry may fire there.

**D13. How long does active-answer protection last?** Once the patient answers, the dialog counts as rank 1. After this time it drops back to its own rank: it stays open, but becomes interruptible.
- A 30 minutes.
- **B ★ 1 hour** (Raul's suggestion). This covers a video or a full ACQ.
- C Until the dialog ends, bounded only by the idle timeout.

Note: a long video with no answers would hit the 30-minute idle timeout (D1) and count as ignored. For education, the idle time should be at least the length of the longest video; per-dialog idle times are an option.

## Decided (Raul, 2026-09-25)

| # | Decision |
|---|---|
| D1 | An unanswered question blocks others for at most **30 minutes**, then counts as ignored and steps aside. |
| D2 | An ignored reminder may **ask once more** before its window ends. The re-ask comes through the re-entry opener, since the patient has already seen it once. |
| D3 | **Expiry:** end of day for nighttime monitoring, compliance coaching, sleep quality and air quality; end of week for the ACQ, FAQ and clinic-visit reminder. |
| D5 | **Strict waiting:** equal ranks never interrupt each other. |
| D6 | **First release = everything with a working trigger today:** spirometry, medication, night preparation (rank 1); ACQ (rank 2); educational content (rank 4); gamification (rank 5). Later: compliance coaching, sleep quality, health literacy, misc (no working trigger yet). |
| D8 | **Re-entry openers approved.** Each is built as an `r_` randomisation group (`r_ReEntry_<Dialog>`), so Loom's pipeline generates more variants in English and Romanian. |
| D9 | The spirometry Yes/No fix is done **as part of the workbench build**. |

Earlier decisions: the ladder (0 safety; 1 spirometry / medication / night prep; 2 ACQ / compliance; 3 sleep quality; 4 education and health literacy; 5 gamification; 6 misc); what sits outside it (patient-started conversations, onboarding, greetings, the well-being check-in); **the defining change** (interrupted dialogs come back from the beginning, with a re-entry opener that gives context); the three states; expiry end of day for spirometry and medication, end of week for education and gamification; planning ahead with *spirometry not within 5 h after medication*.
