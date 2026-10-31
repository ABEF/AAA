# ZZZ Collection - Proof of Permanent Liquidity (PoPL)

PoPL connects transferable ERC-721 NFTs to vault-managed ETH/ZZZ liquidity.
Activation attaches an independently accounted LP share and unlocks funded LP
fees plus rarity-weighted NFT-sale royalties. Holders cannot redeem principal
during normal operation. Governance can permanently end LP activity and return
actual ETH + ZZZ to current NFT owners; transfers, old rewards and royalties remain.

**Undeployed source candidate; production NOT APPROVED.** [Bounded operating policy](docs/ADAPTABLE_POLICY.md) adds future-only mint/entry terms, planned drained VRF rotation, scoped idle/gas controls and per-pool main/gap controls in [accounting6](docs/POSITION_V6.md). The prior
[manual-operation audit](reports/manual-operations-20261031/REVIEW.md) documents
exact controls, ordered inputs and recovery, and adds offline review preparation.
The prior [source audit](reports/day-audit-20261031/REVIEW.md) fixes physical-read
availability, activation bindings and ordinary replacement activity. Source changes do not update existing
Anvil contracts, journals, workers or websites. Public signing remains disabled.

## Project navigation

| Purpose | Start here |
| --- | --- |
| Remaining work | **[Sole Project Todo](TODO.md)**, beside the [feature/evidence reference](docs/IMPLEMENTATION_STATUS.md) |
| Operate the protocol | **[Operator manual and management procedures](docs/OPERATOR_MANUAL.md)**; [callable inputs, outputs and permissions](docs/CONTRACT_FUNCTIONS.md) |
| Current source and compatibility | [Accounting6 profile](docs/POSITION_V6.md), [architecture](docs/ARCHITECTURE.md), [component map](docs/COMPONENT_STATUS.md) |
| LP policy and protection | [Execution policy](docs/LP_EXECUTION_POLICY.md), [keeper safeguards](docs/KEEPER_SAFEGUARDS.md), [two-source pricing](docs/PRICE_SECURITY.md) |
| Verify or approve release | [Current policy evidence](reports/adaptable-policy-20261031/VERIFICATION.md), [release approval record](docs/RELEASE_CHECKLIST.md), [production preflight](docs/PRODUCTION_PREFLIGHT.md) |
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
| [NFT](src/ZZZNFT.sol), [metadata](src/ZZZNFTMetadata.sol) | Transferable ownership, fixed-design random assignment and artwork evolution from authenticated aggregate LP value. |
| [Activation Entry](src/ZZZActivationEntry.sol), [Registry](src/ZZZPoolRegistry.sol) | Atomic native ETH/fixed-ZZZ contributions; one admitted contribution pool at a time. |
| [Vault](src/ZZZVault.sol), [pricing companion](src/ZZZContributionPricing.sol) | Own both physical LP NFTs, record per-NFT shares and prove actual marginal deployed LP before issuing shares. |
| [Liquidity Manager](src/ZZZLiquidityManager.sol), [typed position child](src/ZZZLPPositionExecutor.sol) | Mint/increase, harvest and close a main plus at most one residual. The child has typed actions and fixed Vault recipients, not a generic withdrawal path. |
| [LP Balancer](src/ZZZLPBalancer.sol), [math child](src/ZZZLPBalanceMath.sol) | Compare bounded reviewed swap venues using actual-core sizing; swap entrant budgets or captured maintenance inventory within execution limits. |
| [Strategy](src/ZZZStrategy.sol), [portfolio policy](src/ZZZPortfolioPolicy.sol), [confirmation](src/ZZZRebalanceConfirmation.sol) | Manual range/mode settings, exact human-price threshold, sampled confirmation and reviewed readiness. |
| [Budget](src/ZZZMigrationBudget.sol), [Oracle](src/ZZZOracle.sol) | Fixed transaction valuations, independent USD sources, principal/reserve separation, operation and caller loss floors, compound timing and actual main-floor proof. |
| [FeeController](src/ZZZFeeController.sol), [Rewards](src/ZZZRewards.sol), [Membership](src/ZZZMembership.sol) | Allocate actual harvested fees 80/10/5/5; individual shares and equal activated-NFT collective rights. |
| [RoyaltyRewards](src/ZZZRoyaltyRewards.sol), [converter](src/ZZZRoyaltyConverter.sol), [ClaimRouter](src/ZZZClaimRouter.sol) | Separate received royalties, outage isolation, guarded conversion and current-owner claims. |
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
[Unsigned preparation](docs/ACTIVATION_PREPARATION.md) checks exact assets,
routes, prices, policy, allowance and calldata; it does not sign public transactions.
Fresh inventory is schema8; historical profiles remain separate.

<a id="frontend-components"></a>

### 3. Frontend

[Popldemo](https://popldemo.0xwave.com) remains the existing simulation.
[Poplint](https://www.poplint.0xwave.com/) is the separately built current-contract
read/unsigned-review site. Its existing served build is not the new accounting6
consumer. [Website integration](docs/CURRENT_WEBSITE_PROFILE.md) and
[environment boundaries](docs/SITE_ENVIRONMENTS.md) explain the remaining work.
Missing configuration remains unavailable, never invented data. Anvil signing
and historical local journals remain unchanged.

## NFT lifecycle

Mint a dormant NFT, then activate with native ETH or fixed ZZZ. Activation and
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
attributed Vault idle, preserving the main and NFT shares. Existing emergency
rebalancing consolidates into one main; desired mode must be disabled separately
to keep future adjustments single. See [exact controls](docs/OPERATOR_MANUAL.md#portfolio-management-controls).

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
Unclaimed rights follow the NFT's current owner. Currency failure isolation and
guarded batch conversion preserve earlier entitlements. ERC-2981 requests fees;
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

The [current verification record](reports/adaptable-policy-20261031/VERIFICATION.md)
separates actual local v4 execution, policy/accounting and keeper/API checks,
failed attempts, source stages and normal compiler limits. Older reports retain
their original pins; their counts are not a current full-regression pass.

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
