# Deployment address inventory

## Mint proceeds and approval boundary

The immutable mint recipient gains no management powers. Current direct mint
forwards the full 0.05 ETH. The intended OpenSea integration must keep the buyer's
gross mint price 0.05 ETH and deduct the actual platform fee before paying that
recipient; gas is separate. No platform rate or marketplace contract is approved.
This requires a compatible mint implementation before sealing; an inventory
entry cannot create it. [Integration requirements](MINT_INTEGRATION_QUALIFICATION.md).

## Governance authority versus custody recipient

These are distinct identities. Governance authorizes exact configuration, pool
movement and paused custody exits by calling their modules directly. Access
authenticates the current governance wallet; it does not forward the call. The reviewed
exit recipient receives and controls assets, without gaining protocol governance.
They can use the same wallet only as an explicit reviewed custody/security choice.

| Balance | Does principal exit transfer it? |
| --- | --- |
| Attributed LP principal and included bucket idle | Yes: normal mode closes/converts to ZZZ; explicit raw mode sends actual pair assets, native ETH/ZZZ for the selected pool, without a swap. |
| Claimable LP-owner/collective rewards | No automatic sweep. Their liabilities and backing remain classified in the reward ledgers. |
| NFT-sale royalties | Not by principal exit; the royalty ledger has its own reviewed paused full-currency custody exit/return. |
| Mint proceeds already paid | No: they are already at the immutable mint recipient. |
| Ownership and reward accounting | Not relocated by moving principal. Same-chain whole-collection handoff is a distinct verified path. |

Authority addresses, multisig threshold/signers and provider-specific subscription
ownership remain unselected. No public role or wallet was configured by this update.

**Current candidate:** [selected hookless native ETH/ZZZ](POOL_SELECTION.md) supports atomic same-accounting-pair moves and the separate [governed custody handoff](GOVERNED_CUSTODY_HANDOFF.md). The old LP bridge/pair executor and optional remote-proof custody paths are removed; whole-collection handoff remains separate. The current accounting3 candidate holds and sends actual ETH/ZZZ; native ETH is asset zero, not WETH. Atomic ETH/WETH moves remain unsupported until an explicit conversion boundary is implemented. A reviewed source-chain custodian may bridge externally; no integrated bridge or remote ownership/reward ledger is supplied. Actual production inventory, services and independent qualification remain open. Earlier evidence retains its original scope. [Native accounting verification](../reports/native-eth-port/VERIFICATION.md).

This is an **undeployed candidate, NOT APPROVED**, not a list of configured
public addresses. Complete the [production manifest](../config/production.example.json)
with actual chain IDs, confirmed blocks, code/immutable bindings and independent
review evidence. An address or a successful inventory check is not approval.
The [sole Todo](../TODO.md) owns qualification work; the
[release record](RELEASE_CHECKLIST.md) records final sign-off.

Use [schema-5 preflight](PRODUCTION_PREFLIGHT.md) for the current layout; older
schemas/profiles remain historical inspection only. Record each module/helper
below once, together with exact deployed runtime (including immutables), parent
bindings, source/implementation/admin controls and configuration history. A
compiler template hash is not a deployed runtime pin. Public authorities,
VRF/providers, actual feed/route policies and service choices remain unselected.

## Wallets and authorities to choose

One human operator controls governance and operates the services. The identities
below describe accounts/capabilities, not a requirement for several people.
The existing inventory field `governance.multisig` names the governance wallet;
the field name does not enforce multiple owners. The preflight accepts one signer
and threshold1, subject to the same actual wallet/authority evidence. Preserve
the schema and record the chosen wallet accurately rather than inventing people.

