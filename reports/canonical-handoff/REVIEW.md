# Canonical handoff: internal review

This is an internal design/code review, not an independent audit or release
approval. Execution results and exact source bindings belong in
[VERIFICATION.md](VERIFICATION.md). An implemented check is not a passing test.

## Invariants and trust boundary

- The destination is sealed and inert before source preparation. Its controller,
  modules and helpers are bound by the reviewed deployment commitment. Different
  replacement code is permitted by the user's governance decision; malicious
  approved code can divert liquidity. Hashing that code does not make it safe.
- Source ownership, membership and both reward ledgers remain frozen throughout
  capture, settlement, export, import and funding. Only source-derived, ordered
  records enter the destination. Complete domains include zeros and fractional
  reward checkpoints, not merely rounded current claimable balances.
- All raw receipt cutoffs are captured in one frozen transaction before any
  settlement. The six settlement calls execute once each in fixed order. Export
  and funding are unavailable until all six complete. Late receipts cannot
  become captured receipts because an operator pauses between transactions.
- Funding is exact and classified by module/asset. Destination donations do not
  satisfy a funding leg. An abort cannot reopen the source until every sent leg
  has returned; partial settlement does not undo already allocated rewards.
- Final source retirement and single-successor activation are atomic on the same
  chain. Retirement and cancellation are terminal controller states. No manual
  finality override or timeout activation exists.
- Previous receiver addresses remain relevant. Creator revenue is forwarded
  unsplit one successor at a time, and royalties retain their separate ledger.
  New membership must not capture previously queued local creator funds.

## Findings addressed in the candidate

| Issue | Response | Verification requirement |
| --- | --- | --- |
| A same-chain importer could have a different configured home chain. | Check the destination Vault's home chain during import preparation and freeze. | Wrong-home rejection and usable successor tests. |
| A callback could attempt to freeze while an ingress was only partly accounted. | Fixed Vault/Fees capture barriers, lifecycle checks around economic mutations and coordinator reentrancy protection. | Callback rollback, exact backing and no double-credit cases. |
| Capture and all settlement in one cold governance call exceeded the unchanged 12M test budget. | Capture all cutoffs atomically, then settle one domain per transaction while rights remain frozen. | Full admitted-domain gas measurement and interrupted/duplicate/aborted settlement tests. |
| A 1,000-NFT handoff test represented many transactions under one aggregate test gas cap. | Reset the test meter between bounded export/import calls; retain the unchanged measured 12M budget for each operation. | Complete inventory/accounting preservation, with per-operation measurements rather than an aggregate transaction claim. |

## Open admission and operating risks

Cross-chain consensus proofs, authenticated closure of historical channels, a
lineage-aware message version and exact cross-chain backing transport remain
unimplemented. Any legacy bridge activity prevents this first handoff path;
imported successors cannot initiate v3 principal bridging. Post-halt recovery is
not supplied. These limitations must be resolved before claiming a deployable
future-chain migration design.

Token/wrapper failure, blacklisting, rebasing or dishonest balance responses can
prevent exact settlement, funding or restoration. The design intentionally does
not let governance waive backing to reopen an insolvent source. Dependency
admission and recovery rehearsals remain necessary.

Contract owners and marketplace escrows may hardcode the old collection address.
Preserving their address without a receiver callback does not prove they can
release the replacement NFT. Collection cutover, successor-aware APIs and complete
predecessor claim history require independent integration work. The existing
isolated keeper staging deployment has not been upgraded for these interfaces.

The central [Todo](../../TODO.md#task-security-chain-recovery) owns remaining work.
This report does not create a parallel task-status list.
