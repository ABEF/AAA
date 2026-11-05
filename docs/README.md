# Documentation map

Reviewed2026-11-05. [README](../README.md) explains the project; [sole Todo](../TODO.md)
owns tasks and [feature/evidence reference](IMPLEMENTATION_STATUS.md) owns source
capabilities. **Undeployed; production NOT APPROVED.**

Start with [current profile identities](POSITION_V6.md), [features](IMPLEMENTATION_STATUS.md),
[findings](AUDIT_FINDINGS.md) and the maintained [Operator manual](OPERATOR_MANUAL.md).
Its [short call tables](OPERATOR_MANUAL.md#operator-call-tables) cover every current
ABI function, with exact inputs, examples and explanations of at most five words.
The [full function reference](CONTRACT_FUNCTIONS.md) owns outputs and detailed
caller/value notes. These are documentation templates, never transaction approval.

Current source is accounting6/custody5/portfolio2/direct Entry3 plus royalty
settlement3/recovery2, with original-currency claims and no royalty converter. Historical profiles, research, reports and actual running sites retain
their original meaning. Use [the report map](../reports/README.md) for exact source
scope; a historical audit is not a current operating procedure or release sign-off.

## 1. Smart contracts

| Topic | Current guide |
| --- | --- |
| Architecture and module jobs | [Architecture](ARCHITECTURE.md), [components](COMPONENT_STATUS.md), [current profile6](POSITION_V6.md), [simplified scope](SIMPLIFIED_RELEASE.md) |
| Economic rights and fee meaning | [Economics](ECONOMICS.md), [NFT traits/reveal](NFT_METADATA.md), [royalty settlement](ROYALTY_SETTLEMENT.md), [claims](CLAIM_ROUTER.md) |
| Contribution and actual added LP | [Direct Entry and routing](ACTIVATION_ENTRY.md), [minimums](CONTRIBUTION_MINIMUMS.md), [dynamic valuation](DYNAMIC_LIQUIDITY.md) |
| Prices and conversion | [Two-source security](PRICE_SECURITY.md), [optional Pyth reader](PYTH_PRICE_SOURCE.md), [typed routes](TYPED_V4_ROUTES.md), [ETH fee settlement](LP_ETH_SETTLEMENT.md) |
| LP execution and upkeep | [Policy3/Budget4, LP routing2 and confirmation3](LP_EXECUTION_POLICY.md); bounded reviewed venues, atomic sizing, entrant isolation and sampled85%-threshold confirmation. Distinguish source implementation from live operating qualification. |
| Pool, ranges and retained idle | [Selected pool/admission/settlement](POOL_SELECTION.md), [range policy](RANGE_POLICY_UPDATES.md), [idle ownership](IDLE_AND_DUST.md), [execution limits](EXECUTION_LOSS_POLICY.md), [additional loss after known fees](EXECUTION_QUALITY.md) |
| Caller permissions | [Authority map](ACCESS_PERMISSIONS.md), [source-bound review](../reports/authority-audit-20261103/REVIEW.md) |
| Governance and change limits | [Direct governance](GOVERNANCE.md), [post-seal settings](POST_SEAL_POLICY.md), [change/recovery matrix](CHANGE_AND_RECOVERY.md), [trust boundaries](ARCHITECTURE_EVOLUTION.md) |
| Movement and recovery | [Same-pair movement](GOVERNED_CUSTODY_HANDOFF.md), [parking](CUSTODY_PARKING.md), [collective holder return](HOLDER_COLLECTIVE_EXIT.md), [maintenance/preparation safety](MIGRATION_SAFETY.md), [pre-exit same-chain V6 handoff](CANONICAL_HANDOFF.md), [holder preflight](HOLDER_PREFLIGHT.md) |
| Callable inputs/outputs/permissions | [Short operator tables](OPERATOR_MANUAL.md#operator-call-tables), [full source-bound function reference](CONTRACT_FUNCTIONS.md) |

Manual paused LP recovery: [emergency procedure](EMERGENCY_REBALANCE.md),
[independent confirmation policy](LP_EXECUTION_POLICY.md#requested-rebalance-confirmation-buffer),
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
| Website read/review compatibility | [Served current3 and fresh contract gap](CURRENT_WEBSITE_PROFILE.md), [historical native2](NATIVE_WEBSITE_PROFILE.md), [website/API configuration](DEPLOYMENT_WEBSITE.md). Fresh accounting6/custody5 backend reads/unsigned preparation are implemented in source with direct Entry3; matching website consumption remains open; public signing remains disabled. |
| Disposable local rehearsals | [Test stack](LOCAL_TEST_STACK.md), [local website](LOCAL_WEBSITE.md), [local API rehearsal](LOCAL_API_REHEARSAL.md), [browser wallets](BROWSER_WALLET.md). Commands are explicitly historical/versioned; no claim that a saved port/session is running now. |
| Small-value/integration research | [$1 governed rehearsal](ONE_DOLLAR_REHEARSAL.md), [integration campaign boundaries](INTEGRATION_CAMPAIGN.md). Test substitutes never relax production minima or qualify real services. |

The [whole-project audit brief](WHOLE_PROJECT_AUDIT_PROMPT.md) is the maintained
starting point for an audit. Earlier third-pass and passive-inventory/implementation
plans are exact-Git historical pointers. They do not override current source,
operator procedures or the sole Todo.

## Release, security and upkeep

| Topic | Guide |
| --- | --- |
| Exact-release decision and sequence | [Approval record](RELEASE_CHECKLIST.md), [roadmap](ROADMAP.md), [sole Todo maintenance](TODO_WORKFLOW.md) |
| Actual service/deployment qualification | [Service decisions](PRODUCTION_SERVICES.md), [address inventory](DEPLOYMENT_ADDRESSES.md), [versioned preflight](PRODUCTION_PREFLIGHT.md), [RPC probes](RPC_PREPARATION_QUALIFICATION.md) |
| Minting, randomness and content hosting | [OpenSea/VRF qualification](MINT_INTEGRATION_QUALIFICATION.md), [artwork bundle/publication](ARTWORK_PUBLICATION.md) |
| Audit and development | [Security model](SECURITY.md), [seven audit workstreams](SECURITY_AUDIT_PLAN.md), [frozen review export](FROZEN_REVIEW_BUNDLE.md), [development](DEVELOPMENT.md) |
| Current consolidated findings | [Mechanisms, historical corrections and remaining limits](AUDIT_FINDINGS.md); task status stays in the sole Todo. |
| Current state and evidence | [Project context](../PROJECT_CONTEXT.md), [resume instructions](WORK_HANDOFF.md), [report index](../reports/README.md), [current royalty-source evidence](../reports/royalties-in-kind-20261105/VERIFICATION.md) and [source-scoped historical catalogue](../reports/project-consolidation-20261103/REPORT_CATALOG.md) |

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

## Current adaptable policy

[Accounting6 profile](POSITION_V6.md) and [bounded post-seal controls](ADAPTABLE_POLICY.md)
replace fresh accounting5 assumptions. [Operator inputs](OPERATOR_MANUAL.md#future-operating-settings)
and [callable reference](CONTRACT_FUNCTIONS.md) describe exact procedures. Existing
runtimes, source-scoped evidence and served websites retain their own boundaries.

[Royalty launch window and currency capacity](ROYALTY_LAUNCH_WINDOW.md) owns sale end,1-hour initial cohort, locked receipts, allocate-all and reviewed expansion.
