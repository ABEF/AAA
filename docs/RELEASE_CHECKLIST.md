# Release approval record - NOT APPROVED

**Decision: NOT APPROVED.** No production deployment, sealing or use of real
funds is authorized by this document. Reviewed 2026-10-18.

Development tasks, progress and detailed acceptance criteria have one home:
the [central Todo](../TODO.md), generated from [its ledger](project-todo.json).
The [feature and evidence reference](IMPLEMENTATION_STATUS.md) describes source and
evidence. This file records the final go/no-go decision for one frozen release;
it is not another task checklist.

The [2026-10-18 development verification](WORK_HANDOFF.md) closes the saved
bridge-fixture and cold-gas regression reruns. It does not approve independent
audit, current operating rehearsals, real dependencies or cross-chain migration.
Exact-commit Ubuntu CI remains separate from local evidence.

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
move/resume in the current candidate; it is not an asynchronous bridge guarantee.
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
