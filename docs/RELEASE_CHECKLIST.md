# Release approval record - NOT APPROVED

This records approval of **one frozen release**, not another Todo or a development
log. The [sole Todo](../TODO.md) owns tasks; [features and evidence](IMPLEMENTATION_STATUS.md)
record implemented behavior. Local passes, publication or this document do not
authorize deployment, sealing or public financial transactions.

## Current candidate and evidence limits

| Boundary | Current status |
| --- | --- |
| Accounting and identity | Native ETH/fixed ZZZ, accounting V3 with 8-field local Position and `None=0`, `Active=1`, `Outbound=2`, `Dormant=3`, `Parked=4`. Routing2/pricing2/review1 remain distinct; canonical LP-only V4 rejects older layouts. Historical Anvil/journals keep their original profiles. [Profile](POSITION_V3.md). |
| Governance | Governance V2 is the selected wallet/Safe calling functions directly. No timelock, queued/predecessor executor or OpenZeppelin role grants. Two-step governance handover; separate guardian/keeper and immutable mint recipient. 16 module bindings fixed at seal. |
| Economic controls | Defaults 2% contribution/1% conversion/3% maintenance, each maximum 10%, gas separate. Caller-reviewed Entry maximum and stronger venue minima remain. Approved normal custody floors cannot be weakened later. Per-operation limits do not cap future market loss or repeated turnover. |
| Pool/input policy | User input is only native ETH or fixed ZZZ. All Registry LP pairs must contain that ZZZ; reviewed future WETH/ZZZ/fee-tier replacements remain possible. One contribution pool at a time. Stablecoins may be separate royalty currencies, not contribution inputs. |
| Current source checks | [Refactor review](../reports/auditability-refactor-20261025/REVIEW.md) and [scoped verification](../reports/auditability-refactor-20261025/VERIFICATION.md):31 contracts / 608 functions / 13 receive hooks;37 normal object gates and131-input typechecking pass.20 affected event-schema methods pass. EVM evidence belongs to its exact completed receipt; historical totals are not a fresh full regression. |
| Refactor compatibility | Shared private settlement and v3 checks, separate converters over a neutral abstract base, explicit private NFT/bucket identifiers and named phase constants. [Compiler comparison](../reports/auditability-refactor-20261025/compiler-comparison.md) preserves wire encodings and recursive storage; neutral struct provenance and identical duplicate error metadata are explicit exceptions. New runtime hashes are not approval to replace existing deployments. |
| Code-size qualification | Registry runtime 10,269 bytes. Vault 22,852 leaves 1,724. Access creation 42,081 plus fixed 96-byte arguments totals 42,177, leaving 6,975 below 49,152. The old 29-byte variable-role-array constraint is removed; exact release artifacts/configuration still require approval. |
| Actual dependencies | Selected-pool lifecycle, conversion routes, independent feeds, VRF, authority wallets, marketplace settlement, API/keeper hosting, strategy economics and maximal target-chain gas remain unqualified. |
| Website/wallets | Public simulation/null DEPLOYMENT; signing Anvil-only. Native read/unsigned source is implemented, but current-profile/provider/wallet acceptance and authorized public rollout remain open. Existing local deployments/journals are unchanged. |
| Operations/audit | Target-chain/Linux failure and recovery rehearsals, independent audit/remediation, frozen-source review and final configuration/sign-off remain required. |

The [earlier daily review](../reports/daily-security-20261025/REVIEW.md) records
fixed-ZZZ binding, funded-dust and indexer-provenance changes. Older native,
simplification and handoff reports retain their original code/evidence scope;
they do not verify the later ABI/governance/codec changes. See the [report index](../reports/README.md).
The user-reported [local two-wallet acceptance](../reports/local-wallet-concurrency/MANUAL_ACCEPTANCE.md)
is not production capacity. The 10/25/100-user campaign remains deferred, not passed.

## Release identity

| Approval field | Recorded value |
| --- | --- |
| Exact release commit | Not selected; development HEAD is not release approval |
| Network and chain ID | Not approved |
| Deployment/configuration manifest and content hash | Not approved; examples are not production choices |
| Compiler, dependency lock and bytecode/artifact manifest | No release-specific approved record |
| Actual module/helper/authority addresses and immutable bindings | Not selected and independently approved |
| Source-bound evidence bundle and hashes | No final release bundle accepted |
| Release mode | Same-chain pool moves and explicit source-chain custody exit/return; compatible same-chain whole-collection handoff. No integrated bridge or remote ledger. Exact configuration unapproved. |
| Decision date and accountable release owner | Not recorded |
| Accepted residual risks and rationale | Not approved |

