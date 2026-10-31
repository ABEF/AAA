# Deployment address inventory

Fresh undeployed source: [accounting6 / custody4 / portfolio2 / canonical V6](POSITION_V6.md).
Governance can permanently close LP and return actual ETH+ZZZ to NFT holders;
there is no external principal/royalty custody recipient. Production is **NOT APPROVED**.

## Mint proceeds and approval boundary

The current accepted mint recipient gains no management powers. Current direct mint
forwards the full reviewed current price(default0.05ETH). The intended OpenSea integration must keep the buyer's
gross mint price 0.05 ETH and deduct the actual platform fee before paying that
recipient; gas is separate. No platform rate or marketplace contract is approved.
This requires a compatible mint implementation before sealing; an inventory
entry cannot create it. [Integration requirements](MINT_INTEGRATION_QUALIFICATION.md).

## Governance and principal recipients

Governance authorizes supported settings, same-pair movement, reversible parking
and an irreversible collective holder exit. It does not choose a wallet to receive
LP principal. The fixed Migration module pays each NFT's actual current owner;
only that owner can choose a fallback recipient for a failed automatic payout.

| Balance | Collective exit treatment |
| --- | --- |
| Actual LP close proceeds, attributed idle and pending compound | Exact ETH+fixedZZZ apportioned by frozen shares and paid in bounded batches; no historical USD guarantee. |
| Earned individual/collective LP rewards | Existing ledgers/backing remain claimable by current NFT owners, separately from principal return. |
| Royalties and future receipts | Continue in the separate royalty ledger under preserved activated rarity weights; no external custody drain. |
| Buyback reserve, quarantine and unsolicited prefunds | Not swept into principal or an administrator address. Purpose-bound accounting remains. |
| Mint proceeds already paid | Already held by the recipient at payment time; no management privilege follows. |
| NFT ownership and reward accounting | Stay live through LP exit; before exit only, compatible canonical V6 can carry them to one reviewed same-chain successor. |

Authority wallets and provider-specific subscription ownership remain unselected.
The selected native ETH/fixedZZZ pool and supported fee-tier replacements are the
only admitted LP pair; ERC20 conversion venues remain separate. See
[holder return](HOLDER_COLLECTIVE_EXIT.md) and [pool selection](POOL_SELECTION.md).
Earlier source-bound observations/evidence do not qualify this new profile.

This is an **undeployed candidate, NOT APPROVED**, not a list of configured
public addresses. Complete the [schema8 production manifest](../config/production.example.json)
with actual chain IDs, confirmed blocks, code/immutable bindings and independent
review evidence. An address or a successful inventory check is not approval.
The [sole Todo](../TODO.md) owns qualification work; the
[release record](RELEASE_CHECKLIST.md) records final sign-off.

Use [versioned preflight](PRODUCTION_PREFLIGHT.md) with explicit accounting6 for this layout; older
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
| Mint proceeds recipient | Select the initial future-mint recipient: current direct mint pays the reviewed current price(default0.05 ETH); the required OpenSea path pays net of its actual platform fee from the same reviewed gross buyer price(default0.05 ETH). A treasury may fill this role; it has no custody authority merely by receiving mint payments. |
| Deployment/bootstrap signer | Select the temporary deployment account. It performs write-once bindings and configuration before seal; sealing permanently clears bootstrap. |
| VRF subscription owner/funder | Identify the selected service's subscription ownership, authorized consumers and funding arrangements. These depend on the qualified coordinator, not a PoPL administrator setter. |

The **governance controller is a deployed contract**, `ZZZAccessController`, not
another wallet. Its version2 constructor takes exactly three nonzero addresses:
initial governance, initial keeper and initial guardian. There are no proposer,
executor or canceller accounts/arrays and no scheduling/execution queue. The
governance wallet calls targets directly using its own signing/nonce policy.
Changing that wallet requires `proposeGovernance` from the current wallet and
`acceptGovernance` from the proposed wallet, without a time delay. A zero proposal
cancels. This does not rotate keeper/guardian grants or automatically rotate the separately accepted future mint
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
| `vault` | `ZZZVault` — shared LP custody, NFT shares and terminal principal release to the fixed holder-settlement module |
| `nft` | `ZZZNFT` — canonical ownership, fixed trait draw and royalty request |
| `liquidity` | `ZZZLiquidityManager` — fixed venue settlement |
| `rewards` | `ZZZRewards` — funded LP-owner and equal-collective claims |
| `membership` | `ZZZMembership` — activated-NFT collective membership |
| `fees` | `ZZZFeeController` — fee allocation and separate reserves |
| `strategy` | `ZZZStrategy` — fixed range/execution calculations |
| `compounder` | `ZZZCompounder` — bounded keeper compounding coordination |
| `buyback` | `ZZZBuyback` — reviewed purchase and supply-reducing burn |
| `migration` | `ZZZMigration` — same-pair moves/parking and irreversible exact holder-principal settlement |
| `oracle` | `ZZZOracle` — configured price and uptime policy |
| `pools` | `ZZZPoolRegistry` — eligible pools, native identity and input helpers |
| `canonical` | `ZZZCanonicalHandoff` - fixed canonical lifecycle and exact handoff coordinator |
| `nft_canonical` | `ZZZNFTCanonical` - NFT inventory/ownership codec bound to the NFT |
| `vault_canonical` | `ZZZVaultCanonical` - shares, origin lineage and parked custody codec bound to Vault |
| `fees_canonical` | `ZZZFeesCanonical` - LP-fee reserve codec bound to Fees |

