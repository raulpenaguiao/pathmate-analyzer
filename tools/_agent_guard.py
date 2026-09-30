"""Refuse to run manager-only operations inside an agent session.

Raul, 2026-09-30 (agents/RULES.md "Anthropic API key: manager only"): only
the manager session may call the Anthropic (or any paid LLM) API. On 09-29
agent-run `rgroup_expand.py` calls spent his budget without him noticing.

Signal: agents are launched only by agents/wake.sh or createagent.sh, and
both set AGENT_SLUG=<slug>; the manager session has it empty (its mail is
signed "from: raul", mail.sh's whoami fallback). A speed bump, not a lock:
the key stays readable in .env and an agent could unset the variable - the
rule in RULES.md is what actually binds.

    from _agent_guard import refuse_in_agent_session
    refuse_in_agent_session("rgroup_expand.py (Anthropic API calls)")
"""
from __future__ import annotations

import os
import sys


def agent_slug() -> str:
    return (os.environ.get("AGENT_SLUG") or "").strip()


def refuse_in_agent_session(what: str) -> None:
    """Exit with an explanation if this runs inside an agent session."""
    slug = agent_slug()
    if slug:
        sys.exit(
            f"REFUSED: {what} is manager-only, and this is agent session "
            f"{slug!r} (AGENT_SLUG is set). See agents/RULES.md 'Anthropic API "
            f"key: manager only': prepare the inputs, then hand the run to the "
            f"manager and say what it will cost in calls. (--dry-run makes no "
            f"API calls and is allowed.)")
