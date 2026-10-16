# Architecture review: scoped verification

Review began 2026-10-16 and continued 2026-10-17. Baseline:
`37bf0d220344736e3fcab35c64ff3386a3d57bfa`; work uses
`codex/architecture-evolution-review`. This is internal development evidence.
Production approval remains **NOT APPROVED**.

## Implemented change and scope

The only production Solidity change is in [Vault](../../src/ZZZVault.sol):
`_registerBucket` checks for an existing identity before enforcing the four-slot
cap, and `_reserve` permanently registers capacity before committing its mapping.
Pool validation and reassignment checks still precede admission. Slots are not
released. `bucketCount` includes unfunded reserved `None` identities.

No different-pair conversion, new bridge, canonical ledger migration, configurable
allocation or 3% migration floor was added. The [architecture design](../../docs/ARCHITECTURE_EVOLUTION.md)
describes those boundaries. Activation and top-up economics are unchanged.

## New execution evidence

| Check | Result | Scope |
| --- | --- | --- |
| Reservations, local switches, capacity and pooled security | **38 passed, zero failed/skipped** | [Receipt](capacity/targeted/attempt1/receipt.json): 13 ReservationCapacity, seven PoolSwitching, 14 PooledSecurity and four BucketCapacity cases. Exact source/test hashes unchanged during execution. |
| Keeper reserved-None discovery | **2 passed, zero failed/errors/skips** | [Receipt](keeper/verification.json): actual static-ABI decoding, bounded cursor/state/health behavior with mocked RPC/submission. Keeper source is unchanged. |
| Affected gas, future-chain returns and parking | **53 passed, zero failed/skipped** | [Receipt](capacity/affected/attempt1/receipt.json): four CombinedCapacityGas, 14 CustodyParking, 12 FutureChainMigration and 23 MultiHopMigration cases. |
| Approved-provider trust demonstration | **1 passed, zero failed/skipped** | [Receipt](provider/receipt.json): real source controller/timelock/router/adapter/registry with mock bound custody and remote identities; not a full live migration. |
| Normal production build | **23 object gates passed; 29 production sources bound** | [Build receipt](production/receipt.json): normal compiler configuration, runtime/initcode sizes and source/artifact identities. |
| Fresh static analysis and review coverage | **221 findings reviewed; zero unresolved detector entries** | [Static record](static-analysis/README.md): 130 false positives, 46 accepted risks and 45 informational. Nine fresh mutation checks rejected; 43 unchanged matcher tests reused by exact hashes. |

Local fixtures deliberately use mock venue, feed, authority, randomness or
transport dependencies as identified in each suite. They are not production
gas, provider backing, live service or target-chain approval. No tests were
skipped to hide a failure. Targeted counts must not be added to historical full
suite totals as if one complete run occurred.

The 91 capacity/affected cases bind **88 unique compiler dependencies**, including
26 production sources, through each executed suite's metadata. All 29 production
file hashes are separately unchanged across execution. The four combined-workload
cases passed their unchanged **12,000,000 gas assertions**. Default JSON output did
not retain decoded inner-call gas logs, so no new numerical peak is claimed and
those passing tests were not rerun merely to obtain one.

Vault runtime is **24,122 bytes**, leaving 454 bytes below the runtime limit;
Migration leaves 324 bytes. These narrow margins are not room for the proposed
canonical migration implementation without an explicit module/size design.
Initcode and constructor argument limits still apply at deployment. Static
coverage is an internal review, not independent audit or production approval.

## What was reused, and what was not rerun

Before implementation, [actual hash comparisons](phase1-evidence-reuse.json)
matched 29 production source files, 73 offline test-closure files, 76 prior fork
closure files and 32 static source/configuration files. The 44-file NFT report
and 28-file frontend report artifact manifests also matched. Keeper recovery and
Ubuntu process-rehearsal source bindings matched their recorded scopes.

After changing Vault, the old full Solidity, static and fork receipts remain
**historical**. This iteration runs affected reservation/custody/gas checks; it
does not claim a fresh complete 531-test run or fresh live fork qualification.
Unchanged prior real-venue dependency observations are useful context, not a
post-change end-to-end source attestation.

The broad local Python receipts were not entirely current (Todo generator and
later keeper/RPC changes), so their aggregate counts were not claimed or rerun.
The new two-case keeper regression is separately source-bound. Unchanged
frontend, metadata, royalty distribution, full-collection and infrastructure
suites were not repeated merely to increase a test count. A final frozen release
still needs its required complete source/configuration qualification.

## Review and residual risks

Separate internal reviewers challenged the brief/design before implementation
and reviewed the capacity diff afterward. No confirmed permission or accounting
regression was identified: registration is bounded, idempotent and atomic; pool
validation is a static call; reserved None consumers skip financial reads.
Governance can waste all four permanent slots, and source-side remote admission
proof remains absent. The provider test exposes an explicit custody trust
assumption, not a promise that pins prove honest delivery.

See [findings and failure modes](REVIEW.md). Current wallet, quote, runner and
artwork work already dirty before this review is preserved separately. The
website and server are unchanged. No production contract was deployed and no
public transaction was signed or broadcast.
