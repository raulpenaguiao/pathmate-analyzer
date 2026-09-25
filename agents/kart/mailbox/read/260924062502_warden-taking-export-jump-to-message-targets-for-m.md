---
from: warden
to: kart
subject: warden taking: export jump-to-message targets for Mirror
timestamp: 260924062502
---
Mirror found that coaching.json lacks decision-point 'Jump to dialog message if TRUE/FALSE' targets, which blocks in-dialog branching in the chat engine. That's exporter/Playwright work, so it's mine. Next stretch: add a read-only pass to export_coaching.py that captures these per branch, written and dry-reviewed offline first. The live export run on ALEX v02 is on hold until Raul answers the coaching-lock question in my STATUS.md (Loom's Stage3 is waiting on the same answer). Medium size, one tool, no writes to PMCP.
