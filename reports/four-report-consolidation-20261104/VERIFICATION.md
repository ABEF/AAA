# Four-report reconciliation: verification record

Baseline main `51079549c3e29c02082eaa863afebd3efc692513`.
[Reconciliation](RECONCILIATION.md), [review](REVIEW.md), [exact stages/pins](evidence.json),
[preservation](preservation.json), [36input files](inputs.json).

## Actual new execution

| Exclusive stage | Result / interpretation |
| --- | --- |
| startup-negative |7new methods against original Indexer;6failure/subcase records and1OverflowError subcase. Reproduces unwanted rejected-startup writes, partial schema, leaked handles and post-resource integer failure. Not a passing campaign or7distinct vulnerabilities. |
| startup-corrected |91affected methods pass after atomic setup/cleanup/bounds correction. |
| startup-final |91methods pass after pure identity serialization moves before resource opening. |
| journal-negative |Two later journal-mode methods against archived original source fail in3subcase records. Runtime import explicitly loads the preserved original module; working-tree pins do not pretend to identify that executing negative subject. |
| startup-durable-final |93distinct selected methods pass,0failures/errors/skips. Includes9new startup cases and affected indexer/reorg/log/history/chronology/provenance cases. Exact Python source pins unchanged during execution. |

The result is93distinct final selected methods, not275from repeated positive
stages. The explicit runner records canonical IDs, rejects duplicate/empty
selection, captures raw logs and pins source before/after. Execution uses bundled
Python3.12.14/SQLite3.53.1 on Windows with `-B -X utf8`, disposable real SQLite
files, synthetic RPC and authorizer fault injection. No network, credentials,
running database, contract transaction or service is used.

The [new methods](../../tests_python/test_indexer_startup_atomicity.py) check:
wrong identity preserves journal/schema/cursor/history; real denied DDL/initial
cursor insert rolls back; failed WAL closes the connection; integer overflow
rejects before files; supported boundaries remain accepted; valid restart
continues ownership ingestion; unsafe modes refuse before schema writes; and
silent WAL refusal cannot report successful startup, followed by a valid retry.

One existing history consumer imports helpers from a protected dirty test file.
[AST comparison](published-fixture-check.json) proves all existing helpers/methods
equal HEAD; only two unrelated added test methods differ and neither is selected
or called here. That file remains byte-identical and unstaged. Published static
import closure is separately checked against exact staged/committed blobs.

## Unchanged contract evidence reused

All52production Solidity sources,31closed dependencies and4normal build inputs
match the latest [manual safeguard gates](../manual-safeguard-audit-20261104/production-size-gates.json)
byte-for-byte. Its43normal runtime/initcode gates,471static contexts with scoped
review/reuse,85selected EVM successes across recorded stages and callable37/818/
37/13 scope remain their ORIGINAL evidence. None is a newly executed result of
this consolidation. No overlapping four-report counts are added into a full-suite
claim. Runtime margins remain Migration39/Vault635/Budget237/Balancer360.

No ABI/storage/profile, financial setting, user entitlement or LP behavior changed.
Earlier authority e26fc74 and pre-manual whole-source equality statements retain
their historical limitations. Reconciliation does not independently re-audit
every function or qualify external service/provider behavior.

## Preservation and maintenance

Every original36input file and all older tracked report content except the
maintained index/preserved dirty source-check record matches baseline bytes.
The full commitment manifest and original edited source/documents are archived
externally under `four-report-consolidation-20261104/`. Four unrelated tracked
dirty files retain their original raw hashes and stay excluded from publication.

Todo generation, callable consistency, local/incoming documentation links,
staged/HEAD Python publication closure and exact main publication identity are
recorded during final delivery. Current summaries are consolidated, but original
reports/failures are not rewritten or deleted. No operating database/schema
migration, host restart, site/Anvil/journal/signer/heartbeat change or deployment.

## Primary guidance and limits

[Python sqlite3 transaction guidance](https://docs.python.org/3.11/library/sqlite3.html#transaction-control)
explains implicit executescript commits and explicit transaction boundaries.
[SQLite journal_mode guidance](https://sqlite.org/pragma.html#pragma_journal_mode)
explains mode negotiation, unsafe OFF behavior and why journal mode changes must
occur outside a transaction. The fix uses explicit transactional statements and
checks actual modes rather than assuming a PRAGMA request succeeded.

Valid persistent databases retain table/index names, columns, keys and identity;
no rescan is needed. A failed WAL request after identity commit can leave a
coherent initial schema for same-identity retry. Actual power-loss safety,
filesystem/locking/disk exhaustion, Unix deployment, off-host recovery and
years of replay remain unqualified. The selected tests do not establish host
uptime, unlimited history capacity, target gas, independent audit or release approval.
