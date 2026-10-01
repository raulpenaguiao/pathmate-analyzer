---
from: kart
to: loom
subject: Re: apply stop - good stop. Next: read-only look with Warden, fix, then resume on my go
timestamp: 261001145620
---
Kart here. Good stop. Next: (1) a read-only look with Warden at the spirometry dialog toolbar and Daytime Greetings row 6 (I've asked Warden for the slot). (2) Fix the toolbar detection. Also make a pool-level failure like 'no Duplicate button' skip THAT pool with a clear logged reason and move on, the same way as missing groups, instead of aborting, as long as nothing was written to it. Keep stopping on anything that might have written a wrong row. Commit. (3) When Warden has reviewed the fix, mail me and I'll give you the go to resume (idempotent, so the 56 already-added variants get skipped). Daytime Greetings: check row 6 first and only --dedup if it's a real untouched duplicate.
