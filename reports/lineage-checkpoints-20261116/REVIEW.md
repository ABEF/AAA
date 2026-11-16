# Earnings checkpoints across authenticated replacement deployments

Baseline `51fc12b28de04dcbec6dfa2bd554aea753ad5027`,16November2026.
**Implemented reporting milestone; production NOT APPROVED.** No contract,
economic right, signer, runtime configuration or live environment was changed.

## Result

New **earnings checkpoint3** supports the complete configured accounting7/
custody5/fee-intake1/royalty4 same-chain lineage. One cumulative exact replay is
saved at an operating full-block cursor in an original, middle or current
deployment. Completed older deployments retain separate local ownership,
claims and conversion histories. The reader restores cumulative accounting once,
then processes every later raw event and authenticated handoff.

This closes an actual local implementation gap: checkpoint1/2 rejected all
predecessors. It preserves current-owner rights, collection/NFT/current-holdings
wallet earnings, exact ETH/ZZZ LP phases and original-currency royalty tickets.
Imports, backing transfers, claims and conversions never become new income.
Public endpoint fields and current-price USD semantics remain unchanged.

An epoch means one NFT/reward deployment, **not a pool or rebalance**. This feature
does not move funds, deploy contracts or change canonical handoff permissions.

## Important design choices

| Area | Implemented behavior |
| --- | --- |
| Recent replacement | Cursor may predate activation in an earlier epoch. All later handoffs and the complete rolling24-hour window remain raw. A too-young cursor fails; no synthetic daily total or silent fallback. |
| Cursor selection | Use authenticated activation windows, not overlapping deployment dates. A block containing handoff belongs to its final destination at block end. Cursor must be at/after its reviewed deployment anchor and historically operating, not frozen/preparing/retired. |
| Financial state | One cumulative raw exact state, not independent cumulative models added together. Preserve LP pending/high-low phase/direct credits/ordinals and royalty ticket/cursor state without settling them. |
| Payout history | Every local epoch contributes paid/conversion amounts once. Final all-NFT earned/paid/claimable reconciliation runs against the operating cursor. Retired source aggregate books remain checked. |
| Retired royalties | After backing is forwarded, old royalty pending/claimable views may revert. The builder does not use those live-backing views at retirement; it uses authenticated historical bookkeeping and reconciles remaining rights at the operating cursor. |
| Authentication | Recheck ordered peer/profile/runtime/history identity, origin, both handoff directions, receipt logs/order, ID/root commitments, creation/retirement/cursor anchors and suffix consistency. Checkpoint is reviewed evidence, not a consensus or log-completeness proof. |
| Lifetime growth | Completed prefix histories use history-only seeds; actual SQLite cursor, anchor, creation identity and duplicate-transaction checks remain. No raw prefix scan is needed merely to obtain stored old payouts. |
| Request isolation | Keep immutable encoded sections; decode fresh per-request maps. History-only reads do not decode the entire LP tree payload. No global mutable total cache or automatic artifact reload. |
| Currency admission | The offline historical builder can validate the actually admitted subset of reviewed descriptors at an old cursor before a later royalty currency exists. Unknown actual assets still reject; actual admitted assets retain runtime/decimal checks. Live reads and transaction preparation keep exact equality. |
| Compatibility | Existing1/2 format/codec rules remain. Only configured exact-accounting lineage selects3. Bool/int aliases, old schema relabeling, changed sources/peers and malformed ledger currency assignments reject. |

## Code and interaction changes

- `frontend_api/earnings_checkpoint_v3.py` supplies graph-bound format3,
  cumulative cursor capture, strict admission, immutable sections, history seeds,
  same-graph advancement and bounded offline construction.
- `frontend_api/lineage.py` separates authenticated graph verification from
  history retrieval. Existing raw callers remain raw. Earnings supplies a narrow
  checkpoint-aware history reader and receives verified local histories in a
  per-call map; guards and final canonical rechecks remain.
- `frontend_api/earnings.py` and `wallet_earnings.py` share cursor selection and
  history routing. Earlier completed models are not restored or counted twice.
  Future epochs use their real incoming activation boundary.
