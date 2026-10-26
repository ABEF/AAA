# Immediate governance

## Operator and authority boundary

There is one human project operator: the user. That operator controls the
governance wallet and runs the keeper/services. "Operator" describes the person;
"governance" describes that person's configured on-chain authority. There is no
separate operator role, committee or additional human approval in PoPL.

The selected governance wallet calls each target module directly. The Access
controller authenticates that wallet through `canConfigure(caller)`; it does not
schedule or forward the transaction.
The governance wallet can approve assets/pools/routes/feeds, strategy and keeper policies,
roles, and contribution/conversion/maintenance caps up to10%. It can pause and
unpause, authorize same-pair pool moves, and separately approve paused external
custody exits and compatible whole-collection handoff. This is a powerful trusted
role; sealing fixes implementations, not these approved configuration/exit powers.

One person may control multiple accounts. Keep the automated keeper's limited
service key separate from the governance key; this requires no second operator.
Guardian, bootstrap, mint recipient and custody-recipient permissions retain
their existing boundaries even when controlled by the same person. A single-owner
wallet/Safe is possible; no production address or wallet type is selected here.

The custody recipient is the destination of an approved transfer, **not another
governance role**. It may be an EOA or contract. Receiving principal gives it
actual control outside the Vault, not the ability to reconfigure PoPL. It may
fund only the already approved return/completion path, as may other funders;
that path preserves NFT shares and the original approved backing/minima. There
is no guarantee the custodian will bridge, migrate or return assets.

Guardian can pause immediately, but cannot unpause, configure or move funds.
Ordinary global pause leaves claims and NFT transfers available; the separate
canonical freeze/retirement rules still apply. Keeper executes bounded maintenance
and pays gas, not discretionary custody exit or destination selection. The mint
recipient receives0.05ETH per successful current direct mint and has no powers
from that payment. The required OpenSea path instead keeps0.05ETH gross buyer
price and pays the recipient net of the actual platform fee; that integration
is not implemented. Network gas is separate. Bootstrap disappears at seal. VRF subscription ownership and
funding depend on the provider, which remains unqualified.

Read [address inventory](DEPLOYMENT_ADDRESSES.md),
[custody procedure](GOVERNED_CUSTODY_HANDOFF.md) and [operator manual](OPERATOR_MANUAL.md).
Production addresses remain unset; no role selection or live operation follows.

The user selected **no governance timelock at any point** on 2026-10-18.
This supersedes the earlier two-day template and the proposed narrow route-manager
exception. The candidate is undeployed. Historical reports describe their original
delayed versions; they are not verification of this change.

## Authorization without a waiting period

The current `ZZZAccessController.GOVERNANCE_VERSION()` is **2**. Its constructor
takes `initialGovernance`, `initialKeeper` and `initialGuardian`, each a nonzero
address. It has no Timelock inheritance, proposer/executor/canceller roles,
operation queue or generic transaction executor. Submit reviewed target/value/
calldata through the governance wallet's own signature and nonce process.
If using a Safe, the Safe is the target call's sender; a Safe owner calling from
their personal account does not inherit that authority. Target failure reverts
that transaction. A wallet proposal alone proves neither submission nor execution.

Before sealing, configuration belongs to bootstrap. After sealing, the current
`governance()` wallet configures modules directly while canonical state is
operating and preparation is inactive. Bootstrap is erased; fixed module bindings
cannot be replaced. The controller also keeps the separate guardian/keeper and
canonical lifecycle controls.

### Rotate the governance wallet

1. Inspect `governance()`, `pendingGovernance()`, lifecycle and the proposed wallet's
   actual address, chain, signer/threshold configuration and recovery controls.
2. The current wallet calls `Access.proposeGovernance(candidate)`. There is no
   delay. Passing zero cancels a pending proposal; the controller and current
   governance address cannot be proposed.
3. The proposed wallet itself calls `Access.acceptGovernance()`. Confirm the
   `GovernanceAccepted` event, new `governance()` and zero `pendingGovernance()`.
   Proposing an address does not remove the current wallet's authority.

