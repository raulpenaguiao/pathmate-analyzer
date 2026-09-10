# Export a coaching to JSON — workflow

Turns one PMCP coaching into a single JSON file: every micro-dialog node in
order (with its randomisation group), the full per-language text and
decision-branch logic, and the rule tree with each sending rule's timing and
routing.

It's browser automation over the DevTools protocol — the scripts drive a real
Chromium. **No LLM, no API key.** The Rules sweep opens each sending rule's
editor modal, which commits a no-op re-save on close, so run the full thing
against **sandbox coachings only** and log it under `../../autochanges/`.

**The only manual browser step is deactivating Monitoring** (a live-state
change — the scripts never touch that toggle). Login is automatic from
`.env`; switching between the Micro Dialogs and Rules views is automatic.

---

## One-time setup — credentials in `.env`

In the repo root `.env` (gitignored; copy from `.env.example`):

```
PMCP_USERNAME=you@example.com
PMCP_PASSWORD=...
PMCP_TOTP_SECRET=JBSWY3DPEHPK3PXP        # optional
```

Username + password are always auto-filled. `PMCP_TOTP_SECRET` — the seed
shown (QR code / "manual entry key") when you set up the 2FA authenticator,
spaces fine — is **optional**: with it the 6-digit code is generated too;
without it, the script fills user + password and then waits ~2 min for you to
type the code in the browser. Leave `PMCP_USERNAME`/`PMCP_PASSWORD` blank to
log in fully by hand.

## Step 1 — start the browser and log in

```bash
tools/start_pmcp.sh
```

Launches a Chromium with a debug port on `127.0.0.1:9222` and a throwaway
profile, then logs into the PMCP admin using `.env`. Reuses a browser
already on that port. A cold start can take **up to ~1 minute** to bring the
debug port up — the script waits and prints each stage (launch, wait for
port, login: attach → form ready → typing → clicking → admin app). It exits
non-zero if login didn't complete.

`tools/start_pmcp.sh --no-login` just launches the browser; `--port N` /
`--url URL` / `--env FILE` to override.

## Step 2 — run the export

```bash
cd tools/coaching-bundle-export
./export_coaching.sh --report /path/to/Coaching_<name>.html  my_coaching.json
```

`my_coaching.json` is the single output — whatever name you want. `--report`
is the coaching's **Report-HTML export** (Coaching → Report → save the page)
— optional but strongly recommended: it's the only source of full message
text and decision-branch conditions, *and* it's what the coherence check
compares the DOM sweep against.

`export_coaching.sh` pauses once for the Monitoring toggle, then runs
`export_coaching.py`, which does everything in one pass:

1. **phase 1 — Micro Dialogs.** Navigates to that view itself, sweeps every
   dialog (~8–12 min for ~100; the window goes very wide and off-screen on
   purpose, then is restored). → `microDialogs`, `nodes` (incl. the
   randomisation group).
2. **phase 2 — enrich.** With `--report`, joins the Report HTML for full
   per-language text + decision branches.
3. **phase 3 — Rules.** Navigates to the Rules tab, expands the whole rule
   tree, opens each sending rule's "Edit rule:" modal (~25 no-op re-saves on
   the sandbox). → `rules` (`sections`, `ruleTree`, `sendingRules`).
4. **phase 4 — coherence check.** Compares the sweep to the Report HTML and
   to `coherence_baseline.json` (micro-dialog / node / rule / r_-group
   counts, per-dialog deltas). Writes a `validation` block and **exits
   non-zero** if the sweep collapsed or drifted off the baseline — the
   canary for a PMCP UI change that would otherwise silently break the
   export. Small, expected drift is a warning, not a failure.

### Options (passed straight through to `export_coaching.py`)

| flag | effect |
| --- | --- |
| `--report FILE` | enrich + coherence-check against the Report HTML |
| `--dialogs-only` | phase 1 (+2) only — **no live writes** |
| `--rules-only` | phase 3 only |
| `--no-modals` | rule tree skeleton only, no "Edit rule:" modals (phase 3, zero writes) |
| `--update-baseline` | rewrite `coherence_baseline.json` from this run (do this once against an export you trust) |
| `--yes` | don't pause at the Monitoring step |
| `--cdp URL` | CDP endpoint (default `http://127.0.0.1:9222`) |

## Output shape (one file)

```jsonc
{
  "coaching":     { "name", "languages", "scrapedAt" },
  "microDialogs": [ { "uid", "name", "folderPath", "isFolder", "nodeCount", "nodeUids" } ],
  "nodes":        [ { "uid", "microDialogUid", "order", "type", "comment",
                      "channel", "randomisationGroup", "flags",
                      // with --report:
                      "textByLang", "answerOptionsByLang", "branches" } ],
  "rules": {
    "sections":  ["DAILY BASIS", "PERIODIC BASIS", "USER INTENTION"],
    "ruleTree":  [ { "uid", "section", "depth", "order", "parentUid",
                     "kind": "condition|sender", "caption" } ],
    "sendingRules": [ { "uid", "section", "primaryAction",
                        "microDialogPath": [], "messageGroup",
                        "sendHourVariable", "notAnsweredTimeoutMinutes",
                        "doesAnswerRules": [], "doesNotAnswerRules": [] } ]
  },
  "validation": { "ok": true, "metrics": {…}, "htmlVsSweep": {…},
                  "vsBaseline": {…}, "warnings": [] }
}
```

Full field reference: `DESIGN.md`. Reference rule data for ALEX v01:
`rules_stage3_ALEX_v01.json` + `../../docs/rules_stage3_ALEX_v01.md`.

## When something goes wrong

- **`connect ECONNREFUSED 127.0.0.1:9222`** — the browser was closed. Re-run
  `tools/start_pmcp.sh` and the export.
- **"auto-login did not complete"** — keys missing/wrong in `.env`, or the
  PMCP login page changed shape. Log in by hand in the browser and press
  Enter at the pause, or re-run with `--no-login`.
- **"Micro Dialogs menu not on screen" / "no `.v-tree` on screen"** — the
  script tried to switch views and couldn't (usually: you're not inside the
  coaching's Edit view yet, or Monitoring is still on). Get to Edit with
  Monitoring off and rerun.
- **Every folder / node fails** — the PMCP session expired (~10 min idle).
  Log in again in the browser, re-navigate, rerun. Do **not** reload the
  page — that drops the whole app back to the login screen.
- **One folder fails, the rest are fine** — intermittent Vaadin quirk; just
  rerun.

More detail in `README.md` ("Known hiccups") and the repo root `README.md`
("Navigating the live PMCP portal").
