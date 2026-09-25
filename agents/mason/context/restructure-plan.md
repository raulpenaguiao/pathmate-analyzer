# In flight (2026-09-25, after Raul's 09:43 instruction via Kart)

**Rule change:** NO PMCP writes until Raul sets up a new test-workbench coaching and export. The spirometry Yes/No fix is dropped. The script is kept at `context/fix_spiro_answer_options.py`; it was never applied (the dry run died in navigation). Rows 3-6 are still affected, and row 15 is Loom's stray copy.

**Main task:** "One Question at a Time" with Herald. I supply the design and steps; Herald owns the artifact.
Source pages I'm writing in `docs/pileup/`:
1. `walkthrough.md`: a patient's day, minute by minute (ranks, interruptions, comebacks, ignored reminders, expiry).
2. `build-steps.md`: detailed execution steps, coaching-agnostic (the target is the new workbench).
3. `decisions.md`: concrete questions for Raul, each with options and my recommendation. They go into the artifact, not into mail.
Then mail Herald the paths.

**Unverified platform points** (step 0 in rollout): the clear-cascade flag's effect, same-pass variable visibility, and does-not-answer rules.

**Done:** docs/pileup restructure (3da9a52, 5144117), Interrupt Contract v3 checked.
