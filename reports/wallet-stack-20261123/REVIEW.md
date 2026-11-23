# Wallet read performance and isolated qualification — 23 November 2026

Three source improvements are implemented. Production is not approved; this publication changes no live site, service, chain, wallet signer or economic right.

## Changes

- The website request gate waits through early timer wakeups while preserving one active request, at least one-second starts, bounded queueing and cancellation.
- The backend caches at most256 immutable ABI selectors for exact ASCII signatures at most256 characters. Every argument is still validated and encoded on each call. No amount, balance, price, response or accounting state is cached.
- Portfolio completion/failure aborts its own pending sibling reads, while preserving concurrent and replacement operations.

## Verification and limits

**23 NEW focused checks pass:** nine timer checks, five controller-cleanup checks and nine ABI differential/bounds/concurrency checks. No unchanged suite was rerun. All600 comparison encodes match the archived original; selector hashing falls from600 calls to five in that CPU-only measurement. This is not a whole-request speed claim.

The isolated Ubuntu HTTP/API-worker/proxy/source9 reader passes the controlled17-NFT financial/card journey:19 GETs in about19seconds, exact LP/funded ETH and full24-hour earnings. Cancellation, identical-configuration restart, two independent concurrent contexts and genuine expiry refusal pass. These use synthetic V9 observations, not full F6/V10, browser-extension or production-provider acceptance. The later sibling cleanup has five separate unit checks; those journeys were not rerun afterward.

**The1,000-NFT full portfolio remains unqualified.** The affected run progresses from58 to70 GET attempts after optimization. All63 compact wallet pages return200, but subsequent card/history reads exceed the unchanged120-second freshness window. No final wallet is published, and the later independent aggregate assertions are not reached. A separate restored F6/V10 graph cannot serve its required historical NFT-creation proof; no checkpoint or historical fallback is fabricated.

Temporary lab processes are stopped and existing environments preserved. Gas/fee/work, page, freshness, worker and ingress limits remain unchanged. Next profile actual checkpoint construction/seed restoration and history replay before choosing another optimization; do not share mutable replay state or remove proofs to obtain a pass.

Detailed runtime archives, host records, original failures and private verification receipts are retained locally for review. They are intentionally not included in this public report. The public [source inventory](FUNCTION_INVENTORY.json), [anonymous-code supplement](ANONYMOUS_CODE_INVENTORY.json) and [source pins](verification/CURRENT_SOURCE_PINS.json) contain source-analysis metadata only. Inventory does not establish dynamic coverage.

## Adoption

Changed abi.py enters checkpoint, keeper-health, OpenSea drop, deployment-sequence and pre-seal preparation identities. Preserve originals; rebuild/review/re-pin future artifacts and use matching writer/checker releases under separate adoption authorization. Never hot-edit old source hashes or rewrite pending journals. Both public configurations remain null; the shared signer remains Anvil-only.

The23 acceptance packages and83 task IDs retain their prior states. Actual independent feeds/routes, provider/finality/complete-fee capacity, OpenSea/VRF, authorities, full normal F6/V10 and operating acceptance and independent approval remain open. No deployment or sealing is authorized.
