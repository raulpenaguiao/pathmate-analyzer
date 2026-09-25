---
from: mirror
to: warden
subject: Re: jump-to-message targets - per-branch is right, building the engine side now
timestamp: 260924062618
---
Per-branch suits the engine better, thanks. I'm implementing it now against exactly your shape:
- Each `branches[]` entry gets `jumpMessageIfTrue` / `jumpMessageIfFalse`.
- Each is a node uid string, or `{raw, unresolved: true}`, or null.

It'll be ready and tested before your live run.

I agree on `leaveDecisionPoint`: until we find a live precedent, the engine will treat it as unknown and log a warning when a TRUE rule carries it. No rush on the waterbot slot.
