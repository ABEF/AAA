# Documentation map

| Question | Authoritative document |
| --- | --- |
| What is the project and its stack? | [README](../README.md), [architecture](ARCHITECTURE.md) |
| What is currently verified or still unqualified? | [One current review](../reports/CURRENT_REVIEW.md) |
| Which findings and accepted limits remain? | [One findings register](AUDIT_FINDINGS.md) |
| What should we work on next? | [Sole Todo](../TODO.md), [qualification roadmap](ROADMAP.md) |
| What is implemented? | [Capability catalog](IMPLEMENTATION_STATUS.md) |
| How do I operate, pause, force, recover or change settings? | [Operator manual](OPERATOR_MANUAL.md) |
| Which functions can be called, with which inputs and outputs? | [Generated function reference](CONTRACT_FUNCTIONS.md), [short call tables](OPERATOR_MANUAL.md#operator-call-tables) |
| Is a release approved? | [Release decision record](RELEASE_CHECKLIST.md) |

Implementation, source-scoped verification, installed-service adoption and
production approval are different. Public signing remains disabled; historical
codecs and journals retain their exact identities. Use the owning guide below
for procedures rather than copying instructions out of an old report.

## 1. Smart contracts

| Topic | Current guide |
| --- | --- |
| Architecture and module jobs | [Architecture](ARCHITECTURE.md), [components](ARCHITECTURE.md#component-responsibilities), [current profile7](POSITION_V7.md), [simplified scope](SIMPLIFIED_RELEASE.md), [fixed factory data storage](FACTORY_CODE_STORAGE.md) |
| Exact-unit LP upgrade | [Integrated whole-unit LP books, claims and unchanged raw LP domain inside V10](EXACT_LP_ALLOCATION.md); original V9 evidence and earlier6/V8 readers remain separately scoped. |
| Economic rights and fee meaning | [Economics](ECONOMICS.md), [NFT traits/reveal](NFT_METADATA.md), [royalty settlement](ROYALTY_SETTLEMENT.md), [exact-unit allocation](EXACT_ROYALTY_ALLOCATION.md), [claims](CLAIM_ROUTER.md) |
| Contribution and actual added LP | [Direct Entry and routing](ACTIVATION_ENTRY.md), [minimums](CONTRIBUTION_MINIMUMS.md), [dynamic valuation](DYNAMIC_LIQUIDITY.md) |
| Prices and conversion | [Two-source security](PRICE_SECURITY.md), [optional Pyth reader](PYTH_PRICE_SOURCE.md), [typed routes](TYPED_V4_ROUTES.md), [ETH fee settlement](LP_ETH_SETTLEMENT.md) |
| LP execution and upkeep | [Policy3/Budget4, optional LP routing3 and confirmation3](LP_EXECUTION_POLICY.md); bounded reviewed venues, atomic sizing, entrant isolation and sampled85%-threshold confirmation. Distinguish source implementation from live operating qualification. |
| Pool, ranges and retained idle | [Selected pool/admission/settlement](POOL_SELECTION.md), [range policy](RANGE_POLICY_UPDATES.md), [idle ownership](IDLE_AND_DUST.md), [execution limits](EXECUTION_LOSS_POLICY.md), [additional loss after known fees](EXECUTION_QUALITY.md) |
| Caller permissions | [Authority map](ACCESS_PERMISSIONS.md), [source-bound review](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/authority-audit-20261103/REVIEW.md) |
| Governance and change limits | [Direct governance](GOVERNANCE.md), [post-seal settings](POST_SEAL_POLICY.md), [change/recovery matrix](CHANGE_AND_RECOVERY.md), [trust boundaries](ARCHITECTURE_EVOLUTION.md), [offline deployment sequence](DEPLOYMENT_SEQUENCE.md) |
| Movement and recovery | [Same-pair movement](GOVERNED_CUSTODY_HANDOFF.md), [parking](CUSTODY_PARKING.md), [collective holder return](HOLDER_COLLECTIVE_EXIT.md), [maintenance/preparation safety](MIGRATION_SAFETY.md), [pre-exit same-chain V10 handoff](CANONICAL_HANDOFF.md), [holder preflight](HOLDER_PREFLIGHT.md) |
| Callable inputs/outputs/permissions | [Short operator tables](OPERATOR_MANUAL.md#operator-call-tables), [full source-bound function reference](CONTRACT_FUNCTIONS.md) |

Manual paused LP recovery: [emergency procedure](EMERGENCY_REBALANCE.md),
[independent confirmation policy](LP_EXECUTION_POLICY.md#requested-rebalance-confirmation-buffer),
[new scoped verification](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/independent-rebalance-20261029/VERIFICATION.md).
Governance may bypass financial protections explicitly; this is an accepted
authority risk and does not grant a keeper fallback or deployment approval.

## 2. Backend and operations

| Topic | Current guide |
| --- | --- |
| Confirmed reads and lifecycle | [Read API](FRONTEND_API.md), [lifecycle](FRONTEND_LIFECYCLE.md), [collection](COLLECTION_READS.md) |
| Rewards and lifetime history | [Reviewed checkpoint1/2/3](EARNINGS_CHECKPOINTS.md), [Earnings](EARNINGS_HISTORY.md), [royalty reporting](ROYALTY_REPORTING.md), [raw claim history](FRONTEND_HISTORY.md), [same-chain lineage](FRONTEND_LINEAGE.md), [offline history backup/restore](HISTORY_RECOVERY.md) |
| Unsigned user transactions | [Activation preparation](ACTIVATION_PREPARATION.md), [mint/claim preparation](FRONTEND_TRANSACTIONS.md), [gas-aware next claim batch](CLAIM_PLANNING.md) |
| Ingress, concurrency and storage | [HTTP admission](API_INGRESS.md), [concurrent services](CONCURRENT_SERVICES.md), [indexer recovery](INDEXER_RECOVERY.md), [independent raw-history audit](HISTORY_AUDIT.md) |
| Keeper safeguards | [Implemented protection inventory](KEEPER_SAFEGUARDS.md) - distinguish contract-enforced rules, service controls and remaining risks. |
| Management and keeper | [Typed unsigned manual LP preparation](MANUAL_LP_PREPARATION.md), [Operator manual](OPERATOR_MANUAL.md), [service operations](OPERATIONS.md), [keeper recovery](KEEPER_RECOVERY.md), [operating rehearsals](KEEPER_REHEARSALS.md) |

## 3. Frontend and isolated local profiles

| Topic | Scope |
| --- | --- |
| Demo versus integration release targets | [Environment map](SITE_ENVIRONMENTS.md): popldemo remains the existing simulation; served poplint has its own unconfigured current3 build/root and no demo fallback. |
| Website read/review compatibility | [Served current3 and fresh contract gap](CURRENT_WEBSITE_PROFILE.md), [historical native2](NATIVE_WEBSITE_PROFILE.md), [website/API configuration](DEPLOYMENT_WEBSITE.md). The local [source9/V9 consumer](SOURCE9_WEBSITE_PROFILE.md) implements accounting7/custody5 reads and unsigned Entry3 reviews. The separate [source10/schema5/mint2/V10 consumer](SOURCE10_WEBSITE_PROFILE.md) is implemented locally; actual service/site qualification and rollout remain open; public signing remains disabled. |
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
| Audit and development | [Security model](SECURITY.md), [seven audit workstreams](SECURITY_AUDIT_PLAN.md), [schema4 frozen review export, with original1/2/3 verification](FROZEN_REVIEW_BUNDLE.md), [development](DEVELOPMENT.md) |
| Current consolidated findings | [Mechanisms, historical corrections and remaining limits](AUDIT_FINDINGS.md); task status stays in the sole Todo. |
| Current state and evidence | [Consolidated review](../reports/CURRENT_REVIEW.md), [findings](AUDIT_FINDINGS.md) and [historical retrieval manifest](../evidence/documentation-consolidation-20261127/RETIRED_DOCUMENTS.json) |

## Evidence and documentation maintenance

The sole [current report](../reports/CURRENT_REVIEW.md#evidence-and-history)
explains evidence reuse and historical retrieval. Retired narratives and
superseded guides remain accessible at the
[pre-consolidation Git revision](https://github.com/ABEF/AAA/tree/fdd599c7698d0e1c0709a4a8b50130e5557ba508).
Required machine evidence remains source-bound; complete historical package
verification uses its original Git tree, not the reduced current checkout.

Follow [Todo and documentation maintenance](TODO_WORKFLOW.md). Update the owning
guide, current review and findings when behavior or verification changes; keep
one report and one findings register. Do not add another dated status preamble
to every guide. Keep the operator's inputs, units, failure/reverse steps and
generated callable references complete.

Additional focused procedures: [adaptable policy](ADAPTABLE_POLICY.md),
[royalty opening and capacity](ROYALTY_LAUNCH_WINDOW.md),
[unsigned pre-seal configuration](PRESEAL_CONFIGURATION.md),
[keeper backup](KEEPER_BACKUP.md), [alerts](KEEPER_ALERTS.md),
[unsigned scheduling](KEEPER_SCHEDULING.md), [sidecar recovery](KEEPER_SIDECAR_RECOVERY.md).
