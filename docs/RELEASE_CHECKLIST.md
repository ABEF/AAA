# Release approval record - NOT APPROVED

**Decision: NOT APPROVED.** No production deployment, sealing or use of real
funds is authorized by this document. Reviewed 2026-10-19.

The [earnings extension](EARNINGS_HISTORY.md) implements read-only processed
all-time/24h LP and royalty history, complete configured same-chain continuity and
optional current-price USD marks. [Scoped evidence](../reports/earnings-history/VERIFICATION.md)
covers 186 affected tests across recorded runs, with unchanged contract evidence
reused. Actual feeds, backfill completeness, archival/load/reorg operation and
frontend labels/availability remain unqualified. This does not approve production.

The [royalty reporting extension](ROYALTY_REPORTING.md) adds explicit optional
ABI/configuration and partial currency-availability semantics to single-NFT reads,
plus complete same-chain conversion history separated from claims. Review actual
runtime pins, archive ingestion, client null/eligibility behavior and deployment
compatibility before hosting or enabling UI actions. Local backend tests and
unchanged contract evidence do not qualify live services; earned/USD reporting
has its own profile and operating requirements above. No website/server or deployment change occurred.

The [royalty conversion candidate](ROYALTY_SETTLEMENT.md) adds a fixed pre-seal
converter binding, batch ETH accounting, optional-token failure isolation and an
opt-in keeper job. Independent wrapper/route/feed and runtime-inventory review,
marketplace settlement, live keeper/UI rehearsals and audit remain required.
This feature is not activated on any server or public chain.

The [internal review of October 18 changes](../reports/daily-security-20261018/REVIEW.md)
leaves this decision unchanged. Resolve the VRF/handoff liveness dependency and
contract-holder successor compatibility before qualifying recovery. Total API
work is now bounded in the [local remediation](../reports/api-work-limits/VERIFICATION.md); qualify actual Linux workers, ingress and RPCs before public hosting. Immediate governance trust and
per-operation rather than cumulative loss protection require explicit release
review. The [operator manual](OPERATOR_MANUAL.md) is maintained with behavior changes;
its scenarios still require actual operating qualification. No independent audit or complete current-source regression is claimed.

The [local $1 rehearsal](ONE_DOLLAR_REHEARSAL.md) is a separate generated test
artifact with mocked venue/services and local-chain guards. It does not change
the production $100 minimum or this approval decision. Its evidence cannot stand
in for the production binary, actual route/gas qualification or live operations.

Development tasks, progress and detailed acceptance criteria have one home:
the [central Todo](../TODO.md), generated from [its ledger](project-todo.json).
The [feature and evidence reference](IMPLEMENTATION_STATUS.md) describes source and
evidence. This file records the final go/no-go decision for one frozen release;
it is not another task checklist.

The [2026-10-18 development verification](WORK_HANDOFF.md) closes the saved
bridge-fixture and cold-gas regression reruns. It does not approve independent
audit, current operating rehearsals, real dependencies or cross-chain migration.
Exact-commit Ubuntu CI remains separate from local evidence. The separately
verified [activation preparation](../reports/activation-preparation/VERIFICATION.md)
adds 38 focused backend checks and a local trace/budget probe; it does not qualify
production activation routes, oracles, RPC providers, network fees or wallet UX.

The [dynamic-liquidity delta](../reports/dynamic-liquidity/VERIFICATION.md)
changes production Vault/metadata code and backend projections. Its scoped tests,
normal sizes and internal review do not approve live services, operating parameters,
independent audit or funds. Prior full-regression receipts are not current-source
qualification of this delta.

The subsequent [range-policy delta](../reports/range-policy/VERIFICATION.md)
changes Strategy eligibility and confirmed API context. It adds no force role or
Vault code change. Its timelock/cooldown/rollback and accounting checks do not
qualify chosen production widths, repeated-operation costs, live prices or keeper
operation. Exact-release module runtime pins must include this Strategy version.

The [immediate-governance change](GOVERNANCE.md) removes both mandatory controller
and migration waiting periods. Earlier delayed-operation evidence does not qualify
this authority policy. Exact-release approval must review zero-delay roles and
operations, absence of advance notice, custody guards, runtime identities and
current operating procedures. [Scoped evidence](../reports/immediate-governance/VERIFICATION.md)
is internal development verification; this release remains NOT APPROVED.

