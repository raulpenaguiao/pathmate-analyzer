# coaching-bundle-export

Turns a PMCP coaching's **micro dialogs** into one JSON file
(`coaching.bundle.json`) — every node, in order, with a stable id, its type, all
the editor-grid columns, and the **randomisation group**. With `--enrich` it also
pulls in the full per-language message text and the decision-point branch logic.

This is browser automation + HTML parsing. **No LLM is involved** — you do not
need Claude, an API key, or an internet AI service to run it.

## Files

| File | Role |
| --- | --- |
| `export_bundle.py` | the tool: sweeps the live editor over CDP → `coaching.bundle.json` |
| `enrich_bundle.py` | joins the Report-HTML export for full text + branches → `coaching.bundle.v2.json` (also runs standalone) |
| `_menu_nav.py` | Vaadin MenuBar discovery / navigation helpers used by `export_bundle.py` |
| `DESIGN.md` | the fuller picture: data sources, what's still missing (Stage 3/4), schema |
| `probe_dom.py` | read-only: dump the page's DOM structure / selectors (for when the portal markup changes) |
| `probe_node_editor.py` | read-only: open a node's detail editor and dump its fields (Stage-3 groundwork) |

## Prerequisites

- Python with `playwright` installed: `.venv/bin/pip install playwright`
  (only the package — the browser binary below is separate and you may already
  have one).
- A Chromium you can point at with the DevTools protocol. The commands below use
  Playwright's bundled Chromium; any Chrome/Chromium works.
- Login access to `https://cp22.pathmate.cloud/PMCP/admin` (username + password +
  TOTP).
- For `--enrich`: the coaching's **"Report" HTML export** on disk, and this
  script run from inside the `pathmate-analyzer` repo (it imports
  `app.coaching_model` to parse that HTML — set `PMCP_REPO` if run elsewhere).

## Run it

**1. Start a Chromium with a debug port** (detached, so it survives script
restarts):

```bash
CHROME=~/.cache/ms-playwright/chromium-*/chrome-linux64/chrome    # or your chrome
setsid nohup $CHROME --remote-debugging-port=9222 \
  --user-data-dir=/tmp/pmcp-cdp-profile --no-first-run --start-maximized \
  https://cp22.pathmate.cloud/PMCP/admin >/tmp/pmcp-chrome.log 2>&1 & disown
```

**2. In that window, by hand:** log in, then
`Coaching → <your coaching> → Edit → Basic Settings and Modules →
Monitoring: inactive → Micro Dialogs`, and click any dialog so a table shows.

**3. Run the export:**

```bash
cd /path/to/pathmate-analyzer
export PMCP_CDP=http://127.0.0.1:9222 PMCP_OUT="$PWD/data/rgroups"

# grid data only
.venv/bin/python tools/coaching-bundle-export/export_bundle.py

# grid data + full text + decision branches
.venv/bin/python tools/coaching-bundle-export/export_bundle.py \
  --enrich "$PWD/Coaching_ALEX_v01_zum_Ausprobieren.html"
```

Takes roughly 8–12 minutes for ~100 micro dialogs. The window is widened to
~12000 px during the run (goes off-screen — intentional; it is restored at the
end).

`enrich_bundle.py` can also be run on its own afterwards:

```bash
.venv/bin/python tools/coaching-bundle-export/enrich_bundle.py \
  data/rgroups/coaching.bundle.json Coaching_ALEX_v01_zum_Ausprobieren.html data/rgroups
```

## Output

`coaching.bundle.json` (and `.v2.json` with `--enrich`):

```jsonc
{
  "coaching":     { "name", "languages", "scrapedAt", "stage" },
  "microDialogs": [ { "uid": "md-000", "name", "folderPath": [], "isFolder",
                      "nodeCount", "nodeUids": [], "missingRows": [] } ],
  "nodes": [ {
    "uid": "md-000#003", "microDialogUid": "md-000", "order": 3,
    "type": "message|decision", "rawType": "Message|DECISION POINT",
    "comment", "gridText",                       // gridText is the truncated cell
    "channel", "answerType", "resultVariable", "randomisationGroup",
    "flags": { "commandMessage", "containsMedia", "containsSurvey", "containsRules" },
    // added by --enrich:
    "textByLang": { "en-GB": "", "ro-RO": "" },
    "answerOptionsByLang": {}, "commandByLang": {}, "triggerExprs": [], "mediaFile": "",
    "branches": [ { "condition", "comment", "writesVar", "stopMicroDialog",
                    "leaveDecisionPoint", "jumpDialog", "cascadeDialog", "supported" } ]
  } ]
}
```

Reference run (ALEX v01, 2026-09-03): **107 micro dialogs, 1177 nodes**
(919 Message, 258 Decision Point — the grid has no separate "event"/"command"
type; events are Decision Point rows, commands are flagged Messages), **96
distinct `r_` randomisation groups**. `--enrich` resolved full text for 92 of
107 dialogs (the other 15 are empty folder groupers) with 0 unresolved, and
attached branch logic to 255 of 258 decision points.

## Has it been tested?

- `enrich_bundle.py` — yes, end-to-end against the real `coaching.bundle.json`
  and Report HTML (92 dialogs merged, 0 unresolved).
- `export_bundle.py` — the sweep logic is the code that produced the reference
  bundle above (`data/rgroups/coaching.bundle.json`, 1177 nodes, cross-checked
  against the coaching's own metadata sidecar). The `--enrich` wiring and
  `_menu_nav` import were re-verified.

## Known hiccups

- **"popup 1 for '…' never opened" / hover timeouts on every folder.** The PMCP
  login session expired (silently — the old page still renders, but the server
  rejects clicks). Reload the coaching page in the browser, log in again,
  re-navigate to Micro Dialogs, and rerun. Sessions last ~1–2 h.
- **One folder fails with "popup never opened" but the rest succeed.** An
  intermittent Vaadin MenuBar quirk. Just rerun; or ignore it if that folder is
  an empty grouper (the run continues and its child dialogs are still swept).
- **`cannot import app.coaching_model`.** `--enrich` needs to run from the
  `pathmate-analyzer` repo, or with `PMCP_REPO=/path/to/repo` set.
- **A dialog logs `MISSING [rows]`.** The round-trip sweep didn't capture every
  row of a very tall table. Rare; rerun that one, or widen `PMCP_WIDE`.
- **The `►` overflow item in the menubar won't open under automation.** Handled
  by widening the window so every top-level item renders inline — don't lower
  `PMCP_WIDE` below ~9000.
- The browser must stay on the **Micro Dialogs** view of the target coaching
  with **Monitoring inactive** for the whole run; don't click around in it.
