# Website API adapter: scoped verification - 2026-10-21

**Result: read/unsigned-review candidate verified within the scope below.
Production release remains NOT APPROVED.** Public configuration stays null;
the existing signer remains restricted to the local fixture. No public contract,
API, signer service or production transaction is deployed by this change.

## Implemented

The website separates reviewed API integration from the Anvil session/signer.
It supports ordinary authorized wallet addresses, bounded holdings pages,
confirmed LP and available earnings, exact token-unit activation/growth quotes,
and unsigned mint/approval/Entry/ETH-claim review. It independently compares
reviewed chain anchors, canonical snapshot headers, contract runtime, service
configuration identities, calldata, expiry, price-derived input, marginal LP
addition and network-fee bounds. There is **no send method** in this adapter.

Configuration is fixed at build time, not selected by URL/storage/provider data.
An invalid configuration fails closed. Default simulation and the existing local
launcher remain separate. Missing price/history/balance data never becomes zero.
Eight-card pages never masquerade as full-wallet or collection totals.

## New evidence

| Check | Result and limits |
| --- | --- |
| Eleven API fixtures | Generated through current Python `Projection`, `Transactions` and `ActivationTransactions`, using existing byte-level mocked RPCs. ETH/ZZZ/USDC/USDG activation, exact ERC20 approvals, growth including $5 native/6-decimal cases, mint and ETH claim. This is actual API code with mocked dependencies, not on-chain qualification. |
| Focused JavaScript | **57 pass, zero failures/skips**, including response reconstruction; wrong chain/config/runtime/sender/calldata; stale/reorg/expired snapshots; input precision; $100 rounding/$5 floor; 99% LP bounds; gas arithmetic; exact approvals; claims; unavailable balances; cancellation, account selection/restoration and bounded inventory concurrency. |
| Headless browser | **Eight scenarios pass:** unchanged default demo; ZZZ activation, ETH activation, USDC approval, growth, ETH claim, mint review; invalid configuration. This uses isolated fake wallet/API/node responses, not MetaMask/Rabby acceptance. No wallet transaction/signature method was called. |
| Syntax/build | New modules and app syntax pass; static build has **5,597 files**. No artwork regeneration or economic configuration change. |
| Reused evidence | All thirteen prior chain-reader source bindings still match. Existing signer/client, local backend and unchanged Solidity suites were not rerun. The 10/25/100-user campaign remains deferred. |

Records: [focused TAP](tests.tap), [browser results](browser-result.json),
[source bindings](source-sha256.json), [API fixture generator](../../tests_python/export_website_api_fixtures.py).
Website tests and JSON fixtures live in the website repository. The source binding
record identifies their exact bytes. The fixture hashes can be reproduced by
running the generator with `--output` to an external JSON path.

Initial harness corrections: the generic activation RPC fixture needed a zero
NFT bucket when converted to a complete dormant projection; this was a fixture
correction, not a production backend defect. Playwright's bundled browser was
absent, so the headless check used installed Chrome in a separate temporary
profile. An unsupported Node `json` reporter invocation ran no tests; the final
run uses TAP. These attempts are not counted as passing cases.

## Internal review and remaining boundaries

- **No silent signer expansion:** automatic approval review rejected a proposed
  shared-signer modification. It was not applied. The implemented alternative
  only reads and prepares unsigned reviews; the public signer remains absent.
- The backend and pinned node still have a trust relationship. Matching hashes
  are identity/consistency checks, not cryptographic state proofs, independent
  audit or a finality guarantee. Trace evidence is supplied by the reviewed API.
- Runtime/config changes require explicit requalification. No provider, feed,
  real route, authority, creator payment or production fee policy was inferred.
- No global earnings or wallet subtotal is computed from partial pages. Full
  collection browsing/aggregation in this profile remains open.
- Claimed-source fallback, market-wide concurrency, browser-extension signing,
  speed-up/cancel handling and live provider/hosting qualification remain open.
- No original local chain/service was restarted, reset, funded or transacted
  against. No paused monitoring automation was resumed. The temporary static
  review server is separate from the user's port-8900 fixture.

Operator procedure: [reviewed website profile](../../docs/DEPLOYMENT_WEBSITE.md).
Publication is recorded separately; passing local checks alone does not prove
GitHub or server deployment.
