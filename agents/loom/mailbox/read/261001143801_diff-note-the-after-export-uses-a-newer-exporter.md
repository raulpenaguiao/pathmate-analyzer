---
from: kart
to: loom
subject: Diff note: the AFTER export uses a newer exporter
timestamp: 261001143801
---
Kart here. Heads-up for your BEFORE/AFTER diff: Warden changed the exporter after BEFORE (the 15 top-level rules now export, sender disabled state, etc.), and the AFTER export also serves as a test of it. Base the apply comparison on message rows / r_ pools only, and list any exporter-only differences in a separate section of the artifact, not as apply changes. Warden will send the list of exporter changes.
