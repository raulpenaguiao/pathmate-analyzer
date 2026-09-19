# Medication dose reminders — "Yes:1 No:0" answer-options bug found and fixed

2026-09-19. Surfaced by the user's own real-device test evidence (Signal
screenshots of "Alex DEV"): the dose-1 medication reminder correctly fired
its new v02 dialog (two-bubble "Quick reminder... / Did you take your
medication?"), but the participant's reply bubble literally read
**"Yes:1 No"** — raw config text leaking into the chat instead of two
tappable Yes/No buttons. The underlying value still worked (the correct
No-branch reply followed), so this was a rendering/parsing break, not a
logic break.

## Root cause

PMCP's Answer Options field for a `select one` question requires
**one `Label:Value` option per line** (newline-separated) — confirmed
from this same coaching's own working precedent,
`$mySpiro_spirometerWithinReach` (asked 6 different ways, every instance
stores `Yes:1\nNo:0` / `Da:1\nNu:0` as two lines in the exported
`coaching_ALEX_v01.html`).

All 3 medication dose dialogs' row 1 ("Did you take your medication?")
had this field stored as **one line with a space** instead:
`'Yes:1 No:0'` / `'Da:1 Nu:0'` — confirmed byte-for-byte via
`textarea.input_value()` with `repr()` on each dose's live field. PMCP
can't split a single line into two options, so it fell back to sending
the raw string as literal message text.

## Fix

Re-entered all 3 doses' row-1 Answer Options via
`_dialogs_nav.set_bilingual_field()` (which types via real keystrokes —
a `\n` in the Python string sends a real Enter keypress, producing an
actual newline in the textarea; the bug was in the original one-off
build script's string content, not in this helper). New values:
`en-GB: 'Yes:1\nNo:0'`, `ro-RO: 'Da:1\nNu:0'` for all 3 doses. Each fix
verified via a fresh re-navigation (not just in-session read-back)
before moving to the next dose.

## Navigation note for future reference

The 3 new `(v02)` dose dialogs are NOT siblings of their same-named old
dialogs. They're all 3 grouped together as children of a single folder
confusingly named "Prompt patient to take first dose of controller
medication" (`Prompt patient to take controller medication` >
`Prompt patient to take first dose of controller medication` >
`{first,second,third} dose ... (v02)`). The old pre-redesign 37/39-row
dialogs remain as separate top-level leaves directly under
`Prompt patient to take controller medication` (e.g. "Prompt patient to
take second dose of controller medication" with no `(v02)` suffix) —
these are the intentionally-orphaned reference copies documented in
4.1.5-4.1.7, with zero rules pointing at them; landing there is a
navigation mistake, not a sign the cutover didn't happen.

Also re-confirmed live: the coaching's `v-disabled` edit-lock (menubar +
Rules tree both greyed out, toolbar buttons dead) was NOT the previously
assumed "someone/something has it open elsewhere" server lock — it was
literally the **Monitoring toggle being active** for this coaching
(Basic Settings tab: "Monitoring is inactive/active! Click to
(de)activate."). Deactivating it immediately restored editability. This
should be the first thing checked before assuming a stale multi-session
lock next time the whole coaching goes unresponsive.

## Still open

The real test participant configuring only 2 medication doses (not 3)
means dose-3's rules and this same Answer Options field have never been
exercised by a real user — flagged, not yet investigated.
