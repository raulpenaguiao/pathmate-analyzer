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
PMCP_TOTP_SECRET=JBSWY3DPEHPK3PXP        # base32 seed from the authenticator setup
```

`PMCP_TOTP_SECRET` is the secret shown (often as a QR code / "manual entry
key") when you set up the 2FA authenticator; spaces are fine. Leave the keys
blank to always log in by hand.

## Step 1 — open the browser

```bash
cd tools/coaching-bundle-export
./open_chromium.sh
```

Launches a Chromium with a debug port on `127.0.0.1:9222` and a throwaway
profile, pointed at the PMCP admin login. Reuses one already on that port.
(`./open_chromium.sh 9333` for a different port — pass
`--cdp http://127.0.0.1:9333` to `export_coaching.sh` too.)

## Step 2 — run the export

```bash
./export_coaching.sh --report /path/to/Coaching_<name>.html  my_coaching.json
```

`my_coaching.json` is whatever name you want. `--report` is the coaching's
**Report-HTML export** (Coaching → Report → save the page) — optional but
strongly recommended: it's the only source of full message text and
decision-branch conditions.

What it does:

1. **Auto-login** from `.env` (`pmcp_login.py`) — no-op if already logged in.
   If it can't (missing keys, changed login page), it says so and pauses for
   you to log in by hand.
2. **Pauses once** — *"open your coaching → click Edit → DEACTIVATE
   MONITORING"*. This is the only manual browser action. Monitoring must be
   off or the Micro Dialogs menu's popups silently fail. Turn it back on when
   you're done unless told otherwise. Press Enter.
3. **Micro Dialogs sweep** — navigates to that view itself, sweeps every
   dialog (~8–12 min for ~100; the window goes very wide and off-screen on
   purpose, then is restored).
4. **Rules sweep** — navigates to the Rules tab itself, expands the whole
   rule tree, opens each sending rule's "Edit rule:" modal (~25 no-op
   re-saves on the sandbox).
5. Copies the richest bundle produced to `my_coaching.json` and prints a
   count summary.

### Options

| flag | effect |
| --- | --- |
| `--report FILE` | enrich with full text + decision branches from the Report HTML |
| `--dialogs-only` | Micro Dialogs sweep only — **no live writes** |
| `--rules-only` | Rules sweep only |
| `--env FILE` | `.env` to read credentials from (default `../../.env`) |
| `--no-login` | skip auto-login (you logged in by hand) |
| `--cdp URL` | CDP endpoint (default `http://127.0.0.1:9222`) |
| `--workdir DIR` | where intermediate `coaching.bundle*.json` land (default `../../data/rgroups`) |
| `--yes` | don't pause at the Monitoring step (you already did it) |

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
  `./open_chromium.sh` and the export.
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
