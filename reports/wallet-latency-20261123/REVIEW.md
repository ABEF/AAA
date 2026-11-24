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

## Actual runtime evidence and remaining work

Seven new isolated Ubuntu worker profiles complete. They identify repeated checkpoint validation/decoding; profiler overhead means these are not admission benchmarks. An earlier Windows checkpoint setup exhausted its existing deadline and is preserved without a limit increase.

The bulk-only affected 1,000-NFT/three-currency journey attempts all 80 GETs: protocol, 63 combined pages and 16 NFT/history requests for **eight visible cards**. It still refuses the final request after about 103 seconds because its confirmed block is already about 17 seconds old at the start. That age includes the fixture's intentional 15-second confirmation age. No completed wallet or post-portfolio aggregate assertions are claimed. The original failure remains evidence.

The final three-source wallet rerun is prepared and locally validated, pending explicit authorization to upload its reviewed source/synthetic-data bundle to the isolated Ubuntu lab. The original early-tip schedule, 15-second confirmation age, 120-second freshness, request pacing and all production limits are retained. The separately prepared late-tip alternative remains unused.

The original public RPC returns the requested chain/header but refuses historical account state on the third read; no retry, alternate endpoint or fabricated empty-state response is used. A separate declared standalone F6 fixture attempts 38 unsealed setup transactions before its retained-wire byte bound stops construction. Its new capture codec stores repeated successful code literals once while preserving every request, response hash and byte-exact response reconstruction. Limits remain 6,000 requests, 16 MiB per response and 64 MiB encoded retained evidence. The corrected 44-transaction fixture is prepared; it has not yet run. Neither fixture is live-market, OpenSea, sealed operating or financial/API acceptance.

All previously executed owned processes stopped. Detailed host records, runtime archives, original errors and wire evidence stay private outside Git. Actual normal F6/V10 financial acceptance, real provider/freshness/capacity, operating recovery and independent approval remain open.

## Adoption

Changed earnings/checkpoint sources change checkpoint1/2/3 semantic identities. Preserve original checkpoints, reviews, raw databases and journals byte-for-byte. Explicitly rebuild, independently review and re-pin matching future artifacts before separately authorized adoption; never edit old source hashes or hot-reload an artifact in place. The operator's [checkpoint procedure](../../docs/EARNINGS_CHECKPOINTS.md) and [manual](../../docs/OPERATOR_MANUAL.md#complete-wallet-financial-view) remain authoritative.

The 23 packages/83 stable task IDs retain their states. Both public configurations remain null, the shared signer stays Anvil-only, existing Anvil8902/sites/services are preserved, and the desktop heartbeat remains user-paused. No deployment or sealing is authorized.
