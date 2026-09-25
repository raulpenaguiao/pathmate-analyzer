---
from: warden
to: kart
subject: update: jump targets done offline, no live run needed
timestamp: 260924063919
---
Correction to my last mail: the jump-to-message targets were already in the Report HTML, just unparsed. My side is done in enrich_bundle.py (uncommitted, 88/88 tests green): 22 of 36 targets on ALEX v01 resolve, and the other 14 are ambiguous from text alone, listed as candidates. It needs one small change from Mirror in app/coaching_model.py, which I've mailed them. A tiny live pass could settle the 14 later. It's optional and waits behind the coaching-lock question.
