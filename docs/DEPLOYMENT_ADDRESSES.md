# Deployment address inventory

## Current direct mint versus intended OpenSea proceeds - 2026-10-25

The immutable mint recipient gains no management powers. Current direct mint
forwards the full0.05ETH. The intended OpenSea integration must keep the buyer's
gross mint price0.05ETH and deduct the actual platform fee before paying that
recipient; gas is separate. No platform rate or marketplace contract is approved.
This requires a compatible mint implementation before sealing; an inventory
entry cannot create it. [Integration requirements](MINT_INTEGRATION_QUALIFICATION.md).

## Governance authority versus custody recipient - 2026-10-25

These are distinct identities. Governance authorizes exact configuration, pool
movement and paused custody exits through the zero-delay controller. The reviewed
exit recipient receives and controls assets, without gaining protocol governance.
They can use the same wallet only as an explicit reviewed custody/security choice.

| Balance | Does principal exit transfer it? |
| --- | --- |
| Attributed LP principal and included bucket idle | Yes: normal mode closes/converts toZZZ; explicit raw mode sends actual pair assets, nativeETH/ZZZ for the selected pool, without a swap. |
| Claimable LP-owner/collective rewards | No automatic sweep. Their liabilities and backing remain classified in the reward ledgers. |
| NFT-sale royalties | Not by principal exit; the royalty ledger has its own reviewed paused full-currency custody exit/return. |
| Mint proceeds already paid | No: they are already at the immutable mint recipient. |
| Ownership and reward accounting | Not relocated by moving principal. Same-chain whole-collection handoff is a distinct verified path. |

Authority addresses, multisig threshold/signers and provider-specific subscription
ownership remain unselected. No public role or wallet was configured by this update.

**Current candidate (2026-10-24):** [selected hookless native ETH/ZZZ](POOL_SELECTION.md) supports atomic same-accounting-pair moves and the separate [governed custody handoff](GOVERNED_CUSTODY_HANDOFF.md). The old LP bridge/pair executor is removed; whole-collection handoff remains separate. The native-accounting V2 candidate holds and sends actual ETH/ZZZ; native ETH is asset zero, not WETH. Atomic ETH/WETH moves remain unsupported until an explicit conversion boundary is implemented. Actual production inventory, services and independent qualification remain open; integrated remote ledgers/finality are deferred optional scope. Earlier evidence retains its original scope. [Current native verification](../reports/native-eth-port/VERIFICATION.md).

Migration creates the immutable read-only [`ZZZCustodyValidation`](../src/ZZZCustodyValidation.sol)
companion. Record `Migration.validation()`, its `migration()`/`access()` bindings
and deployed runtime hash, plus Vault's Budget and canonical companions. It does
not hold principal or execute arbitrary calls. `ZZZPairMigration` and its old
bridge/transport companions are historical components, not current deployment
addresses. Qualify the actual pools, currencies, feeds and complete runtime/initcode
sizes. The [schema-5 preflight](PRODUCTION_PREFLIGHT.md) now describes this layout; actual addresses, reviewed pins, fresh observations and independent qualification remain required. Legacy schema 4 keeps its historical interpretation.

The royalty conversion candidate also requires a separately deployed
[`ZZZRoyaltyConverter`](../src/ZZZRoyaltyConverter.sol), constructed with the exact
controller and RoyaltyRewards ledger. Native-only v4 conversion permits wrapper zero; an explicit v3/unwrap path requires its own reviewed wrapper. Governance binds it to the
ledger once **before sealing**. Record its runtime hash and bidirectional bindings,
the explicit conversion profile and each reviewed route/feed. If a wrapper is used, retain its proxy/admin/implementation policy separately.
It is an optional fixed helper, not a replacement sealed controller module. Core
seal validation alone does not prove this optional feature is configured. Each
successor needs its own reviewed binding. Production helper-inventory qualification
remains open; see [setup and stopping procedures](ROYALTY_SETTLEMENT.md).

This is a configuration reference, not a task-status list or approved deployment.
The protocol remains an undeployed candidate. Production public wallets and
PoPL contract addresses are not selected. The [release record](RELEASE_CHECKLIST.md)
remains NOT APPROVED; progress belongs in the [central Todo](../TODO.md).

