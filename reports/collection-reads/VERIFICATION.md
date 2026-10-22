# Confirmed collection reads and production explorer

Reviewed 2026-10-23. Internal scoped verification; production NOT APPROVED.

## Result

Production read API supplies bounded collection chunks at one confirmed block.
It reconciles complete indexed ownership, minted count, reverse mint identities,
eligibility, traits and the actual NFT currentLPValue view. The website validates
all rows/cursors/inventory digests before displaying total attached LP. It retains
per-NFT rounding and unknown marks, not lifetime contributions or guessed prices.
Activated counts eligibility; remote/parked values cannot become local LP.

The opt-in website profile now has a read-only collection explorer: search,
eligibility/rarity/color/style filters, current-LP/newest sorting, 16-row pages,
verified owner and artwork, and current confirmed position details. Earnings remain
independent of LP reads. Missing pages cannot publish a partial inventory or total.
Navigation clears/cancels old reads; late responses cannot repopulate the page.
The shipped public configuration remains null and its collection remains simulated.

## Evidence

- 74 affected Python passes: 16 collection, 34 existing API, 12 wallet summary
  and 12 wallet earnings. Actual SQLite indexer/HTTP and supervised-dispatch checks
  are included; RPC/venue data are explicit byte-level/local substitutes. Imported
  history fixture AST matches main except unrelated test methods not executed by
  this campaign. See fixture-scope.json and results.json.
- 75 affected JavaScript passes: 18 new collection cases plus 57 API/session cases
  imported once. Actual Python output is a sanitized fixture. Checks reject changed
  identities/blocks, bad traits/weights/stages, invented totals, missing chunks,
  duplicate ordinals, cancelled reads and malformed inventories. A 1,000-NFT case
  verifies 63 bounded requests; it is not a user-load/real-market latency test.
- Twelve isolated headless browser scenarios: six new collection desktop/mobile,
  pagination/search/filter/artwork/details, unavailable/missing-page and navigation
  cancellation cases; six retained production-profile wallet/earnings/mint cases.
  Screenshots were inspected. API/RPC/wallet are mocked; no actual extension, chain,
  user browser, transaction, NFT or LP state was touched.
- 34 actual isolated Nginx checks pass, including four new collection allowlist,
  cursor, method and rejection checks. Sanitized logs pass. This is Windows/local
  HTTP with fake backend data; production Linux/TLS/provider hosting remains open.
- Clean static build has 5,598 files; the local repair overlay hash is unchanged.
- Unchanged Solidity, shared signer, coordinator and deferred load campaign were
  not rerun. Public signing remains disabled. No service/chain reset, browser journal
  cleanup, paused-monitor restart or public contract transaction occurred.

## Findings and corrections

Initial JS fixtures mixed Number/BigInt and used a different configuration identity;
fixed the fixtures without weakening validation. Browser checks found omitted new
button selectors and a hidden stale loading presentation after route cancellation;
fixed both and reran the affected browser scenarios. One screenshot helper used an
ambiguous heading selector; narrowed the helper. The collection's new thumbnail
uses the catalogue's actual src field. Summary cards now span the available width.

## Remaining boundaries

The new view is implemented, not a qualified public API deployment. Real pricing,
complete archive/backfill history, production latency at 1,000 NFTs, Linux/TLS/RPC
hosting and independent audit remain open. Existing freshness/RPC/work limits stay
enforced: an oversized/slow complete read fails rather than truncating or mixing
blocks. Browser snapshots identify their block; refresh observes new state.

Different-pair LP conversion/composition epochs and future-chain canonical handoff
remain unfinished before sealing; current pair checks are retained. OpenSea primary
mint integration remains unqualified. The existing local mint-repair overlay and
pending browser archival must be preserved. Publication is recorded separately.
