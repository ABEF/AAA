# Documentation map

[Historical report reconciliation](../reports/historical-reconciliation-20261029/REVIEW.md)
records current fixes and an explicit incomplete per-finding ledger. It does not
reclassify historical failures, old deployments or unqualified services as passes.

[Keeper coordination and operation review](KEEPER_COORDINATION.md): service-only compound waits,
proved internal harvest clocks, read-only LP diagnostics and corrected actual-ABI
reservation observation. No source publication implies operating rollout.

Reviewed2026-10-29. [Root README](../README.md) introduces PoPL and its code.
[TODO.md](../TODO.md) is the only task/status list; [feature reference](IMPLEMENTATION_STATUS.md)
states what exists and what was verified. **Undeployed; production NOT APPROVED.**
Current guides describe accounting4/directgovernance2/fee1/custody3/holder-exitV5.
Historical reports and explicitly legacy local profiles retain their own semantics.

[Current whole-project audit execution](../reports/whole-project-execution-20261029/REVIEW.md) includes
two prompt challenges, exact handwritten/dependency body coverage, keeper/backend/
tooling/artwork repairs and completed callable outputs. Its scoped verification
and unresolved live/independent gates supersede no historical report bytes.

[Normal-operation reassessment](../reports/normal-operation-design-20261029/REVIEW.md) maps contribution/idle/fees,
all service clocks, compound asymmetry, harvest coordination and proposed
non-signing diagnostics. It records design choices; no new timer/planner or
financial policy is implemented by this assessment.

[Operational reliability code follow-up](../reports/operational-reliability-20261029/REVIEW.md) fixes
confirmed history/checkpoints/management/readiness/preflight/tooling defects;
[verification](../reports/operational-reliability-20261029/VERIFICATION.md) separates focused passes,
local metadata checks and unchanged Solidity/build reuse.

## 1. Smart contracts

| Topic | Current guide |
| --- | --- |
| Architecture and module jobs | [Architecture](ARCHITECTURE.md), [components](COMPONENT_STATUS.md), [current profile](POSITION_V4.md), [simplified scope](SIMPLIFIED_RELEASE.md) |
| Economic rights and fee meaning | [Economics](ECONOMICS.md), [NFT traits/reveal](NFT_METADATA.md), [royalty settlement](ROYALTY_SETTLEMENT.md), [claims](CLAIM_ROUTER.md) |
| Contribution and actual added LP | [Atomic Entry](ACTIVATION_ENTRY.md), [routing](ACTIVATION_ROUTING.md), [minimums](CONTRIBUTION_MINIMUMS.md), [dynamic valuation](DYNAMIC_LIQUIDITY.md) |
| Prices and conversion | [Two-source security](PRICE_SECURITY.md), [optional Pyth reader](PYTH_PRICE_SOURCE.md), [typed routes](TYPED_V4_ROUTES.md), [ETH fee settlement](LP_ETH_SETTLEMENT.md) |
| LP execution and upkeep | [Policy2/Budget3, LP routing1 and confirmation2](LP_EXECUTION_POLICY.md); bounded reviewed venues, atomic sizing, entrant isolation and sampled range-exit confirmation. Distinguish source implementation from live operating qualification. |
| Pool, ranges and retained idle | [Selected pool/admission/settlement](POOL_SELECTION.md), [range policy](RANGE_POLICY_UPDATES.md), [idle ownership](IDLE_AND_DUST.md), [execution limits](EXECUTION_LOSS_POLICY.md), [additional loss after known fees](EXECUTION_QUALITY.md) |
| Governance and change limits | [Direct governance](GOVERNANCE.md), [post-seal settings](POST_SEAL_POLICY.md), [change/recovery matrix](CHANGE_AND_RECOVERY.md), [trust boundaries](ARCHITECTURE_EVOLUTION.md) |
| Movement and recovery | [Same-pair movement](GOVERNED_CUSTODY_HANDOFF.md), [parking](CUSTODY_PARKING.md), [collective holder return](HOLDER_COLLECTIVE_EXIT.md), [maintenance/preparation safety](MIGRATION_SAFETY.md), [pre-exit same-chain V5 handoff](CANONICAL_HANDOFF.md), [holder preflight](HOLDER_PREFLIGHT.md) |
| Callable inputs/outputs/permissions | [Generated source-bound function reference](CONTRACT_FUNCTIONS.md) |

