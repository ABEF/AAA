# Wallet-summary integrity and operating-boundary remediation

## Scope

This slice follows the current request's fee-breakdown steering through wallet
summary/collection/earnings chunks, exact current prices, snapshot freshness and
HTTP/worker admission. Initial main is `30eb4df`, after the three earlier backend
composition fixes. It is not a new broad audit or an independent release review.

Reviewed paths include `portfolio.py`, `collection.py`, `wallet_earnings.py`,
`earnings.py`, `earnings_prices.py`, Projection's typed ABI/header/admission/final
checks, request-local work budgets and HTTP/worker/client-admission boundaries.
No public RPC, original SQLite/journal, service, Anvil/NFT/LP/balance, website,
signer or monitor changed. Existing keeper/provider qualification remains open;
this slice did not rerun operating or broad unchanged test suites.

## Confirmed defect: malformed LP data became a partial successful chunk

`ProjectionError` inherits `RpcError`. Wallet `portfolio.read` raised a
ProjectionError for invalid `currentLPValue` Boolean words or a false availability
flag paired with a nonzero amount, then caught its own error under `except
RpcError` and returned a successful chunk with LP unavailable and an ETH total.
Collection/NFT paths already distinguish malformed/contradictory data from an
ordinary unavailable view. This was a backend integrity inconsistency; no funds
or transaction authority were lost or gained.

The LP branch now rethrows `ProjectionError` and `WorkLimit` before handling
ordinary RPC/view failures. The native-claimable branch had the same exception
ordering problem for malformed static ABI and is corrected too. A genuine
contract-view outage still makes that whole metric unavailable/null while the
independent metric may remain available. No missing currency is treated as zero.

The first five new regression methods demonstrate the LP failure: four invalid
subcase assertions fail on the original code, and all five pass after the first
narrow fix. Those preliminary results retain their own exact source/fixture
hashes and archived preimages; they are not added again to final coverage.

## Current-profile inactive NFT invariant in aggregate totals

The single-NFT Projection is separately validated by the profile slice. Wallet
summary bypasses that full Projection for efficiency, so it also needs to avoid
counting impossible funded rewards for a never-activated NFT.

For explicit accounting3 only, summary now reads the pinned royalty ledger's
`weightOf(id)` once, validates the 0..3 bound, and treats zero as the current
fixed implementation's permanent never-activated marker. It still reads actual
LP and native LP/royalty claimable views: an available nonzero LP value or native
entitlement for that inactive NFT rejects the chunk. It does not assume zero,
skip a failed view, or fabricate retroactive rights. Healthy zero-valued inactive
NFTs coexist with activated NFTs in a correct total. Genuine view outages remain
unavailable; already activated NFTs retain claimable rights while principal is
parked/outbound/unvalued because their nonzero royalty weight persists.

This uses one additional block-pinned read per selected NFT, not three status/
share calls or the heavy single-NFT/history projection. Per-item fixture work
rises from four to five calls; a full sixteen-item chunk has at most81 such
item/count reads rather than65. Deployment/history/admission verification has
its separate existing request budget. Historical accounting1/2 keeps its old
read shape and receives no newly guessed getter or profile semantics.

## Final executed verification

- The extended eleven new methods fail six subcases before the ETH/inactive
  fixes: malformed claimable ABI, each impossible inactive LP/LP-fee/royalty
  contribution, and out-of-bound royalty weights. No environment/test errors.
- After correction, **23 distinct methods pass once at the final source**:
  eleven new integrity/state methods plus twelve existing wallet-summary tests.
  The shared deterministic fixture is now explicit accounting3 and models the
  extra weight getter. Its corresponding finite-call bound is updated rather
  than removed. The full affected fixture class reruns because that fixture
  changed; no unrelated broad suite is repeated.
- Malformed native ABI is exercised through actual Projection `_call/_uint`
  decoding with only a synthetic transport response. Other cases use the
  existing canonical-snapshot/ABI fixture. This is not actual provider, hosted
  HTTP, native venue or production-capacity qualification.
- Tests preserve genuine LP/ETH outage isolation, work-limit propagation, valid
  pinned sums, unknown-wallet/reorg/stale/cursor failures, full inventory chunk
  coverage, no assumed inactive zero and historical read compatibility.

See [initial LP failure](summary-integrity-before.json),
[initial LP correction](summary-integrity-after.json),
[extended before](summary-state-before.json) and
[final23](summary-state-after.json). Repeated methods/subcases are not additional
distinct coverage. Original fixture/test/source preimages preserve earlier
source-scoped evidence after the shared fixture update.

## Other boundaries checked

- Projection `_header` already rejects a number different from the requested
  block; chunks use the canonical hash and finish/freshness check before release.
  Inventory and configuration hashes bind all chunks. A suspected number-mixing
  gap was excluded by reading the actual common helper; no redundant fix added.
- Optional earnings-price failure deliberately hides USD while preserving raw
  original-currency amounts. It is not the same as ignoring malformed core LP
  data, and no source amounts are renamed ETH or summed across denominations.
- Worker/client admission uses independent finite connection/worker/client
  leases, request-local budgets and cleanup quarantine. Header/body/time bounds
  and fixed sanitized errors remain. IP budgets are capacity controls, not
  wallet authentication; actual NAT/proxy/service capacity still needs deployment
  qualification. No new bypass was confirmed in these inspected paths.

## Final source identity and operator effect

- `frontend_api/portfolio.py`: `722014b141ff82e189469563f1f661dfaf23e600823a5af77f68b281c30ba6a3`.
- `tests_python/test_wallet_summary.py`: `926d617e1d69ec41e62975241febfc3fbfbcf1904cec0f8dca59f1a99fbc9dd9`.
- `tests_python/test_wallet_summary_integrity.py`: `47ce6419c7a8d8c3c82684c6dae57d4605be989e5d7079accf071c5b28fbfa69`.

Response fields and economic rules are unchanged. An internally inconsistent
wallet-summary snapshot now fails rather than releasing a partial successful
chunk. Consumers must wait for every valid inventory/block-matched chunk before
displaying a total; unavailable or rejected chunks cannot be added as zero.
This source correction requires a reviewed compatible service release before
live use; it did not restart a server or alter any saved state. Production remains
NOT APPROVED, and root owns Todo/operator/memory/publication updates.
