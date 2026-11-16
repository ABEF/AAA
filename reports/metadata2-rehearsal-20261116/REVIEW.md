# Isolated metadata2 constructor, binding and cold-read rehearsal

Reviewed 16 November 2026 against contract main `6626d6846edccf4660ad483919e34272d1d4271c`.
**Controlled local evidence; production NOT APPROVED.** No public deployment,
sealing, real mint, LP operation, website/service rollout or old-node call occurs.

## Result and exact scope

One fresh PID-owned loopback Anvil completed **five top-level creations, three
Access bindings and twelve actual instances**, followed by **19 valid metadata
read snapshots and one exact nonexistent-token rejection**. All expected JSON,
artwork, lifecycle, valuation-availability and settlement checks passed. Estimate
and full 20% padded reads returned the exact 32M reference bytes for all 19 valid
snapshots. The node is stopped, with no pending submission.

The five changed normal objects are AccessController, NFTMetadata, Migration,
NFT and NFTCanonical. Required construction also creates RoyaltyFactory, its
two inert code-data children, ActivationAssetsFactory, CustodyValidation,
RoyaltyRewards and ClaimRouter. These seven children are necessary for those
constructors, not a rerun of the former 25-top-level/44-receipt campaign.

The accepted `metadata2-20261116` compiler family is reused byte-for-byte:
100 source inputs/61 production files/48 normal size gates, Solidity 0.8.26/Cancun,
via-IR/runs1/Yulfalse. No compiler, static analyzer, unchanged Solidity, Python or
browser suite was rerun. The ordinary graph remains schema17/mint2/V10; this
campaign does not rename old runtimes or codec profiles.

## Actual constructors, child code and bindings

| Contract | Full initcode bytes | Actual runtime bytes | Receipt gas | Full 25% padded gas |
| --- | ---: | ---: | ---: | ---: |
| AccessController | 48,113 | 10,590 | 10,224,549 | 12,780,687 |
| NFTMetadata | 24,512 | 24,121 | 5,255,955 | 6,569,944 |
| Migration | 43,768 | 24,005 | 9,248,711 | 11,560,889 |
| NFT | 31,116 | 24,234 | 11,367,023 | 14,208,779 |
| NFTCanonical | 24,275 | 23,130 | 5,055,968 | 6,319,960 |

The three binding receipts consume 174,795 gas combined. Total actual gas for all
eight receipts is **41,327,001**; worst padded creation is **14,208,779/32,000,000**.
These are local execution observations, not Robinhood deployment-fee estimates.
No block/transaction/fee default or production gas profile is raised or adopted.
All twelve instances satisfy normal 24,576 runtime and 49,152 full-initcode limits;
there is no code-size or block-gas exemption.

Every exact ABI-encoded initcode/argument/creator is reconciled with accepted
normal objects and included CREATE traces. Constructor simulation return,
included trace output and actual `eth_getCode` agree. Runtime templates alone
are not treated as deployed immutable pins. All eight frozen submissions match
their nonce, calldata, zero value, destination and full 25% gas review; exact
serialized requests/responses are retained without the old recording alias.

**63 expected getter/state observations** verify module/helper reciprocity,
fixed renderer and controller, royalty factory/data slices, NFT/ClaimRouter,
Migration/CustodyValidation and NFTCanonical/NFT links. Only Migration, NFT and
NFTCanonical are module-bound here. Other modules/policy remain absent, Access
is unsealed/bootstrap-owned, canonical state 0, mintedCount 0 and royalty weight 0.
This partial graph is deliberately not sealable or operationally configured.

## Cold tokenURI measurements

| Controlled read snapshot | Estimate/exact matching call gas | Full 20% padded call gas |
| --- | ---: | ---: |
| `dormant_unrevealed` | 826,831 | 992,198 |
| `dormant_revealed` | 507,394 | 608,873 |
| `activated` | 612,020 | 734,424 |
| `enhanced_boundary` | 611,528 | 733,834 |
| `singularity_boundary` | 615,043 | 738,052 |
| `unavailable_price_guard` | 574,153 | 688,984 |
| `parked` | 553,560 | 664,272 |
| `exit_started_bucket_open` | 636,591 | 763,910 |
| `exit_closed_unallocated` | 563,585 | 676,302 |
| `exit_allocated_not_ready` | 567,440 | 680,928 |
| `exit_payable` | 567,228 | 680,674 |
| `exit_paid` | 566,128 | 679,354 |
| `exit_exact_zero` | 565,831 | 678,998 |
| `terminal_dormant` | 526,952 | 632,343 |
| `replacement_preparing` | 610,753 | 732,904 |
| `canonical_frozen` | 544,527 | 653,433 |
| `canonical_importing` | 545,524 | 654,629 |
| `canonical_retired` | 632,550 | 759,060 |
| `canonical_cancelled` | 547,416 | 656,900 |

