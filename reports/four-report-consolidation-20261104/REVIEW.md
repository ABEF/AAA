# Four-audit consolidation and targeted improvements

November4,2026; baseline main5107954. **Production NOT APPROVED.**
The [finding-by-finding reconciliation](RECONCILIATION.md), [input commitments](inputs.json)
and [verification](VERIFICATION.md) retain the four original scopes and failures.

## What was consolidated

The last four substantive publications are manual recovery, keeper confirmation,
market/lifecycle accounting and the whole-project/indexer supplement. Their
36files remain unchanged. Source findings, repaired test models, intentional
limitations and external qualification are distinguished; a report's word
“current” refers to its own revision. No overlapping test totals are added.

The prior implemented corrections remain present: anchor snapshot/streaming
ownership, receipt-derived reward/NAV models, deadline-aware keeper wake-up,
clear-only router independence, independently selectable emergency sample/clock,
explicit both-zero raw close floors and the corrected typed-child callback test.
Old unchanged-whole-source claims precede the two manual-view corrections and
must not be used as current whole-source evidence. The latest manual report has
matching current Solidity/dependency/build pins.

## New code improvements

The follow-up found a connected startup/recovery gap in
[Indexer](../../indexer/monitor.py):

- A rejected deployment identity could still change journal mode and recreate
  indexes before rejection. Failed multi-statement schema setup could persist a
  partial schema. Setup/identity/cursor insertion now share one explicit writer
  transaction, rolling back together on failure.
- Failures after connecting could retain a database connection. Every post-open
  error now closes it, and valid retry keeps existing ownership/cursor/history.
- Unsupported SQLite identity/LIMIT integers could fail after filesystem work.
  They now reject before directories or connections are created.
- A WAL request returning another mode could previously be treated as successful.
  Startup now requires a durable rollback-capable initial mode and an actual wal
  result. OFF/MEMORY/unknown modes are refused; policy is not weakened to recover.

These are low-severity service/configuration integrity and resource-recovery
defects/hardening, not demonstrated remote theft. No contract, fee split, NFT
right, LP-management rule, authority, API codec or signing behavior changed.
Database table/index names, columns, keys and stored identity are unchanged.

WAL cannot be changed within a transaction. It is negotiated AFTER the validated
schema/identity commits; a refused WAL setup may leave coherently initialized
empty tables and the same initial cursor, but ingestion never starts. Recovery
retries that same identity after storage is fixed; it never deletes state.

## Documentation improvements

Current README/context/handoff/findings/feature/release/roadmap summaries now use
one consolidation entry instead of repeating four chronological summaries. The
sole Todo preserves IDs/statuses/order while correcting stale custody4/schema9/
pre-Entry conversion acceptance wording for the fresh profile. Historical
royalty converters/wrappers/codecs retain their valid separate scope.

The [single operator procedure](../../docs/OPERATOR_MANUAL.md#indexer-startup-failure-and-durable-storage)
explains exact storage bounds, failure states, WAL admission, safe retry,
backup/restart and why changing identity requires a separate reviewed rescan.
Installing source authorizes no restart or live database change.

## Evidence and remaining priorities

93focused Python methods pass, including9new startup regressions. Negative
controls against original code reproduce the rejection/partial-schema/resource/
integer/WAL gaps. Original failures and corrected stages are retained. Exact
unchanged43normal gates/static/callable source evidence is reused; no unchanged
Solidity suite, compiler or analyzer was rerun.

Remaining meaningful improvements need actual evidence or their own reviewed
implementation scope: complete long-lived history and bounded replay economics;
Unix/WAL/backup/off-host recovery; target-chain keeper inclusion/gas and maximum
populated operations; qualified feeds/routes/VRF/authorities/OpenSea; matching
source8 services/site; and independent frozen-release audit/remediation. Tight
Migration39-byte headroom and governance/emergency trust remain explicit.
No deployment, service, website, Anvil, NFT/LP/balance, journal, signer, heartbeat
or public transaction was changed.