- `earnings_checkpoint.py` extracts the existing local history validator;
  `earnings_checkpoint_v2.py` retains public original-epoch capture/restore rules
  while providing a private complete-operating-epoch raw capture helper.
- `earnings_checkpoint_build.py` keeps the existing CLI/budgets/exclusive
  publication, dispatches from the authenticated profile and shares all-NFT
  reconciliation. Graph proofs are verified once per build boundary, not once
  per NFT. Lifetime payout books are combined separately from earned totals.
- `frontend_api/service.py` keeps strict ordinary asset admission. Only the
  new offline builder selects historical descriptors; there is no HTTP/config
  flag, new contribution currency or financial preparation bypass.

## Verification and corrections

[VERIFICATION.md](VERIFICATION.md) and the accompanying records preserve exact
method names, source stages, original failures and hashes. Checks cover two/three
epochs, original/middle/current cursors, a recent replacement, exact accounting,
multi-NFT wallets, dormant/late NFTs, original-currency admission, bounds,
concurrent restore, source/receipt/runtime/root/peer/anchor corruption and
historical standalone formats. Baseline rejection was reproduced from exact
Git source in an isolated import directory after edits; it is not mislabelled
chronological pre-edit execution.

There are **32 unique new passing methods**, zero skips and no old test methods
rerun. Repeated development invocations do not inflate this count.

The work caught and corrected an undefined local in the newly extracted builder
helper, the retired royalty live-balance assumption and repeated full-payload
decoding. Independent review also tightened typed profile equality, completed
ledger currency membership and the reviewed deployment lower bound. Original
failed stages remain; they are not release failures silently converted to passes.

Fixtures run real Projection constructors, Lineage receipt/code/header checks,
SQLite History, earnings/exact replay, builder, reader and publication. Runtime/
lifecycle/admission/getter observations are explicitly synthetic, partly derived
from a full-replay model. Differential equality is not an independent EVM oracle.
Literal LP allocation and11-unit royalty conservation add separate assertions.
No actual V10 contract handoff, provider, maximum state or host is qualified.

## Operator use

Follow [checkpoint3 procedure](../../docs/EARNINGS_CHECKPOINTS.md#checkpoint3-across-replacement-contracts)
and [operator inputs](../../docs/OPERATOR_MANUAL.md#prepare-and-rotate-an-earnings-checkpoint).
The existing unsigned command accepts a reviewed complete lineage config, an
eligible historical block and a new output path. Review independently, pin the
exact `path`/`sha256`, then separately authorize stop/restart. A digest is not an
on-chain `reviewHash` or permission to deploy.

Source semantics changed. Existing1/2/3 artifacts must be rebuilt/reviewed for
this installed backend before adoption; never edit source hashes or graph fields
to make old bytes pass. Preserve raw/WAL backups, old artifacts and configs. The
feature does not automatically prune, rotate, install, restart or approve anything.

## Remaining scope

The [financial-history task](../../TODO.md#task-financial-history) stays **In
progress**. This source milestone does not close:

- New-graph advancement after another replacement. A changed graph requires a
  reviewed rebuild. Importing an approved shorter-graph checkpoint as an offline
  prefix is **not implemented**; sufficiently large raw prefixes can exceed the
  retained event/work bounds and need a separate reviewed import/scaling design.
- The existing eight-predecessor, one-million combined configured event,
 32MiB artifact, tagged-node/depth and RPC/time limits. No default was raised;
  maximum-state/multi-year/provider/memory/latency qualification remains open.
- Archive completeness, independent ingestion comparison, retention/rotation,
  WAL-consistent off-host restore, Linux hosting and operating acceptance.
- Accelerating ordinary ownership/NFT claim-history/transaction-preparation
  consumers. They retain complete raw-history behavior.
- Actual sources/routes/fees/VRF/OpenSea/authorities and independent audit/release
  approval. No real provider or deployment was selected here.

All61 Solidity sources, unrelated dirty files, historical reports, shared signer,
websites, current Anvil/NFT/LP/balances, journals and user-paused heartbeat remain
unchanged. Source publication is separate from adoption.
