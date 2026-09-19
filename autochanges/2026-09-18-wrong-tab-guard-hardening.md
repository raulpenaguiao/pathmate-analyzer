# Baking "check you're on the right tab" into the navigation library itself

2026-09-18. Follow-up to the r_ pipeline end-to-end test: `rgroup_apply.py`
failed with `RuntimeError("top '👋 Hello' not found")` because the browser
was left on the Rules tab from the prior export run, and the script never
checked. The user's direction: this isn't a one-off bug in one script — every
navigation entry point in the shared library must verify it's on the right
screen before acting, as a standing defensive principle, not something each
new caller has to remember to do itself.

## What changed

Rather than patching `rgroup_apply.py`'s one call site, the check went into
the shared primitives every script already goes through, so it can't be
skipped by a future caller either:

- **`_menu_nav.py`**: new `WrongMenuError` + `_require_micro_dialogs(page)`,
  called unconditionally at the top of both `open_folder_path()` and
  `navigate_and_select()` (the two real entry points - `discover()` and
  `all_targets()` inherit the guard for free since they call
  `open_folder_path()` internally). Calls the already-existing
  `ensure_micro_dialogs()`, which doesn't just detect the wrong tab - it
  actively clicks over to Micro Dialogs if it can. So this isn't just a
  clearer error, it's **self-healing**: a script left on the wrong tab now
  silently corrects course instead of failing.
- **`_rules_nav.py`**: same pattern - new `WrongMenuError` +
  `_require_rules_tree(page)`, called at the top of `select_node()`, the one
  primitive `click_expander`, `expand_all`, and `open_rule_modal` all go
  through.
- **`_variables_nav.py`**: `sweep_variables()` previously just documented
  "caller must already be on the Variables view" as an assumed precondition.
  Now calls `open_variables_tab()` itself (already idempotent/cheap when
  already there) and raises clearly if it can't get there.

All three follow the same shape: cheap no-op when already on the right
screen, active self-correction when not, a clear `WrongMenuError` (naming
what's actually wrong) only when correction itself fails - never the old
misleading "top item X not found", which reads like a labeling typo rather
than a navigation precondition never being met.

## Verified live, not just by inspection

1. Manually switched the browser to the Rules tab.
2. Confirmed via a direct check: `.v-menubar.md-menu` count = 0 (genuinely
   not on Micro Dialogs).
3. Ran `rgroup_apply.py --apply --limit 1` for the same
   `r_TimelessGreetings` variant added in the earlier end-to-end test.
   Before this fix, this exact scenario produced the wrong-tab
   `RuntimeError`. After: `added=0 skipped=1 errors=0` - it silently
   switched tabs itself, then correctly recognized the variant as already
   present (idempotency check) instead of erroring OR adding a duplicate.
4. Re-checked `.v-menubar.md-menu` count = 1 afterward, confirming the
   guard actually performed the tab switch, not just tolerated already
   being there.

## Not done here

- Didn't audit every remaining `_dialogs_nav.py` function individually for
  the same gap - its functions all operate on an already-open row/window
  editor rather than starting fresh from a tab, so the class of bug (wrong
  top-level tab) doesn't apply the same way there. Worth a second look if
  a similar wrong-context failure ever surfaces from that module.
- Old orphaned bare-named files in `data/rgroups/` from before the
  timestamping change were left in place at the user's request (manual
  cleanup, on their own schedule).