For the [bounded operating-control candidate](POST_SEAL_POLICY.md), record the
actual NFT and Buyback runtime hashes, fixed VRF provider/lane/subscription/payment
configuration, current `requestConfirmations`/`callbackGasLimit`, immutable
`maxTradeUSD` and current `operatingTradeUSD`. The two request parameters and the
buyback operating limit are deployment policy, not immutable NFT rights or copied
canonical records. Refresh observations after configuration; retain old request
transactions and operation history. The current inventory distinguishes
`immutable_provider_configuration` from the exact two-field
`mutable_request_parameters` list. The schema-5 tooling is implemented; actual native release-inventory qualification remains separate and open.

The [production manifest](../config/production.example.json) records addresses,
chain IDs, observed blocks, code hashes, immutable bindings and review evidence.
An address alone does not establish the right chain, code or authority.

## Wallets and authorities to choose

| Identity | Configuration and responsibility |
| --- | --- |
| Governance multisig | Select its public address, signer public addresses and threshold. It initially receives proposer and canceller roles; NFT ownership is not a governance vote. |
| Guardian | Select the emergency pause account. It cannot unpause or withdraw principal. |
| Keeper | Select a dedicated signer, fund its native gas balance and restrict it to keeper operations. Separate it from governance in production; role separation is an operating recommendation, not a general on-chain prohibition on reusing an address. |
| Mint proceeds recipient | Select the immutable proceeds recipient: current direct mint pays exactly 0.05 ETH; the required OpenSea path pays net of its actual platform fee from the same 0.05 ETH buyer total. A treasury may fill this role; it has no custody authority merely by receiving mint payments. |
| Deployment/bootstrap signer | Select the temporary deployment account. It performs write-once bindings and configuration before seal; sealing permanently clears bootstrap. |
| VRF subscription owner/funder | Identify the selected service's subscription ownership, authorized consumers and funding arrangements. These depend on the qualified coordinator, not a PoPL administrator setter. |
| Optional external payer | Only if separate discretionary funding is used, record the payer/authorizing identity and terms for its immutable inbox. The selected hookless pool earns actual LP fees without a Pons creator agreement; a calculator cannot authorize payments. |
| External custody recipient | For each approved principal/royalty exit, review the exact recipient, chain, EOA/contract status and code hash, custody controls and recovery plan. Recipient custody/liveness is a governance trust, not a holder redemption right. |

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

The current fixed core consists of **17 contracts: one controller plus the 16 required
sealed modules** below, matching `ZZZAccessController.seal()`. The four retired
bridge/receiver/routes/transport IDs cannot be bound by the current controller.
Record the actual per-chain addresses and exact immutable-specific runtimes.

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
| `oracle` | `ZZZOracle` — configured price and uptime policy |
| `pools` | `ZZZPoolRegistry` — eligible pools, native identity and input helpers |
| `canonical` | `ZZZCanonicalHandoff` - fixed canonical lifecycle and exact handoff coordinator |
| `nft_canonical` | `ZZZNFTCanonical` - NFT inventory/ownership codec bound to the NFT |
| `vault_canonical` | `ZZZVaultCanonical` - shares, origin lineage and parked custody codec bound to Vault |
| `fees_canonical` | `ZZZFeesCanonical` - reserves/inboxes codec bound to Fees |

The current inventory has **15 fixed helpers**: thirteen created by their parent contracts and two separately deployed converters. Every immutable-specific runtime and binding must be inventoried:

