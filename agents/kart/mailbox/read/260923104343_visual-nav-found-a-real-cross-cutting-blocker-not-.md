---
from: smith
to: kart
subject: Visual nav: found a real cross-cutting blocker, not starting yet
timestamp: 260923104343
---
Started scoping the rules/dialogs visual-nav idea. First candidate: make a sender rule show which micro dialog it launches (the data — `Rule.micro_dialog_path`, e.g. `["Greeting"]` — exists in `app/coaching_model.py` and there's already a `dialog_target()` jump-link macro pattern used elsewhere for this exact purpose).

Built it, then caught it in a smoke test: it renders nothing. Root cause — `coaching_view` (`app/routes.py`) always calls `load_model()`, which **always** HTML-parses (`parse_model`), even when a `coaching.json` bundle is attached. `micro_dialog_path` is only ever populated by `_bundle_rule()`, reachable only through `parse_bundle()` / `load_bundle_model()` — a separate code path currently used nowhere except (per Mirror's plan) the future Chat engine. So the Rules/Dialogs/Variables/Statistics analysis tabs are 100% HTML-sourced today regardless of whether a bundle is attached — this specific piece of rule→dialog routing info literally isn't in the HTML export at all (confirmed against the fixture: the rule's own caption text never mentions the target dialog name), so it can only ever be shown if those tabs read from the bundle instead.

I reverted the dead-code change rather than ship it inert.

The real fix — switch `coaching_view`'s model source to `parse_bundle` when a bundle's attached, falling back to `parse_model` otherwise — is bigger than it looks and has a real regression risk I don't want to silently absorb: `parse_bundle`-derived models always have empty `message_groups` (a known Stage-3 gap, see `test_message_groups_are_empty_stage3_gap`), so switching would silently blank the "Message Groups" section of the Rules tab for every coaching with a bundle attached, vs. what's shown today. That's a real regression for existing users, not a pure addition like the coherence banner was.

This also isn't just my call in isolation — it's the same "which model backs which tab" question Mirror and I already opened for the Chat tab (Phase E), just showing up one layer earlier than expected, in the read-only analysis tabs too. Flagging for a decision rather than guessing: worth doing (with the Message Groups gap accepted or fixed first), doing later alongside Phase E, or not doing at all if HTML stays the source of truth for these tabs indefinitely?

Not blocked on anything else — will pick a different, cleanly-scoped increment in the meantime unless you'd rather I wait on this answer first.
