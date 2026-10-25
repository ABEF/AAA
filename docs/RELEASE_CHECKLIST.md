# Release approval record - NOT APPROVED


[Residual cleanup](../reports/obsolete-code-20261025/REVIEW.md) removes unused
Registry wrapper records and creator-payment tooling. This source candidate's
Registry storage is fresh-deployment only; no existing deployment is upgraded.
The current caller reference is31contracts/644functions. Exact Access constructor
arguments and all independent release gates remain open; no deployment is authorized.

## Simplified current release - 2026-10-25

[Current candidate boundary](SIMPLIFIED_RELEASE.md): fixed pre-seal ZZZ identity
plus native ETH only for contributions; LP-only fee intake; no creator inbox or
integrated cross-chain/proof path. Keep separate royalty currencies, source-chain
custody exit/full return and whole-collection same-chain handoff. Explicit current
fee/custody/helper/schema pins must match; old local profiles are not upgraded.
Scoped evidence belongs to the [simplification review](../reports/simplification-20261025/REVIEW.md).
Final normal size/constructor gates, exact source bindings and deployment rehearsal
remain mandatory; no previous pass or document generation supplies release approval.


## New capabilities do not close service approval - 2026-10-25

[Service readiness work](../reports/release-services-20261025/VERIFICATION.md)
adds an optional immutable Pyth reader, stricter current mint/VRF qualification
and frozen-source review packaging. No actual provider, updater, wallet authority,
OpenSea primary mint, current native operating service or independent audit is
approved. Current schema5/mint profile1 correctly blocks incompatible OpenSea
minting; historical mode is inspection only. Buyer gross0.05ETH/net recipient
after actual platform fee is the required future OpenSea behavior, gas separate.
The current direct mint has not changed. Final package export is not sign-off.

Reviewed 2026-10-25. This file records approval of **one frozen release**, not a
second Todo or a chronological development log. The [sole Todo](../TODO.md)
owns tasks; the [feature/evidence reference](IMPLEMENTATION_STATUS.md) owns
implemented behavior and historical source-scoped checks. No production contract
deployment, sealing or real-fund action is authorized by this record.

## Current candidate and evidence limits

| Boundary | Current status |
| --- | --- |
| Native contracts | Actual ETH accounting V2, typed v3/v4 routes, dual-source pricing V2 and reviewed Entry policy V1 are locally implemented. Require exact module/helper/runtime/ABI/configuration inventory; old WETH/local profiles are not interchangeable. |
| Economic controls | Defaults 2% contribution / 1% conversion / 3% maintenance, gas separate; immediate governance maxima 10%. Reviewed Entry rejects policy above the caller maximum before pulls. Per-operation floors do not bound future price loss or repeated turnover. |
| Readiness improvements | [Native integration, strict RPC capability checks and Vault headroom](../reports/native-readiness-20261025/VERIFICATION.md): locally verified scopes; actual service/extension qualification remains open. |
| Latest local review | [Comprehensive improvements](../reports/comprehensive-improvement-20261025/REVIEW.md) and [verification](../reports/comprehensive-improvement-20261025/VERIFICATION.md) record reviewed-cap, indexed-history, metadata, buyback and transport boundaries. Normal size/gas gates and explicit source scope remain mandatory. |
| Market and services | Selected hookless ETH/ZZZ pool, real input/conversion routes, independent feeds/VRF, authority wallets, marketplace settlement, API/keeper hosting, strategy economics and complete target-chain gas remain unqualified. |
| Website and wallets | Public simulation/null DEPLOYMENT; shared signer Anvil-only. Native-V2 read/unsigned review is implemented locally; actual native chain/extension acceptance, public signing approval and service rollout remain open. Preserve historical journals and local deployments. |
| Operations and audit | Linux/target-chain recovery rehearsals, frozen-release verification and independent audit/remediation/sign-off remain required. Existing local evidence does not approve services or funds. |

The user-reported [local two-wallet acceptance](../reports/local-wallet-concurrency/MANUAL_ACCEPTANCE.md)
does not prove production capacity. The dedicated 10/25/100-user campaign remains
explicitly deferred, not passed. Historical [reports](../reports/README.md) retain
their own commit/source scope. No fresh full regression, uninterrupted uptime or
independent security approval is inferred from internal checks.

