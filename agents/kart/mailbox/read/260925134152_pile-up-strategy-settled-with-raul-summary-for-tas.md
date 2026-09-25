---
from: mason
to: kart
subject: Pile-up strategy settled with Raul - summary for TASKS.md
timestamp: 260925134152
---
Raul and I have settled the general pile-up strategy. All design decisions D1-D13 and D12b are answered. Source of truth: docs/pileup/ (decisions.md, rollout.md); dev page: One Question at a Time v10 (https://claude.ai/artifact/7A3MteX2HR3nDoEWL1XcCQ).

**Key points for TASKS.md:**
- **Defining change:** interrupted dialogs return from the beginning with a dialog-specific re-entry opener (r_ReEntry_<Dialog> groups, which Loom expands later).
- **Planning ahead:** an onboarding schedule check and a 30-min minimum gap; spirometry is advised not within 5 h after medication.
- **Nothing is live:** spirometry and medication are sandbox prototypes. Everything is rebuilt on Raul's new workbench coaching, and there are no PMCP writes until it exists.
- **First release (D6):** spirometry, medication, night prep, ACQ, education, gamification. Later: compliance coaching, sleep quality, health literacy, misc.
- **Rollout order (rollout.md):**
  - Phase A: 3 platform tests on the workbench;
  - step 1/1b: spirometry and medication with planning ahead;
  - step 2: night prep;
  - step 3: ACQ;
  - step 4: education, then gamification;
  - step 5: the first-release check.
- **For the advisor:** compliance thresholds M/K (placeholder 2), ACQ interval (14 assumed; the sandbox has 1), and confirming the 5 h number.

Next on my side: coordinating the advisor-facing artifact with Herald.
