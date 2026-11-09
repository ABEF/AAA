# Market qualification verification boundaries

Baseline `99a01e97887156be0d31b61d453df4e29eb8a055`.
See [review](REVIEW.md) for findings. No production approval, public transaction,
deployed change, or independent audit is claimed.

## Distinct evidence layers

| Layer | Exact scope | What remains unverified |
| --- | --- | --- |
| Pricing catalogs/docs |34 original artifacts plus their manifest; retrieved official Chainlink/Pyth/RedStone data, source rules and preserved failures | No global proof of absent custom feeds; no independent upstream/admin review, updater funding or correct-chain liveness selection |
| Pricing chain reads | Canonical block109785732/hash4f11bc…ce92, depth12; actual rounds, code and proxy/control reads; canonical rechecks | No usable independent ETH/fixedZZZ pair, provider honesty, uptime or price-policy approval |
| Markets |356 payloads plus original manifest; same block109785803/hash4a55b8…9498;102 Initialize keys,71 compatible-fee states,3 v3 candidates,107 quote calls | Bounded provider-dependent discovery, no global optimum/future liquidity, independent USD, route admission or target gas |
| Existing verified source/runtime | Official deployment registry pinned12e3736…, actual quoter/core/fixedZZZ/wrapper source and209 dependency files with original licenses | No independent recompilation or upstream audit; code hashes alone do not freeze proxy controls |
| Current production objects | All90 raw production/dependency pins match the retained mint2 normal objects | Reuse, not a new compiler, static analyzer or whole-suite run |
| New owned fork |59 deployment/configuration transactions,2 direct diagnostic mints,2 actual activation reverts,2 blocked growth cases,2 read-only core-delta traces | Controlled correlated prices, mock VRF, unbound-direct mint and local gas; not independent feeds, mint2/OpenSea, public funds or production composition approval |

These counts are different records/actions, not additive coverage percentages.
Zero successful activations and zero successful growth cases are reported here.
Atomic rollback is a verified rejection, not financial-flow acceptance.

## Pricing evidence integrity

[Pricing manifest](pricing/artifact-sha256.json) binds34 payloads. The package
retains authoritative RedStone push-v2/pull-v3 extracts alongside superseded
parser extracts and network/explorer failures. Catalog identity/addresses and
source ABI support are kept separate. Pyth actual age173991s and pair
disagreement465.063bps fail unchanged86400s/300bps rules. Both Chainlink proxies
resolve the same underlying aggregator/owner; they are not counted as two feeds.
No source was updated, admitted, configured or deployed.

## Market evidence integrity

[Market manifest](markets/market-evidence-manifest.json) SHA256:
`3b2198b890ce9e972f4e2022fc2e3195dd761890c1605a7093a7954e61303adb`.
All356 original payload byte lengths/hashes were verified at destination.
The original large-log-range rejection, HTTP403s, quote failures and partial
Windows-longpath export remain. Successful raw ABI/source capture and selected
extractions are separately recorded; no failed stage is relabelled as success.

Official-quoter partial-fill errors are cross-checked against exact deployed
source semantics. TickMath/current-L/net/bitmap reads and a separate actual-core
fork trace confirm the selected reverse-capacity diagnosis. Active L or a failed
generic RPC alone would be insufficient evidence for that conclusion.

## Fork execution and preservation

[Fork evidence](fork/EVIDENCE.md) includes lossless scripts, source closure,
plans, assertions, exact receipts, quote traces and owned-process cleanup.
The source-bound archive SHA256 is
`a39c66a83fb4b3b0d32b78149d352ce8376f380ba971c738fd77081cd1b33354`.
All67 raw archive entries and decompressed large-trace hashes are verified.

| Local transaction | Result | Gas used |
| --- | --- | ---: |
| ETH activation `0xf18ff4126696d33a9f437c66da0fedd614e8596f0ac6f4fa8df8bdd324f4df39` | Reverted; input/LP/NFT/Entry rollback asserted |9,676,169 |
| ZZZ activation `0x60ee70f4845ce0380cc1f1c5edb1e04edeabe4f223ddaab8f7c7c09a667d3e3e` | Reverted; input/LP/NFT/Entry rollback asserted |8,190,123 |

These hashes and gas costs are **disposable local fork receipts**, never public
Robinhood transaction or fee-budget qualification. Existing12M budget/full20%
estimate headroom is unchanged. Exact raw input units use the same-anchor ETH
reference and derived pool ZZZ value; all four fixture sources are deliberately
correlated. There is no independently qualified USD consensus in this fork.

The first attempt stopped at Git safe-directory admission; the next could not
witness the public chain through restricted transport before starting Anvil.
The final authorized network-capable attempt completed. Both initial failures
remain in the archive; no global Git policy was changed to fix admission.
The new hidden fork and exact-anchor cache are stopped. All90 production pins
and four protected pre-existing dirty files match. Existing8902, site/server,
signer, journals and user-paused heartbeat were not changed.

No extra solver run was justified: all eight ETH candidate quotes completed well
within their200k call budgets, and exact output/spot conditions explain rejected
larger trades. No financial setting or synthetic market-depth change was used.
Growth was correctly blocked rather than tested against a fabricated active NFT.

## Documentation and publication

Current pricing, pool, route, service, operator, feature/release, roadmap and
memory guidance incorporate these findings. Historical reports remain immutable;
their earlier synthetic-depth positives, old source scopes and limitations are
not reinterpreted. Todo stable IDs/statuses and stronger user/caller financial
limits are preserved. Current royalty claims remain in original currencies;
LP conversion and v3 wrapper choice are explicitly separate.

Because executable production sources did not change, unchanged normal/static
and contract tests are reused at exact pins rather than rerun. Final generated
[Todo/reference checks](final-reference-gates.json) pass; the
[integrity receipt](final-integrity.json) verifies34 pricing payloads,356 market
payloads,67 raw fork archive entries,90 unchanged production/dependency sources,
the four protected unrelated files and shared signer. It checks21 Markdown files
and their local-file links with no new broken file links; fragment
anchors/external sites are not comprehensively checked. Exact staged/committed
publication checks remain separate. Actual independent feeds/routes, configured worker and
consumer, target gas/provider/recovery, OpenSea/VRF/authority and independent
release approval remain open.
