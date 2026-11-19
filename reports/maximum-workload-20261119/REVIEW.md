# Controlled maximum-state contributions and maintenance

19 November 2026. Baseline main: `c1b123c2defb30c66134037d3d44c2a24f22eee4`.
Production remains undeployed and NOT APPROVED.

**Eleven of twelve contribution states fit32M/full20%. All five executable
maintenance states fit24M/full25%; three intended safeguard refusals reproduce.**
The remaining opening ZZZ/all-slow state estimates27,142,801 gas:32,571,362 with
full padding, exceeding32M by571,362. Its32M execution and financial checks
succeed, but the selected operating policy correctly refuses its headroom.
Do not substitute trace gas or discard padding to approve it.

[Qualification](QUALIFICATION.json), [producer](producer/MANIFEST.json) and
[plan](PLAN.md) retain exact source, inputs and limits. No production Solidity,
financial right, permission, gas/read/fee default or running configuration changes.

## Actual populated state and independent assertions

The new producer mints1,000 NFTs through the verified mint2 SeaDrop fixture and
performs999 actual Entry activations. It reverses rarity order: Legendary,
Rare, then Commun; the final dormant NFT is Commun. It uses two holding addresses,
not1,000 signers. The actual governed capacity increase admits64 ERC20 currencies
PLUS native ETH,65 assets. Activation/growth still accepts only native ETH
and the fixed ZZZ. Stored birth boundaries include the cold16-entry
append edge. The main and one residual are both funded, contained and Vault-owned.

Each contribution checks marginal MAIN LP, aggregate BOTH-leg NAV plus idle and
designated compound, net-NAV share issuance, incumbent rights, unchanged residual
ID/liquidity/ticks/amounts, unchanged main range/centre/rebalance clock, exact
approvals, custody and failure rollback. Old/future royalty cohorts, faults and
all65 currency books are checked. At completion every royalty currency is actually
paid to its entitled current owners and its allocated liability/backing drains.
Raw ETH/ZZZ LP entitlements sum exactly to allocated LP liabilities; ZZZ remains
pending separate guarded ETH conversion. This is not conversion-route or claim
batch-gas qualification. Designated compound/buyback reserves and fee dust are
separate from holder liabilities.

Maintenance reconciles actual fees from EACH physical position, funded
80/10/5/5 allocation and dust, preserved1,000 owners/shares/royalty tickets,
all65 unchanged royalty books, captured maintenance-value floors and physical
close/mint ownership. The exact padded traces receive financial verification.
There is no emergency bypass or automatic fallback to a wider operating cap.

## Cold contribution results

Maximum admitted estimate26,666,666; each accepted exact padded call succeeds.
Rows are new scenarios, not twelve new test methods.

| State | Cold estimate | Full20% | Result |
| --- | ---: | ---: | --- |
| 999-opening-eth | 23,823,412 | 28,588,095 | Fits32M |
| 999-opening-zzz | 24,433,723 | 29,320,468 | Fits32M |
| 999-opening-zzz-allslow | 27,142,801 | 32,571,362 | REFUSED: full20% exceeds32M |
| 999-opening-eth-allfault | 18,090,728 | 21,708,874 | Fits32M |
| 999-rotated-zzz | 22,741,996 | 27,290,396 | Fits32M |
| 999-rotated-eth-onefault | 22,066,454 | 26,479,745 | Fits32M |
| 999-rotated-zzz-allfault | 18,623,960 | 22,348,752 | Fits32M |
| 999-rotated-eth-allslow | 24,840,763 | 29,808,916 | Fits32M |
| 999-rotated-eth | 22,131,684 | 26,558,021 | Fits32M |
| 1000-grow-eth | 11,647,089 | 13,976,507 | Fits32M |
| 1000-grow-zzz-allfault | 12,255,819 | 14,706,983 | Fits32M |
| 1000-grow-zzz | 12,255,819 | 14,706,983 | Fits32M |

Nine activation records retain their original checker source. Only the three
growth preflights were rerun after correcting a checker assumption; no completed
activation was repeated. [Initial records](cold/initial/SUMMARY.json) preserve
the three incomplete growth measurements, which are not budget refusals.
[Growth rechecks](cold/growth-recheck/SUMMARY.json) complete those three only.

## Cold maintenance results

Maximum admitted estimate19,200,000. Intended refusals are not executable gas
passes. The generic InvalidState selector alone does not prove which overlapping
eligibility condition rejected replay; inputs and actual errors are retained.