## Required sign-off record

| Review responsibility | Named reviewer / independence | Exact evidence and decision |
| --- | --- | --- |
| Frozen source, economics, independent security audit/remediation | Not recorded | No approval |
| Deployment configuration, dependencies, authorities and sealing | Not recorded | No approval |
| Target-chain integration, operating recovery and monitoring | Not recorded | No approval |

Independent reviewers must assess the applicable launch acceptance criteria in
[the audit/release task](../TODO.md#task-audit-release) against the same commit,
network, manifests and evidence. Missing criteria need an explicit scope-based
reason, not silent removal. A passing validator, local mocks, internal static
review, an exported audit package or old CI does not supply independent sign-off.

The exact release inventory must bind governance2/accounting3/routing2/pricing2/
review1 and canonical V4 to actual runtime/helper/parent identities. Service
observations remain separate from reviewed provider policy. Governance multisig
signers/threshold, guardian/keeper gas and recovery, feeds/routes/updaters and VRF
funding must all be real selected choices, not example addresses.

OpenSea primary mint requires a compatible reviewed integration: buyer gross
0.05 ETH, recipient net after the actual platform fee, gas separate. Current direct
mint still forwards all 0.05 ETH. ERC-2981 only requests secondary-sale royalties;
actual marketplace receipt, refresh and ownership/cutover behavior require evidence.
Neither platform support nor a live randomness provider is implied by local mocks.

Changes to deployed code, dependency implementations, bindings, economics,
network or operating configuration require review of the affected approval and
an updated release identity. Sign-off is separate from explicit authorization
to submit public transactions.

## Initial launch and movement boundary

Principal belongs to its independently accounted NFT shares; holders cannot
redeem it. `moveFunds` atomically moves between admitted pools with the same
ordered actual assets. Another ETH/ZZZ fee tier is compatible after review;
ETH/WETH or other pair conversion is not an atomic move.

Normal paused custody exit converts attributed principal to fixed ZZZ under its
captured floor. Explicit raw exit sends actual pair assets under reviewed raw
minima, without a USD-loss promise or automatic fallback. The external EOA/contract
is trusted: source contracts cannot prevent diversion or compel return. Completion
requires actual funded LP; recovery requires full actual sent assets. Royalty
custody has a separate paused currency path retaining liabilities and suspension.

No integrated bridge/provider, remote destination ledger or cross-chain canonical
activation is required or retained. The custodian can independently bridge or
perform an issuer exchange, but this does not relocate NFT ownership or reward
ledgers. Issuer migration requires a fresh reviewed deployment of the new fixed
ZZZ; there is no post-seal identity replacement setter.

Qualify complete same-chain handoff of frozen owners, both ledgers and classified
backing, with full abort, late receipts, contract-holder compatibility and atomic
retirement/activation. Current V4 rejects older rows; no automatic storage/journal
upgrade exists. Future-chain transport, old-schema import and post-halt ownership
recovery are outside this release. See [custody procedure](GOVERNED_CUSTODY_HANDOFF.md),
[canonical scope](CANONICAL_HANDOFF.md) and [architecture evolution](ARCHITECTURE_EVOLUTION.md).

## Acceptance references

<a id="required-testing-layers"></a>
The three required layers are maintained in
[frozen-release local/Ubuntu verification](../TODO.md#task-audit-release),
[actual Robinhood mainnet fork](../TODO.md#task-mainnet-fork) and
[Robinhood Testnet rehearsal](../TODO.md#task-testnet-rehearsal).

<a id="market-valuation-and-operating-integration"></a>
Market, wallet and operating acceptance is maintained under
[selected pool](../TODO.md#task-pons-qualification),
[activation assets](../TODO.md#task-activation-assets),
[transaction journey](../TODO.md#task-transaction-ui) and
[keeper recovery](../TODO.md#task-keeper-recovery).

[Holder preflight](HOLDER_PREFLIGHT.md) supplies a pinned ownership/code inventory,
not escrow or replacement approval. Include frozen coverage, exact contract-holder
release/claim and marketplace cutover evidence. [LP settlement](LP_ETH_SETTLEMENT.md)
and [royalty settlement](ROYALTY_SETTLEMENT.md) need actual source/route/feed and
recipient behavior, current native backing, conversion/claim timing, keeper gas
and failure/recovery evidence. Earlier missing-native-payout findings and later
source-only repairs keep their historical boundaries; neither supplies release approval.
