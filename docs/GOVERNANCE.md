# Immediate governance

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
| Pause | Guardian or governance, immediately. Only governance can unpause. |
| Propose LP migration | Governance authorizes the exact plan. `MIGRATION_DELAY()` is zero. |
| Execute an approved LP migration | Authorized keeper, immediately if every execution/custody/route check passes. No autonomous choice of destination. |
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
1% contribution and 3% supported local-move/rebalance execution-loss limits.

Migration eligibility is immediate, but bridge delivery is asynchronous and may
fail or wait for authentic settlement. Future cross-chain canonical activation
still requires verified source finality with no multisig-only override. An
approved plan is not a guarantee that external assets or venues are available.

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