Both steps require operating canonical state and no active preparation; freeze or
retirement cannot be bypassed by rotation. This does **not** rotate keepers,
guardians, bootstrap or the immutable mint recipient. Rotate those separately
where supported. Lost governance keys have no controller-admin rescue path.

| Action | Permission and timing |
| --- | --- |
| Select an existing enabled activation route | The transaction/quote selects it; no new governance action is needed. |
| Enable/disable ETH or the fixed ZZZ, rotate approved routes or select a supported pool | Direct governance call; no waiting period. No third contribution currency or ZZZ retargeting. Token, factory, code, price and venue checks still apply. |
| Change feeds, wrapper policies, operators or strategy parameters | Exact governance operation; no waiting period. Existing parameter and binding restrictions remain. |
| Global pause | Guardian or governance, immediately. Only governance can unpause. |
| Stop a pool / pause only NFT minting | Governance `PoolRegistry.disablePool` clears flags without dependency reads; `NFT.setMintPaused` controls new mints. No waiting period or new role. Reopening a pool uses full validation; resuming minting does not override global/lifecycle controls. |
| Approve custody exit | Governance authorizes the exact reviewed plan and destination; no governance waiting period. `Migration.approve` is the current interface, not a retired bridge proposal. |
| Move LP / execute custody exit | Governance calls `Migration.moveFunds` for supported same-pair movement or `Migration.exit` for an approved paused custody plan. Keeper authority alone is insufficient. |
| Preparation, parking, handoff or successor approval | Governance, with no time delay; required state transitions, exact backing and source retirement remain mandatory. |
| Replace sealed implementations with arbitrary new code | No generic in-place upgrade exists. Only implemented, compatible handoff mechanisms can authorize a reviewed successor. |

No separate fast-route manager role is added. New routers, price feeds and
successors remain security-sensitive governance choices even though they can be
approved immediately. Same-day configuration does not add unsupported swap
algorithms, pair conversion or cross-chain canonical migration capabilities.

## What is not a governance timelock

Keeper rebalance cooldowns, transaction deadlines, oracle freshness and sequencer
recovery checks and confirmation/finality policies serve execution
or accounting safety. They remain. Approval cannot skip missing funding, pause/
preparation/frozen-state checks, ownership checks, approved-route checks or the
captured execution limits: defaults2% contribution/1% conversion/3% maintenance,
with immediately governed maxima10%. An original approved custody floor is not
retroactively relaxed by changing the live cap. Explicit raw exit uses approved
raw minima instead of a fabricated USD guarantee.

The current launch scope uses same-chain pool moves and source-chain external
custody. The recipient handles external token migration or bridging; integrated
bridges and remote NFT/reward-ledger transport are not implemented. No remote-proof
interface remains. An approved plan does not guarantee token, venue or custodian availability.

## Accepted trust boundary and release evidence

There is **no advance on-chain warning window** for governance changes. Compromised
or malicious governance can immediately approve harmful feeds, routes, providers
or compatible replacement code. Nonredeemable principal and sealed local code do
not make those choices safe. Multisig signer security, transaction simulation,
independent dependency/replacement review and monitoring remain necessary.
The user accepts different reviewed successor code; no identical-code rule is added.

The current accounting3 release inventory binds `GOVERNANCE_VERSION=2`, the actual
governance wallet, zero pending governance, operator grants, reviewed multisig
signers/threshold and complete history. It has no Timelock role/delay fields.
Historical manifests retain their original interpretation only through explicit
historical inspection; they do not qualify the current release. Authority review
must accept immediate operations and custody trust. No production authority
address or release approval is supplied by this decision.

The [earlier zero-delay review](../reports/immediate-governance/VERIFICATION.md)
describes its original scheduled-controller source, not this direct-governance
implementation. See the
[central security task](../TODO.md#task-security-governance) and the
[release approval record](RELEASE_CHECKLIST.md).