| Identity | Configuration and responsibility |
| --- | --- |
| Governance wallet, controlled by the operator | Select its public address, actual signer/threshold policy and recovery controls. A single-owner configuration is supported. This wallet is `Access.governance()` and directly calls governed modules; NFT ownership is not a governance vote. |
| Guardian | Select the emergency pause account. It cannot unpause or withdraw principal. |
| Keeper | Select a dedicated signer, fund its native gas balance and restrict it to keeper operations. Separate it from governance in production; role separation is an operating recommendation, not a general on-chain prohibition on reusing an address. |
| Mint proceeds recipient | Select the immutable proceeds recipient: current direct mint pays exactly 0.05 ETH; the required OpenSea path pays net of its actual platform fee from the same 0.05 ETH buyer total. A treasury may fill this role; it has no custody authority merely by receiving mint payments. |
| Deployment/bootstrap signer | Select the temporary deployment account. It performs write-once bindings and configuration before seal; sealing permanently clears bootstrap. |
| VRF subscription owner/funder | Identify the selected service's subscription ownership, authorized consumers and funding arrangements. These depend on the qualified coordinator, not a PoPL administrator setter. |
| External custody recipient | For each approved principal/royalty exit, review the exact recipient, chain, EOA/contract status and code hash, custody controls and recovery plan. Recipient custody/liveness is a governance trust, not a holder redemption right. |

The **governance controller is a deployed contract**, `ZZZAccessController`, not
another wallet. Its version2 constructor takes exactly three nonzero addresses:
initial governance, initial keeper and initial guardian. There are no proposer,
executor or canceller accounts/arrays and no scheduling/execution queue. The
governance wallet calls targets directly using its own signing/nonce policy.
Changing that wallet requires `proposeGovernance` from the current wallet and
`acceptGovernance` from the proposed wallet, without a time delay. A zero proposal
cancels. This does not rotate keeper/guardian grants or the immutable mint
recipient. Record `GOVERNANCE_VERSION=2`, `governance()` and zero
`pendingGovernance()` in the release snapshot. Multisig, guardian and keeper
recovery arrangements still need independent review.

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
| `access` | `ZZZAccessController` — authenticates direct governance and fixes sealed module bindings |
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
| `fees_canonical` | `ZZZFeesCanonical` - LP-fee reserve codec bound to Fees |

The current inventory has **15 fixed helpers**: thirteen created by their parent contracts and two separately deployed converters. This is a different set from the historical 15-helper profile: ActivationAssetsFactory replaces the removed RewardReceiverFactory. Every immutable-specific runtime and binding must be inventoried:

| Creator | Helper addresses and bindings |
| --- | --- |
| Pool registry construction | `ZZZActivationAssets` through the controller's immutable factory, plus `ZZZActivationEntry`; verify registry/controller/helper relationships, `SOURCE_POLICY_VERSION() == 1`, the fixed deployment `zzz()` identity and its complete source-policy history. Bootstrap selects ZZZ once before sealing; only native ETH/that ZZZ may be enabled contribution inputs. Target LP and royalty currencies are separate. |
| Controller constructor | `ZZZRoyaltyFactory` and `ZZZActivationAssetsFactory`. The former supplies the NFT's royalty ledger; the latter creates one fixed Assets child per Registry. Verify `Access.activationAssetsFactory()`, factory `access()`, `assetsOf(Registry)` and `Registry.activationAssets()` all agree. Neither factory is an administrator-controlled executor. |
| NFT constructor | `ZZZRoyaltyRewards` through the controller's fixed factory, plus `ZZZClaimRouter` and `ZZZNFTMetadata`; verify NFT/controller/royalty bindings. |
| Oracle constructor | `ZZZContributionPricing`; verify `Oracle.contributionPricing()`, helper `oracle()`/`access()`, `active() == false` at the confirmed inventory anchor, and exact immutable-specific runtime. It holds no funds or approvals. |
| Vault constructor | `ZZZMigrationBudget`; verify `Vault.migrationBudget`, helper `vault`/`access` bindings and deployed runtime. It has no custody or configurable executor. |
| Migration constructor | `ZZZCustodyValidation`; verify `Migration.validation`, helper `migration`/`access` bindings and runtime. It is read-only and has no custody/execution authority. |
| Entry and converter constructors | Each creates a distinct `ZZZV4RouteExecutor`; verify its exact `parent()` and parent `v4Executor()` getter. |
| Separate LP and royalty converters | Deploy each with its own immutable ledger/controller and explicit optional wrapper; bind each ledger before sealing if that conversion stream is required. Core seal validation does not prove an optional converter is configured. |

The royalty receiver is **`NFT.royaltyRewards()` (`ZZZRoyaltyRewards`)**, not an
administrator wallet. ERC-2981 requests 5% there; actual admitted receipts go to
eligible holders under the separate 1/2/3 rarity-weighted ledger.

