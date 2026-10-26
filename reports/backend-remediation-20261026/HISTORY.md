# Funded LP history conservation and NFT reward math

Reviewed 26 October 2026 (Europe/Paris). This work changes backend validation,
not Solidity, economic rights, custody, rates, signing or a deployment profile.
All executions used synthetic byte-level RPC responses and disposable SQLite
databases. No network request, public transaction, service, existing index,
Anvil state, wallet journal or website was changed.

## Confirmed defects and fixes

The existing replay independently accepted a FeeController `FeesAllocated`
event and a Rewards `PoolRewardsCredited` event. Chain reward indexes were
reconciled, but the fee event's gross and reserved portions were not tied to
that funded credit. With actual current3/fee1 Projection, History, Indexer and
SQLite composition:

1. Changing only `FeesAllocated(100,0)` to `(200,0)` returned collection gross
   **200**, compound **10** and buyback **10**, while the original funded credit,
   actual indexes and NFT entitlement still represented **80 individual + 10
   collective**. [Recorded counterexample](lp-conservation-counterexample.json).
2. Removing the fee log while retaining the credit and matching chain views
   still returned NFT/wallet earnings.
3. A configured fee-intake1 deployment did not check the actual bound
   FeeController's `FEE_INTAKE_VERSION()`. A response of zero was accepted.
4. After adding credit conservation, changing only carried dust from zero to
   19 still returned gross **119**, although the actual pinned fee dust was
   zero. [Recorded dust counterexample](lp-dust-counterexample.json).

These are reporting-integrity and availability-boundary defects, not an
on-chain withdrawal or entitlement exploit. Corrupt or contradictory history
must fail explicitly rather than publish plausible financial amounts.

The backend now uses explicit fee-intake1 semantics:

- [Profile verification](../../frontend_api/earnings.py) reads the actual
  sealed FeeController runtime, controller/module binding and intake version.
- [Replay](../../frontend_api/earnings_replay.py) requires every positive fee
  distribution to match exactly one preceding funded reward credit from the
  configured Rewards emitter, for the same bucket, asset and transaction.
  An allocation of `20*n` requires `16*n` individual and `2*n` collective units.
- A sub-20-unit carried-only receipt requires no reward credit. Existing-owner
  dust settlement instead matches its exact individual-only credit. Unrelated
  royalty logs may interleave; immediate adjacency is not required. Multiple
  collect/settle pairs in one transaction remain valid.
- An unmatched credit rejects the next recognized event from another
  transaction, or rejects epoch completion. An epoch switch cannot discard it.
- Each epoch's observed fee keys are reconciled against the actual
  FeeController `dust(bucket,asset)` at its pinned cutoff, including a final
  zero remainder. The [typed native getter](../../frontend_api/service.py)
  accepts native ETH only in that getter's asset argument.
- [Wallet replay](../../frontend_api/wallet_earnings.py) selects the same
  explicit grammar per verified epoch. Imported ownership/prefund records are
  skipped until the verified successor activation; inherited earnings are not
  added again. Observed fee keys reset per epoch, while lifetime accounting
  survives.

Legacy fee-intake0 keeps its former explicit event grammar and does not call
the new version/dust getters. No response schema changes. No automatic database
repair or profile relabeling is performed.

## Independent NFT reward calculation

The strengthened example deliberately separates LP shares from rarity:

| NFT | LP share | Royalty weight | Individual LP from 600 gross | Equal collective | Royalties from 600 | Total NFT income |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 11 | 100/600 | 3/6 | 80 | 20 | 300 | 400 |
| 22 | 300/600 | 1/6 | 240 | 20 | 100 | 360 |
| 33 | 200/600 | 2/6 | 160 | 20 | 200 | 380 |

The NFT sum is **1,140**: 540 holder LP fees plus 600 royalties. The other
60 LP units remain 30 compounding and 30 buyback allocations. Rarity never
changes individual LP shares or the equal collective share.

