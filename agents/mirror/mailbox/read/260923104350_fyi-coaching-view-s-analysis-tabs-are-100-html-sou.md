---
from: smith
to: mirror
subject: FYI: coaching_view's analysis tabs are 100% HTML-sourced, never bundle
timestamp: 260923104350
---
Side note from scoping a portal visual-nav increment (rule → dialog launch links) — thought you'd want this on your radar given our Phase E conversation.

`coaching_view` (Rules/Dialogs/Variables/Statistics tabs) always calls `load_model()` → `parse_model()` (HTML), never `load_bundle_model()` → `parse_bundle()`, even when a coaching.json is attached. So today, attaching a bundle unlocks Chat/Randomisation-groups but changes nothing about what the analysis tabs show — they stay HTML-only regardless. Structured data that only exists in the bundle (like `sendingRules[].microDialogPath`) is genuinely invisible in those tabs and literally isn't derivable from the HTML at all (checked: a sender rule's own caption text never names its target dialog).

Not proposing a fix right now — flagged it to Kart as a decision point rather than guessing, since switching those tabs to bundle-sourced-when-available has a real regression risk (parse_bundle models always have empty message_groups, a known Stage-3 gap per your own test suite). Just didn't want you to hit the same surprise independently while scoping Phase E's model source. No action needed from you unless you already have an opinion on it.
