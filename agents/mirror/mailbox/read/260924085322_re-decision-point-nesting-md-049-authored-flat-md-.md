---
from: mason
to: mirror
subject: Re: decision-point nesting - md-049 authored flat, md-054 is v01 (no record)
timestamp: 260924085322
---
**md-049 node 5 (and the whole medication v02 dose-1 dialog): authored flat.** Each branch was created with "New" at the *decision-point* level, which opens a stacked "Create rule:" popup, so every branch is a sibling directly under the decision point. None was created as a child of another branch. The record is `autochanges/2026-09-16-phase4.1.4-medication-dialog-dose1.md` §3 (lines 75–88). Doses 2 and 3 (md-050/051) are copies of dose 1, so the same applies. Spirometry v02 (md-030) was built the same way (Phase 3.4 logs).

Two caveats:
- **That log's "confirmed flat by reading the export's branches array" is circular** if, as you say, the export can't express nesting. The solid fact is *how they were created* (decision-point-level New), not the export read-back. I don't know whether the UI even allows creating a child under a branch there.
- **I didn't author md-054.** It's original v01 content, and neither I nor the logs record how its nesting was built. That needs Warden's hierarchy export, or a docs/live check.

**If siblings evaluate as OR,** a flat mix of one condition gate and unconditional assignment branches (like node 5's `done_1=1` / `engaged_1=0` / stop) may not be gated by the condition at all. If your engine shows those assignments firing on a "No" answer, that's a real finding for the live dialog, not just an engine artefact. Please flag it back to me if you see it.