Creator-payment inboxes and their factory are removed from the current source.
There is no payer/inbox address to configure, and `Fees.FEE_INTAKE_VERSION() == 1`
identifies the LP-only intake. Historical receiver addresses and event records
stay attached to their original deployments; never replace them with zero
addresses or present them as new current helpers.

The ZZZ contribution identity is fixed per deployment. `ActivationAssets.configureZZZ`
is a one-time bootstrap operation before sealing; governance cannot replace that
identity later. Enable/disable and reviewed route/price policy remain distinct
controls. A future ZZZ contract migration uses custody exit, an external issuer
exchange and a fresh reviewed deployment. That exchange alone does not transfer
the original NFT ownership or reward ledgers.

## Existing network dependencies

Use chain-specific reviewed public addresses and implementation/administrator
identities, not ticker symbols or addresses copied from another chain.

| Dependency group | Required address inventory |
| --- | --- |
| Uniswap v4 settlement | PoolManager, PositionManager, StateView and Permit2; verify every constructor/getter relationship. |
| Assets | Reviewed current ZZZ and native ETH contribution identities, any explicitly used WETH wrapper, every LP currency, reward asset and royalty asset. Review decimals, backing, transfer behavior and proxy powers. Native ETH is address zero, not an ERC20 address. A royalty currency does not become an activation input. |
| Selected hookless native venue | Exact ETH/ZZZ PoolKey/ID, static fee and spacing, zero hook, pinned core/position/state/Permit2 runtimes and wiring; native asset-zero identity and reviewed native USD feed. Native settlement does not require WETH policy. Record Uniswap's protocol-fee controller separately. No Pons hook/factory/creator payout is required. |
| Valuation | Explicit `pricing_version: 2`; every priced asset's full two-source policy, append-only ID/ordinal, source runtimes, independence IDs, USD denomination, decimals, reviewed ages/disagreement and proxy/admin/implementation authorities. Observe both raw rounds and `priceBounds` fingerprint at the same confirmed block. Genuine sequencer status or independently approved initial no-feed chain policy remains separate. |
| Randomness | Qualified VRF coordinator and its implementation/admin/operator identities, subscription consumers and payment asset where applicable. A matching ABI is not qualification. |
| Optional input conversion | Each admitted typed v3 or static hookless v4 route, exact source/output assets, venue/runtime/fee bindings and full-operation qualification. A route does not establish a safe USD source. |

Current selected-market identities and dated observations are retained in
[pool selection](POOL_SELECTION.md) and the [pinned pool observation](../reports/hookless-pool/observed-pool.json).
[Activation routing](ACTIVATION_ROUTING.md) and [service decisions](PRODUCTION_SERVICES.md)
record remaining qualification; none is production approval. A v4 **pool ID is a
bytes32 identity**, not a wallet or a separate pool-contract address. Native
admission supports initialized static, hookless ETH/ZZZ fee tiers on the pinned
Robinhood deployment; supported ERC20 pools use ordinary admission. Registration
does not enable arbitrary venues. Actual independent source pairs for ETH/ZZZ and any separately priced royalty conversion assets, plus VRF qualification, remain unset. No stable peg is assumed. See [pricing requirements](PRICE_SECURITY.md).

## External custody and whole-collection replacement

Atomic supported local moves need no external recipient. A separately approved
external exit records the exact source-chain recipient, recipient code hash (including an EOA's
actual code hash), destination custody and optional local destination pool, snapshot,
raw minimums, mode and review hash. Normal exit sends configured ZZZ; explicit raw
exit sends both actual accounting assets: native ETH/ZZZ for the selected pool.
`completeLocal` and `recover` require exactly the declared native amount as
`msg.value`, or zero ETH for ERC20-only funding. Wrapper independence does not
remove core/token/recipient failure risks. Record actual departure amounts and outstanding
liabilities; no blanket sweep or automatic raw fallback is available.

Record `Migration.CUSTODY_VERSION() == 2` and the `ZZZ_CUSTODY_V2` request-ID
domain. Requests have no destination-chain or verifier fields. There is no remote
completion/proof endpoint or remote ledger to configure. `recover(id,deadline)`
requires full actual original-currency funding; external bridging by the recipient
does not close a source plan. The old bridge/router/receiver and remote-proof
instructions are historical, not current configuration.

