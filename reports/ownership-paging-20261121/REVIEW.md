# Website adoption of confirmed ownership paging

21 November 2026. Contract baseline:
`d85415c9c34244d19df44fb9dcc9ccf9ce187d5e`.
Website baseline: `69c4b621d91fd16d16cc15671cca7dd51c7b79ac`.
Website publication: [`7271b79`](https://github.com/ABEF/AAA-website/commit/7271b79cfc330616d2278f87c0110bd239e669c3). [Exact published bytes](PUBLICATION.json) match the tested source.

**Current source9/schema4 and source10/schema5 now consume every verified
ownership page before returning a complete wallet inventory. 69 NEW focused
checks pass in one run. No unchanged test method was rerun.** This is website
source adoption, not installation or production approval.

## Implemented behavior

The website's `DeploymentAPI.walletInventory` uses the existing additive
`GET /v1/wallets/{owner}/nfts/{block}/{offset}` API. The validated protocol
snapshot supplies the fixed confirmed block and lifecycle. It copies those
values before asynchronous work, verifies page zero, then fetches remaining
pages in pairs. At most two ownership-page requests are in flight.

| Check | Enforced behavior |
| --- | --- |
| Envelope | Exact schema1, kind, availability, owner, chain, NFT contract and accounting profile |
| Bounds | Count0-1000, chunk16, exact selected length/verified_count, aligned contiguous offsets, exact next_offset and complete formula |
| IDs | Positive canonical decimal uint256 strings, numeric BigInt order and uniqueness within and across pages |
| Coverage | Every page from offset0;1,000 IDs require63 pages. A final page alone never establishes completeness |
| Identity | Same configuration, block number/hash/time, count and inventory digest throughout |
| History | Available exact target/hash with valid start anchors and indexer cursor beyond target; advancing operational counters do not falsely invalidate the fixed inventory |
| Lifecycle | Semantic equality to the captured protocol lifecycle and across pages, independent of JSON key order |
| Confirmation | Existing RPC provenance/runtime proof remains per page, with explicit confirmation-depth-only/canonical flags and final revalidation |
| Digest | Recompute SHA256 of all ordered decimal IDs joined by ASCII commas; reject any mismatch |
| Failure | Abort sibling requests; discard partial inventory on malformed/missing pages, reorg, expiry, cancellation or superseding account/page revision |

The helper uses the remaining freshness of its captured anchor as a read-expiry
timer. It does not increase the manifest age bound or per-request resource
limits. Final canonical/freshness checks occur after inventory assembly and
again after card reads, before portfolio publication. Existing immutable native
graph proofs are already cached by exact block hash; that existing cache is not
weakened or replaced by an unpinned ownership cache.

The result is an explicitly consumer-assembled complete inventory, retaining
the shape required by existing wallet summaries/history and the eight-card UI.
No partial IDs, balances or totals are published as complete. There is no
automatic retry or fallback to the legacy endpoint after a page failure.

Schemas1-3 retain their original schema2 complete endpoint and existing checks.
No historical manifest, response, runtime or pending operation is relabeled.

## Confirmed-state and financial boundaries

The ownership inventory and wallet summaries/history bind a fixed block. The
individual NFT endpoint has no fixed-block selector: cards retain their existing
independently confirmed latest snapshots and current-owner validation. They may
therefore use a later confirmed block. This change does not claim an atomic
whole-portfolio financial snapshot or weaken card ownership checks to manufacture
one. A transferred NFT or expired anchor can fail the refresh.

Reads do not alter NFT owners, shares, royalties, claims, economic eligibility,
transaction preparation or saved intents. `browser-wallet.js`, both null public
configurations and all signing gates remain byte-identical. Source9/source10
remain unsigned, including on Anvil. No backend or contract source changes,
checkpoint semantic-source change, gas/fee/loss ceiling change or new authority
is introduced.

## Verification actually performed

[Raw TAP output](stdout.tap), [stderr](stderr.log) and [source-bound result](RESULT.json)
record a single new-file run: **69 tests,69 passes,0 failures,0 skips**,0.563s.
The reader and new test file also pass syntax-only parsing. Source hashes before
and after the run match.

- 1,000 full-width IDs,63 contiguous pages, exact digest, bounded two-request
 concurrency and out-of-order pair completion;
- empty/16/17-ID boundaries, both fresh profiles and unchanged legacy1-3 route;
- malformed/missing/duplicate/out-of-order IDs, envelope/cursor/count/digest,
 identity/profile/history/finality/anchor drift and no HTTP404/429/503 fallback;
- fixed lifecycle with reordered keys, changed lifecycle, caller-anchor mutation,
 external cancellation, superseding revision, sibling abort and remaining-age
 expiry;
- final reorg/lost-confirmation refusal and rejection without cached partial
 holdings;
- one production `DeploymentAPI` constructor, Source10 native-reader and NFT
 validator composition using saved synthetic backend DTOs and graph replies,
 with explicitly synthetic ownership-page envelopes. This case does not replace
 those production methods with test stubs. Other wire-focused cases explicitly
 isolate graph/card methods.

The new file imports only production modules and safe fixture helpers, never an
old test module that would register historical test bodies. Existing tests and
saved DTO files are unchanged. Registration in the maintained future test
selection adds this file without executing the old selection now.

These are Node/synthetic transport checks, not browser rendering, actual HTTP
hosting, real-provider capacity, fresh backend/EVM execution, price qualification
or full1,000-NFT financial workload acceptance. No unchanged browser/Solidity/
Python suite, fork, population, deployment or gas campaign is rerun.

## Documentation, adoption and remaining work

The existing `portfolio` Todo now records source adoption and retains its
in-progress status. All83 task IDs/statuses remain. Current website guidance,
API/profile/environment docs, findings, feature reference, roadmap, repository
context and [operator procedure](../../docs/OPERATOR_MANUAL.md#website-ownership-paging)
distinguish implemented ownership assembly from remaining live acceptance.

Operator setup uses the existing reviewed manifest and matching API/history
profile; no new JSON switch or contract call is necessary. Preserve original
checkpoint/review/DB files and review the matching deployment/semantic-source
pins before any separately authorized service/site adoption. This website-only
change itself changes no backend checkpoint identity.

Actual provider/history latency, complete wallet summary/earnings completion
within existing freshness limits, browser/host integration and matching served
source10 rollout remain open. Public production signing, market dependencies,
OpenSea/VRF/authorities and independent review remain separate gates.

No site build or deployment was performed. Popldemo, served current3 poplint,
dist overlays, services, Anvil/NFT/LP/balances, journals/checkpoints, credentials
and user-paused heartbeat remain untouched. Original edited guidance and exact
baseline hashes were archived outside Git before changes; unrelated contract
dirty files are preserved and excluded. Source publication is not rollout.
