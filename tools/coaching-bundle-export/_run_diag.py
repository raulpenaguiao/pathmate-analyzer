"""Run diagnostics for every PMCP automation tool: make a failure or a stall
explain itself, instead of needing someone to reproduce it by hand.

Added 2026-09-25 after an export stalled >20 min and then died with a
misleading "could not re-enter the Edit view". Diagnosing it took three
manual screenshots, and the stall itself could not be located at all
afterwards. Four pieces:

  start_run_log(tool, name)  timestamp every stdout/stderr line and tee it to
                             data/logs/<tool>/<tool>_<name>_<ts>.log
                             (gitignored; logs are not exports)
  step(label)                name what the run is doing right now
  Heartbeat                  a thread that prints "still on <step> since ..."
                             whenever nothing has been printed for a while,
                             so a stall shows where it is within a minute
  snapshot(page, tag)        on failure: a screenshot + a JSON of page state
                             (session expired? which view? menubar
                             overflowed? open windows/notifications) next to
                             the log, plus a one-line diagnose() cause

Usage in a tool's main():

    log_path = D.start_run_log("export", slug)
    with D.Heartbeat():
        D.step("phase 1: micro dialogs")
        ...
        except SystemExit as e:
            await D.snapshot(page, "fail", str(e.code))
            raise
"""
from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LOG_ROOT = REPO / "data" / "logs"

_state = {"step": "starting", "step_since": time.time(),
          "last_out": time.time(), "log_dir": None, "stem": None}


class _TimestampTee:
    """Wrap a text stream: prefix each line with HH:MM:SS, mirror it to a
    log file, and record when the last line was written (for Heartbeat)."""

    def __init__(self, stream, logf):
        self.stream, self.logf, self._bol = stream, logf, True

    def write(self, s: str) -> int:
        if not s:
            return 0
        out = []
        for part in s.splitlines(keepends=True):
            if self._bol:
                out.append(time.strftime("%H:%M:%S "))
            out.append(part)
            self._bol = part.endswith("\n")
        text = "".join(out)
        self.stream.write(text)
        self.logf.write(text)
        self.stream.flush()
        self.logf.flush()
        _state["last_out"] = time.time()
        return len(s)

    def flush(self):
        self.stream.flush()
        self.logf.flush()

    def isatty(self):
        return False


def start_run_log(tool: str, name: str = "") -> Path:
    """Timestamp and tee all further stdout/stderr to a per-run log file.
    Returns the log path. Safe to call once per process."""
    ts = time.strftime("%Y%m%d-%H%M%S")
    d = LOG_ROOT / tool
    d.mkdir(parents=True, exist_ok=True)
    stem = f"{tool}_{name}_{ts}" if name else f"{tool}_{ts}"
    path = d / f"{stem}.log"
    logf = open(path, "a", encoding="utf-8")  # noqa: SIM115 - lives for the run
    sys.stdout = _TimestampTee(sys.__stdout__, logf)
    sys.stderr = _TimestampTee(sys.__stderr__, logf)
    _state.update(log_dir=d, stem=stem)
    print(f"run log -> {path}")
    return path


def step(label: str) -> None:
    """Record what the run is doing now (shown by Heartbeat and snapshot)."""
    _state["step"] = label
    _state["step_since"] = time.time()


class Heartbeat:
    """Context manager: a daemon thread that prints a 'still on <step>' line
    whenever nothing has been printed for `quiet_s` seconds. A thread, not an
    asyncio task, so it still fires if the event loop itself is stuck."""

    def __init__(self, quiet_s: int = 60):
        self.quiet_s = quiet_s
        self._stop = threading.Event()

    def _run(self):
        while not self._stop.wait(10):
            now = time.time()
            # only when the SAME step has been running that long, not merely
            # when output is sparse (the sweep prints every 20 dialogs, which
            # made normal progress look stuck on 2026-09-25)
            if (now - _state["last_out"] >= self.quiet_s
                    and now - _state["step_since"] >= self.quiet_s):
                since = time.strftime("%H:%M:%S", time.localtime(_state["step_since"]))
                print(f"  .. still on [{_state['step']}] since {since} "
                      f"({now - _state['step_since']:.0f}s, no output for "
                      f"{now - _state['last_out']:.0f}s)")

    def __enter__(self):
        threading.Thread(target=self._run, daemon=True).start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        return False