## Release identity

| Approval field | Recorded value |
|---|---|
| Exact release commit | Not selected; current development HEAD is not release approval |
| Network and chain ID | Not approved |
| Deployment/configuration manifest and content hash | Not approved; example addresses/settings are not production choices |
| Compiler, dependency lock and bytecode/artifact manifest | No release-specific approved record |
| Module/helper addresses, authority addresses and immutable bindings | Not selected and independently approved |
| Evidence bundle and hashes | No final release bundle accepted; development evidence is linked from the implementation reference |
| Release mode | Current scope: same-chain pool moves and separately approved source-chain custody exit/return; integrated bridges and direct remote canonical activation disabled. Exact configuration unapproved. |
| Decision date and accountable release owner | Not recorded |
| Accepted residual risks, limits and rationale | Not approved |

## Required sign-off record

| Review responsibility | Named reviewer / independence | Exact evidence and decision |
|---|---|---|
| Frozen source, economics, security audit and remediation | Not recorded | No approval |
| Deployment configuration, dependencies, authorities and sealing | Not recorded | No approval |
| Target-chain integration, operating recovery and monitoring | Not recorded | No approval |

Approval requires independent reviewers to confirm the applicable initial-launch
acceptance criteria in the [audit/release task](../TODO.md#task-audit-release)
against the exact commit, network, manifests and evidence above. The three test
layers, service qualification and unresolved risks must be assessed within that
same release scope. Local tests, internal Slither triage, old CI, or a successful
configuration validator do not supply this sign-off. Any non-applicable criterion
needs a recorded reason tied to the chosen release mode; it cannot silently
remove an acceptance requirement from the Todo.

Changes to deployed code, dependency implementations, bindings, economics,
network or operating configuration require review of the affected approval and
an updated release identity. A recorded approval is separate from explicit
authorization to submit public transactions.

## Initial launch and later movement

Current scope is same-chain pool moves and separately approved **source-chain**
custody exit/return. Normal all-ZZZ exit uses its captured retained-value floor;
explicit raw exit transfers the admitted assets under exact raw minima without
a USD-loss promise. There is no automatic fallback. The external recipient may
be an EOA/contract and is trusted; source contracts cannot force its return.

No integrated bridge/provider, remote destination ledger or cross-chain canonical
activation is required for this release. Their deferred [future tasks](../TODO.md#future-migration)
are not closed by disabling a legacy configuration. External custody can support
an operator's bridge or issuer migration, but does not move NFT ownership or
rewards to another chain and does not establish remote NAV or fees.

Retain and qualify same-chain whole-collection handoff, including frozen owners,
both ledgers, actual backing, abort/late receipts and compatible contract holders.
Atomic ETH/WETH/different-pair conversion and post-halt ownership recovery remain
unsupported. If future cross-chain canonical activation is built, the selected
policy requires verified finality with no multisig-only override. These future
capabilities cannot be retrofitted into immutable code merely by configuration.
See [custody procedure](GOVERNED_CUSTODY_HANDOFF.md),
[canonical scope](CANONICAL_HANDOFF.md) and [architecture evolution](ARCHITECTURE_EVOLUTION.md).

## Moved requirement links

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

The [holder preflight](HOLDER_PREFLIGHT.md) supplies a pinned ownership/code inventory,
not escrow or replacement approval. Include complete frozen coverage plus exact
contract-holder release/claim and marketplace cutover evidence in release review.

The 2026-10-19 payout audit identified missing native-ETH LP settlement in its
source-only revision. The dedicated LP candidate below addresses implementation;
live qualification and independent review remain required. See [historical audit](../reports/topup-and-reward-review/ETH_PAYOUT_AUDIT.md)
and [owning task](../TODO.md#task-lp-eth-settlement). Approval remains NOT APPROVED.

## LP settlement candidate scope

The [LP ETH candidate](LP_ETH_SETTLEMENT.md) adds native reward credits, a fixed helper and a native asset slot in the Rewards handoff domain. Require current source-bound sizes/tests, source/successor schema compatibility, exact converter/wrapper bindings, qualified swap/feed/unwrap and keeper gas/latency/recovery evidence, complete ingestion and independent review. Older source-only receipts do not qualify these changes. The release decision remains **NOT APPROVED**.
