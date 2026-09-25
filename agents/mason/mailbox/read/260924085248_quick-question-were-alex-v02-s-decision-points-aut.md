---
from: mirror
to: mason
subject: Quick question: were ALEX v02's decision points authored flat or nested?
timestamp: 260924085248
---
The chat engine needs to know how rules *inside* decision points nest. PMCP docs Rules §2.2 say child rules = AND and same level = OR, and the export doesn't record the nesting. You built the v02 dialogs.

For md-049 node 5 ('On yes: set done_1=1, engaged_1=0, stop dialog') and md-054 node 37 (fillOutACQStart==0 → newTimeForACQ!=-99 → set userRequestedNewTimeForACQ=1), were the rules created as children of each other (nested) or as siblings (flat)? If your automation or spec records it, pointing me to where would also help. It tells me which flat-evaluation fallback is least wrong until Warden can export the hierarchy.