STATE_JS = r"""
() => {
  const t = document.body ? document.body.innerText : '';
  const bar = [...document.querySelectorAll('.v-menubar.md-menu > .v-menubar-menuitem')];
  return {
    url: location.href,
    loginForm: !!document.querySelector('input[type=password]'),
    sessionExpired: [...document.querySelectorAll('.v-Notification')]
      .some(n => /session expired/i.test(n.textContent || '')),
    coachingHeader: (t.match(/Coaching\s+"([^"]+)"/) || [])[1] || null,
    onCoachingsList: /COACHING STATUS/.test(t),
    menubarItems: bar.length,
    menubarLast: bar.length ? bar[bar.length - 1].textContent.trim() : null,
    windows: [...document.querySelectorAll('.v-window')]
      .map(w => w.textContent.replace(/\s+/g, ' ').trim().slice(0, 200)),
    notifications: [...document.querySelectorAll('.v-Notification')]
      .map(n => n.textContent.replace(/\s+/g, ' ').trim().slice(0, 200)),
    viewport: [innerWidth, innerHeight],
  };
}
"""


def diagnose(state: dict) -> str:
    """One-line most-likely cause from a STATE_JS result."""
    if not state:
        return "no page state (browser/CDP gone?)"
    if state.get("sessionExpired"):
        return ("PMCP session EXPIRED - run tools/start_pmcp.sh, re-open the "
                "coaching -> Edit, rerun")
    if state.get("loginForm"):
        return "on the LOGIN screen - run tools/start_pmcp.sh"
    if state.get("windows"):
        return f"a modal window is open: {state['windows'][0][:80]!r}"
    if state.get("menubarLast") == "►":
        return (f"Micro Dialogs menubar OVERFLOWED ({state['menubarItems']} "
                f"items then '►') - window too narrow (viewport "
                f"{state['viewport'][0]}px)")
    if state.get("onCoachingsList"):
        return "on the Coachings LIST, not inside a coaching's Edit view"
    if not state.get("coachingHeader"):
        return "not inside any coaching's Edit view"
    if state.get("menubarItems"):
        # everything checks out - seen 2026-09-25 on 3 click/popup timeouts
        return ("page looks HEALTHY (logged in, Edit view, full menubar, no "
                "modal) - a transient click/popup timeout in the Vaadin UI; "
                "retrying the step normally clears it")
    return "no known failure signature - see the screenshot"


async def snapshot(page, tag: str, reason: str = "") -> str:
    """Save <log stem>_<tag>.png + .json next to the run log and print the
    diagnosed cause. Never raises (it runs on the failure path)."""
    d = _state["log_dir"] or (LOG_ROOT / "misc")
    stem = f"{_state['stem'] or 'run'}_{tag}"
    try:
        d.mkdir(parents=True, exist_ok=True)
        state = await page.evaluate(STATE_JS)
    except Exception as e:  # noqa: BLE001
        state = {"error": repr(e)}
    cause = diagnose(state if "error" not in state else {})
    state.update(step=_state["step"], reason=reason, cause=cause,
                 at=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
    try:
        (d / f"{stem}.json").write_text(json.dumps(state, indent=2, ensure_ascii=False))
        await page.screenshot(path=str(d / f"{stem}.png"))
    except Exception as e:  # noqa: BLE001
        print(f"  ! snapshot incomplete: {e!r}")
    print(f"  !! [{tag}] during [{_state['step']}]: {cause}")
    print(f"     snapshot -> {d / stem}.png/.json")
    return cause
