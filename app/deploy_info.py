"""Reads DEPLOY.md - a small generated file (by run.sh locally, or by the
release_frontend workflow before syncing to the server) recording which
commit produced the code currently running. Not tracked in git: its content
is only meaningful for the specific checkout/deploy that generated it.
"""
from __future__ import annotations

from pathlib import Path

_DEPLOY_MD_PATH = Path(__file__).resolve().parent.parent / "DEPLOY.md"

_FIELDS = {
    "- Commit:": "commit",
    "- Author:": "author",
    "- Message:": "message",
}


def read_deploy_info() -> dict | None:
    if not _DEPLOY_MD_PATH.exists():
        return None

    info = {}
    for line in _DEPLOY_MD_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        for prefix, key in _FIELDS.items():
            if line.startswith(prefix):
                info[key] = line[len(prefix):].strip()

    return info or None
