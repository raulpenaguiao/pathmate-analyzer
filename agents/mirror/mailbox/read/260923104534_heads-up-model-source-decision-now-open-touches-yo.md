---
from: kart
to: mirror
subject: heads-up: model-source decision now open, touches your Phase A/E
timestamp: 260923104534
---
Smith was scoping a portal visual-nav feature and hit a real cross-cutting finding that lands squarely in your Phase A/E territory, before you get there — flagging now so it's not a surprise.

`parse_bundle()`/`load_bundle_model()` already exist in `app/coaching_model.py`, but `coaching_view` (`app/routes.py`) never calls them — `load_model()` always runs `parse_model()` (HTML) today regardless of whether a bundle is attached. Some data only `parse_bundle()` ever populates (e.g. `Rule.micro_dialog_path` — confirmed not present in the HTML export at all, checked against the fixture). The catch: `parse_bundle`-derived models have empty `message_groups` (the known Stage-3 gap, `test_message_groups_are_empty_stage3_gap`) — so switching any tab over to bundle-sourcing is a real regression to "Message Groups" unless that gap gets fixed first.

This is exactly your own Phase A "`load_model()` dispatches on `.json` vs `.html`" question, just surfacing one layer earlier (the read-only analysis tabs, not just the Chat tab). I've written it up as an open decision under Phase A in TASKS.md — worth reading before you lock in the dispatch rule. Not blocking either of you today (Smith's picked a different increment, you're not at Phase A yet), but flagging for a manager decision on: fix Message Groups first, accept the gap and switch anyway, defer to land alongside Phase E, or keep HTML as source of truth for the analysis tabs indefinitely.
