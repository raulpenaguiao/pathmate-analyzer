"""Portal glue for the r_ randomisation-group pipeline (steps 1-3).

Steps 1-3 of tools/rgroups-table/ run against an attached coaching.json and
never touch a browser, so they're safe to run inside the Flask process. Step
4 (writing the generated variants into the live PMCP editor over Playwright)
stays a CLI-only tool -- it needs a CDP-connected Chromium the portal process
doesn't have. See tools/rgroups-table/rgroup_apply.py.
"""
from __future__ import annotations

import csv
import sys
import threading
import uuid
from pathlib import Path

from app.config import Config

_TOOLS_DIR = Config.BASE_DIR / "tools" / "rgroups-table"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import rgroup_expand  # noqa: E402
import rgroup_prepare  # noqa: E402
import rgroup_report  # noqa: E402


def _path(coaching_id: str, suffix: str) -> Path:
    return Config.COACHING_FILES_DIR / f"{coaching_id}.{suffix}"


def table_path(coaching_id: str) -> Path:
    return _path(coaching_id, "rgroups_table.csv")


def requests_path(coaching_id: str) -> Path:
    return _path(coaching_id, "rgroups_requests.csv")


def generated_path(coaching_id: str) -> Path:
    return _path(coaching_id, "rgroups_generated.csv")


def _write_csv(path: Path, cols: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def _read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------------------
# Step 1 & 2 -- synchronous, no network calls
# ---------------------------------------------------------------------------

def run_report(coaching_id: str, bundle: dict) -> dict:
    rows = rgroup_report.collect(bundle)
    _write_csv(table_path(coaching_id), rgroup_report.COLS, rows)
    groups = {r["randomisationGroup"] for r in rows}
    pools = {r["pool"] for r in rows}
    thin = {r["pool"] for r in rows if r["thin"] == "yes"}
    return {
        "groups": len(groups), "messages": len(rows),
        "pools": len(pools), "thinPools": len(thin),
    }


def run_prepare(coaching_id: str) -> dict:
    tpath = table_path(coaching_id)
    if not tpath.is_file():
        raise FileNotFoundError("run step 1 (build the table) first")
    rows = _read_csv(tpath)
    reqs = rgroup_prepare.build_requests(rows)
    _write_csv(requests_path(coaching_id), rgroup_prepare.COLS, reqs)
    variants = sum(int(r["needVariants"]) for r in reqs)
    return {"pools": len(reqs), "variants": variants}


# ---------------------------------------------------------------------------
# Step 3 -- LLM calls, run in a background thread with pollable progress.
# In-memory job registry: fine for a small internal, single-operator portal
# (see app/storage.py's docstring); not meant to survive a process restart.
# ---------------------------------------------------------------------------

JOBS: dict[str, dict] = {}
_JOBS_LOCK = threading.Lock()


def start_expand_job(coaching_id: str, provider: str, limit: int, api_key: str) -> str:
    rpath = requests_path(coaching_id)
    if not rpath.is_file():
        raise FileNotFoundError("run step 2 (prepare requests) first")
    reqs = _read_csv(rpath)
    if not reqs:
        raise ValueError("no thin pools to expand")
    limit = max(1, min(limit, len(reqs)))
    job_id = uuid.uuid4().hex

    with _JOBS_LOCK:
        JOBS[job_id] = {
            "coachingId": coaching_id, "total": limit, "current": 0, "done": 0,
            "pool": "", "lastStatus": "", "finished": False,
            "okCount": 0, "totalVariants": 0, "error": None,
        }

    def _progress(i, n, pool, status):
        with _JOBS_LOCK:
            job = JOBS.get(job_id)
            if job is None:
                return
            job["total"] = n
            job["current"] = i
            job["pool"] = pool
            if status != "start":
                job["done"] = i
                job["lastStatus"] = status

    def _run():
        try:
            gen_rows, _prompts = rgroup_expand.expand(
                reqs, provider, limit, dry=False, progress=_progress, api_key=api_key,
            )
            _write_csv(generated_path(coaching_id), rgroup_expand.GEN_COLS, gen_rows)
            ok = sum(1 for r in gen_rows if r["status"] == "ok")
            with _JOBS_LOCK:
                JOBS[job_id].update(
                    finished=True, okCount=ok, totalVariants=len(gen_rows),
                )
        except Exception as e:  # noqa: BLE001 -- surfaced to the poller, not raised
            with _JOBS_LOCK:
                JOBS[job_id].update(finished=True, error=str(e))

    threading.Thread(target=_run, daemon=True).start()
    return job_id


def job_status(job_id: str) -> dict | None:
    with _JOBS_LOCK:
        job = JOBS.get(job_id)
        return dict(job) if job else None
