# Immediate governance: internal delta review

The user explicitly removed all governance timelocks on 2026-10-18. This review
covers that decision and implementation, not an independent audit or release approval.

## Implementation and authority

The production behavioral changes are limited to AccessController and Migration.
AccessController retains OpenZeppelin TimelockController's exact operation IDs,
proposer/executor/canceller access checks, rollback, predecessors and replay rules.
Its constructor now rejects nonzero delay; both scheduling overrides reject
nonzero operation delay before calling the unchanged parent implementations.
The existing `updateDelay` override always reverts. Timestamp zero/one are
rejected because OpenZeppelin reserves them for unset/completed operations.

No direct arbitrary governance executor, caller-selected delegatecall, new fast
manager, key, custody recipient or generic upgrade is introduced. The controller
still cannot call as the Vault. Bootstrap revocation, fixed sealed module bindings,
canonical lifecycle guards and guardian/keeper boundaries are unchanged. Open
executor mode executes an approved exact operation, not arbitrary user calldata.

Migration's public delay constant is zero. A plan records its proposal timestamp
as `earliest`; its layout, IDs, snapshot, epoch, status transitions, authorizations
and economic checks are unchanged. Only governance proposes and only an authorized
keeper executes. Timeliness does not replace actual route readiness, current
custody, exact balances, existing reentrancy guards or authenticated settlement.
Cancellation only protects a plan that has not already executed.

## Risks accepted or still open

- Governance has **no advance warning period**. Malicious/compromised governance
  may approve dangerous feeds, assets, providers or successors immediately.
  Multisig controls and independent reviews remain trust/operating requirements,
  not new on-chain delays. A guardian pause is not a governance veto: governance
  can unpause. Existing sealed-core and nonredeemability rules do not make an
  arbitrary approved successor honest.
- Zero-delay scheduling permits same-transaction proposal/execution when a
  multisig batches the calls. A late canceller cannot undo an executed operation.
  Changes can invalidate pending quotes; final complete simulation and on-chain
  execution guards remain necessary. Existing callback-time preparation checks
  must still roll back conflicting economic work.
- Keeper cooldowns, oracle freshness/sequencer recovery, transaction deadlines,
  confirmations and future verified finality are unchanged safety conditions.
  No production bridge/finality service or full cross-chain canonical handoff is
  supplied by removing the wait.
- Deployment configuration must bind the new AccessController/Migration runtimes,
  zero-delay authority policy, exact roles and current independent evidence.
  Positive-delay or old parking-review manifests are rejected by the validator.
  Existing deployed services, website and monitoring have not been modified.

## Static review

Fresh Slither analysis covers the current production build. The 376 existing
expressions matched their earlier classifications; their authority dependencies
were reviewed again for this change. In particular, Migration no longer relies
on a waiting period, and canonical freeze is immediately governance-authorized.
Two additional timestamp findings concern only the zero/one timestamp sentinel
guard in single/batch scheduling; it does not select rewards, prices or entropy.
Both are false positives for exploitable economic timestamp dependence.

The current review explicitly updates the affected rationales and records the
absence of notice. Historical reports are preserved; the current canonical
review file is updated for CI. See [verification](VERIFICATION.md) for actual
executed checks, source bindings, failures and limitations.
