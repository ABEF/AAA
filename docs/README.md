# Documentation map

Reviewed2026-10-27. [Root README](../README.md) introduces PoPL and its code.
[TODO.md](../TODO.md) is the only task/status list; [feature reference](IMPLEMENTATION_STATUS.md)
states what exists and what was verified. **Undeployed; production NOT APPROVED.**
Current guides below describe accounting3/directgovernance2/fee1/localV4.
Historical reports and explicitly legacy local profiles retain their own semantics.

## 1. Smart contracts

| Topic | Current guide |
| --- | --- |
| Architecture and module jobs | [Architecture](ARCHITECTURE.md), [components](COMPONENT_STATUS.md), [local profile](POSITION_V3.md), [simplified scope](SIMPLIFIED_RELEASE.md) |
| Economic rights and fee meaning | [Economics](ECONOMICS.md), [NFT traits/reveal](NFT_METADATA.md), [royalty settlement](ROYALTY_SETTLEMENT.md), [claims](CLAIM_ROUTER.md) |
| Contribution and actual added LP | [Atomic Entry](ACTIVATION_ENTRY.md), [routing](ACTIVATION_ROUTING.md), [minimums](CONTRIBUTION_MINIMUMS.md), [dynamic valuation](DYNAMIC_LIQUIDITY.md) |
| Prices and conversion | [Two-source security](PRICE_SECURITY.md), [optional Pyth reader](PYTH_PRICE_SOURCE.md), [typed routes](TYPED_V4_ROUTES.md), [ETH fee settlement](LP_ETH_SETTLEMENT.md) |
| Pool, ranges and retained idle | [Selected pool/admission/settlement](POOL_SELECTION.md), [range policy](RANGE_POLICY_UPDATES.md), [idle ownership](IDLE_AND_DUST.md), [execution limits](EXECUTION_LOSS_POLICY.md) |
| Governance and change limits | [Direct governance](GOVERNANCE.md), [post-seal settings](POST_SEAL_POLICY.md), [change/recovery matrix](CHANGE_AND_RECOVERY.md), [trust boundaries](ARCHITECTURE_EVOLUTION.md) |
| Movement and recovery | [Governed external custody](GOVERNED_CUSTODY_HANDOFF.md), [parking](CUSTODY_PARKING.md), [maintenance/preparation safety](MIGRATION_SAFETY.md), [same-chain collection handoff](CANONICAL_HANDOFF.md), [holder preflight](HOLDER_PREFLIGHT.md) |
| Callable inputs/outputs/permissions | [Generated source-bound function reference](CONTRACT_FUNCTIONS.md) |

## 2. Backend and operations

| Topic | Current guide |
| --- | --- |
| Confirmed reads and lifecycle | [Read API](FRONTEND_API.md), [lifecycle](FRONTEND_LIFECYCLE.md), [collection](COLLECTION_READS.md) |
| Rewards and lifetime history | [Earnings](EARNINGS_HISTORY.md), [royalty reporting](ROYALTY_REPORTING.md), [raw claim history](FRONTEND_HISTORY.md), [same-chain lineage](FRONTEND_LINEAGE.md) |
| Unsigned user transactions | [Activation preparation](ACTIVATION_PREPARATION.md), [mint/claim preparation](FRONTEND_TRANSACTIONS.md) |
| Ingress, concurrency and storage | [HTTP admission](API_INGRESS.md), [concurrent services](CONCURRENT_SERVICES.md), [indexer recovery](INDEXER_RECOVERY.md), [independent raw-history audit](HISTORY_AUDIT.md) |
| Management and keeper | [Operator manual](OPERATOR_MANUAL.md), [service operations](OPERATIONS.md), [keeper recovery](KEEPER_RECOVERY.md), [operating rehearsals](KEEPER_REHEARSALS.md) |

## 3. Frontend and isolated local profiles

| Topic | Scope |
| --- | --- |
| Demo versus integration release targets | [Environment map](SITE_ENVIRONMENTS.md): popldemo remains the existing simulation; poplint has its own current3 build/root/configuration and no demo fallback. |
| Published website read/review profile | [Native website boundary](NATIVE_WEBSITE_PROFILE.md), [website/API configuration](DEPLOYMENT_WEBSITE.md). Published native2 is not current3 acceptance; public signing remains disabled. |
| Disposable local rehearsals | [Test stack](LOCAL_TEST_STACK.md), [local website](LOCAL_WEBSITE.md), [local API rehearsal](LOCAL_API_REHEARSAL.md), [browser wallets](BROWSER_WALLET.md). Commands are explicitly historical/versioned; no claim that a saved port/session is running now. |
| Small-value/integration research | [$1 local build](ONE_DOLLAR_REHEARSAL.md), [integration campaign boundaries](INTEGRATION_CAMPAIGN.md). Test substitutes never relax production minima or qualify real services. |

## Release, security and upkeep

| Topic | Guide |
| --- | --- |
| Exact-release decision and sequence | [Approval record](RELEASE_CHECKLIST.md), [roadmap](ROADMAP.md), [sole Todo maintenance](TODO_WORKFLOW.md) |
| Actual service/deployment qualification | [Service decisions](PRODUCTION_SERVICES.md), [address inventory](DEPLOYMENT_ADDRESSES.md), [schema5 preflight](PRODUCTION_PREFLIGHT.md), [RPC probes](RPC_PREPARATION_QUALIFICATION.md) |
| Minting, randomness and content hosting | [OpenSea/VRF qualification](MINT_INTEGRATION_QUALIFICATION.md), [artwork bundle/publication](ARTWORK_PUBLICATION.md) |
| Audit and development | [Security model](SECURITY.md), [seven audit workstreams](SECURITY_AUDIT_PLAN.md), [frozen review export](FROZEN_REVIEW_BUNDLE.md), [development](DEVELOPMENT.md) |
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
