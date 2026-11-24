# Wallet checkpoint performance — 23–24 November 2026

Two backend optimizations preserve exact accounting and existing admission checks. Production is not approved. This source change updates no live site, service, chain, signer, authority or financial limit.

## Improvements

- Checkpoint2 allocation validation visits shared tree ancestors once instead of repeating each NFT's complete path. The original uint/split rules, phase, denominator, backing and whole-unit conservation checks remain. The traversal is read-only, checks work deadlines and shares no state between trees, books or requests.
- Ordinary ownership/history reads decode an independently owned history-only seed from compact immutable bytes. The constructor still authenticates and validates the **entire** checkpoint first. Financial consumers retain complete restoration. This follows the existing lineage-reader pattern; lineage dispatch, canonical/indexed anchors, the full 86,400-second suffix and final proofs remain.

The extra immutable history section obeys the existing 32 MiB artifact bound. It is neither a live-data cache nor a process-memory qualification. No operator switch or contract call is added.

## Focused verification

| Scope | Actual result |
| --- | --- |
| Bulk checkpoint validation | 12 NEW methods pass once: all 1,000 ordinals, four buckets, dormant NFTs, both books, phase/uint edges, malformed state, conservation, immutability and deadline interruption |
| History-only seed | 16 NEW methods pass in disjoint stages: 15 initial passes, then one corrected test assertion passes alone. The original test-only error is retained; there is no final whole-file rerun |
| Private fixture capture | [12 NEW offline methods](verification/CAPTURE_FIXTURE.json) verify byte-exact code-response reconstruction, damaged/missing blobs, invalid literals, atomic refusal and retained-byte accounting |

No unchanged test bodies, contract suite or browser suite ran. The [bulk receipt](verification/BULK_VALIDATION.json), [history receipt](verification/HISTORY_SEED.json), [dispatch boundary](verification/HISTORY_DISPATCH_BOUNDARY.json) and [current pins](verification/CURRENT_SOURCE_PINS.json) distinguish source scope from execution. The [function inventory](FUNCTION_INVENTORY.json) records 182 Python files/2,003 named definitions; [anonymous scope](ANONYMOUS_CODE_INVENTORY.json) retains 278 lambdas and two unchanged Yul helpers. Frozen F6 61/39/4 maps and 1,021 ABI rows remain unchanged. Inventory is not dynamic coverage.

## Authorized runtime results — 24 November

The operator explicitly authorized both reviewed uploads and isolated runs after the earlier approval block. Both exact bundles ran sequentially with the original safeguards and existing environments preserved.

- **Controlled wallet pass:** all80 HTTP200 responses and all37 expected assertions complete for1,000 NFTs/three currencies and eight cards. Elapsed98.834s; final snapshot age116.018s leaves3.982s under120s. The original early-tip/15-second confirmation schedule is retained; no midjourney refresh or late-tip alternative. Exact raw/component USD, full86,400-second history, claims/conversion exclusions and final proofs actually complete. All eight preservation hashes match. This narrow finite pass does not qualify actual F6/V10, providers or sustained load. See the [wallet receipt](verification/WALLET_RUNTIME.json).
- **Constructor/live-code-history pass:**44 local setup transactions create/bind39 normal F6 instances with exact source/initcode checks and genuine NFT-contract parent/creation/latest code proof. Complete wire capture reconstructs2,666 repeated code responses from44 literals:14,620,075 encoded bytes under the unchanged64MiB bound. These use declared constructor dependency doubles and remain unsealed, without minting, LP funding, public transactions or financial/API acceptance.
- **Portable history recovery remains open:** export/reload records a ValueError/refusal before any dump response or dump file is retained. The available evidence does not identify the precise cause; no16MiB-overflow diagnosis or reload pass is claimed. The [history receipt](verification/HISTORY_RUNTIME.json) explicitly reports constructor/history-only completion.
- **Environment preservation passes:** five existing service states match the actual pre-upload snapshot, and all five owned lab units are stopped. The unused alternative has no execution footprint. Source, journals, original checkpoints/raw databases and the older baseline are preserved. [Sanitized comparison](verification/ENVIRONMENT_PRESERVATION.json).

Detailed host records, code-proof artifacts and authenticated wire records remain private. No unchanged tests or earlier passed wallet/recovery journeys are rerun.

## Earlier profiling and preparation evidence

The paragraphs below retain the pre-authorization stage and original failures; their pending-run statements are historical. The authorized results above supersede those preparation statuses.


Seven new isolated Ubuntu worker profiles complete. They identify repeated checkpoint validation/decoding; profiler overhead means these are not admission benchmarks. An earlier Windows checkpoint setup exhausted its existing deadline and is preserved without a limit increase.

The bulk-only affected 1,000-NFT/three-currency journey attempts all 80 GETs: protocol, 63 combined pages and 16 NFT/history requests for **eight visible cards**. It still refuses the final request after about 103 seconds because its confirmed block is already about 17 seconds old at the start. That age includes the fixture's intentional 15-second confirmation age. No completed wallet or post-portfolio aggregate assertions are claimed. The original failure remains evidence.

The final three-source wallet rerun is prepared and locally validated, pending explicit authorization to upload its reviewed source/synthetic-data bundle to the isolated Ubuntu lab. The original early-tip schedule, 15-second confirmation age, 120-second freshness, request pacing and all production limits are retained. The separately prepared late-tip alternative remains unused.

The original public RPC returns the requested chain/header but refuses historical account state on the third read; no retry, alternate endpoint or fabricated empty-state response is used. A separate declared standalone F6 fixture attempts 38 unsealed setup transactions before its retained-wire byte bound stops construction. Its new capture codec stores repeated successful code literals once while preserving every request, response hash and byte-exact response reconstruction. Limits remain 6,000 requests, 16 MiB per response and 64 MiB encoded retained evidence. The corrected 44-transaction fixture is prepared; it has not yet run. Neither fixture is live-market, OpenSea, sealed operating or financial/API acceptance.

The [independent captured-evidence review](verification/HISTORY_CAPTURE_REVIEW.json) verifies all100 source/four build pins,39 independently encoded normal initcodes, actual CREATE returns and later code/hash/size,44 included success receipts with full25% gas padding,112 typed binding readbacks and the actual contract-creation history. The trusted compiler output omits immutable-reference ranges for37 runtime objects; direct static runtime-template equality is therefore not claimed. Two verifier-only refusals and their corrected scoped follow-up remain private. No compiler, EVM or transaction rerun was used for this review.

All previously executed owned processes stopped. Detailed host records, runtime archives, original errors and wire evidence stay private outside Git. Actual normal F6/V10 financial acceptance, real provider/freshness/capacity, operating recovery and independent approval remain open.

## Adoption

Changed earnings/checkpoint sources change checkpoint1/2/3 semantic identities. Preserve original checkpoints, reviews, raw databases and journals byte-for-byte. Explicitly rebuild, independently review and re-pin matching future artifacts before separately authorized adoption; never edit old source hashes or hot-reload an artifact in place. The operator's [checkpoint procedure](../../docs/EARNINGS_CHECKPOINTS.md) and [manual](../../docs/OPERATOR_MANUAL.md#complete-wallet-financial-view) remain authoritative.

The 23 packages/83 stable task IDs retain their states. Both public configurations remain null, the shared signer stays Anvil-only, existing Anvil8902/sites/services are preserved, and the desktop heartbeat remains user-paused. Source publication alone authorizes no deployment or sealing. The separately authorized isolated construction above does not approve public deployment, sealing or release.