| Creator | Helper addresses and bindings |
| --- | --- |
| Pool registry constructor | `ZZZActivationAssets` and `ZZZActivationEntry`; verify registry/controller/helper relationships. |
| Controller constructor | `ZZZRoyaltyFactory`; only its atomic creation/binding path supplies the NFT's royalty ledger. Verify factory controller and observed NFT ledger. |
| NFT constructor | `ZZZRoyaltyRewards` through the controller's fixed factory, plus `ZZZClaimRouter` and `ZZZNFTMetadata`; verify NFT/controller/royalty bindings. |
| Oracle constructor | `ZZZContributionPricing`; verify `Oracle.contributionPricing()`, helper `oracle()`/`access()`, `active() == false` at the confirmed inventory anchor, and exact immutable-specific runtime. It holds no funds or approvals. |
| Vault constructor | `ZZZMigrationBudget`; verify `Vault.migrationBudget`, helper `vault`/`access` bindings and deployed runtime. It has no custody or configurable executor. |
| FeeController constructor | `ZZZRewardReceiverFactory`; verify immutable Fees/controller bindings and `Fees.receiverFactory`. It creates exact bound inboxes and supplies read-only validation/encoding helpers. |
| Migration constructor | `ZZZCustodyValidation`; verify `Migration.validation`, helper `migration`/`access` bindings and runtime. It is read-only and has no custody/execution authority. |
| Entry and converter constructors | Each creates a distinct `ZZZV4RouteExecutor`; verify its exact `parent()` and parent `v4Executor()` getter. |
| Separate LP and royalty converters | Deploy each with its own immutable ledger/controller and explicit optional wrapper; bind each ledger before sealing. |

The royalty receiver is **`NFT.royaltyRewards()` (`ZZZRoyaltyRewards`)**, not an
administrator wallet. ERC-2981 requests 5% there; actual admitted receipts go to
eligible holders under the separate 1/2/3 rarity-weighted ledger.

Later governance may create immutable per-bucket `ZZZRewardReceiver` creator
payment inboxes through the fee controller's fixed factory. Record every inbox and its fixed
fee-controller, bucket, token-pair and optional native-wrapper bindings. They are
not interchangeable with the royalty ledger, mint recipient or external custody recipient.
These optional inboxes are not new sealed module IDs. The current Vault permits
at most four historical local buckets, limiting reachable per-bucket inboxes to
four even though the factory retains a separate ceiling of 16.

## Existing network dependencies

Use chain-specific reviewed public addresses and implementation/administrator
identities, not ticker symbols or addresses copied from another chain.

| Dependency group | Required address inventory |
| --- | --- |
| Uniswap v4 settlement | PoolManager, PositionManager, StateView and Permit2; verify every constructor/getter relationship. |
| Assets | ZZZ, any explicitly used WETH wrapper, every admitted activation input, LP currency, reward asset and royalty asset. Review decimals, backing, transfer behavior and proxy powers. Native ETH uses the native currency convention, not an ERC-20 address. |
| Selected hookless native venue | Exact ETH/ZZZ PoolKey/ID, static fee and spacing, zero hook, pinned core/position/state/Permit2 runtimes and wiring; native asset-zero identity and reviewed native USD feed. Native settlement does not require WETH policy. Record Uniswap's protocol-fee controller separately. No Pons hook/factory/creator payout is required. |
| Valuation | Explicit `pricing_version: 2`; every priced asset's full two-source policy, append-only ID/ordinal, source runtimes, independence IDs, USD denomination, decimals, reviewed ages/disagreement and proxy/admin/implementation authorities. Observe both raw rounds and `priceBounds` fingerprint at the same confirmed block. Genuine sequencer status or independently approved initial no-feed chain policy remains separate. |
| Randomness | Qualified VRF coordinator and its implementation/admin/operator identities, subscription consumers and payment asset where applicable. A matching ABI is not qualification. |
| Optional input conversion | Each admitted typed v3 or static hookless v4 route, exact source/output assets, venue/runtime/fee bindings and full-operation qualification. A route does not establish a safe USD source. |

Current selected-market identities and dated observations are retained in
[pool selection](POOL_SELECTION.md) and the [pinned pool observation](../reports/hookless-pool/observed-pool.json).
Earlier [Pons research](ROBINHOOD_POOL.md) retains its historical scope.
[Activation routing](ACTIVATION_ROUTING.md) and [service decisions](PRODUCTION_SERVICES.md)
record remaining qualification; none is production approval. A v4 **pool ID is a
bytes32 identity**, not a wallet or a separate pool-contract address. Native
admission supports initialized static, hookless ETH/ZZZ fee tiers on the pinned
Robinhood deployment; supported ERC20 pools use ordinary admission. Registration
does not enable arbitrary venues. Production source pairs for ETH/ZZZ/USDG/USDC, their independent qualification and VRF remain unset. See [pricing requirements](PRICE_SECURITY.md).

## External custody and future-chain dependencies