The fresh source has **21 fixed helpers**, distinct from the 17 core contracts.
ProtocolPolicy, Budget, Balancer, PortfolioPolicy and Confirmation are separately deployed fixed
controller companions. Their parent getters resolve the sealed Access module
and are checked reciprocally; there is no mutable parent setter. Do not reuse a
historical 15/17-helper inventory or infer deployed runtimes from compiler templates.

| Creation/binding | Helper addresses and verification |
| --- | --- |
| Separate policy companion | `ZZZProtocolPolicy(controller,initialMintRecipient)` before consumers, bind-once Access.protocolPolicy, version1/runtime/scoped values and fingerprints. No custody. |
| Controller factories | `ZZZRoyaltyFactory` and `ZZZActivationAssetsFactory`; immutable Access/factory relationships and factory registry/NFT outputs. |
| Registry construction | Fixed `ZZZActivationAssets` through the factory and `ZZZActivationEntry`; Registry/Access/source-policy1 and one fixed ZZZ. |
| NFT construction | `ZZZRoyaltyRewards`, `ZZZClaimRouter`, `ZZZNFTMetadata`; exact NFT/controller/ledger relationships. |
| Oracle construction | `ZZZContributionPricing`; exact Oracle/Access, pricing2 and reviewed Entry2 bindings; inactive capture context at anchor. |
| Separate Budget | `ZZZMigrationBudget(controller)` is supplied to Vault. Verify actual Vault getter, Access-resolved `vault()` parent, compound4/confirmation3/emergency2 and runtime. It owns no custody. |
| Separate LP Balancer | `ZZZLPBalancer(controller,core,state)` is supplied to Manager; sealed parent, core/state, LP routing2/quality1 and exact runtime. Inventory actual execution pools/solver/quality separately. |
| Balancer arithmetic child | `ZZZLPBalanceMath`; `Balancer.balanceMath()`, immutable `balancer()` parent, version1 and runtime. |
| Manager physical child | `ZZZLPPositionExecutor`; `Manager.positionOperator()`, immutable Manager/core/state/PosM/Permit2/router, version1 and runtime. Typed physical LP operations preserve Vault ownership; this is not another human operator. |
| Separate Strategy companions | `ZZZPortfolioPolicy(controller)` and `ZZZRebalanceConfirmation(controller)` supplied to Strategy. Verify reciprocal Strategy/Access, portfolio2/confirmation3 and runtime. Read actual desired/applied geometry, trigger/revisions/reviews, half-side default 5000 and per-pool main floor6000–9999bps(default6000), complementary residual bound and positive gap spacings. |
| Confirmation policy | Selected600 seconds/strict 300 second gap,240 second source checks and same-side 85% physical/reference threshold. Constructor gap 0 blocks ordinary readiness. Source late paid enrollment/jitter are separate service rules, not observed market history. |
| Migration construction | `ZZZCustodyValidation`; exact Migration/Access parent, custody4 tuple including liquidity-sensitive portfolioHash and runtime. |
| Entry/converter route children | Three distinct `ZZZV4RouteExecutor` instances: Entry, LP converter and royalty converter. Match each immutable `parent()` and owning `v4Executor()`. |
| Separate converters | LP and royalty converters have distinct fixed ledgers/controller and explicit optional wrappers; bind their ledgers before sealing if required. |

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
controls. For an issuer exchange, collective exit returns actual old ETH/ZZZ to holders;
there is no operator custody wallet to exchange it on their behalf. A new fixed
token/project requires fresh review and does not automatically move old NFT
ownership, royalties or reward ledgers.

## Existing network dependencies

Use chain-specific reviewed public addresses and implementation/administrator
identities, not ticker symbols or addresses copied from another chain.

