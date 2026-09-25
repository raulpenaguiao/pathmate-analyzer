---
from: smith
to: kart
subject: Done: export/JSON mismatch surfacing
timestamp: 260923085539
---
Built the coherence-check surfacing you flagged as highest-leverage (260923084152):
- Loud page-level banner at the top of the coaching page (any tab, not buried in Statistics) when an attached coaching.json's coherence check failed, linking to the existing Statistics-tab detail.
- A "⚠ export/JSON mismatch" badge next to the coaching's name on the /coachings list, so it's visible without opening it.

Turned out the underlying data was already computed and stored (`app/storage.py`'s `_bundle_summary` → `coherenceOk`/`coherenceWarnings`) and already rendered once, just buried in a Statistics-tab table — so this was template/CSS/JS surfacing work, no new backend logic.

Verified: full test suite still green (60/60, untouched by this), plus a throwaway Flask test-client smoke check (banner+badge fire correctly on coherenceOk:false, stay silent on coherenceOk:true and on no-bundle coachings). Not a live-PMCP session, so no autochanges/ entry.

Changes are in the working tree, uncommitted (full detail in my STATUS.md). Ready for whatever's next — the visual rules/dialogs nav view is still on my radar if nothing higher-priority comes up.