Each independent read uses the actual normal NFT entrypoint, renderer,
NFTCanonical, Access, Migration and royalty code; none of the twelve real
instances is replaced. Token ID is uint256 maximum (78 decimal digits), and the test
artwork URI is 41 UTF-8 bytes. Twenty cases use 51 reviewed storage slots through
temporary per-call `stateDiff`; ten distinct genesis-only read doubles supply
other dependencies. Synthetic USD/portfolio getters are cheap controlled
counterparts, **not the full production Oracle/dual-feed/venue call cost**.
The fixture is a partial metadata read snapshot, not proof of a reachable sealed
mint, LP placement, handoff, payout or royalty-ledger transition.

No access list prewarms the reads; every call is a separate EVM execution. A
bounded 50,000 gas opcode trace reaches the renderer and records first SLOAD cost
**2,100**, confirming cold storage access. It intentionally exhausts gas and is
not the semantic successful-read trace. Separate 32M reference calls establish
the expected complete JSON. Separate-call cold-access semantics follow
[EIP-2929](https://eips.ethereum.org/EIPS/eip-2929); access-list prewarming is
defined by [EIP-2930](https://eips.ethereum.org/EIPS/eip-2930).

A bounded search records adjacent matching/nonmatching gas values. In these
nineteen fixtures, estimate and padded calls match the reference, and each
recorded adjacent lower call fails. This is an observed local boundary, not a
proof of global gas monotonicity or a universal production minimum. Low gas can
also be caught as unavailable valuation in other configurations: always check
the requested semantic result, not just successful RPC/EVM completion. Expected
price-unavailable/Parked snapshots remain labelled fallback; LP exited remains
distinct from Dormant and retains royalty activation. No fallback is counted as
a healthy priced read.

The actual pinned Anvil 1.4.4 accepts per-call state/trace overrides in this run;
the feature is an RPC extension and must be separately qualified on a hosting
provider. See [pinned Anvil API](https://github.com/foundry-rs/foundry/blob/v1.4.4/crates/anvil/src/eth/api.rs)
and [Geth trace-call documentation](https://geth.ethereum.org/docs/interacting-with-geth/rpc/ns-debug).
Metadata reads submit no transactions and spend no chain funds; providers can
still apply computation, timeout, response-size or billing limits.

## Isolation, improvements and preservation

Pre-start independent review corrected four **external test-runner** gaps:
unbounded counterpart replacement, insufficient cold proof, incomplete state
snapshots and an inherited full-graph policy assumption. Frozen typed fixtures,
closed read/slot manifests, opcode tracing and a selective exact transaction
path correct them. Pure recording-fake/encoding preflights are explicitly not
EVM/gas evidence. No production contract defect or financial-policy change was
needed for this rehearsal; final verification flags propagate without hiding
failed/partial results.

Actual before/after records match the latest head/hash/stateRoot/time, all 23
accounts' code/nonces/balances, all 51 overridden slots and unminted-owner revert.
All63 getter expectations are rechecked after reads. Recorded RPCs admit only
one disposable impersonation and the eight intended zero-value local sends;
there is no mint/seal/reset/fork/import/payout or public endpoint. The process,
loopback socket and genesis are authenticated before every mutation, with
scrubbed environment and owned-process-only shutdown.

Historical Anvil ports 8902/57306 are never queried, adopted or killed. Existing
state is preserved through non-contact/isolation; no old state-root equality is
claimed. Source/protected-work preservation is verified separately. Local
addresses, fixture code and actual runtime pins never enter production
inventories, website configurations or existing journals. Both sites, the shared
Anvil-only signer and user-paused heartbeat remain unchanged.

## Remaining qualification

This closes the current five-object **controlled local** constructor/binding
and metadata-read measurement gap. It does not qualify final release URI length,
real feeds/depth/routes, full source-call cost, maximum workloads, actual chain
fees, RPC/media/cache limits, OpenSea collection support, hosted watcher restart/
recovery, authority keys, actual SeaDrop/VRF or independent audit. Those remain
owned by [deployment](../../TODO.md#task-deployment-initcode) and
[metadata operations](../../TODO.md#task-metadata-ops). No unchanged suite or
full deployment rerun is needed merely to publish these observations.

## Evidence

See [verification manifest](VERIFICATION.json), [gas summary](GAS.json),
[independent review](INDEPENDENT_REVIEW.json) and [frozen evidence bundle](evidence.zip).
Independent read-only review reconciles all 1,663 recorded RPC responses and
derives all twelve CREATE addresses independently from creator nonces. Native
host inventory confirms the owned PID is absent and its fresh port has no
listener. A first observer-only locale decoding failure is preserved separately;
the corrected byte-decoded host observation performs no RPC and does not repeat
EVM measurements. Original rehearsal data are unaffected.

The bundle includes original request/response records, actual receipts/CREATE
traces/code, fixture/slot manifests, both state snapshots, successful and
low-gas responses, cold proof, owned shutdown and reviewed one-campaign scripts.
It is archival evidence, not a supported public deployer or operational config.
The earlier [full local construction report](../local-deployment-rehearsal-20261115/REVIEW.md)
and [metadata source verification](../metadata-lifecycle-fixes-20261116/REVIEW.md)
retain their exact original scopes.
