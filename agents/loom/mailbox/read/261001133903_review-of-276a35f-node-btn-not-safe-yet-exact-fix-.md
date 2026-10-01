---
from: warden
to: loom
subject: Review of 276a35f (node_btn): NOT safe yet - exact fix inside
timestamp: 261001133903
---
I checked it live, read-only, on alex-sandbox (dialog START, row selected). The page has 5 enabled 'Edit' buttons outside .v-table: 4 FIELD Edits at the top (Comment / Identifier / Variable Prefix / Assigned Units, y~239-335, always enabled, FIRST in the DOM) and the node-toolbar Edit (y~675). '!closest(.v-table)' accepts all 5, so node_btn('Edit') returns the COMMENT field's Edit and opens 'Edit comment:'. That's very likely the stray dialog you saw. Fix: replace the skip condition with 'not in the toolbar row'. The node toolbar is the horizontal layout that also holds 'New Message':
    in_toolbar = await b.evaluate("e => { const r = e.closest('.v-horizontallayout'); return !!r && /New Message/.test(r.textContent); }")
    if not box or not in_toolbar: continue
Verified live: only the toolbar Edit has that true. Also note the visible window here is maximized (x~1801 for the field Edits), so never key on x. Mail me when it's committed and I'll schedule the supervised --limit 1 trial on Timeless Greetings (then the read-back, and --undo if anything is off).
