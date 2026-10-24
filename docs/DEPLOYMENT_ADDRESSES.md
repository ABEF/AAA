# Deployment address inventory

**Current candidate (2026-10-24):** [selected hookless native ETH/ZZZ](POOL_SELECTION.md) supports atomic same-accounting-pair moves and the separate [governed custody handoff](GOVERNED_CUSTODY_HANDOFF.md). The old LP bridge/pair executor is removed; whole-collection handoff remains separate. The native-accounting V2 candidate holds and sends actual ETH/ZZZ; native ETH is asset zero, not WETH. Atomic ETH/WETH moves remain unsupported until an explicit conversion boundary is implemented. Real finality/remote accounting, production inventory, services and independent qualification remain open. Earlier evidence retains its original scope. [Current native verification](../reports/native-eth-port/VERIFICATION.md).

Migration creates the immutable read-only [`ZZZCustodyValidation`](../src/ZZZCustodyValidation.sol)
companion. Record `Migration.validation()`, its `migration()`/`access()` bindings
and deployed runtime hash, plus Vault's Budget and canonical companions. It does
not hold principal or execute arbitrary calls. `ZZZPairMigration` and its old
bridge/transport companions are historical components, not current deployment
addresses. Qualify the actual pools, currencies, feeds and complete runtime/initcode
sizes; the legacy production gate remains blocked pending an independently reviewed
inventory update.

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

Nine fixed helpers/factories are created automatically and must also be inventoried:

| Creator | Helper addresses and bindings |
| --- | --- |
| Pool registry constructor | `ZZZActivationAssets` and `ZZZActivationEntry`; verify registry/controller/helper relationships. |
| Controller constructor | `ZZZRoyaltyFactory`; only its atomic creation/binding path supplies the NFT's royalty ledger. Verify factory controller and observed NFT ledger. |
| NFT constructor | `ZZZRoyaltyRewards` through the controller's fixed factory, plus `ZZZClaimRouter` and `ZZZNFTMetadata`; verify NFT/controller/royalty bindings. |
| Vault constructor | `ZZZMigrationBudget`; verify `Vault.migrationBudget`, helper `vault`/`access` bindings and deployed runtime. It has no custody or configurable executor. |
| FeeController constructor | `ZZZRewardReceiverFactory`; verify immutable Fees/controller bindings and `Fees.receiverFactory`. It creates exact bound inboxes and supplies read-only validation/encoding helpers. |
| Migration constructor | `ZZZCustodyValidation`; verify `Migration.validation`, helper `migration`/`access` bindings and runtime. It is read-only and has no custody/execution authority. |

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
| Valuation | Each token's actual USD feed/proxy and relevant implementation/admin authorities; genuine sequencer-status source or explicitly approved chain-specific initial policy. |
| Randomness | Qualified VRF coordinator and its implementation/admin/operator identities, subscription consumers and payment asset where applicable. A matching ABI is not qualification. |
| Optional input conversion | Each admitted single-hop V3 router, factory, pool and input/output token address; reviewed code pins, fee and immutable route identity. |

Current selected-market identities and dated observations are retained in
[pool selection](POOL_SELECTION.md) and the [pinned pool observation](../reports/hookless-pool/observed-pool.json).
Earlier [Pons research](ROBINHOOD_POOL.md) retains its historical scope.
[Activation routing](ACTIVATION_ROUTING.md) and [service decisions](PRODUCTION_SERVICES.md)
record remaining qualification; none is production approval. A v4 **pool ID is a
bytes32 identity**, not a wallet or a separate pool-contract address. Native
admission supports initialized static, hookless ETH/ZZZ fee tiers on the pinned
Robinhood deployment; supported ERC20 pools use ordinary admission. Registration
does not enable arbitrary venues. Production ZZZ/USD pricing and VRF remain unset.

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
once to Rewards before sealing. Its current single-hop v3 path uses a reviewed
WETH wrapper at that explicit conversion boundary. Record controller/ledger,
wrapper runtime/implementation policy, route/feed review and keeper pins. This
helper has no custody of LP principal. Retain the 1% maximum ZZZ conversion loss,
gas separate, and require a cheaper independently qualified route; the selected
approximately 1.101% pool does not qualify full conversion at reference prices.
Typed v4 conversion remains pre-seal work. See [setup and recovery](LP_ETH_SETTLEMENT.md).

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
