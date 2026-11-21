# Compact wallet reads and bounded earnings — 21 November 2026

Combined ownership/financial pages remove the previous request-count impossibility
for the controlled1,000-NFT/three-currency wallet. Currency paging removes the
16-NFT/65-royalty unsliced RPC impossibility without higher limits. This is source
implementation and finite controlled qualification; production is not approved.

## Material changes

- Added accounting7 `wallet_view_profile:1` and GET
  `/v1/wallets/{owner}/view/{block}/{nft_offset}/{asset_offset}`. Each page has at
  most16NFTs/four descriptors, full NFT/currency inventories and independent
  digests, history, lifecycle and canonical cutoff. Summary appears only at the
  first currency slice and must not be counted again.
- Preserved complete raw history/exact-unit replay, global reconciliation, LP
  component checks and full-source conversion/claim accounting. Only the current
  per-NFT paid-entitlement checks, returned rows and price reads are currency-paged.
  Complete earnings require every NFT/currency tile. USD is computed after raw
  per-currency aggregation; claims/conversions/imports are not income.
- Request-local canonical reuse sits outside the existing BudgetedRPC. Only
  identical successful eth_call/eth_getCode with exact canonical blockHash can
  share raw results; all decoders, runtime and semantic checks still run. Head,
  chain, headers, final/canonical/checkpoint checks and failures remain live.
  Copies are cleared on every exit. Retention is bounded to64KiB encoded key+JSON
  per entry/8MiB total, including keys; larger replies/keys bypass reuse. These
  are encoded-byte bounds, not process RSS guarantees.
- Source9/source10 use the explicitly advertised compact wire and reuse its
  financial result in the view, avoiding separate ownership/summary/earnings
  passes. Existing profile families and old wires remain explicit. Missing
  capability uses the previous reader; unknown capability or failed advertised
  compact reads never silently downgrade.
- Current-profile GETs share a per-origin/prefix gate: starts at least1second
  apart, one active, at most32 queued; no automatic retry. This self-paces under
  the unchanged server allowance and does not reserve capacity for the browser.
- Later optional currency reads can leave earnings unavailable while complete
  holdings/summary survive only for429 or explicitly classified503 service_busy.
  Generic503, integrity/history/work failures, cancellation and stale/reorged
  proofs remain terminal. Safe backend transport failure is explicitly null.
- Final portfolio publication now rechecks captured financial age AFTER card,
  canonical and identity awaits. Added the missing strict Nginx GET allowlist for
  legacy fixed-block ownership pages, preserving all methods/rates/bounds.

## Controlled workloads

Production Projection, History/SQLite, exact LP replay, royalty reconciliation and
Prices execute against new synthetic V9/source9 runtime/view/feed observations.
All66 descriptors in the large-currency case have explicit controlled price
policies, unlike the earlier three-price refusal. No live chain or provider runs.

| Holdings / descriptors | Protocol + compact reads | Maximum RPC/request | Max response bytes | Summed handler time |
| --- | ---: | ---: | ---: | ---: |
|1 /3 |2 |274 |13,399 |1.086s |
|17 /3 |3 |499 |17,042 |1.089s |
|16 /66 (65royalty + LP-only ZZZ) |18 |904 |24,159 |16.810s |
|1,000 /3 |64 |499 |17,069 |83.621s |

The1,000 case verifies3,000 NFT/currency pairs; the66-descriptor case verifies1,056
pairs over17currency pages. Literal raw/USD expectations check current-owner
history through transfer, prior claim/conversion, exact86,400s boundary exclusion,
LP80% individual/10% collective income and excluded5%/5% reserves. ETH claimable
header remains ETH-only; pending source ZZZ LP and token royalties are separate.

With8visible cards each requesting NFT+history, complete1,000-wallet refresh is
80API reads rather than206 (earlier190 core reads plus16cards). Actual unchanged
ClientAdmission permits its last ideal zero-latency read at68s. The browser's
stricter self-pacing lower bound is79s. Neither is a latency guarantee: the
producer uses a fixed wall clock, serial handler time omits worker startup,
network, RPC/provider and card costs, and no live HTTP/TLS/host freshness is passed.