| State | Cold estimate | Full25% | Result |
| --- | ---: | ---: | --- |
| harvest | 1,267,441 | 1,584,302 | Fits24M |
| harvest-no-new-fees | 448,013 | 560,017 | Fits24M |
| compound | 10,492,097 | 13,115,122 | Fits24M |
| compound-before-interval | Guard refusal | Not a gas pass | Expected rejection verified |
| ordinary-replace | 15,129,459 | 18,911,824 | Fits24M |
| rebalance-replay-before-cooldown | Guard refusal | Not a gas pass | Expected rejection verified |
| to-lp1-merge | 11,989,644 | 14,987,055 | Fits24M |
| compound-stale-price | Guard refusal | Not a gas pass | Expected rejection verified |

[Maintenance receipts](cold/maintenance/SUMMARY.json) bind exact calls and
padded traces. Worst padded executable maintenance is18,911,824/24M.

## Corrected test and measurement assumptions

The [attempt archive](attempts/MANIFEST.json) preserves all failed/empty stages.
Only one NEW producer method is involved; its source changes required affected
reruns. No unchanged old test method or suite executed.

- 01/02 execute zero tests and are non-passes, never added to coverage.
- 03 reaches999 activations but its setup incorrectly expects an ordinary price
  trigger after enabling residual mode. The corrected setup uses the existing
  operator-directed mode-change exception after12hours, retaining financial guards.
- 04 reaches the real guarded adjustment and returns Slippage with the original
  synthetic1M external reference depth. That refusal remains; no limit is relaxed.
- 05 completes all twelve contribution branches and the first six maintenance
  branches, then its outside-trader helper requests a sqrt limit equal to current
  spot during merge preparation. Uniswap correctly rejects it. The corrected
  test helper reads each actual market and skips only an already-equal movement.
- 06 completes the whole journey, claims and all twenty state exports.

The separate positive control supplies5M additional actual Core liquidity to the
EXTERNAL reference, making6M versus the original1M. Only the outside test actor
receives10M ETH/ZZZ for supplying liquidity and trading. Initial prices, destination
external depth100k, independent reference depth2M, holder balances and protocol
reserves are unchanged. This is synthetic execution depth, not a real-route approval.

The initial growth checker wrongly required positive compound reserves after
activation had moved them into attributed idle. Its growth-only predicate now
accepts that valid classification, retains both-leg/funded-liability checks and
records typed failures. [Recorded diagnosis](controls/growth-fix/RECORDED_FAILURE_PROOF.json)
and exact old/new source scopes remain. No on-chain accounting bug is inferred.

There are31 distinct new offline checker logic controls: original10 contribution,
6 growth-fix and15 final maintenance controls, plus8 CLI smoke/refusal checks.
The earlier11 maintenance controls are an earlier source stage, not11 extra
methods. These controls verify tools, not production financial behavior.

## Source, measurement and preservation boundaries

All61 project sources and original compiler controls remain exact F6 pins.
The new producer compiles its201-source test dependency closure, including58
project sources. Real AccessController, PoolRegistry and optional Pyth source
are not instantiated here: controlled Access/registry and feeds/VRF/Permit2 remain
explicit seams. The unchanged trusted normal100-source graph/48 gates are reused,
not rerun or called constructor/operating approval. [Baseline](BASELINE.json)
records the protected unrelated files and original documentation hashes.

Large harness-only aggregate gas,512MiB memory and1MiB test-code allowances are
not deployment or transaction limits. A temporary owned-export filesystem
permission is restored exactly; optimizer/solc/Cancun settings stay unchanged.
Actual cold verification uses23 new accountless loopback node runs, maximum3
concurrent, with empty-code callers, authenticated current-state snapshots,
harness-call exclusion and recorded read-only requests. All owned nodes stop.
The1600-request/900-second instrumentation bound does not change production API
limits. No public RPC, signature, transaction, deployment or service adoption occurs.
Local gas prices do not qualify Robinhood execution limits or complete network fees.

## Remaining work and useful optimization target

The slow64-currency ZZZ opening state needs at least476,135 LESS ESTIMATED gas
for the existing profile. [Offline attribution](attribution/NOTES.md) uses the
retained trace without another EVM run; it preserves signed trace/refund residuals
and never sums overlapping frame work into a transaction budget. A private
bounded enrollment bitmap is an unimplemented candidate, not measured savings.
Fresh codecs/Factory/runtime pins, size/canonical/entitlement proofs would be
required. Do not lower50k reads/1M isolated sync, skip currencies, raise the ceiling
or relabel this refusal to manufacture qualification.

The following remain unqualified: every order/rarity permutation, full-width
lifetime coefficient spills combined with this workload, huge principal/per-NFT
caps,32 venues/four buckets, arbitrary actual token implementations and receivers,
full current-codec canonical cutover, complete claim/conversion/API/website
workloads, normal keeper software/jitter/host recovery, real independent feeds,
market depth/routes, providers/complete fees, OpenSea/VRF/authorities and independent
release approval. Finite cases do not prove all possibilities. Existing chains,
journals/checkpoints, sites, signer and user-paused heartbeat are unchanged.
