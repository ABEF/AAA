# Supplied-pool lifecycle: guarded isolated fork

20 November 2026. Baseline main `4b6497be76191a8a3a5295267b4706f811d5a899`.
Production remains undeployed and NOT APPROVED. Final production-pool selection
is deferred; the supplied pool remains the authorized integration test target.

## Work and scope

The [plan](PLAN.md) targets the missing current F6 physical LP partition rather
than replaying the old accounting3 eleven-method suite or an old population.
Production source, compiler, ABI, runtime, policy, rights and budgets stay fixed.
Only newly scoped report tools and isolated tests change.

[Eight new offline controls](harness/REVIEW.md) pass for immutable request
recording, startup cleanup, intended-revert classification and owned-listener
checks. Fake transport/processes prove only the report-driver behavior. An
explicit [successful-stage comparison](harness/METHOD_REUSE_04.json) supports
reuse of unchanged recording/startup bodies; changed cleanup/send methods retain
their own scope. Two later deadline controls and two actual offline Cast cases
cover newly corrected fixture inputs; none is a production or full EVM suite.

[The RPC screen](rpc/REVIEW.md) makes four new HTTP requests without retries.
The official public endpoint refuses access; BlockVectra confirms chain4663 but
rejects the fixed block outside its declared900-block window. No alternate
anonymous archive endpoint is qualified. Provider-account leads are unselected.

## Derived cache and actual run

The new report-only transport admits candidate warm entries only when BOTH exact
canonical request and result digests match successful cached events in the
unchanged prior archive. Source/archive/member hashes and exact anchor bind the
derivation. Unknown, conflicting, mutable/latest and failed entries are not
invented cache data. This is a derived, hash-verified seed, not a raw upstream
cache export or independent proof of all provider state.

Fresh chain, exact anchor and number0/genesis checks precede loading64 admitted
entries. New reads are throttled to0.5requests/second, with a refusal latch and
bounded work. Future captures snapshot serialized requests and retain successful
cache values. Reverse test-trade sizing uses a bounded fraction of newly bought
ZZZ rather than depending on any pre-existing wallet token balance. This is
fixture robustness, not a claim that an earlier giant trade occurred.

### Actual result

**The current F6 physical LP partition passed.** [Saved-wire verification](run/VERIFICATION.json)
reconciles448 immutable request/response rows and39 included transactions:
38 positive estimate/full25% submissions plus one intended failed transaction
with a fixed1M envelope. Necessary setup and previously passed phases are not
counted as additional coverage. The final run took about42seconds with19 live
public reads,137 cache hits and no retry or rate-limit refusal. Across the three
online attempts,107 live reads and314 cache hits are recorded; earlier work is
not hidden from the final warm-run figures.

| Physical behavior | Actual proof |
| --- | --- |
| Mint and custody | Native ETH/ZZZ LP NFT4331098 is owned by the typed custody fixture; initial L180704995773128430458. |
| Increase | L rises to198775495350441273503, with the same owner/range. |
| Guarded rollback | Same successful increase budgets, but minimum L changed toMAX128, produce exact `Slippage()`;858,751gas is below the1M envelope. Custody ETH/ZZZ, L and approval stay unchanged. |
| Fee generation | Two bounded external test-trader swaps execute against the real core; both outputs are positive. This is not the production balancing router. |
| Actual collection |10,009,999,999weiETH and1,409,486,118,578,156rawZZZ arrive in custody, with L unchanged. |
| Repeat collection | No new income or state delta without intervening swaps. |
| Close | Both actual principal amounts return exactly on top of post-harvest balances; active L returns to its original0 and ownerOf fails with exact `NOT_MINTED`. |
| Leftovers/permissions | Manager/LP child native/token balances and ERC20/Permit2 spend amounts are zero. Deliberately unused setup funding stays in test custody. |

The [deadline check](run/DEADLINE_VERIFICATION.json) binds six reviewed raw headers
and exact calldata deadlines to head timestamp+300. Successful contract execution
preserves the actual now..now+600 source guard. Receipt timestamp fields are
absent, so this is not independent recovery of every mined timestamp; the saved
final header separately binds closing time. Owned PID15904 is stopped, with no
pending submission. Its881,747-byte owned-state dump is a local rehearsal
artifact, never a protocol checkpoint or public recovery instruction.

### Failures retained and corrected

1. An exact compiler source-unit spelling mismatch refused offline before node
   or network work. Fixture content/output were reused with the literal retained
   metadata key; no production compilation or new source profile.
2. The inherited fixture used now+3600; the actual contract correctly rejects
   more than600seconds. Fresh per-operation300second reviews after disclosed
   owned-local empty blocks fix test timing without weakening the guard.
3. The report ABI wrapper rendered Python `True` instead of Cast's `true`.
   That failure occurred after valid mint/increase/rollback, before any trade.
   Canonical Boolean rendering is checked offline before the final run.
4. A verifier-only uniqueness assertion treated repeated setup labels as unique.
   Its source/failure is retained; correction narrows uniqueness to the exact LP
   phases. It causes no extra EVM replay or fabricated transaction pass.

[The source stages and archive](run/EVIDENCE_MANIFEST.json) retain all attempts,
fresh identity checks, derived/imported cache provenance, raw requests, receipts
and cleanup. Final [run notes](run/REVIEW.md) distinguish actual successes from
prepared source changes. The reported42seconds and19 reads describe the final
warm run, not the entire campaign. All three owned online nodes are stopped.

## Verification limits

This is a physical Manager integration using real selected Uniswap/token
contracts, MockAccess/custody/budget/admission controls, correlated USD fixtures
and synthetic local funding. It does not qualify the production swap router,
Entry activation/top-up, NFT shares or80/10/5/5 reward allocation, optional
two-position strategy, independent valuation, external depth, actual full fees,
provider service capacity or release readiness. Their previous evidence and
remaining obligations stay separate. No unchanged behavioral suite ran.

## Preservation

All public transport is read-only. All funding and transactions are limited to
the newly owned loopback fork. Existing Anvil8902, NFTs/LP/balances, sites,
services, journals/checkpoints, signer restrictions and the paused heartbeat are
preserved. The four unrelated dirty files and all original failures stay intact.

The direct476,135-estimate cold-activation shortfall, actual external depth and
independent feeds/routes, complete target fees/provider capacity, full Entry/NFT
accounting, custom OpenSea/VRF and independent release acceptance remain separate.
