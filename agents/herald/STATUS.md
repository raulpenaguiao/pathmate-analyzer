# Herald — status

## 2026-09-21

Read all six baseline advisor artifacts (One Question at a Time, The
Interrupt Contract, The ALEX Rulebook, The Navigation Layer, ALEX v02
Progress Tree, Watching It Write Itself).

Actioned the one open item from the starter mail: the "51→10 rows, same
content" claim in **One Question at a Time** overstated things — 3
wording-variant pools lost their live `r_` randomisation tags during the
spirometry dialog rebuild. Content is intact/recoverable, just not
currently randomising as a pool.

- Mailed Mason (owns the v02 dialog rebuilds) to track down and retag the
  3 pools; pointed him at Loom for r_ tooling if a live diff helps.
- Republished **One Question at a Time** (v2) with the "same content"
  wording removed and an explicit caveat + chip in step 3, until Mason
  confirms the fix.

Will pull the caveat back out once Mason reports it's landed. No other
discrepancies found across the six artifacts this pass.

## 2026-09-23

Mason replied: only 2 of the 3 flagged pools are a real gap
(`r_PromptForSpirometry_Stage1_Push`/`_Stage3`) — Loom is retagging those
now. The 3rd (`r_PostponeSpirometry`) wasn't lost, it was deliberately
retired in the redesign (spec §2.4/§3.2). Corrected the artifact's caveat
from "3 pools" to "2", noted the 3rd was a false alarm (v3). Still
waiting on Loom's retag landing live before the caveat comes out
entirely — tracked in `agents/herald/context/open-followups.md`.

## 2026-09-23 — session handoff (restart)

Flushing state ahead of Raul's planned agent-wide restart. Everything
above is current as of now; nothing else is in flight.

**Open item** (full detail in `context/open-followups.md`): "One Question
at a Time" (https://claude.ai/artifact/7A3MteX2HR3nDoEWL1XcCQ, currently
v3) carries a caveat that 2 wording-variant pools in the spirometry
dialog lost their live `r_` tags during the v02 rebuild. Loom is
retagging them now (per Mason). **Next action for the new session**:
check Mason's/Loom's STATUS.md for confirmation the retag is live, then
republish the artifact removing the caveat/chip and restoring "same
content" in step 3. Nothing to do until that confirmation lands.

**Housekeeping**: this session had a mailbox-listener poll loop running
in the background (per RULES.md rule 5) plus a `Monitor` watch on it —
both tied to this session and not expected to survive the restart. The
new session should just set up its own fresh listener per the current
rule 5, not try to resume this one.

Stopping here per Raul's instruction — not starting anything new.

## 2026-09-23 — resumed after restart

Read the auto-resume mail (RULES 4b) and acted on my own open item.
Loom's STATUS.md shows `r_PromptForSpirometry_Stage1_Push` is retagged
and confirmed live; `_Stage3` is not, and Loom is blocked on the PMCP
session-drop question that Warden escalated to Raul. Republished **One
Question at a Time** (v4,
https://claude.ai/artifact/7A3MteX2HR3nDoEWL1XcCQ): the caveat and chip now
say "1 pool untagged", and it notes the second pool was fixed. Next step:
once Loom confirms Stage3 is live, remove the caveat and chip entirely and
restore "same content" in step 3. Waiting on Loom until then.

## 2026-09-24

Acted on Warden's rule that md- uids are export positions, so dialogs are
referred to by `path`. Replaced the one uid in my own notes with the path.
Checked all six advisor artifacts: the only hit is `md-030` in Kart's
Progress Tree, and that line is also out of date about Stage1_Push. Mailed
Kart rather than editing an artifact Kart owns. Still waiting on Loom's
Stage3 retag to drop the last caveat from One Question at a Time.

## 2026-09-25 — summary for Raul's check-in (last 24h)

**Done**
- **md- uid rule** (Warden): no uids in my notes now. Checked all six advisor
  artifacts. The one hit, in Kart's Progress Tree, was mailed to Kart, who
  fixed it in v11.
- **`docs/coaching_categories_table.md`**: told Mirror "yes, deletable" from
  my side. No advisor artifact cites it, and Mason's answer is what decides it.
- **One Question at a Time** is still at v4 ("1 pool untagged").

**In flight / open**
- **Stage3 retag**: Loom's STATUS (09-24 ~13:40) says it is partly written
  and the live state is unverified. I'm deliberately not touching the v4
  caveat until Loom reads the rows back. After that I'll either drop the
  caveat or restate it exactly.
- **Question for Raul (not started)**: should I check the PMCP-behaviour
  claims in the six advisor artifacts against the official v6.0 docs? This
  matters most for The Interrupt Contract and The Navigation Layer. It's
  scope expansion, so I'm waiting on his go-ahead.
- **Noted, not mine to fix**: Mason flagged that The Interrupt Contract
  (09-18) says it reuses the two "Transition message..." dialogs "as-is",
  but those were deleted in Phase 2. Watching It Write Itself repeats the
  same ladder framing. Both need a pass once Raul and Mason settle the
  interrupt design (restart-with-resume-line vs. the artifact's ladder).
  Raising it here for the conversation.
- **Update, 09-25 morning**: Loom verified the live state from Warden's fresh
  export (`..._20260925-093313.json`). The Stage3 pool is re-tagged and live
  with 2 of 6 wordings; 4 are still to add. Republished **One Question at a
  Time** v5: the caveat now says one pool is fully restored and the other is
  randomising again with 2 of 6. Once Loom adds the last 4, I'll drop the
  caveat entirely.
