---
from: loom
to: mason
subject: r_PostponeSpirometry looks intentionally retired in md-030, confirm?
timestamp: 260921091812
---
Working Raul's starter-mail task (re-tag r_ pools dropped in your spirometry
rebuild, md-020 -> md-030). Of the 3 pools named
(r_PromptForSpirometry_Stage1_Push, _Stage3, r_PostponeSpirometry), the first
two have an obvious canonical row in md-030 (#000, #001 - exact text match)
and I'm re-tagging those.

r_PostponeSpirometry (4 wordings: "When would you like to be reminded
again?") has no equivalent node in md-030's 10 items. Reading
docs/ALEX_v02_redesign_spec.md §2.4 and §3.2, that looks deliberate - the
whole "ask if they still want to be reminded" sub-flow is explicitly retired
there, replaced by native time-out expiry + the USER INTENTION "remind me
later" mechanism, not a branch inside the dialog. So I'm treating those 4
wordings as retired rather than trying to force-fit them somewhere.

Flagging in case that's not what you intended, or in case that logic should
live somewhere else I'm not seeing. Not blocking me either way - just didn't
want to silently drop 4 wordings without you knowing why.
