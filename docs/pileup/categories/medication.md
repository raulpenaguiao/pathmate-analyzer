# Controller medication adherence

**Rank 1** · **Comes back until:** end of day · **Status:** prototyped on the sandbox (3 doses; will be reset); to be rebuilt on the workbench

**Goal.** The patient inhales their controller medication, up to three doses a day, each at its own chosen time.

**What the patient sees.** "Quick reminder: it's time for your medication!" → "Did you take your medication?" (Yes/No) → thanks.

**Timing.** Each dose nags for up to 3 hours after its chosen time.

**Spacing.** A confirmed dose starts a 5-hour window in which spirometry won't ask. If a dose is moved before spirometry is done, ALEX offers spirometry first (D12, [planning-ahead.md](../planning-ahead.md)).

**If interrupted.**
- *Before answering:* that dose's reminder comes back and starts over.
- *Once answered:* it doesn't come back.

**Open items.**
- Rebuild on the workbench with the interrupt design.
- A latent flaw: the "is actively answering" flag sits next to its answer check instead of under it. It's in the sandbox prototype; build it correctly on the workbench.

---
*Implementation:* dialogs "Prompt patient to take {first,second,third} dose of controller medication (v02)". All three sit in the folder "Prompt patient to take controller medication / Prompt patient to take first dose of controller medication"; the folder's name is misleading. Variables: `$myMedication_{doseTime,windowEnd,done,reminderStage,engaged}_i`, with grace `$hyperparameterMedicationGraceMinutes` = 180. v01's dose-2-under-dose-3 nesting bug was removed with the old rules.
