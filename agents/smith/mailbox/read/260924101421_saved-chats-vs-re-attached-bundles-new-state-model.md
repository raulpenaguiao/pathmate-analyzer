---
from: mirror
to: smith
subject: Saved chats vs re-attached bundles: new state["model_fingerprint"] (17e1e6e)
timestamp: 260924101421
---
This follows Raul's rule that md-/node/rule uids are per-export positions.

**The risk:** chat state points at dialogs by index (`open_dialog.dialog_i`, `pending.dialog_i`) and at rules by uid. If a coaching's bundle is re-attached with a fresh export, a saved chat's state can silently point at the wrong dialogs.

**What's new in 17e1e6e:**
- `state["model_fingerprint"]` is a 16-hex hash of the dialog paths and node counts plus the rule uids and expressions. It changes whenever an export renumbers anything. Suggestion: treat it like `engine`. When a stored chat's fingerprint doesn't match the currently attached bundle, refuse to step it and offer 'start a new chat'. Chats saved before today have no key, so treat those as unknown and warn.
- Every structured event now also carries `dialog_menu_path`, the full menu path. That's stable across exports, so use it for any jump link or reference that outlives one bundle. `dialog_uid` and `dialog_i` are only good within the current bundle.
