# Royalty conversion: internal security review

Reviewed 2026-10-19. This is an internal source review with local execution,
not an independent audit or production approval. See [verification](VERIFICATION.md)
for the exact final source and tool bindings; older attempts remain distinct.

## Accounting and authority

- `convertBatch` accepts only the existing authorized keeper, the sealed canonical
  NFT binding and operating/unpaused/non-preparing state. IDs are strictly sorted,
  unique, active and limited to 32. It aggregates checkpointed earned whole units,
  never quarantined receipts, raw unknown funds, LP assets or arbitrary balances.
- Source debt is removed before external execution. ETH output is measured and
  credited to those same NFT IDs, proportionally to source amounts. It is never
  processed through the global native-royalty index. Native pending receipts are
  synchronized before conversion; fractions/dust stay in the source ledger.
- All received ETH is allocated using cumulative floor differences. Selection/order
  can influence rounding by a wei; no independent floor remainder is swept to an
  operator. No native liability or entitlement is created without received backing.
- Original-currency claims remain valid. A concurrent claim or changed balance may
  invalidate a prepared batch's minimum, but cannot produce duplicate payment.
  Ownership is not cached by conversion: the eventual current owner claims.
- Converter, ledger and wrapper addresses are fixed. The ledger binds a converter
  only once before seal with bidirectional controller/ledger checks. The converter
  only pulls from and pays its bound ledger; no arbitrary target, recipient or
  rescue is provided. A successor binds its own converter before sealing.

## External execution and callback review

- The executor uses a typed single-hop V3 call. Reviewed runtime hashes and pool/
  factory/router/token wiring are checked around the swap. The 99% oracle floor
  rounds upward; caller minima can only strengthen it. A zero/stale oracle fails,
  and the ten-minute deadline bound remains. Network gas is outside this cap.
- Exact transfer deltas, bounded approvals/reset, wrapper-balance restoration and
  native deltas reject dishonest outputs, tax/rebase behavior and partial execution.
  WETH must unwrap exactly; its admitted proxy admin/implementation/owner pins are
  checked. Direct-code policy mode is suitable only for an independently reviewed
  non-proxy wrapper. A runtime hash alone cannot identify an unreviewed proxy.
- Ledger and converter mutation entrypoints have independent reentrancy guards.
  Conversion checks preparation/pause/keeper again after callbacks and the ledger's
  economic modifier checks canonical state after execution. Failed checks revert
  swaps and every intermediate accounting update together.
- **Review fix:** `claimable` and `pending` now reject callback reads while a ledger
  operation is in progress. Otherwise a token approval-reset callback could observe
  returned ETH before its batch-specific debt was recorded, appearing as ordinary
  unindexed receipts. The new read-only callback test verifies rejection. Public
  raw storage getters are not a substitute for these consistent valuation views.

## Failure isolation and migration

The user explicitly accepted delayed per-currency eligibility. Each optional token
sync has a 250,000-gas self-call boundary, copies no returned failure bytes and can
only be entered by the ledger itself. A gas reserve prevents deliberately starving
the isolated call; overall transaction gas shortages still revert. The total
inventory is bounded by 17 currencies and 1,000 activations. Healthy activation
updates global rarity weight and healthy-asset eligibility; failed assets retain
their earlier cohort and emit a deferred event.

Recovery indexes unseen funds using the earlier eligible weight, then enrolls the
waiting activation interval at that new index. This intentionally includes receipts
arriving during an outage: exact arrival ownership cannot be reconstructed from an
unreadable ERC20 balance. Newly active NFTs receive no retroactive catch-up for
that currency. Empty earlier cohorts quarantine their receipts. Binary searches
over bounded recovery intervals avoid unbounded per-holder synchronization.

Canonical capture still requires readable exact backing. Settlement uses the
earlier asset weight, recovers waiting members, and exports effective per-NFT paid
indices. Import rebuilds activation ordinals and enables the fully settled cohort
on activation. Exported record shapes and classified backing remain unchanged.
Tests cover converted ETH plus remaining token rights through export/import as
well as existing full handoff and abort tests. This is same-chain evidence only.

## Keeper and operational risks

The optional worker reads at one confirmed canonical hash and checks bindings,
runtime pins, limits and route source. It scans one currency and at most 32 NFTs,
rotates currencies even after a failure, and alternates priority with other upkeep.
Only the existing serial sender simulates, estimates, budgets, records pending
intent and signs. There is no separate signer or nonce path. Existing receipts
remain the authority after restart; converted balances are already zero on-chain.
Code/policy drift, gas caps, stale/reorged snapshots and failed quotes defer work.
An extra gas-to-output budget prevents uneconomic tiny conversions; gas comes
from the keeper wallet, not holder royalties.

The implementation does not qualify real currencies, mutable token/router
implementations, RPC liveness, MEV, prices, wrapper solvency, OpenSea settlement or
an operating signer. Immediate governance can admit harmful dependencies; no
timelock was silently reintroduced. A broken token can still block its own claims,
`syncAll` and exact canonical backing operations. Source-currency dust can remain
until further receipts make whole units claimable. See the [operator procedure](../../docs/ROYALTY_SETTLEMENT.md).

## Release boundary

No production contracts or servers were deployed/changed. The separate frontend
still needs conversion history and per-currency eligibility presentation. Actual
runtime inventory (including the new optional fixed helper), qualified routes and
feeds, dry/live keeper and marketplace rehearsals, final-source review and
independent audit/remediation remain open in the central Todo. Existing 80/10/5/5
LP allocation, requested 5% royalties and rarity weights remain unchanged.
