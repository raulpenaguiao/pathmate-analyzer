# tools

Everything here is dev/CLI tooling that runs outside the Flask portal (`app/`)
— either driving the live PMCP editor over a CDP-connected browser, or working
against a `coaching.json` export already on disk. Nothing in this directory is
imported by the portal at request time, except `tools/rgroups-table/rgroup_*.py`,
which `app/rgroups_tool.py` imports directly (`sys.path`, no subprocess) to
back the portal's "Randomisation groups" tab — see that subfolder's README.

## Subfolders

| Folder | What it does |
| --- | --- |
| [`coaching-bundle-export/`](coaching-bundle-export/README.md) | The exporter: sweeps a live PMCP coaching over Playwright/CDP into one `coaching.json` (micro dialogs, nodes, rules, sending-rule timing) plus a coherence check against the Report HTML. Also holds the `probe_*.py` recon scripts used to reverse-engineer PMCP's Vaadin DOM, and their `spike/` capture dump. |
| [`rgroups-table/`](rgroups-table/README.md) | The `r_` randomisation-group pipeline: 4 steps over a pre-made `coaching.json` (build a table of every `r_*` message → prepare an LLM request manifest for thin pools → generate variants → write them into the live editor). Steps 1-3 are also wired into the portal. |

## Loose scripts

| Script | What it does |
| --- | --- |
| `start_pmcp.sh` | Launches a Chromium with a CDP debug port and logs it into the PMCP admin using `.env` credentials (user+password, optional TOTP). One self-contained step for every other tool here that needs a live, logged-in browser — see `coaching-bundle-export/WORKFLOW.md`. `--port` / `--url` / `--env` / `--no-login`. |
| `run.sh` | Runs the Flask portal locally for development: creates `.venv` and `.env` on first run if missing, installs `requirements.txt`, generates deploy info, then `exec`s `wsgi.py`. Safe to run from a fresh checkout. |
| `release_frontend.sh` | Triggers a production deploy: commits an empty "Release frontend" commit on the current branch, tags it `release_frontend-<UTC timestamp>`, and pushes both — `.github/workflows/release_frontend.yml` fires on that tag pattern and rsyncs + restarts the remote service. Does **not** stage or commit your working-tree changes; commit what you want released first. |

## Conventions across these tools

- **CDP tools never call the coaching export themselves.** The export
  (`coaching-bundle-export/export_coaching.py`) is the only thing that drives
  a live browser to *produce* `coaching.json`; it's comparatively slow and
  costly to run, so every downstream tool (`rgroups-table/`) takes a
  pre-made `coaching.json` as input instead of re-scraping it.
- **Destructive/costly steps require `--limit`.** Anything that calls an LLM
  or writes into the live editor takes a required `--limit N` — see
  `rgroups-table/README.md`.
- **Dry-run by default.** Anything that writes into the live PMCP editor
  defaults to printing a plan and requires an explicit `--apply` to write.
- Each subfolder's own `README.md` is the detailed reference; this file is
  just the map.
