"""Shared safety guard for every PMCP write tool in this repo.

Confirmed 2026-09-11 (`autochanges/2026-09-11-alex-v02-phase0-recon.md` /
`docs/ALEX_v02_redesign_spec.md` §6 area): no existing write tool checks
which coaching the CDP-attached tab is actually on before writing.
`tools/rgroups-table/rgroup_apply.py` writes to whatever tab has a Micro
Dialogs menubar open, trusting the operator navigated to the sandbox first.
Call `assert_expected_coaching()` before any write action in a new tool, and
prefer retrofitting it into existing ones rather than carrying the gap
forward.

The coaching's name is a plain, always-present label in the Edit view's
header - confirmed live: `<div class="v-label ... title-label ...">Coaching
"ALEX v01 zum Ausprobieren"</div>` - present on every section tab
(Information, Rules, Micro Dialogs, ...), not just one.

Coaching locks (documented, official PMCP v6.0 docs, checked 2026-09-23):
- `/start-here`: "Only one coaching admin can work on the coaching
  intervention at a time. To work simultaneously, additional users need to
  log in with their author accounts."
- `/sections/account`: "When an admin user is logged into a coaching, it
  will be locked by that user. Choosing `Reset All Locks` will log out
  anyone currently engaged in the coaching session." The docs also say a
  lock can outlive a closed browser.
So an automation run can be kicked out mid-run by anyone else opening the
same coaching as an admin, or by a Reset All Locks. A crashed run can also
leave the coaching locked for everyone else. The docs say nothing either
way about a one-session-per-account limit.
(Loom's repeated alex-dev-2 drops on 2026-09-23 were NOT a lock: per Raul,
the session simply expired while the agent sat waiting on a late human
reply. A run that pauses for input should expect to re-login afterwards.)
"""
from __future__ import annotations

import os
import re

DEFAULT_EXPECTED = "ALEX v01 zum Ausprobieren"
ENV_VAR = "PMCP_EXPECTED_COACHING"

TITLE_JS = r"""
() => {
  // there can be more than one .title-label in the DOM at once (e.g. an
  // empty one from another section) - find the one actually holding a
  // 'Coaching "..."' caption, confirmed live 2026-09-11.
  const hit = [...document.querySelectorAll('.title-label')]
    .map(el => el.textContent.trim())
    .find(t => /^Coaching "/.test(t));
  return hit || null;
}
"""


class WrongCoachingError(RuntimeError):
    """Raised when the CDP-attached tab is not on the expected coaching."""


async def current_coaching_name(page) -> str | None:
    """The open coaching's name (from the Edit view's title label), or None
    if the page isn't currently inside any coaching's Edit view."""
    try:
        text = await page.evaluate(TITLE_JS)
    except Exception:  # noqa: BLE001
        return None
    if not text:
        return None
    m = re.search(r'Coaching "([^"]+)"', text)
    return m.group(1) if m else None


async def assert_expected_coaching(page, expected: str | None = None) -> str:
    """Raise WrongCoachingError unless the open coaching matches `expected`
    (default: $PMCP_EXPECTED_COACHING, else this repo's sandbox coaching).
    Call this once right before the first write action in any tool that
    mutates live coaching state - never assume the operator navigated
    correctly."""
    expected = expected or os.environ.get(ENV_VAR, DEFAULT_EXPECTED)
    name = await current_coaching_name(page)
    if name is None:
        raise WrongCoachingError(
            "could not read a coaching name from the current page - is it "
            "actually inside a coaching's Edit view? Refusing to write.")
    if name != expected:
        raise WrongCoachingError(
            f"CDP tab is on coaching {name!r}, expected {expected!r}. "
            f"Refusing to write. Navigate to the right coaching, or set "
            f"{ENV_VAR} to override if this is intentional."
        )
    return name
