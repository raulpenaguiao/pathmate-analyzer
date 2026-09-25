# Warden — status

_Updated 2026-09-24._

## Browser queue
1. **Mason**: fix md-030 (v02 spirometry) rows 3-4 one-line Yes/No options (Smith found it).
   MUST come before Loom, whose add-flow duplicates those rows.
2. **Loom**: add 4 Stage3 variants (also waits on Raul's OK).
3. **Warden**: sweep stale-table fix, then re-export to verify all of the above.

## Done 2026-09-25 (uncommitted)
- Fresh full ALEX export: `data/exports/coaching_alex-v01-zum-ausprobieren_20260925-093313.json`
  (0 dialog errors). 3 dialogs read a stale table (Quit spirometry, Infocard 3,
  Offer assistance); enrich left them text-unresolved.
- Root-caused Raul's failed export: `enter_edit_view` gave up after a fixed 2s
  (now polls 20s). Not session expiry.
- The login check was fooled by the "Session expired!" banner: fixed in start_pmcp.sh,
  the exporter, and `_pmcp_safety.session_expired()`.
- New `_run_diag.py`: timestamped run log (data/logs/<tool>/, gitignored),
  stall heartbeat, failure screenshot + diagnosis. Wired into the exporter.
- The coherence check now FAILS on missing rows and on per-dialog node counts
  that don't match the Report, naming the dialogs.
- `path` / `dialogPath` fields (uids are not stable names).

## Done 2026-09-24 (committed 0686367)
- Decision-point jump-to-message targets and rule nesting (`depth` /
  `parentIndex`) are now in the export. Both were already in the Report HTML,
  just unparsed. They pair with Mirror's `DecisionBranch` fields (2749c6f).
  Complete enriched export:
  `data/exports/coaching_alex-v01-zum-ausprobieren_20260917-174650_jumps.json`.
  35 jump targets resolve and 14 are ambiguous from text alone (a live pass
  could settle them later).
- The 0918 ALEX export was a partial sweep (md-060..089 failed). The exporter
  now flags "PARTIAL EXPORT", adds a `_PARTIAL` filename suffix, and re-widens
  and retries on `MenuOverflowError`. The overflow cause is unverified live.
- `_pmcp_safety.py` documents PMCP coaching locks.

## Rule (Raul, 2026-09-24)
md-/node uids are per-export positions, never static names. Across exports use
`path` / `dialogPath` (exporter + enrich now emit them; uncommitted). All agents mailed.

## Resolved
- Loom's alex-dev-2 session drops (2026-09-23) were a plain session expiry
  while waiting on a late human reply (Raul), not a lock.
- Loom's blank-field guard in `rgroup_apply.py` is verified in place.

## Open, not mine to act on
- The portal's attached ALEX bundle ("ALEXv1_14th") is a stale 09-14 export.
  Swapping it is Raul's/Smith's call (explained to Raul 2026-09-24).

## Full detail
See `agents/warden/context/inflight.md`.
