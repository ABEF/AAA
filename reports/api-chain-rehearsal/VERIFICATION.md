# Actual API/Anvil rehearsal and full-wallet totals

Reviewed 2026-10-22. Internal scoped verification; production NOT APPROVED.

## Changes and evidence

- New isolated launcher: actual production read/preparation worker APIs, source-
  authenticated core, disposable Anvil and the existing API website coordinator.
- Production read-only wallet-summary endpoint: fixed 16-NFT chunks, one confirmed
  hash, complete inventory digest and no partial-total display. Website shows LP
  attached and funded ETH claimable across all holdings, independently of 8-card
  pages. Account changes clear totals and reset pagination.
- **46 affected Python tests pass** (12 new summary plus 34 existing API boundary
  cases); **70 affected JavaScript cases pass** (13 summary plus 57 API/session).
- Actual five holder transactions: mint, native activation, exact USDC approval,
  $5 USDC growth and combined ETH LP/royalty claim. Receipts, original reviews,
  balances and assertions are in the adjacent JSON evidence. Activation has no
  older rewards; approval does not alter LP; Entry adds at least 99% marginal LP.
- Claim recovery: deliberately fail the API protocol read after actual confirmation,
  retain the journal, construct a new coordinator and recover the same hash. One
  send only; balance increase equals claim minus receipt gas; LP is unchanged.
- Actual 18-NFT wallet crosses two summary chunks and three card pages. Exact
  before/after claim totals reconcile. Synthetic 1000-item chunk bounds are not a
  1000-user/production capacity test. Six real-API headless browser read/layout scenarios pass: holdings, totals, pagination, reload, account change, and desktop/mobile presentation. See browser.json.

## Corrections during rehearsal

The first fixture compile completed but Foundry's signature-cache write failed;
the scoped retry passed. The launcher correctly refused a CRLF/source-hash mismatch;
normalizing the new source to the compiler's LF input fixed it. The new mock venue
then lacked its position-approval interface; fixed only that local fixture.
The first actual journey confirmed mint/ETH activation, but USDC preparation
rejected a missing mock-pool liquidity getter before any approval. Added the
explicit funded mock-reserve view and restarted only this new disposable fixture.
No production validator was weakened. Earlier attempt receipts remain external.

The first browser probe supported only one listener per event, masking the
session's account-change listener when the signer subscribed. Corrected the test
provider to support multiple listeners. Review also fixed a real UI gap: account
changes must reset pagination and cancel old aggregate reads.

## Boundaries and review

No production Solidity, shared BrowserWallet/BrowserClient, public signing policy
or public DEPLOYMENT change. APIs/protocol accounting and chain transactions are
real locally; venue/price/VRF behavior remains explicitly mocked. The wallet is an
EIP-1193 RPC shim; actual MetaMask/Rabby popup acceptance remains open. Public
services, different-pair/cross-chain capabilities and independent audit are not
qualified. Existing 8900 processes were absent before this work; saved files remain.
Paused monitoring and the deferred load campaign remain unchanged.

Twelve of thirteen prior signer/backend bindings remain byte-identical; the
shared local launcher alone changed to select the new fixture. See reused-bindings.json.
Unchanged signer and Solidity suites were not rerun. New code has no key input,
arbitrary external RPC or operator HTTP endpoint. Summary reads recheck canonical
deployment, complete indexed ownership, per-chunk ownerOf, balances, freshness
and ancestry. Unavailable values cannot become zero; account/cursor/hash mismatches
discard the whole result. Budget exhaustion remains terminal. Do not extrapolate
local measurements to production throughput. Full-wallet historical earnings and
collection-wide aggregation remain open; no balances are relabeled as earnings.

See [operator runbook](../../docs/LOCAL_API_REHEARSAL.md). Publication is separate.

The adjacent probe scripts are historical captures from the external rehearsal
directory, whose `runs/` records and website checkout they reference. Do not run
them against another or public deployment. Use the runbook for a fresh fixture.
