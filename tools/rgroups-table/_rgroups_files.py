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

import re
import time
import unicodedata
from pathlib import Path

TS_FORMAT = "%y%m%d%H%M%S"


def now_ts() -> str:
    return time.strftime(TS_FORMAT)


def norm_text(text: str) -> str:
    """Comparison key for duplicate wordings: case-, diacritic-, punctuation-
    and emoji-insensitive (so 's-cedilla' vs 's-comma' or a trailing '!' don't
    hide a repeat). `$placeholders` are kept."""
    t = unicodedata.normalize("NFKD", text or "").casefold()
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    return " ".join(re.sub(r"[^\w$]+", " ", t).split())


def input_file(data_dir: Path, name: str, prefix: str) -> Path:
    """The input a step was told to read: a path, or a bare name inside
    data_dir. Exits unless it exists and is a `<prefix>_*.csv` (so a table
    can't be fed to expand by mistake). Every step takes its input
    explicitly (Raul, 2026-09-30): "the latest file" could be another
    coaching's, since several coachings share data/rgroups/."""
    import sys
    p = Path(name)
    if not p.is_file():
        p = data_dir / name
    if not p.is_file():
        sys.exit(f"not found: {name} (looked as given and in {data_dir})")
    if not (p.name.startswith(prefix + "_") and p.suffix == ".csv"):
        sys.exit(f"{p.name} is not a {prefix}_*.csv file")
    return p


def latest(data_dir: Path, prefix: str, suffix: str) -> Path | None:
    """Most recent data_dir/{prefix}_{ts}{suffix} file, by the embedded
    timestamp. None if the directory doesn't exist yet or no such file is
    there."""
    if not data_dir.is_dir():
        return None
    matches = sorted(data_dir.glob(f"{prefix}_*{suffix}"))
    return matches[-1] if matches else None
