# NFT economic-rights audit work

Internal review of the undeployed candidate, 2026-10-16. **Not an independent
audit or approval for real funds.**

- [Corrected prompt](REVISED_PROMPT.md): changes made to the supplied scope before execution.
- [Review and findings](REVIEW.md): identity, ownership, funding paths and remaining risks.
- [Implementation assessment](IMPLEMENTATION.md): existing behavior versus new work, by component.
- [Executed verification](VERIFICATION.md): commands, results, corrections, gas and evidence limits.
- [Functional coverage](COVERAGE.md): requirements mapped to tests; not a coverage percentage.
- [Machine-readable summary](verification-summary.json) and [file hashes](artifact-sha256.json).
- [Security audit plan](../../docs/SECURITY_AUDIT_PLAN.md) and [central Todo](../../TODO.md#security--audit).

Fresh final verification: 531 offline Solidity passes, zero failures, two expected
fork setup skips; 23 normal module/helper size gates; 29 production source
bindings. The extended NFT-rights invariant completed 65,536 calls with zero
reverts. The broader local Python candidate passed 628 tests, with five Unix-only
cases reserved for Ubuntu; that candidate includes separately unpublished work.

The previous internal static analysis and 33 actual fork cases were **not rerun**
for this audit. [Hash comparisons](unchanged-production-evidence.json) bind their
executed dependency closures to current source. Those earlier receipts retain
their original command, block, fixture and source scope. Failed/intermediate
test-harness attempts and build-cache permission failures are retained separately.

The reviewed four-bucket safety bound does not limit the collection to four NFTs:
all 1,000 NFTs can share one LP. Destination capacity reservations, canonical
home-chain recovery, live services and independent audit remain open. No public
transaction, deployment, website release or keeper/staging change is part of this
work. Git publication includes only the scoped contract/tests/evidence/checklists;
unrelated local frontend, quote, process-runner and artwork work remains separate.
