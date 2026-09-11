# 2026-09-11 — ALEX v02 redesign, Phase 1 recon (Rules-tab write mechanics)

**Coaching:** "ALEX v01 zum Ausprobieren" (sandbox — not production, per the
user).
**Driving:** Claude, over the CDP session the user started earlier in the
day (same session as the Phase 0 recon log).
**Goal:** Phase 1 of `TASKS.md`'s "ALEX v02 redesign" section — figure out
how to actually WRITE to the Rules tab. Confirmed 2026-09-11 (Phase 0 log)
that no write path exists there today; `_rules_nav.py` only reads.

## What was navigated

1. Rules tab → `expand_all()` (121/122 nodes, unchanged from Stage 3) →
   located the same rule Stage 3 sampled as `rule00`
   ("🧐💬 If required, send feedback on poor compliance with lung function
   monitoring scheme…", index 48 in this session's tree order — indices are
   not stable across sessions, always re-locate by caption).
2. Opened its "Edit rule:" modal via `_rules_nav.open_rule_modal`.
3. Clicked each of the outer modal's first 4 "Edit" buttons in turn
   (discovery only — dumped the resulting sub-window, then Cancel, never
   OK/Save).
4. Directly inspected the outer modal's checkboxes/filterselects/sliders'
   real `disabled` DOM property (not just the text-rendering `_rules_nav`
   already does) to find which fields are live in the outer form vs. which
   need a nested editor.

## Writes

None. Every sub-window opened was dismissed with **Cancel**, never OK. The
outer modal itself was closed with `_rules_nav.close_windows()`, whose
"Close" **is** a no-op re-save (same as every prior Stage-3 session) — one
more harmless same-value commit on this sandbox rule, already resaved ~dozens
of times.

## Findings

### The outer modal's first 4 "Edit" buttons, mapped

In DOM order, confirmed live (not the field grouping I'd guessed from the
message editor's pattern):

| # | Opens | Purpose |
|---|---|---|
| 0 | "Edit comment:" | the rule's `Comment` field |
| 1 | "Edit rule (with placeholders):" | the `Rule [x]` condition expression, with a scrollable `$variable` picker |
| 2 | "Edit text (with placeholders):" | the `Comparison term [y]`, same variable picker |
| 3 | "Edit variable:" | creating/picking the **result variable name** — "Existing variables to select (optional)" + a text input, i.e. this is how you set `storeResultVar`'s value, not a display of it |

All four sub-windows are simple `Cancel`/`OK` popups — no further nesting.
**Not yet tested: actually clicking OK on any of them.** This pass was
discovery-only; a same-value OK-commit test (the standard way this repo has
validated a write path before, e.g. `rgroup_apply.py`'s message-text edit)
is the next concrete step before `set_rule_field()` is trusted for these
four.

### Everything else is directly live in the outer form — no nested editor

Confirmed by reading the real `input.disabled` / class list, not the
approximate text dump:

- **The 4 TRUE-result action checkboxes** (`Send message` / `Start micro
  dialog` / `Mark case as solved…` / `Stop…and finish coaching`) are **all
  `disabled: false`** — directly clickable in the outer form. On the sampled
  rule: `[false, true, false, false]` (only "Start micro dialog" checked),
  matching Stage 3's captured data.
- **At least one filterselect is directly live** (`disabled: false`) — almost
  certainly `Micro dialog to start`, since Stage 3's text dump showed it
  holding a real value (`Prompt patient to conduct daily spirometry > …`)
  while `messageGroup`/`storeResultVar` showed `[disabled]`. This session
  found **4** filterselects total with pattern `[enabled, disabled, enabled,
  enabled]` on this rule — one more `enabled` than expected from the
  Stage-3 text dump (which implied only 1 of ~3 should be live). **Not yet
  reconciled** — the extra two live filterselects may belong to the (empty,
  on this rule) DOES-answer/DOES-NOT-answer action-target pickers rendering
  in the DOM even unused. Needs a rule where more of these are populated to
  map cleanly by value, not just by disabled-state.
- **Both sliders are `disabled: true`** — this is `Hour to send message`
  and `Minutes … not answered`. Neither is directly draggable. The outer
  modal's button list includes quick-pick buttons (`1`/`5`/`10`/`30`/`60`
  for the timeout, seen without an `infinite` option here — contrast the
  message-level timeout field from Phase 0, which does have `infinite`) —
  **whether clicking one of these presets is itself a real, isolated write
  (bypassing the disabled slider), or whether it too needs an enabling
  action first, is unconfirmed.** This is the single most important open
  question for Phase 3, since the reminder redesign's core mechanism is
  exactly these two timing fields. Test deliberately, on a throwaway
  condition rule if possible, before relying on it for spirometry.

## Tooling — new file

`tools/coaching-bundle-export/probe_rule_write.py` — read-only-by-default
discovery over `_rules_nav.py`'s existing helpers; opens the 4 field-group
sub-editors and dumps them, cancels every one, and reports (without
clicking) whether an OK button exists on the 4th. No `set_*` write helpers
exist in the repo yet — see `TASKS.md` Phase 1 for what's still needed
before Phase 3 can run for real:

1. A same-value OK-commit test on each of the 4 popup editors (comment /
   rule-expr / term-expr / result-variable), to confirm the write path
   before trusting it.
2. Resolve whether the timeout quick-pick buttons directly commit, or need
   an unlock step first.
3. Reconcile the filterselect count/mapping (4 seen vs. ~3 expected) on a
   rule where DOES-answer/DOES-NOT-answer routing is actually populated.
4. Only then: write `set_rule_field()` / a `rule_apply.py` with the same
   `--limit`/dry-run-unless-`--apply` gate as `rgroup_apply.py`, **plus**
   the coaching-identity check that tool is missing (flagged in Phase 0's
   log too).

## Addendum: coaching-identity safety check (built + verified live)

Built `tools/coaching-bundle-export/_pmcp_safety.py`
(`assert_expected_coaching()`), closing the gap flagged in the Phase 0 log:
no existing write tool verified which coaching the CDP tab was actually on.
Reads `.title-label`'s `Coaching "..."` text (there can be a second, empty
`.title-label` elsewhere in the DOM — match on the `Coaching "` prefix, not
just the class). Verified live, both branches: correctly resolved
`ALEX v01 zum Ausprobieren` on the open tab, and correctly raised
`WrongCoachingError` when asked to assert a different name. Retrofitted into
`tools/rgroups-table/rgroup_apply.py --apply` (prints the confirmed coaching
name, exits with a clear message instead of writing if it doesn't match).
Any future write tool (the Rules-tab one included) must call this before its
first write.

## Session hygiene notes

- Tree node indices from `dump_tree()` are **not stable across script runs**
  in the same session, let alone across sessions — always re-locate a
  target rule by caption substring, never hardcode an index (this cost one
  wasted `open_rule_modal` timeout mid-session — see below).
- One `open_rule_modal` call failed with `element is not enabled` after a
  previous script's `close_windows()` — re-ran the same call a few seconds
  later and it worked with no other change. Matches the already-documented
  "intermittent Vaadin quirk, just rerun" behaviour; confirmed session/tree
  were healthy throughout (`.v-tree` present, 0 stray `.v-window`s, correct
  coaching still open) so this wasn't session expiry or a leftover modal —
  a third, transient cause to expect alongside those two.
