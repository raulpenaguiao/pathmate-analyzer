"""One-at-a-time lock for the shared PMCP browser (CDP :9222).

Every tool that drives the live portal claims this lock when it starts and
releases it when it exits. A second tool refuses to start and says who holds
it. Added 2026-09-25: the browser queue was run by mail, and mail lags. An
export was handed to Raul while Loom's rgroup_apply write was already
running, because Loom hadn't read the hold message yet. The lock, not a
queue in someone's head, is the source of truth.

    import _browser_lock as BL
    BL.claim("export_coaching")          # raises BrowserBusy if held
    ...                                  # released automatically at exit

    python _browser_lock.py              # who holds it right now?
    python _browser_lock.py release      # clear a lock (only if its process is dead)

The lock is a JSON file under data/locks/ (gitignored). A lock whose process
is gone is stale and is taken over automatically, with a note. Owner = $AGENT_SLUG
(the agent's codename slug), else the OS user (a human run).
"""
from __future__ import annotations

import atexit
import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LOCK = REPO / "data" / "locks" / "pmcp-browser.lock"


class BrowserBusy(RuntimeError):
    """Another live process holds the PMCP browser."""


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def holder() -> dict | None:
    """The current lock record if its process is alive, else None."""
    try:
        rec = json.loads(LOCK.read_text())
    except (FileNotFoundError, ValueError):
        return None
    return rec if _alive(int(rec.get("pid", 0))) else None


# Scripts known to drive the live browser. Belt and braces for tools that
# don't claim the lock yet: a running one blocks a claim just like a lock.
DRIVERS = ("rgroup_apply.py", "export_coaching.py", "probe_", "prune_dialogs.py",
           "create_variables", "_medication", "rebuild_")


def running_drivers() -> list[str]:
    """Other processes whose command line runs a known browser-driving script."""
    me, out = os.getpid(), []
    for d in Path("/proc").iterdir():
        if not d.name.isdigit() or int(d.name) == me:
            continue
        try:
            argv = (d / "cmdline").read_bytes().decode(errors="replace").split("\0")
        except OSError:
            continue
        # the interpreter itself, running the script as its first argument -
        # not shells/timeout wrappers that merely mention it in their command
        if not argv or not Path(argv[0]).name.startswith("python"):
            continue
        script = next((a for a in argv[1:] if not a.startswith("-")), "")
        if any(k in Path(script).name for k in DRIVERS):
            out.append(f"pid {d.name}: {' '.join(argv).strip()[:160]}")
    return out


def describe(rec: dict) -> str:
    return (f"{rec.get('tool')} (owner {rec.get('owner')}, pid {rec.get('pid')}) "
            f"since {rec.get('since')}")


def claim(tool: str) -> dict:
    """Take the lock for this process or raise BrowserBusy. Re-entrant for
    the same pid. Released automatically at interpreter exit."""
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    cur = holder()
    if cur and int(cur["pid"]) != os.getpid():
        raise BrowserBusy(
            f"PMCP browser is in use by {describe(cur)} - wait for it to finish "
            f"(check: python tools/coaching-bundle-export/_browser_lock.py)")
    others = running_drivers()
    if others:
        raise BrowserBusy("PMCP browser looks in use - another browser-driving "
                          "script is running (it holds no lock):\n  "
                          + "\n  ".join(others))
    if LOCK.exists() and not cur:
        try:
            print(f"(taking over a stale browser lock: {LOCK.read_text().strip()[:160]})")
        except OSError:
            pass
    rec = {"tool": tool,
           "owner": os.environ.get("AGENT_SLUG") or os.environ.get("USER", "?"),
           "pid": os.getpid(), "since": time.strftime("%Y-%m-%d %H:%M:%S"),
           "cmd": " ".join(sys.argv)[:300]}
    LOCK.write_text(json.dumps(rec))
    atexit.register(release)
    return rec


def release() -> None:
    """Drop the lock if this process holds it."""
    try:
        rec = json.loads(LOCK.read_text())
    except (FileNotFoundError, ValueError):
        return
    if int(rec.get("pid", 0)) == os.getpid():
        LOCK.unlink(missing_ok=True)


if __name__ == "__main__":
    if sys.argv[1:] == ["release"]:
        cur = holder()
        if cur:
            sys.exit(f"refusing: held by a LIVE process - {describe(cur)}")
        LOCK.unlink(missing_ok=True)
        print("cleared")
    else:
        cur = holder()
        others = running_drivers()
        print(f"held by {describe(cur)}\n  {cur.get('cmd')}" if cur else
              ("no lock, but running: \n  " + "\n  ".join(others)) if others else "free")
