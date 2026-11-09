# ZZZ Collection - Proof of Permanent Liquidity (PoPL)

The earlier [actual Entry3 rehearsal](reports/source9-actual-entry-20261109/REVIEW.md)
fixes two production reader/trace defects and verifies ETH/ZZZ activation and
growth through real unsigned website/API reviews on an isolated fork. Successful
cases explicitly use synthetic market depth and controlled feeds/VRF; the real
thin-depth rejection remains a release blocker. [Source9](docs/SOURCE9_WEBSITE_PROFILE.md)
supports reviewed optional activation gas policy2. Public configurations remain
null; existing sites, lab, journals and the shared signer are unchanged.

Current [fee-flow corrections](reports/fee-flow-audit-20261107/REVIEW.md) protect
the final ETH conversion value, size affordable keeper batches, stop stale sends
and preserve zero-noop earnings history. Explicit unsigned gas policy2 is an
optional reviewed backend setting after sealing; no deployed environment changes.

PoPL connects transferable ERC-721 NFTs to vault-managed ETH/ZZZ liquidity.
Activation attaches an independently accounted LP share and unlocks funded LP
fees plus rarity-weighted NFT-sale royalties. Holders cannot redeem principal
during normal operation. Governance can permanently end LP activity and return
actual ETH + ZZZ to current NFT owners; transfers, old rewards and royalties remain.

**Source candidate; not deployed for production. Production NOT APPROVED.** Fresh
[accounting7/direct Entry3/custody5](docs/POSITION_V7.md) implements
[bounded operating policy](docs/ADAPTABLE_POLICY.md) and reviewed
[manual recovery](docs/OPERATOR_MANUAL.md). Source publication does not update
existing contracts, services, journals or websites. Public signing remains disabled.


Fresh [exact-unit LP accounting7](docs/EXACT_LP_ALLOCATION.md) connects authenticated NFT shares and membership to whole-unit claims, same-NFT conversion and lossless raw-phase accounting. Current mint2 extends the outer canonical schema to V10; original V9 integration evidence keeps its source scope. Every allocated raw unit is assigned without a fractional reserve; historical6/V8 state remains separately interpreted. [Integration verification](reports/exact-lp-integration-20261106/VERIFICATION.md) records source, EVM, backend, size and gas limits. Earlier execution/harvest reviews retain their original source scopes. No running environment is upgraded.

The [operator management preparer](reports/operator-management-20261109/REVIEW.md)
now fetches exact inputs and simulates unsigned parking, resume, residual-only
closure and the complete collective-exit sequence. Explicit floors and gas
budgets remain operator choices; no signing or automatic fallback is added.
Existing [checkpoint2/B-C-D tools](reports/checkpoint2-manual-20261107/REVIEW.md)
remain separate. No contract/runtime or installed environment changes.

The new [OpenSea mint source](docs/OPENSEA_MINT.md) implements configurable
free-team/paid-allowlist/public phases (initially20/500/480). Unused allowlist
supply rolls into public; unused team slots stay reserved. CanonicalV10 preserves
original recipients and lifetime mint limits. Actual custom-drop onboarding,
fee/payer/provider and operating qualification remain open. Explicit mint2/V10 backend read/claim support is implemented; website and installed-service adoption remain separate.

## Project navigation

[Consolidated audit findings](docs/AUDIT_FINDINGS.md) explains past findings against
the current code; [the report map](reports/README.md) separates current evidence
from historical scopes. [Todo](TODO.md) remains the only task-status checklist.

