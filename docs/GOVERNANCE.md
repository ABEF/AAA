# Immediate governance

## Current role and custody boundary - 2026-10-25

Governance multisig signers authorize exact zero-delay controller operations.
The multisig can approve assets/pools/routes/feeds, strategy and keeper policies,
roles, and contribution/conversion/maintenance caps up to10%. It can pause and
unpause, authorize same-pair pool moves, and separately approve paused external
custody exits and compatible whole-collection handoff. This is a powerful trusted
role; sealing fixes implementations, not these approved configuration/exit powers.

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

`ZZZAccessController` keeps OpenZeppelin's operation hashing, proposer/executor/
canceller roles, exact calldata, predecessor ordering and replay protection.
Its inherited Solidity type is named `TimelockController`, but PoPL requires
**zero** constructor delay, **zero** per-operation delay and rejects every
`updateDelay` call. Neither single nor batch scheduling can introduce a wait.

An authorized proposer registers the exact operation with `schedule(..., 0)` or
`scheduleBatch(..., 0)`. An authorized executor can execute it immediately, in the
same block. A multisig can batch registration and execution in one transaction.
Registration is an authorization record, not a cooling-off period. An unfinished
predecessor still prevents execution; elapsed time cannot substitute for completion.

The local template uses the governance multisig as proposer and an open executor.
Anyone may submit the **unchanged approved operation** in that configuration;
they cannot choose new calldata or receive governance permissions. A cancelled,
unknown, changed or completed operation cannot execute. Target failure rolls back
its effects; a failed operation remains available for cancellation or retry.

After sealing, governed modules still accept configuration only from the
controller, not directly from a multisig member, keeper, guardian or NFT holder.
Bootstrap is erased and fixed module bindings cannot be replaced.

| Action | Permission and timing |
| --- | --- |
| Select an existing enabled activation route | The transaction/quote selects it; no new governance action is needed. |
| Add/disable activation assets, routes or supported pools | Exact governance operation; no waiting period. Token, factory, code, price and venue checks still apply. |
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
recovery checks, confirmations and verified cross-chain finality serve execution
or accounting safety. They remain. Approval cannot skip missing funding, pause/
preparation/frozen-state checks, ownership checks, approved-route checks or the
captured execution limits: defaults2% contribution/1% conversion/3% maintenance,
with immediately governed maxima10%. An original approved custody floor is not
retroactively relaxed by changing the live cap. Explicit raw exit uses approved
raw minima instead of a fabricated USD guarantee.

The current launch scope uses same-chain pool moves and source-chain external
custody. The recipient handles external token migration or bridging; integrated
bridges and remote NFT/reward-ledger transport are deferred optional scope. The
remaining remote-proof interface does not supply a provider, verifier or remote
ledger. An approved plan does not guarantee token, venue or custodian availability.

## Accepted trust boundary and release evidence

There is **no advance on-chain warning window** for governance changes. Compromised
or malicious governance can immediately approve harmful feeds, routes, providers
or compatible replacement code. Nonredeemable principal and sealed local code do
not make those choices safe. Multisig signer security, transaction simulation,
independent dependency/replacement review and monitoring remain necessary.
The user accepts different reviewed successor code; no identical-code rule is added.

The manifest retains legacy keys for compatibility: `timelock_seconds: 0`,
`delay_fixed: true`, `post_seal_routes_timelocked: false`,
`migration_delay_seconds: 0`. Its authority evidence must explicitly review
immediate operations/migration and accept the absence of notice. Existing delayed
deployment manifests cannot qualify this release. No production authority address
or release approval is supplied by this decision.

See [scoped verification](../reports/immediate-governance/VERIFICATION.md), the
[central security task](../TODO.md#task-security-governance) and the
[release approval record](RELEASE_CHECKLIST.md).
