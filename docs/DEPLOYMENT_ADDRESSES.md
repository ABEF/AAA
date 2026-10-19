# Deployment address inventory

The royalty conversion candidate also requires a separately deployed
[`ZZZRoyaltyConverter`](../src/ZZZRoyaltyConverter.sol), constructed with the exact
controller, RoyaltyRewards ledger and WETH wrapper. Governance binds it to the
ledger once **before sealing**. Record its runtime hash and bidirectional bindings,
wrapper proxy/admin/implementation policy and each reviewed conversion route/feed.
It is an optional fixed helper, not a replacement sealed controller module. Core
seal validation alone does not prove this optional feature is configured. Each
successor needs its own reviewed binding. Production helper-inventory qualification
remains open; see [setup and stopping procedures](ROYALTY_SETTLEMENT.md).

This is a configuration reference, not a task-status list or approved deployment.
The protocol remains an undeployed candidate. Production public wallets and
PoPL contract addresses are not selected. The [release record](RELEASE_CHECKLIST.md)
remains NOT APPROVED; progress belongs in the [central Todo](../TODO.md).

The [production manifest](../config/production.example.json) records addresses,
chain IDs, observed blocks, code hashes, immutable bindings and review evidence.
An address alone does not establish the right chain, code or authority.

## Wallets and authorities to choose

| Identity | Configuration and responsibility |
| --- | --- |
| Governance multisig | Select its public address, signer public addresses and threshold. It initially receives proposer and canceller roles; NFT ownership is not a governance vote. |
| Guardian | Select the emergency pause account. It cannot unpause or withdraw principal. |
| Keeper | Select a dedicated signer, fund its native gas balance and restrict it to keeper operations. Separate it from governance in production; role separation is an operating recommendation, not a general on-chain prohibition on reusing an address. |
| Mint proceeds recipient | Select the immutable recipient of exactly 0.05 ETH per successful dormant mint. A treasury may fill this role; it has no custody authority merely by receiving mint payments. |
| Deployment/bootstrap signer | Select the temporary deployment account. It performs write-once bindings and configuration before seal; sealing permanently clears bootstrap. |
| VRF subscription owner/funder | Identify the selected service's subscription ownership, authorized consumers and funding arrangements. These depend on the qualified coordinator, not a PoPL administrator setter. |
| External creator payer | Record the agreed payer or payment-authorizing identity and terms. The creator sends actual funds to the immutable protocol inbox; a calculator cannot authorize payments. |

The **governance controller is a deployed contract**, `ZZZAccessController`, rather than another
wallet to create. The local template sets `GOVERNANCE_MULTISIG` as proposer and
`address(0)` as executor, meaning anyone can execute only the exact already
approved operation, immediately. A dedicated executor wallet is unnecessary for that
configuration. Initial proposers also receive the canceller role. Additional
role memberships must appear in the reviewed manifest and complete role history.
Multisig members, guardian and keeper may have external wallet administration
and recovery arrangements that require separate review.

No dedicated **burn wallet** is required: [Buyback](../src/ZZZBuyback.sol) invokes
`ZZZ.burn` and checks the token supply reduction. Compounding and buyback reserves
are protocol accounting balances, not payments to an administrator treasury.
The LP allocation remains 80/10/5/5 with no automatic governance/keeper salary.

## PoPL contracts produced by deployment

The fixed core consists of 21 contracts (controller plus 20 sealed modules). These are recorded per participating
chain; `Ids.TRANSPORT` names the fixed router, not a selected bridge provider.

| Manifest name | Contract |
| --- | --- |
| `access` | `ZZZAccessController` — zero-delay governance and sealed module bindings |
| `vault` | `ZZZVault` — permanent principal custody and NFT share ledger |
| `nft` | `ZZZNFT` — canonical ownership, fixed trait draw and royalty request |
| `liquidity` | `ZZZLiquidityManager` — fixed venue settlement |
| `rewards` | `ZZZRewards` — funded LP-owner and equal-collective claims |
| `membership` | `ZZZMembership` — activated-NFT collective membership |
| `fees` | `ZZZFeeController` — fee allocation and separate reserves |
| `strategy` | `ZZZStrategy` — fixed range/execution calculations |
| `compounder` | `ZZZCompounder` — bounded keeper compounding coordination |
| `buyback` | `ZZZBuyback` — reviewed purchase and supply-reducing burn |
| `migration` | `ZZZMigration` — governed custody plans, parking and resume |
| `bridge` | `ZZZBridgeAdapter` — fixed economic message boundary |
| `receiver` | `ZZZMigrationReceiver` — authenticated arrival, finalization and ACKs |
| `oracle` | `ZZZOracle` — configured price and uptime policy |
| `pools` | `ZZZPoolRegistry` — eligible pools, wrapper and input helpers |
| `routes` | `ZZZMigrationRegistry` — immutable economic route identities |
| `transport` | `ZZZBridgeRouter` — immutable provider-policy routing |
| `canonical` | `ZZZCanonicalHandoff` - fixed canonical lifecycle and exact handoff coordinator |
| `nft_canonical` | `ZZZNFTCanonical` - NFT inventory/ownership codec bound to the NFT |
| `vault_canonical` | `ZZZVaultCanonical` - shares, origin lineage and parked custody codec bound to Vault |
| `fees_canonical` | `ZZZFeesCanonical` - reserves/inboxes codec bound to Fees |