For normal all-ZZZ exit, configure `Migration.currentZZZ()` exactly once during
bootstrap before sealing and verify that it equals `ActivationAssets.zzz()` with
the reviewed runtime hash. Sealing rejects an unset or mismatched identity. It
is not a future governance replacement target. The explicit raw exit later
avoids normal-target price/swap dependencies; its actual-asset minima, custody
authorization and transfers still apply.

Whole-collection ownership/reward relocation is a separate canonical handoff,
currently implemented only as a same-chain candidate. It cannot capture while
principal or royalty custody is outstanding. A destination address or a review
hash alone proves neither return funding nor safe remote accounting. See the
[governed custody procedure](GOVERNED_CUSTODY_HANDOFF.md) and [canonical handoff](CANONICAL_HANDOFF.md).

## Configuration that is not a wallet address

Record chain IDs; deployment/confirmed block hashes; runtime/initcode identities; the accounting version and canonical schema;
actual governance signers/threshold and direct governance version2; VRF key hash, subscription ID,
confirmations and callback budget; pool keys/IDs and strategy bounds; conversion
route IDs; source-chain custody version/request/snapshot/review identities;
content CIDs and metadata URI; RPC URLs; API/indexer
origins; keeper monitoring, backup and alert endpoints. Secrets and private keys
must remain outside source, manifests and Git.

Record immutable VRF provider/lane/subscription/payment settings separately
from bounded future `requestConfirmations`/`callbackGasLimit`, and immutable
Buyback `maxTradeUSD` separately from current `operatingTradeUSD`. Refresh
observations after a setting change; original requests/history remain unchanged.
The mutable VRF list contains exactly those two request parameters. These
operating policies are not imported NFT economic rights. See
[post-seal controls](POST_SEAL_POLICY.md).

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

Record `Vault.ACCOUNTING_VERSION() == 3` and the canonical coordinator's
`SCHEMA == keccak256("ZZZ_CANONICAL_SAME_CHAIN_NATIVE_LP_ONLY_V4")` with their exact
runtime pins. Current release inventory also declares `fee_intake_version: 1`,
with the current 15-helper layout and Fees `FEE_INTAKE_VERSION() == 1`. Absent/zero retains
the historical 15-helper accounting2/fee0 inventory for inspection only. Earlier
accounting2/fee1 uses the distinct LP-only V3 schema. Neither historical codec
nor V1 WETH accounting can be imported into this current
handoff. Both reviewed peers must expose the same schema. Native principal,
LP-fee reserves, Rewards and royalties
are independently captured and funded. Handoff transfers each asset to its peer
companion first, then acknowledges it with zero `msg.value`; the companion forwards
already transferred native funding once. Abort reverses the same classified legs.

Current Position rows contain eight words: pool ID, LP token ID, idle0, idle1,
depositUSD, centerX96, lastRebalance and status. Their status meanings are None0,
Active1, Outbound2, Dormant3, Parked4; no home/location cross-chain fields exist.
Use fresh accounting3 API/keeper configuration and distinct state paths.
Keep per-deployment predecessor profiles, original currencies and saved journals;
never reinterpret old WETH as ETH or reset pending transactions to change versions.
The existing 8902 fixture remains on its old profile. Public `DEPLOYMENT` remains
null, shared browser signing remains Anvil-only and actual current-profile qualification is open.

## Exact controller constructor size

The current direct controller has three static address arguments, adding96 ABI
bytes to creation code. It has no dynamic role arrays. Qualify the exact frozen
creation code plus these actual arguments against EIP-3860 and its runtime
against EIP-170; the earlier scheduled-controller 29-byte margin is historical.

Use the actual governance wallet address as initial governance. If it is a Safe,
use its **contract address**, not its internal owner address; its threshold is
managed by that wallet. A governance EOA uses its own address directly. Additional
keeper/guardian grants use `setKeeper`/`setGuardian`; governance wallet rotation
uses the two-step handover. Preserve full reviewed authority history and exact
runtime/bootstrap/source/exit bindings. Removing obsolete role arrays does not
relax compiler limits or qualify the new deployment automatically.
