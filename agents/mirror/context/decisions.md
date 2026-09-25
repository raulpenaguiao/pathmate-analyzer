# Decisions & deviations from the plan doc

## load_model() dispatch — deliberately NOT changed (2026-09-23)

`docs/stage4_chat_engine_plan.md` Phase A originally said `load_model()`
should dispatch on `.json` vs `.html`. That assumed the plan's original
"coaching.json is the one stored file" model, written before Smith built
the bundle as a separate *attachment* to an HTML-based coaching
(`storage.save_coaching_bundle`/`coaching_bundle_path`).

Given that reality, I added a second, separate entry point instead —
`load_bundle_model(coaching_id)` — and left `load_model()`/`parse_model()`
completely untouched. Only the (not-yet-wired) Chat engine calls
`load_bundle_model`; every other tab (`coaching_view`'s Rules/Dialogs/
Variables/Statistics) keeps reading HTML exactly as before.

Smith found (2026-09-23, scoping a portal visual-nav feature) that this
means those analysis tabs never see bundle-only data (e.g.
`Rule.micro_dialog_path`), and flagged switching them to Kart as an open
decision (TASKS.md, under Phase A) — since bundle-parsed models have empty
`message_groups` (known Stage-3 gap), switching would regress that section.
I replied to Kart: not my call, that's Smith's/the portal's tradeoff, not
the engine's — my own scope is the engine, and Chat is the only Phase A-F
consumer of `parse_bundle()`. Recommended leaving HTML as source of truth
for the analysis tabs until/unless Smith decides otherwise.

**If revisiting**: this note is the reasoning trail; check TASKS.md/Kart's
reply for whatever the manager actually decided before assuming this is
still current.