| Dependency group | Required address inventory |
| --- | --- |
| Uniswap v4 settlement | PoolManager, PositionManager, StateView and Permit2; verify every constructor/getter relationship. |
| Assets | Reviewed current ZZZ and native ETH contribution identities, any explicitly used conversion wrapper, the fixed ETH/ZZZ LP pair, reward assets and royalty assets. Review decimals, backing, transfer behavior and proxy powers. Native ETH is address zero, not an ERC20 address. A royalty currency does not become an activation input. |
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
Robinhood deployment; generic ERC20 LP admission is removed. Separate typed
conversion venues do not become LP pools. Registration does not qualify a route. Actual independent source pairs for ETH/ZZZ and any separately priced royalty conversion assets, plus VRF qualification, remain unset. No stable peg is assumed. See [pricing requirements](PRICE_SECURITY.md).

## Collective holder return and whole-collection replacement

Record `Migration.CUSTODY_VERSION()==4`, `currentZZZ()`, exact runtime and fixed
Vault/controller/validation bindings. Bootstrap configures that same ZZZ once;
sealing rejects an unset/mismatched contribution/settlement identity. This is
not a recipient or replaceable token contract.

At collective exit, record `Access.lpExitStarted`, review hash, snapshotted NFT
count/buckets/shares, raw close minima/deadlines, actual close receipts, allocation
cursor, per-NFT principal, payouts and remaining backing. `Exited=5` means known
zero attached LP; unpaid principal is a separate ledger following current NFT
ownership. Operator batching cannot select beneficiaries. Receiver failures keep
rights backed and permit current-owner fallback. Pending compound joins principal;
earned rewards, royalties and buyback reserve remain separate.

No external recipient, all-ZZZ conversion exit, `completeLocal`, `recover`, royalty
custody exit, request-ID domain or bridge provider is configured. No automatic
fallback swaps or generic sweep exists. See [operator steps](HOLDER_COLLECTIVE_EXIT.md).

Whole-collection handoff is available only before exit starts, with compatible
same-chain V6 peers and exact classified funding. Afterward it is permanently
blocked even when all principal has been paid, because the importer cannot carry
terminal payout accounting or safely reopen LP. A future royalty-only successor
requires separately reviewed schema/code. [Canonical procedure](CANONICAL_HANDOFF.md).

## Configuration that is not a wallet address

Record chain IDs; deployment/confirmed block hashes; runtime/initcode identities; the accounting version and canonical schema;
actual governance signers/threshold and direct governance version2; VRF key hash, subscription ID,
confirmations and callback budget; pool keys/IDs and strategy bounds; conversion
route IDs; holder-exit version/review and per-NFT settlement identities;
content CIDs and metadata URI; RPC URLs; API/indexer
origins; keeper monitoring, backup and alert endpoints. Secrets and private keys
must remain outside source, manifests and Git.

Record the current reviewed ProtocolPolicy provider/lane/subscription/payment
configuration, generation and scoped revision. Pending requests keep their
original provider-recorded settings; planned provider rotation requires every
old draw finalized. Future request confirmations/callback gas have bounded
settings and never reroll or repair an old request. Record Buyback's reviewed
`maxTradeUSD` separately from `operatingTradeUSD`; both are configurable within
their source bounds, while the ZZZ target and reserve ownership remain fixed.
Include current mint/payee, entry minima, separate idle/gas and cosmetic policies
with their scoped fingerprints. Refresh observations after changes. None of
these operating settings rewrites imported NFT economic rights. See
[post-seal controls](POST_SEAL_POLICY.md) and [bounded policy](ADAPTABLE_POLICY.md).

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
helper has no custody of LP principal. The conversion limit defaults to 1%, governance-adjustable up to 10%, with gas separate. At the default cap the selected approximately 1.101%-fee pool still needs a cheaper independently qualified conversion route. [Versioned inventory and observation](PRODUCTION_PREFLIGHT.md) must match the selected contract profile; no route is invented. See [setup and recovery](LP_ETH_SETTLEMENT.md).

## Native accounting and canonical version inventory

Record `Vault.ACCOUNTING_VERSION() == 6` and `ProtocolPolicy.PROTOCOL_POLICY_VERSION() == 1` and the canonical coordinator's
`SCHEMA == keccak256("ZZZ_CANONICAL_SAME_CHAIN_ADAPTABLE_POLICY_V6")` with their exact
runtime pins. Current release inventory also declares `fee_intake_version: 1`,
with the fresh21-helper layout and Fees `FEE_INTAKE_VERSION() == 1`. Absent/zero retains
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
Active1, reserved Outbound2, Dormant3, Parked4, Exited5; no home/location cross-chain fields exist.
Use fresh accounting6/portfolio2 API/keeper configuration and distinct state paths.
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