A subsequent 300-share top-up to NFT11 changes future LP shares to **4:3:2**.
It does not rewrite past amounts or change royalty weights **3:1:2**. After
another 900 gross LP fee receipt and 600 royalties, cumulative NFT income is
**1,050 / 730 / 770**, totaling **2,550** (1,350 net LP plus 1,200 royalties).
The exact independent expected sums are asserted, not derived by calling the
production calculation a second time.

Collection gross allocation and an NFT's own net rewards remain distinct.
Earned history adds credited individual LP, eligible collective LP and eligible
rarity-weighted royalties. Claims, transfers, conversions and custody returns
are not new income. Lifetime history follows the NFT across owners. Existing
source-currency conversion/claim reconciliation remains in place; a native
credit must not be added a second time to an already combined claimable view.
USD history marks originally earned currencies at today's confirmed prices;
it is not the current ETH claimable balance, a historical USD mark, or a
promise of conversion proceeds. Missing required prices remain unavailable.

## Executed evidence and exact scopes

| Record | Result | Scope |
| --- | --- | --- |
| [Original before](lp-conservation-before.json), [log](lp-conservation-before.log) | 4 methods; 4 assertion failures across 3 methods, 1 positive passes; no errors | Real current3 API/SQLite composition before the conservation fix. Missing allocation has separate NFT and wallet subcases. |
| [Original after](lp-conservation-after.json), [log](lp-conservation-after.log) | 8 methods pass | Four API and four strict replay methods at the original recorded production/test hashes. |
| [Original test preimage](lp-conservation-eight-test-preimage.py.txt) | Preserved | Exact test source used by the preceding 8-method capture; SHA-256 matches that capture. |
| [Independent weights/top-up](history-semantic.json), [log](history-semantic.log) | 1 changed method passes | Nonproportional LP/rarity example and future top-up; a focused rerun, not an extra distinct method. |
| [Dust before](history-dust-before.json), [log](history-dust-before.log) | 3 methods; 1 fails three endpoint subcases, 2 positives pass; no errors | False carried remainder accepted by collection/NFT/wallet; legitimate native dust and legacy controls. |
| [Dust after](history-dust-after.json), [log](history-dust-after.log) | 7 methods pass | Three dust API and four affected API regressions after pinned dust reconciliation. Fixture adds the actual new getter; this is a separately recorded source scope. |
| [Canonical fee1](history-canonical.json), [log](history-canonical.log) | 1 new method passes | Current grammar, successor import skipping, per-epoch key reset, retained lifetime totals and valid post-activation fee pair/dust. |

The final [test module](../../tests_python/test_lp_fee_conservation.py) defines
**12 distinct methods**. The scoped rows above overlap and must not be summed
as additional distinct coverage. The separate aggregate affected-suite capture,
owned by the parent review, determines final-source combined coverage. No full
release regression, live provider, on-chain qualification or independent audit
is claimed here. Runners retain failed assertions, exact selection, timings and
source hashes; all captures record unchanged inputs during their own execution.

## Remaining trust and resource limits

- This rejects contradictory indexed history against pinned authoritative
  views. Head state cannot prove historical event completeness, authenticity or
  per-period ordering against a provider/operator capable of supplying coherent
  false data. Preserve independent raw receipts and use the existing complete
  ingestion/history-audit operating gates.
- In particular, deleting an isolated fee-only receipt for a previously
  unobserved key leaves no reward-index signal and no touched key. A later
  receipt or settlement may expose the omission; this patch does not claim a
  cryptographic proof of that missing historical receipt. Intermediate dust or
  timing manipulation that restores the true final remainder still requires
  authentic complete logs to rule out.
- Dust checks add one bounded pinned read per **observed fee key in that
  epoch**, never a new all-bucket/all-admitted-currency sweep. The configured
  existing asset/bucket/event bounds and shared request RPC/deadline budget
  remain active. A missing getter, mismatched value, stale anchor or exhausted
  budget rejects the response; it does not manufacture zero income.
- Dust and index arithmetic use raw source units and exact integer carries.
  Global index-rounding residue remains reserved; this backend change does not
  transfer or sweep it. Live funding/token behavior still depends on the
  reviewed on-chain contracts and providers.
- Production service, feed, route, randomness, authority, marketplace and
  operating qualification plus independent audit remain open.