The [independent stop-controls candidate](../reports/operator-controls/VERIFICATION.md)
changes NFT/Registry runtimes and the read API. Production inventories, authority
operation rehearsals, provider outage/restart and successor mint-state review
must use these exact implementations. Scoped local verification does not close
the independent audit, live services or deployment approval gates.

## Release identity

| Approval field | Recorded value |
|---|---|
| Exact release commit | Not selected; current development HEAD is not release approval |
| Network and chain ID | Not approved |
| Deployment/configuration manifest and content hash | Not approved; example addresses/settings are not production choices |
| Compiler, dependency lock and bytecode/artifact manifest | No release-specific approved record |
| Module/helper addresses, authority addresses and immutable bindings | Not selected and independently approved |
| Evidence bundle and hashes | No final release bundle accepted; development evidence is linked from the implementation reference |
| Release mode | Intended initial mode: migration disabled; actual configuration not yet approved |
| Decision date and accountable release owner | Not recorded |
| Accepted residual risks, limits and rationale | Not approved |

## Required sign-off record

| Review responsibility | Named reviewer / independence | Exact evidence and decision |
|---|---|---|
| Frozen source, economics, security audit and remediation | Not recorded | No approval |
| Deployment configuration, dependencies, authorities and sealing | Not recorded | No approval |
| Target-chain integration, operating recovery and monitoring | Not recorded | No approval |

Approval requires independent reviewers to confirm the applicable initial-launch
acceptance criteria in the [audit/release task](../TODO.md#task-audit-release)
against the exact commit, network, manifests and evidence above. The three test
layers, service qualification and unresolved risks must be assessed within that
same release scope. Local tests, internal Slither triage, old CI, or a successful
configuration validator do not supply this sign-off. Any non-applicable criterion
needs a recorded reason tied to the chosen release mode; it cannot silently
remove an acceptance requirement from the Todo.

Changes to deployed code, dependency implementations, bindings, economics,
network or operating configuration require review of the affected approval and
an updated release identity. A recorded approval is separate from explicit
authorization to submit public transactions.

## Initial launch and later migration

An initial launch may be approved with `migration.enabled=false`, empty
provider/policy/route inventories and observed zero registered/outbound policy
counts, as specified in the
[operations runbook](OPERATIONS.md#migration-disabled-initial-launch).
[Destination capacity](../TODO.md#task-destination-slots) and
[real bridge operation](../TODO.md#task-bridge-operation) remain open future
activation gates; disabled migration is not evidence that they are implemented
or safe. Enabling migration needs a separate approved configuration and review.
The [canonical migration requirement](../TODO.md#task-security-chain-recovery)
remains a pre-seal gate even for a migration-disabled launch: the user selected
controlled whole-protocol migration while the source works, deferring post-halt
recovery. The current code cannot gain that capability after sealing.

Different-pair conversion and canonical portability require pre-seal design,
implementation and qualification; disabling bridges does not add those capabilities to sealed code. The
accepted 3% migration execution budget is enforced only for supported atomic local
move/resume and ordinary rebalance in the current candidate; it is not an asynchronous bridge guarantee.
Reversible preparation and a same-chain handoff candidate are implemented. Full
cross-chain canonical handoff remains absent: same-chain atomic activation is not
a proof/transport implementation for another chain. Historic bridge channels,
v3 lineage, successor template admission and escrow/marketplace compatibility
require explicit review. See [the implemented boundary](CANONICAL_HANDOFF.md).
The selected finality policy forbids a multisig-only override. See
[migration safety](MIGRATION_SAFETY.md) and [architecture evolution](ARCHITECTURE_EVOLUTION.md).

## Moved requirement links

<a id="required-testing-layers"></a>
The three required layers are maintained in
[frozen-release local/Ubuntu verification](../TODO.md#task-audit-release),
[actual Robinhood mainnet fork](../TODO.md#task-mainnet-fork) and
[Robinhood Testnet rehearsal](../TODO.md#task-testnet-rehearsal).

<a id="market-valuation-and-operating-integration"></a>
Market, wallet and operating acceptance is maintained under
[selected pool](../TODO.md#task-pons-qualification),
[activation assets](../TODO.md#task-activation-assets),
[transaction journey](../TODO.md#task-transaction-ui) and
[keeper recovery](../TODO.md#task-keeper-recovery).

The [holder preflight](HOLDER_PREFLIGHT.md) supplies a pinned ownership/code inventory,
not escrow or replacement approval. Include complete frozen coverage plus exact
contract-holder release/claim and marketplace cutover evidence in release review.
