# Spirometry re-tag task — in-flight state (2026-09-21)

Full writeup in STATUS.md; this is the resumable state if cut off mid-task.

## Where things stand right now

- **Done**: swapped `rgroup_apply.py`'s local `TABLE_JS`/`read_table()` for
  `S.read_table_dense(page)` per Warden's mail. Compiles clean
  (`python3 -m py_compile tools/rgroups-table/rgroup_apply.py`). Owed: a
  real `--dry-run --limit 1` live check of this swap — bundle it into the
  same browser session as the re-tag work below, don't open the browser
  twice for two small things.
- **Mailed, waiting on replies**:
  - Warden (260921091805) — asked to coordinate CDP browser time (rule 4)
    to inspect the "Randomisation group" field's edit sub-editor DOM
    (haven't seen it live) before writing a new tagging mode.
  - Mason (260921091812) — flagged that `r_PostponeSpirometry` looks
    intentionally retired per redesign spec §2.4/§3.2 (no equivalent node
    in md-030), not accidentally dropped. Not blocking, just wanted him to
    confirm since he owns the spec.
- **Not yet started**: writing the actual new `rgroup_apply.py` tagging
  mode (see plan below) — blocked on Warden's browser slot + seeing the
  live DOM. ~70min waiting, no reply yet from Warden or Mason (Warden has
  read my mail per his empty inbox, Mason hasn't - he's mid a bigger
  blocking architecture question to the manager per his STATUS.md, so
  may be a while).

## De-risked while waiting (no browser needed, found in existing spike dumps)

`tools/coaching-bundle-export/spike/form_Spirometry_row0.json` (from
Warden's `probe_add_message.py`, run 2026-09-11) already has the full HTML
dump of the "Edit micro dialog message:" property sheet for a real
Spirometry-dialog row, including the "Randomisation group:" field: same
grid-layout pattern as "text (with placeholders):" (label + read-only
value box + its own "Edit" button) — confirms the existing `spot`-locator
technique in `rgroup_apply.py` (find `.v-label` matching a regex, nearest
"Edit" button by y-position) will work unchanged, just swap the label
regex to `/Randomisation group/i`. `form_Spirometry_row1/2.json` show the
read-only value as plain text, e.g. `r_FeedbackOnGoodCompliance` /
`(no value set)` — not a checkbox/multi-value widget.

`spike/cascade_v2_subwindow.json` (from `probe_cascade_checkbox.py`, which
hit this sub-editor by accident while probing a different field) confirms
its sub-editor is titled **"Edit randomisation group:"** with **Cancel/OK**
buttons (same shape as the text sub-editor `set_lang_text` already
handles) and 0 checkboxes inside — narrows it to a text/combo input, but
that probe only captured `checks`, not input widgets, so the exact input
selector (`textarea` vs `input[type=text]` vs Vaadin `.v-filterselect`
combobox) is still unconfirmed. That's the one thing actually worth a
live look before writing the write path — everything else above is
solid enough to code against already.

**CONFIRMED LIVE 2026-09-23** (read-only, Cancel'd, no writes) against the
real tagged row md-020 row 4 (r_PromptForSpirometry_Stage1_Push): the
"Randomisation group:" sub-editor is a single plain
`<input type="text" class="v-textfield ...">`, pre-filled with the
current group value, + Cancel/OK. Not a combobox/dropdown/checkbox list.
So the primitive is: click the field's own Edit button (same
label-then-nearest-button technique already in `rgroup_apply.py` for
"text (with placeholders):", just label regex `/randomisation group/i`),
`page.locator('.v-window').last.locator('input[type=text]').first.fill(GROUP)`,
click OK, then Close the outer modal. Same shape as `set_lang_text`, just
simpler (one field, not a language-tab toggle).

**Also confirmed**: the top-level Micro Dialogs menubar needs the window
widened first (`Browser.setWindowBounds` width ~12000px via CDP, same as
`export_coaching.py`'s `_widen_for_menubar` / already done inside
`rgroup_apply.py::run_apply`) — at normal width it overflows into a `►`
popup that scripted clicks can't open, so `navigate_and_select` silently
fails to find top-level items past the first handful. Wasn't obvious from
reading the code alone since `run_apply` does this widening unconditionally
before its per-variant loop; a bare probe script needs to do it too.

## The plan once browser access + DOM inspection happen

1. Inspect the Randomisation Group field's edit sub-editor on an
   already-tagged reference row (e.g. `md-020`'s r_PromptForSpirometry_
   Stage1_Push row) — read-only, figure out selector/widget type (text
   field? dropdown? autocomplete?).
2. Confirm current (untagged) state on `md-030#000` and `md-030#001`
   read-only.
3. Write a new mode in `rgroup_apply.py` (e.g. `--tag GROUP --pool 'X @ Y'
   --match <text prefix>` or similar) that: finds the row by en-GB text
   prefix match (same pattern as the rest of the file), opens the message
   editor, opens the Randomisation Group field's sub-editor, sets it to
   the target group, OK, Close, then verifies live via read_table that the
   column now shows the group — idempotent (skip if already correctly
   tagged), matching the existing code's style.
4. Get Warden to review the new nav code (his stated role).
5. Run it live for the 2 real target rows:
   - `md-030#000` -> `r_PromptForSpirometry_Stage1_Push`
   - `md-030#001` -> `r_PromptForSpirometry_Stage3`
6. Once tagged, the existing `rgroup_apply.py` add-flow (no changes
   needed) should be able to pull the remaining variants from `md-020`'s
   pools onto the new rows the normal way — need a CSV row for those,
   i.e. may need to regenerate `rgroups_generated_*.csv` or hand-build a
   small one from the existing `rgroups_table.csv` rows (101-103,
   105-110) since these are pre-existing wordings, not new LLM-generated
   ones — check whether `rgroup_apply.py`'s `build_plan()` can source
   straight from `rgroups_table.csv` for this restore case, or whether a
   one-off CSV needs hand-assembly. Not yet checked.
7. `r_PostponeSpirometry`: hold until Mason confirms; if confirmed
   retired, no action — note it as intentionally dropped somewhere
   durable (STATUS.md update, maybe a line in the redesign spec itself if
   Mason wants).

## Restore data, ready to use once tagging works

Destination path (md-030, for `_menu_nav.navigate_and_select`):
`["Prompt patient to conduct daily spirometry", "Prompt patient to conduct daily spirometry (v02)"]`
(md-030's own name has the "(v02)" suffix; it's nested one level under
md-020's folder, NOT under md-020's own name-as-leaf — confirmed from the
Sep 18 export's `folderPath`.)

**r_PromptForSpirometry_Stage1_Push** — canonical/already-present =
md-020#004 = md-030#000 exact text match ("Quick reminder to check your
lung function with spirometry today!"). Remaining 2 siblings to add once
tagged (source: `rgroups_table.csv`, still-live md-020 rows):
1. (canonical, already there) "Quick reminder to check your lung function
   with spirometry today!" / ro: "Îți reamintesc să îți verifici astăzi
   funcția pulmonară cu ajutorul spirometrului!"
2. "It's spirometry time! Let's make sure your lungs are doing well
   today." / ro: "Este timpul pentru spirometrie! Să verificăm cât de
   sănătoși sunt plămânii tăi astăzi."
3. "Hey $participantName, time for your daily spirometry check! 🌬️" / ro:
   "Salut, $participantName! E momentul pentru testul zilnic de
   spirometrie! 🌬️"

**r_PromptForSpirometry_Stage3** — canonical/already-present = md-020#011
= md-030#001 exact text match ("Do you have your spirometer handy?").
Remaining 5 siblings to add once tagged:
1. (canonical, already there) "Do you have your spirometer handy?" / ro:
   "Ai spirometrul la îndemână?"
2. "Is your spirometer close by?" / ro: "Este spirometrul tău în
   apropiere?"
3. "Do you have your spirometer with you?" / ro: "Ai spirometrul cu
   tine?"
4. "Is your spirometer within reach?" / ro: "Este spirometrul la
   îndemână?"
5. "Do you have access to your spirometer?" / ro: "Ai acces la
   spirometrul tău?"
6. "Is your spirometer nearby?" / ro: "Este spirometrul la îndemână?"

## STATUS 2026-09-23: implemented, dry-run verified, awaiting Warden review

Code is written and live in the working tree (`tools/rgroups-table/
rgroup_apply.py`, uncommitted, +153/-50). CSV-dry-run confirms both plans
are exactly right (see STATUS.md for full detail). Mailed Warden for
review of the new nav code before running it live for real
(260923085838). Once he clears it (or says go ahead without further
review), the actual write commands are:

```
.venv/bin/python tools/rgroups-table/rgroup_apply.py \
  --restore-from 'r_PromptForSpirometry_Stage1_Push @ Prompt patient to conduct daily spirometry' \
  --to-path 'Prompt patient to conduct daily spirometry / Prompt patient to conduct daily spirometry (v02)' \
  --bootstrap-text 'Quick reminder to check your lung function with spirometry today!' \
  --limit 5

.venv/bin/python tools/rgroups-table/rgroup_apply.py \
  --restore-from 'r_PromptForSpirometry_Stage3 @ Prompt patient to conduct daily spirometry' \
  --to-path 'Prompt patient to conduct daily spirometry / Prompt patient to conduct daily spirometry (v02)' \
  --bootstrap-text 'Do you have your spirometer handy?' \
  --limit 10
```

(browser window must already be widened - `run_apply` does this itself
at the top, 3600px, unconfirmed whether sufficient for this specific
deep-in-the-menu dialog since my manual probe needed 12000px to clear
the trailing overflow arrow for a LATER item - worth watching the first
live run closely for a "top item not found" failure; if it happens, widen
further before retrying, don't just re-run blind.)

After both run clean: re-read the coaching export or rerun
`rgroup_report.py` to confirm `rgroups_table.csv` picks up the two
restored pools under md-030, and note this in an autochanges/ entry per
repo convention (other agents' sessions log major live-coaching changes
there).

## STATUS 2026-09-23 (later) — Stage1_Push done, Stage3 blocked on session drops

Stage1_Push: DONE and confirmed live (md-030 rows 0-2, all tagged,
adjacent, correct text/ro-RO).

Stage3: NOT done. Real bug found+fixed along the way: `rgroup_apply.py`
hardcoded window width 3600px wasn't wide enough for this specific deep
top-level menu item ("Prompt patient to conduct daily spirometry" is far
enough into the ~107-item top-level Micro Dialogs menu that its popup
wouldn't reliably open) - now `WIDE = int(os.environ.get("PMCP_WIDE",
"12000"))`, same convention/default as `export_coaching.py`'s
`_widen_for_menubar`. That fix is real and worth keeping regardless of
what's below.

After that fix, hit something else: the PMCP session for account
`alex-dev-2` kept dropping to the login screen within seconds of a
successful navigation, across 3 separate re-logins, each confirmed by
directly reading the page (saw the literal login form). Far faster than
the README's documented ~1-2h silent-expiry pitfall, and happened with
only one CDP tab open the whole time (checked). Strong suspicion: PMCP
may be single-session-per-account, and something else logged into
`alex-dev-2` concurrently, silently kicking my session. Mailed Warden
(260923122741) rather than keep cycling logins on the shared account -
holding off on further live attempts until he replies.

**To resume once cleared**: same command as Stage1_Push's, already
verified correct via CSV dry-run:
```
PMCP_CDP=http://127.0.0.1:9222 .venv/bin/python tools/rgroups-table/rgroup_apply.py \
  --restore-from 'r_PromptForSpirometry_Stage3 @ Prompt patient to conduct daily spirometry' \
  --to-path 'Prompt patient to conduct daily spirometry / Prompt patient to conduct daily spirometry (v02)' \
  --bootstrap-text 'Do you have your spirometer handy?' \
  --limit 10
```
On the next live run, if it drops again: record whether it lands on the
LOGIN screen or a "coaching locked" state. Per Warden (260923204125), that
tells the two causes apart. Docs: an admin in a coaching locks it, and
"Reset All Locks" logs out anyone in the coaching session.
Idempotent - safe to just re-run once the session issue is resolved,
no manual cleanup needed first. Confirm login (`echo $body text` for
"Login" vs the app) before running, not just that start_pmcp.sh printed
"logged in" - it can drop again fast.

## Implementation approach decided (superseded by the above, kept for the reasoning trail)

Deliberately did NOT inject a hand-built file into `data/rgroups/
rgroups_generated_*.csv` — `build_plan()`'s `latest()` auto-chain would
silently make it the default target for anyone's next bare
`rgroup_apply.py` run, which is exactly the "ad hoc live-content risk"
AGENT.md warns against. Instead: add a proper new pipeline mode (source
variants straight from the committed `rgroups_table.csv`, not the
git-ignored `generated.csv`) — this is a real recurring need per the
starter mail ("watch for the same pattern in every dialog Mason rebuilds
from here"), not a one-off hack. Rough shape: `--restore-pool 'GROUP @
OLD_DIALOG' --to-path 'Folder / New Dialog'`. In `run_apply`'s existing
per-variant loop, when the target group isn't found in the destination
table at all (today's `if src is None: error`), and restore mode is on,
fall back to locating the *canonical variant's own text* anywhere in the
table (any group column value, including blank), tag that row's
Randomisation Group field via the new field-editor primitive, re-read the
table, and let the rest of the existing loop run unchanged — the
loop's own already-adjacent/already-present idempotency check will then
correctly no-op on the canonical variant itself and only add the
remaining siblings. Haven't written this yet — wanted the live DOM check
(input widget type in "Edit randomisation group:") first so the new
primitive isn't written against a guess.

## Key facts already established (don't re-derive)

- Old dialog `md-020` "Prompt patient to conduct daily spirometry" is
  untouched, still has full r_ pools (22 tagged rows across 12 groups).
- New dialog `md-030` "Prompt patient to conduct daily spirometry (v02)"
  is Mason's rebuild, 10 nodes (#000-#009), all untagged
  (`randomisationGroup: ""` in the export JSON). Text matches confirmed
  exact for #000 and #001 against the old pool's canonical wording.
- `rgroup_apply.py`'s add-flow (line ~505 pre-swap, search `no existing
  row with this group`) requires an existing tagged row to select+
  Duplicate — no bootstrap path exists yet. That's the actual gap.
- Source data used: `data/exports/coaching_alex-v01-zum-ausprobieren_
  20260918-103948.json` (newest export, post-Mason-rebuild).