| Purpose | Start here |
| --- | --- |
| Remaining work | **[Sole Project Todo](TODO.md)**, beside the [feature/evidence reference](docs/IMPLEMENTATION_STATUS.md) |
| Operate the protocol | **[Operator manual and short call tables](docs/OPERATOR_MANUAL.md#operator-call-tables)**; [full inputs, outputs and permissions](docs/CONTRACT_FUNCTIONS.md) |
| Current source and compatibility | [Accounting7 profile](docs/POSITION_V7.md), [architecture](docs/ARCHITECTURE.md), [component map](docs/COMPONENT_STATUS.md) |
| LP policy and protection | [Execution policy](docs/LP_EXECUTION_POLICY.md), [keeper safeguards](docs/KEEPER_SAFEGUARDS.md), [two-source pricing](docs/PRICE_SECURITY.md) |
| Verify or approve release | [Exact-unit LP integration](reports/exact-lp-integration-20261106/VERIFICATION.md), [Same-main governance consolidation](reports/residual-main-consolidation-20261106/REVIEW.md), [Main/residual lifecycle audit](reports/residual-lifecycle-20261106/REVIEW.md), [factory/claim improvements](reports/factory-claims-20261105/REVIEW.md), [royalty audit](reports/last24h-audit-20261105/REVIEW.md), [source-scoped authority evidence](reports/authority-audit-20261103/VERIFICATION.md), [whole-project review](reports/comprehensive-audit-20261104/REVIEW.md), [release approval record](docs/RELEASE_CHECKLIST.md), [production preflight](docs/PRODUCTION_PREFLIGHT.md) |
| Find older work | [Documentation map](docs/README.md), [historical reports](reports/README.md), [reconciliation](reports/historical-reconciliation-completion-20261029/REVIEW.md) |

## Architecture overview

| Layer | Owns this responsibility | Explore |
| --- | --- | --- |
| **1. Smart contracts** | Ownership, LP custody, independent NFT shares, funded rewards and permissions. | [Contract components](#contract-components) |
| **2. Backend and operations** | Confirmed reads, unsigned transaction preparation and authorized maintenance. | [Services and data flow](#backend-components) |
| **3. Frontend** | Product explanation, portfolio display and versioned wallet review. | [Website boundaries](#frontend-components) |

<a id="contract-components"></a>

### 1. Smart contracts

| Component | Job |
| --- | --- |
| [NFT](src/ZZZNFT.sol), [mint policy](src/ZZZSeaDropMint.sol), [metadata](src/ZZZNFTMetadata.sol) | Dormant SeaDrop minting with reviewed quotas and atomic payment rollback; transferable ownership, fixed-design random assignment and on-chain LP evolution. |
| [Activation Entry](src/ZZZActivationEntry.sol), [Registry](src/ZZZPoolRegistry.sol) | Atomic native ETH/fixed-ZZZ contributions; one admitted contribution pool at a time. |
| [Vault](src/ZZZVault.sol), [pricing companion](src/ZZZContributionPricing.sol) | Own both physical LP NFTs, record per-NFT shares and prove actual marginal deployed LP before issuing shares. |
| [Liquidity Manager](src/ZZZLiquidityManager.sol), [typed position child](src/ZZZLPPositionExecutor.sol) | Mint/increase, harvest and close a main plus at most one residual. The child has typed actions and fixed Vault recipients, not a generic withdrawal path. |
| [LP Balancer](src/ZZZLPBalancer.sol), [math child](src/ZZZLPBalanceMath.sol) | Compare bounded reviewed swap venues using actual-core sizing; ordinary replacement quotes must leave an active main. Entrant and captured maintenance budgets remain separate. |
| [Strategy](src/ZZZStrategy.sol), [portfolio policy](src/ZZZPortfolioPolicy.sol), [confirmation](src/ZZZRebalanceConfirmation.sol) | Manual range/mode settings, exact human-price threshold, sampled confirmation and reviewed readiness. |
| [Budget](src/ZZZMigrationBudget.sol), [Oracle](src/ZZZOracle.sol) | Fixed transaction valuations, independent USD sources, principal/reserve separation, operation and caller loss floors, compound timing and actual main-floor proof. |
| [FeeController](src/ZZZFeeController.sol), [Rewards](src/ZZZRewards.sol), [Membership](src/ZZZMembership.sol), [fixed LP codec](src/ZZZRewardsCanonical.sol) | Allocate actual harvested fees 80/10/5/5; exact-unit individual shares and equal activated-NFT collective rights; a constructor-fixed typed codec preserves raw fairness phase during replacement. |
| [RoyaltyRewards](src/ZZZRoyaltyRewards.sol), [ClaimRouter](src/ZZZClaimRouter.sol) | Exact-unit original-currency royalties with GCD-normalized rarity weights, rotating indivisible units, outage isolation and current-owner claims; no royalty swaps. The allocator is internal library code, not another deployed helper. [Rule and limits](docs/EXACT_ROYALTY_ALLOCATION.md). |
| [Compounder](src/ZZZCompounder.sol), [Buyback](src/ZZZBuyback.sol) | Reinvest designated reserves or buy and burn the same fixed ZZZ, independently of user claims. |
| [Migration](src/ZZZMigration.sol), [canonical helpers](src/ZZZVaultCanonical.sol) | Both-leg same-pair moves/parking, terminal holder return and compatible pre-exit same-chain replacement. No bridge or external custody-address exit. |
| [ProtocolPolicy](src/ZZZProtocolPolicy.sol) | Fixed noncustodial helper for bounded future entry/sale, gas, display and drained-randomness policy; reviews bind scoped revisions. |
| [AccessController](src/ZZZAccessController.sol) | Direct governance, guardian pause, limited keeper grants and frozen module bindings after sealing. No timelock machinery. |

Many NFTs share one logical bucket. It holds one main physical LP by default,
or a main plus one optional residual in the **same ETH/ZZZ pool**. Valuation,
harvesting and recovery include both. The four-bucket bound covers retained
history/admission; it does not permit unbounded residual creation.

<a id="backend-components"></a>

### 2. Backend and operations

The [Python keeper](keeper/monitor.py) reads confirmed state, simulates permitted
maintenance and persists nonce/receipt recovery. Pending transactions recover
before new work. [Read API](docs/FRONTEND_API.md) and [indexer](indexer/monitor.py)
authenticate ownership, both LP legs, balances and earnings at pinned blocks.
Fresh7 verifies each physical principal amount and exact portfolio identities;
[the lifecycle matrix](reports/residual-lifecycle-20261106/LIFECYCLE.md) explains
opening, fills, operator recovery and merging.
[Unsigned preparation](docs/ACTIVATION_PREPARATION.md) checks exact assets,
balancing venues, prices, policy, allowance and calldata; it does not sign public transactions.
Fresh contract inventory is schema17/mint2/residual-reinvest1/direct Entry3/royalty4 with20 callable helpers plus two inert [factory data children](docs/FACTORY_CODE_STORAGE.md). Reporting5 and exact LP tree formats remain; canonicalV10 adds original-recipient mint books. Explicit backend `mint_integration_version:2` adds pinned V10 read/claim/lineage support and rejects direct mint preparation with Use OpenSea. Omission keeps mint1/V9; source9 website and installed consumers retain their prior profiles pending explicit matching adoption. [Gas-aware claim planning](docs/CLAIM_PLANNING.md) prepares only the next exact simulated batch, preserving all remaining selections.
[Earnings checkpoint1](docs/EARNINGS_CHECKPOINTS.md) is historical profile6-only. Fresh7 supports raw replay or explicit reviewed checkpoint2 with raw exact-tree state and a complete rolling-day suffix; lineage/other readers and live workload qualification remain open. [OpenSea qualification](docs/MINT_INTEGRATION_QUALIFICATION.md) remains separate from ERC2981.

<a id="frontend-components"></a>

### 3. Frontend

[Popldemo](https://popldemo.0xwave.com) remains the existing simulation.
[Poplint](https://www.poplint.0xwave.com/) is the separately built current-contract
read/unsigned-review site. Its existing served build is not the new accounting7
consumer. [Website integration](docs/CURRENT_WEBSITE_PROFILE.md) and
[environment boundaries](docs/SITE_ENVIRONMENTS.md) explain the remaining work.
Missing configuration remains unavailable, never invented data. Anvil signing
and historical local journals remain unchanged.

## NFT lifecycle

Mint a dormant NFT through the reviewed [OpenSea phases](docs/OPENSEA_MINT.md), then activate with native ETH or fixed ZZZ. Activation and
growth minima default to $100/$5; governance may change future terms through
ProtocolPolicy, subject to stronger pool minima. Two independently
reviewed USD sources per priced asset must agree within 3%. Contribution loss
defaults to 2%, conversion 1%, maintenance 3%; governance ceilings are 10%, gas
separate. Approval alone changes no LP. Shares and artwork update only after
successful actual deployment and atomic accounting checks.

Fresh ordinary upkeep triggers at **85% of actual centre-to-boundary distance**
in ZZZ-in-ETH price space, corroborated by an independent reference. It requires
a 10-minute sampled window, four-minute checks, strict five-minute maximum
recorded gap, then fresh durable 1–5-minute service jitter. The initial 12-hour
hard minimum remains. Deliberate geometry changes apply after cooldown.
This is sampled evidence and modest scheduling uncertainty, not MEV immunity.

Single-position mode remains default. Optional hybrid replacement swaps only
enough to meet the pool's configured main floor (default60%, governed6000–9999bps),
with the complementary ceiling for one residual (default40%). The initial residual uses half the corresponding
side of the main, with a default full tick-spacing gap from spot. Governance may
change its width and positive spacing count within feasible geometry. These are placement-time limits, not continuously maintained weights.
Disabling mode keeps both legs accounted until a guarded atomic merge succeeds.
Paused governance can instead close only the residual into the same bucket's
attributed Vault idle, preserving the main and NFT shares. The new governance
`consolidateResidual` instead reinvests that idle into the SAME main, atomically
applies mode OFF and preserves shares/centre/rebalance clock. Guarded auto routing
and explicitly forced manifests remain separate. [Inputs](docs/OPERATOR_MANUAL.md#same-main-residual-consolidation). Existing emergency
rebalancing consolidates into one main; desired mode must be disabled separately
to keep future adjustments single. See [exact controls](docs/OPERATOR_MANUAL.md#portfolio-management-controls).

Management permissions are listed in the [authority guide](docs/ACCESS_PERMISSIONS.md).
Fresh custody5 makes terminal principal allocation/direct payout governance-only.
**Holders still claim their earned LP rewards and royalties.** They do not need
operator approval to claim; terminal principal payout is a separate operation.

## Revenue and claims

### LP trading revenue

Actual collection from both legs is combined before the fixed **80% individual /
10% equal activated collective / 5% compounding / 5% ZZZ buyback-burn** split.
Hourly harvesting is independent of swaps, compounding, buybacks and claims.
Claims do not themselves reinvest or burn. Per-NFT earnings, claimable balances
and previously claimed totals are distinct.

### NFT-sale royalties

Only actual receipts fund royalties. Revealed Commun/Rare/Legendary weights are
×1/×2/×3; eligibility begins on activation. Rarity never changes LP fee shares.
Unclaimed rights follow the NFT's current owner. Each admitted royalty currency
is claimed as received, with no swap or unwrap; currency outage isolation protects
earlier entitlements. ERC-2981 requests fees;
actual marketplace payment still requires qualification.

## Collection and artwork

The planned supply is 1,000 NFTs with exact rarity quotas 600/300/100. Prepared
artwork is assigned through the fixed draw; production verifiable randomness is
still unqualified. Colours and patterns are artwork traits independent of rarity.
LP evolution uses authenticated current value of both positions and attributed
idle/compound; it does not promise a permanent USD floor.

## Governance, custody and recovery

### Authority and configuration

The user is the human operator/governance authority. The automated keeper has a
separate limited capability. Sealing fixes implementations, parents and token
identity; reviewed routes, range widths, mode and many operating settings remain
configurable. See [change limits](docs/CHANGE_AND_RECOVERY.md).

### Recovery paths

Governance can move or park both LP legs, or irreversibly close and return actual
principal plus designated compound by NFT shares to current holders. Bounded
direct payout batches isolate rejecting receivers; earned rewards/buyback reserves
remain separate. No external custody address, token replacement or bridge exists.
Whole-collection replacement requires both legs closed and is blocked after exit.
Paused manual emergency rebalancing retains structural accounting but can bypass
explicit financial guards; governance can therefore cause near-total losses.

## Keeper and operating services

The worker defaults to dry run. Raw checks can occur during cooldown; paid
confirmation enrollment starts near eligibility to avoid hours of unnecessary
writes. Compounding waits for an in-range main below the adjustment threshold and no pending geometry change;
hourly harvesting remains independent. See [operations](docs/OPERATIONS.md),
[coordination](docs/KEEPER_COORDINATION.md) and [recovery](docs/KEEPER_RECOVERY.md).
Host restart, RPC inclusion, gas and writer/checker rollout remain qualification gates.

## Verification and release status

### Find the relevant evidence

| Need | Reference |
| --- | --- |
| Current capabilities, source pins and limits | [Feature/evidence reference](docs/IMPLEMENTATION_STATUS.md), [authority verification](reports/authority-audit-20261103/VERIFICATION.md), [whole-project supplement](reports/comprehensive-audit-20261104/REVIEW.md) |
| Historical findings applied to the current code | [Consolidated findings](docs/AUDIT_FINDINGS.md), [report map](reports/README.md) |
| Exact management action, inputs, stop/restart and recovery | [Operator manual](docs/OPERATOR_MANUAL.md), [callable reference](docs/CONTRACT_FUNCTIONS.md) |
| What remains and final approval | [Sole Todo](TODO.md), [roadmap](docs/ROADMAP.md), [release record](docs/RELEASE_CHECKLIST.md) |

Local checks, scoped source review and documentation reconciliation do not imply
published CI, target-chain operation, independent audit or production approval.

### Production approval

Actual independent feeds/routes/VRF, authorities, OpenSea, current-profile website
and services, target gas/strategy economics, operating recovery and independent
audit/remediation remain open. The [sole Todo](TODO.md) owns tasks and the
[release record](docs/RELEASE_CHECKLIST.md) owns final sign-off. No public deployment
or service rollout is authorized by source implementation/publication.

## Try the local browser test

Use the [historical local-stack guide](docs/LOCAL_TEST_STACK.md) for the preserved
versioned setup. Do not reset it to resemble newer source or infer a port is live.

## Development

### Setup and verification

Use the [supported environment](docs/DEVELOPMENT.md):

```bash
bash scripts/install-deps.sh
bash scripts/verify.sh
python3 scripts/sync-project-todo.py --check
```

Solidity remains pinned to 0.8.26/Cancun with the normal via-IR profile. Run useful
affected checks; preserve exact source pins before reusing earlier evidence.
Do not relax runtime/initcode gates or test filters to obtain a pass.

### Small-value experiments

The [$1 isolated rehearsal](docs/ONE_DOLLAR_REHEARSAL.md) uses separately authorized
test-deployment policy configuration; it does not patch fresh source or alter
production defaults, loss settings or rights. Local substitutes qualify no provider.

### Keep project records consistent

Update [task ledger](docs/project-todo.json), generated Todo, features/evidence,
operator/callable procedures and context together using the
[maintenance procedure](docs/TODO_WORKFLOW.md). Publication and deployment are separate.

Fresh royalty4 retains the [one-hour sale-close activation window](docs/ROYALTY_LAUNCH_WINDOW.md)
and adds [exact-unit allocation](docs/EXACT_ROYALTY_ALLOCATION.md): GCD-normalized rarity
weights, deterministic rotating indivisible units, and no allocated rounding
remainder after all eligible claims. Initial holding, prefunds, zero participants,
unsupported currencies and pathological-token failures remain distinct. CanonicalV9
rejects older peers. Actual OpenSea, gas/workloads and independent approval remain open.
