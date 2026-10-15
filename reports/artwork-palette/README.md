# Eight-color artwork static-analysis review — 2026-10-15

This is an internal, source-bound review of the artwork-palette change. It is not an independent audit or authorization to deploy contracts. Earlier website-alignment reports remain historical evidence for their own source revision.

## Fresh analysis and coverage

- Slither **0.11.6** completed successfully against the unchanged final snapshot of **26 Solidity sources and three build/configuration files**.
- Native analysis produced **179 findings**: 29 High, 65 Medium, 58 Low, 22 Informational and five Optimization detections. Analyzer severity is distinct from the reviewed disposition.
- All 179 detections have individual recorded dispositions: **110 false positives, 42 accepted risks and 27 informational**, with **zero unresolved** review entries.
- The unchanged source-bound checker passes against the [fresh compact report](slither.json), [current review](../production/slither-review.json) and exact source/configuration hashes. See [coverage](slither-coverage.json) and [provenance](slither-review-metadata.json).
- The previous 177-entry review is preserved byte-for-byte at [historical review](../history/slither-review-pre-artwork-palette.json). No historical verification artifact was overwritten to claim current-source coverage.

The CI gate remains unchanged: `scripts/verify-slither.sh` runs a fresh analyzer and then `scripts/check-slither-review.py` against `reports/production/slither-review.json`. No detector, source hash, finding identity or failure condition was disabled.

## What changed in the review

Of the current findings, **171 exactly match prior individually reviewed finding identities**. Four NFT findings have only line-location changes; their current functions were reread, preserving the existing caller restrictions, reentrancy guards and callback ordering. One current Vault `_join` finding merges the same three complete state-write/cross-function atoms formerly presented in two records. The existing explicit, narrow multiset comparison verifies that its entire call context and atom union are unchanged. Vault and fee source did not change in this artwork pass.

Three new findings were individually reviewed and independently checked by a second collaborating agent:

| Finding | Disposition and current-source explanation |
| --- | --- |
| `uninitialized-local`: `_visualAttributes.number` | False positive. Solidity initializes the local integer to zero. Prefix increment numbers the bounded palette components as Color 1–3. This counter is used only for JSON labels and never for prices, custody, randomness or mutable storage indexing. |
| `too-many-digits`: `ZZZArtwork.COMMUN` | Informational. This is a 1,200-byte table of 600 big-endian `uint16` visual inventory codes, not a numeric economic constant. Generated source and every encoded entry match the canonical catalogue and its hashes. |
| `too-many-digits`: `ZZZArtwork.RARE` | Informational. This is the corresponding 600-byte table of 300 inventory codes, with the same complete byte/hash and decoding checks. |

Exact descriptions, rationales, evidence and remaining release gates are in [new-findings review](new-findings-review.json). Accepted risks inherited from the prior review remain open production considerations; recording a disposition does not eliminate them.

## Artwork assignment review

The new per-rarity sparse Fisher–Yates draw uses the rarity's **remaining count before decrement**, moves its last remaining entry into the selected slot and clears the last slot. The plus-one sentinel preserves index zero correctly; its largest stored value is 600 and fits `uint16`. [Independent dense-list model comparison](independent-draw-model.json) passed for 100 word sequences per 600/300/100-entry final four-pattern catalogue, including all-zero, always-last and maximum-`uint256` words. All 100,000 draws agreed with the reference; every index was consumed once, preserving exact quotas and the fixed duplicate limits.

Only authenticated two-word request fulfillment supplies the rarity/artwork words. Request-to-NFT binding, one fulfillment, strict mint-order finalization and no reroll remain in force. Palette and circuit pattern are written only once during finalization, then stay fixed through activation, value changes and transfers. Full inventory consumption therefore preserves 600 Commun / 300 Rare / 100 Legendary, no more than four identical complete palette/pattern/rarity looks, and distinct Legendary finished looks. Color and circuit traits have no financial weight. The final four-pattern catalogue is Flowing arcs, Segmented panels, Orbital rings and Vertical ribs; the earlier five-pattern review is retained externally as intermediate evidence.

The modulo reduction of full-width random words has negligible statistical bias bounded by fewer than 1,000 outcomes out of `2^256`; this is not a substitute for verifying the actual coordinator's proof security. Matching an ABI and exercising a mock still does not establish production VRF support.

## Matcher and environment evidence

The [matcher replay](slither-matcher-replay.json) passes both the native 179-record report and a 180-record fixture using the former split representation of the same `_join` write atoms. This fixture is a checker replay, not another analyzer run. All seven adverse mutations were rejected: missing finding, changed description, changed severity, duplicate finding, changed write atom, unresolved disposition and source-hash drift.

The final four-pattern native build completed with exit zero before fresh Slither analysis. The preceding five-pattern intermediate run needed a Windows signature-cache access retry; those earlier receipts remain separately preserved externally. Windows represents the analyzer's findings exit `-1` as `4294967295`; JSON success, absence of analyzer errors and full source-bound review coverage are checked separately.

Recheck the retained report from the repository root:

```sh
python3 scripts/check-slither-review.py reports/artwork-palette/slither.json
python3 scripts/generate-artwork-library.py --check
```

Current Forge, size and Python evidence is recorded separately in [artwork verification](../artwork-palettes/README.md). Production VRF, immutable asset publication, selected native-ETH/Pons custody and payout integration, bridge/backing, final configuration/staging and independent external audit remain required. No public-chain deployment or real transaction occurred.