The producer predates the final cache-retention guard. No unchanged case reran.
[Saved-wire cap compatibility](CAP_COMPATIBILITY.json) checks all captured eligible
replies offline: max encoded entry1,194bytes, conservative per-request retention
upper bound1,079,376bytes, below both new caps. This establishes nonbinding caps
for those saved small synthetic replies, not new timing or real runtime capacity.

## Verification and original failures

-26 distinct NEW canonical-cache Python methods pass in21+1+4stages. A new
  capture-timing regression first failed, was corrected, then alone passed.
  Four final retention checks cover oversized replies/keys, aggregate exhaustion
  and nonserializable results. Earlier passing bodies were not repeated.
-19 distinct NEW compact API/Python methods pass:18initial, one affected admission
  expectation corrected/rerun, plus one proxy ownership regression red/green.
  Includes actual owned loopback GET/POST/admission behavior, worker dispatch/
  result limits, selected cursors and identity/history/final failure boundaries.
-90 distinct NEW JS methods have passing stages:80initial, then5producer/ASCII
  passes with one UI fixture failure, then6follow-up passes (five new successes
  plus only the affected503 assertion rerun). Four saved producer fixtures pass
  the actual consumer. Controlled source10 constructor/native/NFT composition,
  per-origin gate, cancellation, empty contradictions, raw-first rounding,
  malformed/missing pages, classified failures and late expiry are covered.
- The original maximum-currency stage reached all17pages but failed its final
  source-immutability assertion when checkpoint source closure changed during
  the run. Only that failed workload reran.1/17 use the earlier declared closure;
  maximum/1,000 use the later closure. None used a checkpoint. Original outputs,
  executed drivers and exact source scopes are preserved.
- First21cache/80JS tool outputs were not saved as separate original streams or
  contemporaneous test-byte hashes. They are explicitly marked faithful tool
  transcriptions/reconstructed source stages. Later raw streams/before-after
  hashes are captured; the minor transcription timing correction is an immutable
  [erratum](agent-evidence/TRANSCRIPTION_ERRATA.json), not overwritten evidence.
- No historical suite or unchanged Solidity/browser/Python method reran. Only
  explicitly affected assertions/failures were repeated. Counts do not prove
  exhaustive dynamic coverage or independent approval.

Current static inventory:182Python files,2,001 named definitions
(1,818functions/183classes),278lambdas; unchanged F6 source61/dependency39/control4,
1,021ABI rows. The normal verifier points to the new source-bound inventory.

## Boundaries and remaining work

1.1,000NFTs ×66descriptors needs1,071compact tiles: it cannot finish within120s.
  The consumer explicitly leaves earnings unavailable while collecting complete
  first-slice holdings/summary. No partial income is published, history truncated
  or limit raised. Still-open full cross-product capacity is separate from the
  two demonstrated old architectural blockers now addressed.
2.Actual providers, HTTP/TLS/Ubuntu/worker concurrency, shared-IP traffic and
  deployment-to-head history/freshness require operating qualification. Fixtures
  are V9/source9 with synthetic runtimes; source10 browser composition is controlled,
  not full normal F6/V10 EVM/market acceptance. Real feeds/routes/fees remain open.
3.Checkpoint semantic-source identity intentionally changes, including new
  wallet_view/canonical_cache and affected portfolio/prices. Preserve all original
  checkpoint1/2/3, review, raw DB and journals. Explicitly rebuild/review/re-pin
  matching artifacts for separately authorized backend/worker/proxy/website
  adoption; never hot-edit hashes or reinterpret old artifacts.
4.No contracts, financial rights, caps,25s/1,024RPC/2,048POST/1MiB limits, age/admission
  bounds, signer or public configuration changed. No website build/rollout,
  service/chain reset, public transaction/seal or heartbeat restart occurred.

See [operator procedure](../../docs/OPERATOR_MANUAL.md#complete-wallet-financial-view),
[API wire](../../docs/FRONTEND_API.md#compact-wallet-view-and-bounded-currencies),
[qualification](QUALIFICATION.json), [source reconciliation](SOURCE_SCOPE_RECONCILIATION.json)
and [current workload inventory](FUNCTION_INVENTORY.json).
