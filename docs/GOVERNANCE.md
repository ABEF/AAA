# Immediate governance

## Operator and authority boundary

There is one human project operator: the user. That operator controls governance
and runs the services. There is no separate operator role, committee or additional
human approval. Keep the automated keeper's limited service key separate from the
governance key; this does not imply another person. Production authorities remain
unset. The fresh candidate is accounting4/custody3/canonicalV5, **NOT APPROVED**.

The selected governance wallet calls target modules directly. Access authenticates
it through `canConfigure(caller)`; Access does not schedule or forward calls.
Governance configures supported sources, pools, routes, feeds, roles, ranges and
ordinary loss caps within bounds. It can pause/unpause, move same-pair LP, park it,
start irreversible collective holder return, or approve compatible pre-exit
same-chain replacement. Sealing fixes implementations and the ZZZ identity; it
does not remove configuration or reviewed-successor trust.

There is no operator-selected custody recipient. Collective exit returns actual
ETH+ZZZ by NFT shares to current owners. Permissionless allocation/delivery callers
cannot start exit or choose beneficiaries. Failed recipients stay backed for retry
or an owner-only fallback. No external custody exit, all-ZZZ consolidation,
issuer-exchange executor or bridge remains.

A separate globally paused, governance-only `Migration.emergencyRebalance`
manifest can explicitly bypass selected economic/timing checks. Disabling
financial guards can lose nearly all principal. Structural custody, settlement,
shares/rewards and lifecycle constraints remain. This is manual emergency work,
never an automatic keeper fallback. [Exact risk and controls](EMERGENCY_REBALANCE.md).

Guardian can pause, but cannot unpause, configure or move principal. Ordinary
pause preserves claims and transfers; canonical freezes and terminal locks have
separate effects. Keeper executes authorized bounded maintenance and pays gas.
Governance alone does not imply a keeper grant for ordinary `Vault.rebalance`.
Bootstrap disappears at seal. The immutable mint recipient gains no management
authority from receiving payments. Current direct mint forwards0.05ETH; the
required OpenSea path must keep0.05ETH gross buyer price and pay that recipient
net of the actual marketplace fee, gas separate. That integration is unfinished.
VRF subscription ownership/funding depends on the unqualified provider.

Read the [address inventory](DEPLOYMENT_ADDRESSES.md),
[holder-return procedure](HOLDER_COLLECTIVE_EXIT.md) and
[operator manual](OPERATOR_MANUAL.md). Documentation performs no live operation.

The user selected no governance timelock on2026-10-18. Old two-day templates,
zero-delay scheduled controllers and proposed route-manager roles are historical.

## Authorization without a waiting period

`ZZZAccessController.GOVERNANCE_VERSION()==2`. Its constructor takes nonzero
`initialGovernance`, `initialKeeper` and `initialGuardian`. No Timelock inheritance,
proposer/executor/canceller roles, operation queue or generic executor remains.
Use the governance wallet's own exact target/value/calldata, signatures and nonce.
A Safe owner calling from a personal wallet does not inherit the Safe's authority.
A wallet proposal alone is neither submission nor successful execution.

Before sealing, bootstrap configures the system. After sealing, the current
governance wallet configures supported modules while their lifecycle guards allow
it. Bootstrap is erased and module bindings cannot be replaced. Guardian/keeper
capabilities remain separately granted and revocable within their actual controls.

### Rotate the governance wallet

1. Inspect `governance()`, `pendingGovernance()`, lifecycle and the proposed
   wallet's exact chain/address, signers, threshold and recovery controls.
2. Current governance calls `Access.proposeGovernance(candidate)`. There is no
   delay. Zero cancels; the controller/current governance cannot be proposed.
3. The candidate itself calls `Access.acceptGovernance()`. Verify the event,
   new governance and cleared pending proposal. Proposal alone preserves the old
   wallet's authority. Preparation/frozen/terminal handoff states block rotation.

This does not rotate keepers, guardians or the immutable mint recipient. Lost
governance keys have no controller-admin rescue. One-person governance remains
supported; no new wallet or mandatory multi-person approval is imposed.

| Action | Permission and boundary |
| --- | --- |
| Select an enabled contribution route | The owner transaction selects it; exact policy/asset/caller guards remain. |
| Enable fixed ETH/ZZZ sources, routes or supported pools | Direct governance; no third contribution token or ZZZ replacement. Re-enabling validates actual dependencies. |
| Change feeds, converter wrapper policies, roles or strategy settings | Direct governance within each module's bounds and lifecycle. No delay proves a dependency safe. |
| Global pause/unpause | Guardian or governance pauses; only governance unpauses. Terminal exit is irreversible. |
| Stop a pool or minting only | `disablePool` clears selected capabilities without failing dependency reads; `setMintPaused` stops new mint requests. Full pool validation is needed to reopen. |
| Move/park/resume LP | Governance uses guarded `moveFunds`, exact paused `park`, or fresh guarded `resume`; same native ETH/fixedZZZ pair only. |
| Start/close collective exit | Paused governance calls `beginCollectiveExit(reviewHash)` then `closeBucket` for each captured bucket with reviewed raw minima. No chosen recipient. |
| Allocate/deliver principal | After all buckets close, anyone advances bounded `allocatePrincipal`/`distributePrincipal`; actual current owners receive funds. Operator normally submits/pays gas. |
| Manual emergency rebalance | Globally paused governance alone uses the reviewed retained-check manifest; optional financial bypass accepts near-total-loss risk. |
| Preparation/parking/canonical handoff | Governance controls the exact lifecycle; complete records/backing and atomic same-chain retirement/activation or funded abort remain required. |
| Replace sealed code | No generic in-place upgrade. Only implemented compatible pre-exit canonical handoff permits reviewed replacement code. |

## What is not a governance timelock

Ordinary rebalance cooldowns, sampled confirmation, transaction expiry, oracle
freshness and sequencer/finality policy serve execution/accounting safety. Direct
governance does not remove them. Ordinary defaults remain contribution2%,
conversion1%, maintenance3%, each governed up to10%; stronger caller/venue floors
and captured policy remain binding. The explicitly separate emergency manifest
may bypass selected economic/timing groups, not structural custody/accounting or
terminal/canonical locks. Parking and collective closes use raw minima, without
inventing a USD-loss promise. [Loss controls](EXECUTION_LOSS_POLICY.md).

Same-pair movement/parking keep principal inside the protocol. Collective exit
returns old ETH/ZZZ to holders; any later token exchange/new-chain project is
separate and does not automatically relocate existing NFT/reward rights. Failed
tokens, venues, governance access or receivers can still prevent recovery.

## Accepted trust boundary and release evidence

There is no advance warning window. Compromised governance can approve harmful
feeds, routes, parameters or compatible replacement code. Approved code hashes
identify bytes, not honest behavior. The user accepted reviewed different
successor code; no identical-code restriction is added. Emergency financial
bypass expands this trust further. [Change boundaries](CHANGE_AND_RECOVERY.md).

Fresh accounting4/schema6 inventory binds governance2, actual governance and
pending-governance state, capability grants and their complete history. Actual
wallet type, signers/threshold and recovery require qualification; no mandatory
committee is implied. Historical manifests retain their own semantics and cannot
approve a fresh deployment.

The [zero-delay review](../reports/immediate-governance/VERIFICATION.md) describes
its original scheduled controller, not this direct controller or later emergency
authority. Current sources, exact runtime/configuration observations, operating
rehearsals and independent audit/remediation remain required. See the
[sole governance task](../TODO.md#task-security-governance) and
[release approval record](RELEASE_CHECKLIST.md).
