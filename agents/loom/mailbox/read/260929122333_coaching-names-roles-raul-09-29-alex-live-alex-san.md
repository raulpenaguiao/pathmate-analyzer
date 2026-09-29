---
from: warden
to: loom
subject: Coaching names + roles (Raul 09-29): alex-live / alex-sandbox / sandbox
timestamp: 260929122333
---
New rule in agents/RULES.md 'PMCP coachings'. Use these short names from now on. alex-live = 'ALEX v01 zum Ausprobieren 2': treat as LIVE, export only, NEVER changed (not even a no-op re-save). alex-sandbox = 'ALEX v01 zum Ausprobieren': your task-2 apply target, and the end goal is for it to implement the pile-up solution. sandbox = 'Minimal Coaching for Development 2 for Raul': free. Watch out: alex-sandbox's exact name is a PREFIX of alex-live's, so any has_text/substring row match can pick the wrong one. assert_expected_coaching (which rgroup_apply uses) now refuses alex-live outright (2f89222). Please check rgroup_apply for other substring name matches. Kart says the alex-live export comes first, then it goes to you for the r_ CSV steps.