Atomic supported local moves need no external recipient. A separately approved
external exit records the exact recipient, recipient code hash (including an EOA's
actual code hash), destination chain/custody and optional destination pool, snapshot,
raw minimums, mode and review hash. Normal exit sends configured ZZZ; explicit raw
exit sends both actual accounting assets: native ETH/ZZZ for the selected pool.
`completeLocal` and `recover` require exactly the declared native amount as
`msg.value`, or zero ETH for ERC20-only funding. Wrapper independence does not
remove core/token/recipient failure risks. Record actual departure amounts and outstanding
liabilities; no blanket sweep or automatic raw fallback is available.

For cross-chain verification/return, additionally inventory the exact verifier and
runtime, finalized source/destination facts, authenticated custody/backing and
channel-closure proof scheme. There is no multisig/timeout substitute and no
production verifier, bridge provider or remote ledger is supplied. The old bridge
router/adapter/registry/receiver stack is removed; its historical channel/policy
instructions must not be used to configure this candidate.

Whole-collection ownership/reward relocation is a separate canonical handoff,
currently implemented only as a same-chain candidate. It cannot capture while
principal or royalty custody is outstanding. A destination address or a review
hash alone proves neither return funding nor safe remote accounting. See the
[governed custody procedure](GOVERNED_CUSTODY_HANDOFF.md) and [canonical handoff](CANONICAL_HANDOFF.md).

## Configuration that is not a wallet address

Record chain IDs; deployment/confirmed block hashes; runtime/initcode identities; the accounting version and canonical schema;
multisig threshold; zero governance and migration delays; VRF key hash, subscription ID,
confirmations and callback budget; pool keys/IDs and strategy bounds; conversion
route IDs; custody request/snapshot/review identities and any qualified finality
proof boundary; content CIDs and metadata URI; RPC URLs; API/indexer
origins; keeper monitoring, backup and alert endpoints. Secrets and private keys
must remain outside source, manifests and Git.

The [deployment template](../script/DeployCore.s.sol) is restricted to local
chain IDs 31337/31338 and deliberately does not seal. It is not an approved public
deployment script. Anvil/staging addresses and test tokens must never be relabelled
as production addresses. Every actual deployment requires exact-release review,
source/bytecode/binding observations and explicit authorization.

## LP settlement helper

Native ETH LP fees enter holder/collective accounting directly; they do not
need wrapping or conversion. ZZZ and other non-native holder fees require a
separately deployed [ZZZLPRewardConverter](../src/ZZZLPRewardConverter.sol), bound
once to Rewards before sealing. Its typed hookless v4 path settles actual ETH without a wrapper. The separate v3/unwrap profile still requires its reviewed wrapper. Record controller/ledger, parent-bound executor, current conversion cap, route/feed review and keeper pins. This
helper has no custody of LP principal. The conversion limit defaults to 1%, governance-adjustable up to 10%, with gas separate. At the default cap the selected approximately 1.101%-fee pool still needs a cheaper independently qualified conversion route. [Schema-5 inventory and observation](PRODUCTION_PREFLIGHT.md) verify actual selected policy; no route is invented. See [setup and recovery](LP_ETH_SETTLEMENT.md).

## Native accounting and canonical version inventory

Record `Vault.ACCOUNTING_VERSION() == 2` and the canonical coordinator's
`SCHEMA == keccak256("ZZZ_CANONICAL_SAME_CHAIN_NATIVE_V2")` with their exact
runtime pins. A V1 WETH-accounting source cannot be imported into this V2 handoff;
there is no silent old-source codec conversion. Both reviewed peers must expose
the same schema. Native principal, Fees reserves/inboxes, Rewards and royalties
are independently captured and funded. Handoff transfers each asset to its peer
companion first, then acknowledges it with zero `msg.value`; the companion forwards
already transferred native funding once. Abort reverses the same classified legs.

Use fresh version 2 API/keeper configuration and state for a native deployment.
Keep per-deployment predecessor profiles, original currencies and saved journals;
never reinterpret old WETH as ETH or reset pending transactions to change versions.
The existing 8902 fixture remains on its old profile. Public `DEPLOYMENT` remains
null, shared browser signing remains Anvil-only and website V2 qualification is open.