Eight fixed helpers/factories are created automatically and must also be inventoried:

| Creator | Helper addresses and bindings |
| --- | --- |
| Pool registry constructor | `ZZZActivationAssets` and `ZZZActivationEntry`; verify registry/controller/helper relationships. |
| Controller constructor | `ZZZRoyaltyFactory`; only its atomic creation/binding path supplies the NFT's royalty ledger. Verify factory controller and observed NFT ledger. |
| NFT constructor | `ZZZRoyaltyRewards` through the controller's fixed factory, plus `ZZZClaimRouter` and `ZZZNFTMetadata`; verify NFT/controller/royalty bindings. |
| Vault constructor | `ZZZMigrationBudget`; verify `Vault.migrationBudget`, helper `vault`/`access` bindings and deployed runtime. It has no custody or configurable executor. |
| FeeController constructor | `ZZZRewardReceiverFactory`; verify immutable Fees/controller bindings and `Fees.receiverFactory`. It creates exact bound inboxes and supplies read-only validation/encoding helpers. |

The royalty receiver is **`NFT.royaltyRewards()` (`ZZZRoyaltyRewards`)**, not an
administrator wallet. ERC-2981 requests 5% there; actual admitted receipts go to
eligible holders under the separate 1/2/3 rarity-weighted ledger.

Later governance may create immutable per-bucket `ZZZRewardReceiver` creator
payment inboxes through the fee controller's fixed factory. Record every inbox and its fixed
fee-controller, bucket, token-pair and optional native-wrapper bindings. They are
not interchangeable with the royalty ledger, mint recipient or bridge receiver.
These additional inboxes are not new sealed module IDs.

## Existing network dependencies

Use chain-specific reviewed public addresses and implementation/administrator
identities, not ticker symbols or addresses copied from another chain.

| Dependency group | Required address inventory |
| --- | --- |
| Uniswap v4 settlement | PoolManager, PositionManager, StateView and Permit2; verify every constructor/getter relationship. |
| Assets | ZZZ, WETH/native wrapper, every admitted activation input, LP currency, reward asset and royalty asset. Review decimals, backing, transfer behavior and proxy powers. Native ETH uses the native currency convention, not an ERC-20 address. |
| Selected native/Pons venue | Hook, factory, wrapper proxy, implementation, admin and admin owner; complete reviewed runtime and policy history. Pons creator/protocol/escrow recipients are external identities, not PoPL authority wallets. |
| Valuation | Each token's actual USD feed/proxy and relevant implementation/admin authorities; genuine sequencer-status source or explicitly approved chain-specific initial policy. |
| Randomness | Qualified VRF coordinator and its implementation/admin/operator identities, subscription consumers and payment asset where applicable. A matching ABI is not qualification. |
| Optional input conversion | Each admitted single-hop V3 router, factory, pool and input/output token address; reviewed code pins, fee and immutable route identity. |

Known selected-market identities and dated observations are retained in
[pool research](ROBINHOOD_POOL.md), [activation routing](ACTIVATION_ROUTING.md)
and [service decisions](PRODUCTION_SERVICES.md). They are not production approval.
In particular, a v4 **pool ID is a bytes32 identity**, not a wallet or a separate
pool-contract address. The current code admits only its selected pinned native
exception plus supported conventional pools; registration is not permission to
execute arbitrary venues. No production ZZZ/USD or VRF choice is invented here.

## Optional future cross-chain dependencies

An initial reviewed launch can leave migration disabled with no provider or
transport routes. The fixed bridge adapter/router still exist in the core.

Before any actual bridge use, inventory each physical provider wrapper/SDK
endpoint on each chain, its router and channel bindings, relevant external
validator/admin/upgrade authorities, and its counterpart contracts. Record the
destination's PoPL modules, immutable helpers, equivalent backed token addresses,
pools, feeds and custody governance, as well as confirmed permanent bucket
admission. The source does not authenticate remote reservation proof automatically.

Transport-policy IDs must bind the exact source/destination chains, providers,
routers, code/configuration hashes and reviewed channel. Principal, completion
ACK, canonical-location ACK and old reward routes retain their original endpoint
identities. A destination address or nonzero review hash is not proof of safe
custody or token backing. No production provider is selected by this reference.

## Configuration that is not a wallet address

Record chain IDs; deployment/confirmed block hashes; runtime/initcode identities;
multisig threshold; zero governance and migration delays; VRF key hash, subscription ID,
confirmations and callback budget; pool keys/IDs and strategy bounds; provider
channel/policy/route IDs; content CIDs and metadata URI; RPC URLs; API/indexer
origins; keeper monitoring, backup and alert endpoints. Secrets and private keys
must remain outside source, manifests and Git.

The [deployment template](../script/DeployCore.s.sol) is restricted to local
chain IDs 31337/31338 and deliberately does not seal. It is not an approved public
deployment script. Anvil/staging addresses and test tokens must never be relabelled
as production addresses. Every actual deployment requires exact-release review,
source/bytecode/binding observations and explicit authorization.
