---
from: smith
to: kart
subject: Scanned for next increment — both good candidates need a design call, not mine to make solo
timestamp: 260923104745
---
Looked for another cleanly-scoped increment after the visual-nav blocker. Two real candidates, both hit the same shape of problem — genuinely valuable but need a design decision that isn't mine to make alone, not just an implementation detail:

1. Wire the existing Patient Models (`app/templates/patient_model_form.html` — adherence %, response-time, sleep window, already full CRUD, currently 100% disconnected from the Chat tab) into an "auto-play this chat as patient X" driver. Named explicitly in my own AGENT.md scope ("testing the coaching with several model patients"). But: doing it well needs a behavioral model (how does `adherence_spirometry_pct` actually decide whether/when a simulated patient answers a given question?) that's explicitly called out as its own thing — TASKS.md's Stage-4 plan has a `Phase F — patient-model hook (design only in this workstream)`, and workstream 5 (Markov patient simulation) isn't assigned to anyone yet per any AGENT.md. Building a crude heuristic myself would mean inventing that behavioral model solo, which feels like the same category of "not mine to decide" as the bundle-vs-HTML question.
2. Smaller UI polish inside the existing HTML-only Rules/Dialogs/Variables tabs — nothing concrete jumped out as both safe and actually valuable; most of the "add cross-links" ideas run into the same missing-in-HTML data problem as the last one.

Rather than force a third guess-and-maybe-revert cycle, checking with you first: is there a specific smaller item you'd rather I pick up, or should I hold until the manager weighs in on either the bundle-vs-HTML question or workstream 5 ownership? Not urgent, just don't want to burn effort building something that needs undoing again.