Manual paused LP recovery: [emergency procedure](EMERGENCY_REBALANCE.md),
[independent confirmation policy](LP_EXECUTION_POLICY.md#independent-reference-in-confirmation2),
[new scoped verification](../reports/independent-rebalance-20261029/VERIFICATION.md).
Governance may bypass financial protections explicitly; this is an accepted
authority risk and does not grant a keeper fallback or deployment approval.

## 2. Backend and operations

| Topic | Current guide |
| --- | --- |
| Confirmed reads and lifecycle | [Read API](FRONTEND_API.md), [lifecycle](FRONTEND_LIFECYCLE.md), [collection](COLLECTION_READS.md) |
| Rewards and lifetime history | [Earnings](EARNINGS_HISTORY.md), [royalty reporting](ROYALTY_REPORTING.md), [raw claim history](FRONTEND_HISTORY.md), [same-chain lineage](FRONTEND_LINEAGE.md) |
| Unsigned user transactions | [Activation preparation](ACTIVATION_PREPARATION.md), [mint/claim preparation](FRONTEND_TRANSACTIONS.md) |
| Ingress, concurrency and storage | [HTTP admission](API_INGRESS.md), [concurrent services](CONCURRENT_SERVICES.md), [indexer recovery](INDEXER_RECOVERY.md), [independent raw-history audit](HISTORY_AUDIT.md) |
| Keeper safeguards | [Implemented protection inventory](KEEPER_SAFEGUARDS.md) - distinguish contract-enforced rules, service controls and remaining risks. |
| Management and keeper | [Operator manual](OPERATOR_MANUAL.md), [service operations](OPERATIONS.md), [keeper recovery](KEEPER_RECOVERY.md), [operating rehearsals](KEEPER_REHEARSALS.md) |

## 3. Frontend and isolated local profiles

| Topic | Scope |
| --- | --- |
| Demo versus integration release targets | [Environment map](SITE_ENVIRONMENTS.md): popldemo remains the existing simulation; served poplint has its own unconfigured current3 build/root and no demo fallback. |
| Website read/review compatibility | [Served current3 and fresh4 gap](CURRENT_WEBSITE_PROFILE.md), [historical native2](NATIVE_WEBSITE_PROFILE.md), [website/API configuration](DEPLOYMENT_WEBSITE.md). Fresh accounting4/custody3/V5 frontend integration is not implemented; public signing remains disabled. |
| Disposable local rehearsals | [Test stack](LOCAL_TEST_STACK.md), [local website](LOCAL_WEBSITE.md), [local API rehearsal](LOCAL_API_REHEARSAL.md), [browser wallets](BROWSER_WALLET.md). Commands are explicitly historical/versioned; no claim that a saved port/session is running now. |
| Small-value/integration research | [$1 local build](ONE_DOLLAR_REHEARSAL.md), [integration campaign boundaries](INTEGRATION_CAMPAIGN.md). Test substitutes never relax production minima or qualify real services. |

The [whole-project audit brief](WHOLE_PROJECT_AUDIT_PROMPT.md),
[two prompt challenges](../reports/whole-project-audit-20261029/PROMPT_REVIEW.md)
and [results](../reports/whole-project-audit-20261029/REVIEW.md) record the broader
review and later four-minute service-cadence decision. The earlier
[third-pass brief](THIRD_PASS_AUDIT_PROMPT.md) and
[results](../reports/third-pass-20261028/REVIEW.md) retain their frozen
October26-28 scope. Both distinguish actual repairs
from accepted limits and externally blocked qualification.

## Release, security and upkeep

| Topic | Guide |
| --- | --- |
| Exact-release decision and sequence | [Approval record](RELEASE_CHECKLIST.md), [roadmap](ROADMAP.md), [sole Todo maintenance](TODO_WORKFLOW.md) |
| Actual service/deployment qualification | [Service decisions](PRODUCTION_SERVICES.md), [address inventory](DEPLOYMENT_ADDRESSES.md), [versioned preflight](PRODUCTION_PREFLIGHT.md), [RPC probes](RPC_PREPARATION_QUALIFICATION.md) |
| Minting, randomness and content hosting | [OpenSea/VRF qualification](MINT_INTEGRATION_QUALIFICATION.md), [artwork bundle/publication](ARTWORK_PUBLICATION.md) |
| Audit and development | [Security model](SECURITY.md), [seven audit workstreams](SECURITY_AUDIT_PLAN.md), [frozen review export](FROZEN_REVIEW_BUNDLE.md), [development](DEVELOPMENT.md) |
| Latest confirmation follow-up | [Review](../reports/confirmation-followup-20261028/REVIEW.md), [verification](../reports/confirmation-followup-20261028/VERIFICATION.md): keeper resets, physical LP/pool binding, policy health and custody totals; no Solidity or operating rollout. |
| Current state and evidence | [Project context](../PROJECT_CONTEXT.md), [resume instructions](WORK_HANDOFF.md), [report index](../reports/README.md), [latest fee-integrity evidence](../reports/backend-remediation-20261026/VERIFICATION.md) |

## Historical references

[Bridge onboarding](BRIDGE_ONBOARDING.md), [creator inboxes](EXTERNAL_REWARDS.md),
[creator-revenue measurement](REVENUE_SHARE.md), [Pons pool](ROBINHOOD_POOL.md),
[different-pair executor](PAIR_MIGRATION.md), [cross-chain canonical proposal](CANONICAL_MIGRATION_DESIGN.md)
and [v0.2 audit](AUDIT.md) are short stable historical pointers. Their full text
is available at the exact linked Git revision. They are not current functions,
launch requirements or operator instructions. [Changelog](CHANGELOG.md) is a
historical chronology; audit/test receipts in reports keep original bytes and scope.

Redundant product, source-asset, native-adapter, OpenSea-summary and early-reference
pages are merged into their owning guides; removal details and old Git paths are
recorded in [documentation cleanup](../reports/documentation-cleanup-20261026/README.md).
Existing actual dependency/package pins and [primary-source review](../reports/full-audit-20261025/UPSTREAM.md)
take precedence over early unpinned upstream links.
