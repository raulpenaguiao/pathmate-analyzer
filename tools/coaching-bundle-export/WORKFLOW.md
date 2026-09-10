# Export a coaching to JSON — workflow

Turns one PMCP coaching into a single JSON file: every micro-dialog node in
order (with its randomisation group), the full per-language text and
decision-branch logic, and the rule tree with each sending rule's timing and
routing.

It's browser automation over the DevTools protocol — you drive a real logged-in
Chromium, the scripts read it. **No LLM, no API key.** The Rules sweep opens
each sending rule's editor modal, which commits a no-op re-save on close, so
run the full thing against **sandbox coachings only** and log it under
`../../autochanges/`.

---

## Step 1 — open the browser

```bash
cd tools/coaching-bundle-export
./open_chromium.sh
```

Launches a Chromium with a debug port on `127.0.0.1:9222` and a throwaway
profile, pointed at the PMCP admin login. If one is already running on that
port it just reuses it.

(`./open_chromium.sh 9333` to use a different port; pass the port to
`export_coaching.sh --cdp http://127.0.0.1:9333` too.)

## Step 2 — log in and open the coaching (by hand, in that window)

1. Log in — username + password + **TOTP**.
2. **Coachings** in the left nav → click your coaching's row → **Edit**
   (selecting the row and clicking Edit are two separate clicks).
3. **Basic Settings and Modules** → **Monitoring: click to deactivate.**
   This is required — the Micro Dialogs menu's popups silently fail while
   Monitoring is active. It changes live coaching state, so do it by hand;
   turn it back on when you're done unless told otherwise.

Leave the browser on this coaching. The next step will tell you which
sub-view (Micro Dialogs, then Rules) to switch to, and wait for you.

## Step 3 — run the export

```bash
./export_coaching.sh --report /path/to/Coaching_<name>.html  my_coaching.json
```

`my_coaching.json` is whatever name you want. `--report` is the coaching's
**Report-HTML export** (Coaching → Report → save the page) — optional but
strongly recommended: it's the only source of full message text and
decision-branch conditions.

The script pauses twice and tells you exactly what to click:

1. **"Put the browser on the MICRO DIALOGS view"** — Edit → Micro Dialogs,
   one dialog's table visible. Press Enter → it sweeps every dialog
   (~8–12 min for ~100 dialogs; the window goes very wide and off-screen on
   purpose, then is restored).
2. **"Put the browser on the RULES tab"** — Edit → Rules, the tree with the
   four `Execution on …` rows. Press Enter → it expands the whole rule tree
   and opens each sending rule's "Edit rule:" modal (~25 no-op re-saves on
   the sandbox).

Then it copies the richest bundle produced to `my_coaching.json` and prints a
count summary.

### Options

| flag | effect |
| --- | --- |
| `--report FILE` | enrich with full text + decision branches from the Report HTML |
| `--dialogs-only` | Micro Dialogs sweep only — **no live writes** |
| `--rules-only` | Rules sweep only |
| `--cdp URL` | CDP endpoint (default `http://127.0.0.1:9222`) |
| `--workdir DIR` | where intermediate `coaching.bundle*.json` land (default `../../data/rgroups`) |
| `--yes` | don't pause for the "switch view" prompts (you pre-positioned the browser) |

## Output shape

```jsonc
{
  "coaching":     { "name", "languages", "scrapedAt", "stage" },
  "microDialogs": [ { "uid", "name", "folderPath", "nodeCount", "nodeUids" } ],
  "nodes":        [ { "uid", "microDialogUid", "order", "type", "comment",
                      "channel", "randomisationGroup", "flags",
                      // with --report:
                      "textByLang", "answerOptionsByLang", "branches" } ],
  "rules": {                                  // from the Rules sweep
    "sections":  ["DAILY BASIS", "PERIODIC BASIS", "USER INTENTION"],
    "ruleTree":  [ { "uid", "section", "depth", "order", "parentUid",
                     "kind": "condition|sender", "caption" } ],
    "sendingRules": [ { "uid", "section", "primaryAction",
                        "microDialogPath": [], "messageGroup",
                        "sendHourVariable", "notAnsweredTimeoutMinutes",
                        "doesAnswerRules": [], "doesNotAnswerRules": [] } ]
  }
}
```

Full field reference: `DESIGN.md`. Reference output for ALEX v01:
`rules_stage3_ALEX_v01.json` + `../../docs/rules_stage3_ALEX_v01.md`.

## When something goes wrong

- **`connect ECONNREFUSED 127.0.0.1:9222`** — the browser was closed. Re-run
  `./open_chromium.sh` and step 2.
- **"no `.v-tree` on screen" / "no dialog table"** — wrong sub-view, or the
  view drifted back to the coaching's Information page. Click the right tab
  and rerun (the Rules script re-clicks "Rules" for you).
- **Every folder / node fails** — the PMCP session expired (~10 min idle).
  Log in again in the browser, re-navigate, rerun. Do **not** reload the
  page — that drops the whole app back to the login screen.
- **One folder fails, the rest are fine** — intermittent Vaadin quirk; just
  rerun.

More detail in `README.md` ("Known hiccups") and the repo root `README.md`
("Navigating the live PMCP portal").
