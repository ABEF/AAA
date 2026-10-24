# Liquidity placement, idle and keeper range review - 2026-10-25

Baseline: main `d06fcde9f641799ffdffa0d4a304c663ff0b7545`. This is an
undeployed development candidate, not a release approval. Older local drafts
and prior source-bound evidence must remain distinct.

## Accepted decisions

- Contributions default to **2% execution loss/undeployed value**, conversion
  stays **1%**, ordinary maintenance stays **3%**; gas is separate. Existing
  immediate governance setters retain the hard10% maximum. Raising a default
  does not fix idle or authorize automatic cap changes.
- The keeper may select only governance-preapproved **+/-25% and +/-50%**
  ranges, under explicitly reviewed bounded rules. These percentages describe
  **ZZZ's price in ETH**, not the inverse raw ETH/ZZZ pool ratio.
- Existing raw-price deployments/configurations retain their original semantics.
  New orientation and automatic selection require explicit versioned opt-in,
  runtime pins and reviewed policy. No production thresholds are invented.
- Current migration scope is guarded same-chain pool movement and explicit
  source-chain custody exit. The external custodian performs token migration or
  bridging. Integrated bridges/remote NFT and reward-ledger relocation are deferred
  optional work, not requirements for this release. Same-chain whole-collection
  handoff is retained; post-halt recovery is not solved.

## Design constraints

1. Improve placement before accepting more idle: at most two balancing passes,
   re-reading actual post-swap state and ignoring corrections no greater than1bp
   of available input. Keep marginal deployed-LP checks, final prices/policy,
   exact balances/approvals and incumbent fee separation. No unbounded search.
2. Reinvest **attributed bucket idle** through the existing compounding path,
   with fixed-price aggregate maintenance checks and cooldown. No raw-balance
   sweep, operator recipient, donation use, holder redemption or claim haircut.
3. Keep reward fractions, global division dust, compound/buyback reserves,
   quarantines and unknown donations classified. A tiny balance is not evidence
   of surplus. No generic clear-all function.
4. Keep adaptive policy default-disabled. Selection changes only desired width;
   the ordinary guarded rebalance applies actual ticks afterward. Bind reviewed
   pool policy, selected orientation, drift thresholds and cooldown; prevent
   repeated selection while an earlier width change is unapplied. Drift is not
   a continuous volatility observation and polling is not an execution promise.
5. Preserve old pending transaction recovery and signing-time budget semantics.
   Remove new retired bridge scheduling without deleting original pending evidence.

## Useful verification only

Strengthen affected harnesses first. Prove the original selected-fee shallow
case at an explicitly retained1% cap, thinner infeasible rollback, actual idle-only
LP increase, incumbent rewards/shares/prefund conservation, failed-operation
rollback and cooldown. Measure actual two-pass execution separately from the
substituted maximum-state cold-gas fixture; neither proves the other's scope.

Verify both range orientations, outward tick rounding, inverse up/down drift,
permission/configuration/lifecycle bounds, disabled/stale/pending policy and
keeper restart/readiness. Backend profiles must not silently reinterpret old
eligibility or absent getters. Rebuild changed objects under unchanged normal
runtime/initcode and gas limits. Preserve failing-first and oversize diagnostics;
reuse only exact unchanged evidence. No full regression or independent audit is
implied by focused tests.

## Preservation and publication

Do not touch existing8902/Anvil/NFT/LP/balance/journal/dist-overlay state,
website source/build/server, public signing/deployments or paused monitoring.
Keep public DEPLOYMENT null and the signer Anvil-only. Update the sole Todo,
features, roadmap, release/operator guidance and both memories. Publish only
owned changes on main; verify Git/remote separately from test evidence.
