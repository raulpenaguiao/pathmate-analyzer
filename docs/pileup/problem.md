# What goes wrong in ALEX v01

**Symptom.** The patient ignores the morning "do your spirometry" reminder. Hours later it resurfaces in the middle of the evening, and the patient is left looking at a question with no idea what it refers to or where to pick up.

## The design flaw: returning without context

v01 interrupts dialogs on purpose and brings them back afterwards. That is intended behaviour, and PMCP's own v6.0 guidance calls bringing interrupted dialogs back the *preferred* approach, because patients can answer at their own pace ("Defining the conversational coaching flow" best-practice page).

**What v01 gets wrong is how a dialog comes back.** It resumes the parked question at the exact point it stopped. The only framing is one generic transition line ("we had previously stopped somewhere else… let us resume the previous conversation"). The patient is dropped mid-conversation, hours later, and is expected to remember what was being asked and why. The dialog assumes a context the patient no longer has.

**This is the flaw v02 closes, and it is the defining architecture change.** An interrupted dialog comes back **from the beginning**, through a re-entry opener written for that dialog. The opener says what this is about and why it's back, and it doesn't assume the patient remembers. → [interruptions.md](interruptions.md)

## Mechanisms v02 keeps, but organizes better

These are not design flaws. The mechanisms exist in v01 and are intended; v02 makes them explicit and consistent:

- **Priority.** v01 orders dialogs through rule order and per-rule timeouts. v02 replaces that implicit ordering with an explicit ranking by category. → [priority.md](priority.md)
- **Interruption.** More important content is meant to be able to cut in. v02 keeps this, and states exactly who may interrupt whom.
- **Expiry.** v01 has one end-of-day sweep, for spirometry only. v02 gives every reminder a window, and every returning dialog an expiry (end of day or end of week). → [reminder-pattern.md](reminder-pattern.md)

**A structural finding from the live rules (14 Sep export).** Before the redesign, no sending rule checked whether another question was already open, so dialogs whose times coincided could fire together. Spirometry and medication have since been rebuilt with that check.

*Details: [archive/pileup_findings_ALEX_v01.md](archive/pileup_findings_ALEX_v01.md) and §1 of [archive/ALEX_v02_redesign_spec.md](archive/ALEX_v02_redesign_spec.md).*
