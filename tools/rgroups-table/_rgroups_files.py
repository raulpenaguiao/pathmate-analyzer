"""Shared timestamp + latest-file helpers for the r_ pipeline's standalone
steps. Each step's own CSV output embeds the YYMMDDHHMMSS it was run at
(`now_ts()`); each downstream step defaults to the most RECENTLY-RUN input
matching file (`latest()`), not a fixed name - so re-running an earlier
step never silently clobbers a prior run's file, and a step always chains
off of whatever actually ran last, not whatever happens to sort last by
mtime or be the only file with the old fixed name.

The YYMMDDHHMMSS format sorts correctly as a plain string (fixed-width,
most-significant field first) - `latest()` relies on that instead of
touching mtimes, so it reflects when a run's data was actually generated
even if the file itself was later copied/touched.
"""
from __future__ import annotations

import time
from pathlib import Path

TS_FORMAT = "%y%m%d%H%M%S"


def now_ts() -> str:
    return time.strftime(TS_FORMAT)


def latest(data_dir: Path, prefix: str, suffix: str) -> Path | None:
    """Most recent data_dir/{prefix}_{ts}{suffix} file, by the embedded
    timestamp. None if the directory doesn't exist yet or no such file is
    there."""
    if not data_dir.is_dir():
        return None
    matches = sorted(data_dir.glob(f"{prefix}_*{suffix}"))
    return matches[-1] if matches else None
