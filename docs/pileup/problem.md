# What goes wrong in ALEX v01

**Symptom.** The patient ignores the morning "do your spirometry" reminder. Hours later it resurfaces and displaces the evening dialog that was actually due, instead of getting out of the way.

**Why it happens.** Three design choices in v01 add up to the pile-up:

1. **Reminders never expire.** They are PMCP's default *blocking* questions, which stay open until the patient answers.
2. **Nothing has a priority.** A stale reminder and a scheduled questionnaire are treated the same, so whichever got there first holds the conversation.
3. **Interrupted reminders are always brought back.** v01 parks the old question when something new starts, then resumes it afterwards ("we had previously stopped somewhere else… let us resume"). There is no limit on how old the parked question may be. The only cleanup is one end-of-day sweep, for spirometry only.

**What is *not* the problem.** Bringing an interrupted dialog back is not wrong in itself. PMCP's own v6.0 guidance calls it the *preferred* approach, because it lets patients answer at their own pace ("Defining the conversational coaching flow" best-practice page). The bug is bringing things back **with no expiry and no priority**. So the fix keeps the comeback, and adds a rank (see [priority.md](priority.md)) and an expiry (see [interruptions.md](interruptions.md)).

**A structural finding from the live rules (14 Sep export).** Before the redesign, not a single sending rule checked whether another question was already open. Any two dialogs whose times happened to coincide for a participant could fire together. Spirometry and medication have since been rebuilt with that check; the others haven't yet.

*Details: [archive/pileup_findings_ALEX_v01.md](archive/pileup_findings_ALEX_v01.md) and §1 of [archive/ALEX_v02_redesign_spec.md](archive/ALEX_v02_redesign_spec.md).*
