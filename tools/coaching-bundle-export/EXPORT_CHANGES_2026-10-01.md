# Exporter changes since the alex-sandbox BEFORE export (2026-10-01)

BEFORE = `data/exports/coaching_alex-v01-zum-ausprobieren_20261001-112433.json`
(exporter at 65697d8). The AFTER export of task 2 runs on the current exporter, so it
differs from BEFORE for two reasons: Loom's apply (the r_ variants) and the
changes below. Use this list to tell them apart.

## New fields (exporter only)

| where | field | meaning | commit |
|---|---|---|---|
| `rules.sendingRules[]` | `actionBoxes` | the 4 action checkboxes: `{label, checked, disabled}` | da60101 |
| `rules.sendingRules[]` | `answerTabs` | DOES / DOES NOT answer tabs: `{name, disabled}` (greyed state fixed in 2fbd15b) | da60101, 2fbd15b |
| `rules.sendingRules[]` | `disabledFields` | which editor fields are greyed (e.g. `messageGroup`, `notAnsweredTimeout`) | da60101 |
| `rules.sendingRules[]` | `microDialogToStartRaw` | exactly what "Micro dialog to start" shows, incl. `$participantNextMicroDialogIdentifier` | 999787f |
| `rules.ruleTree[]` | `section = "NO EXECUTION SECTION"` | rules at the top level, outside the 4 sections (were dropped before) | cd25e59 |

## Changed values (exporter only)

- **Rule tree:** alex-sandbox's **15 top-level rules outside the 4 sections** are now included
  (v02 medication gates 2-5 for doses 1-3, plus 3 "Fire medication dose N reminder"
  senders). Expect about **171 -> 186 rules** and **18 -> 21 senders**. Because rule uids
  are positional, `r-NNN` numbers shift. Compare rules by `caption` / `parentChain`.
- **`storeResultVariable`:** no longer picks up the message-group name (alex-live r-071)
  when the field shows "(no value set)"; it's `null` then (2fbd15b).
- **`answerTabs[].disabled`:** now `true` where PMCP greys the tabs (dialog-start rules);
  it was wrongly always `false` (2fbd15b).
- **Rule-tree log line:** "N nodes: X with child rules, Y terminal" replaces the
  meaningless "0 leaves" (cd25e59). Log only, not in the JSON.

## Coherence check (phase 5)

- New **warning** (not a failure) naming the rules outside the 4 sections.
- Baseline drift is expected on `ruleTreeNodes` and `sendingRules` (they go UP, which
  only warns). The run is compared with the previous baseline first, and only
  updates it if it passes (ef8f83a).
- **Fails** if any sender in the rule tree wasn't read (ef8f83a).

## Not changed

Dialog sweep, nodes, text, jumps, variables: no format changes since BEFORE.
Differences there come from Loom's apply (new r_ variant rows) or from PMCP.
