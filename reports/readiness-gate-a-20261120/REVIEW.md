# Gate A — actual launch feasibility and compiler assessment

20 November 2026. Baseline `519ff4f075022f789f46facbab56f0a944705b11`, main.
**Production remains undeployed and NOT APPROVED.** This executes the first
available research/source-review work in the [readiness plan](../../docs/ROADMAP.md).
It does not complete Gate A, authorize signing/deployment or change the selected
pool, financial safeguards, gas defaults, provider or running configuration.

## Work completed

| Package | Concrete result | Exact evidence boundary |
| --- | --- | --- |
| P02: compiler advisories | All eight current registry variants assessed against exact F6 input/settings/100-source AST. No confirmed reachable defect requiring an upgrade found. | [Compiler review](../compiler-applicability-20261120/REVIEW.md). Seven NEW offline analysis controls pass; no compiler/EVM/old-suite rerun. Generated-code and independent-review limits remain. |
| P03/P04: actual prices and markets | Fresh canonical capture at119000058,20November11:01:08UTC;36 completed read-only HTTP calls. Still no qualified independent pair or complete execution market. | [Market review](../market-feasibility-20261120/REVIEW.md), original transport failure and raw responses retained. Anonymous endpoint observed only. |
| P04: fixed-ZZZ token controls | Fresh3248-byte runtime equals retained explorer-verified source runtime. Seven source files and18-function ABI reviewed: ordinary ERC20Burnable, no token owner/tax/pause/upgrade or post-constructor mint interface. Deployer/curve/factory references grant no token privileges. | [Token assessment](TOKEN_REVIEW.json). Explorer source verification reused, not independently recompiled; no nonzero burn executed or full dependency qualification. |
| P05/P14/P15: platforms and providers | Current primary-document and exact NFT ABI review identifies specific OpenSea integration and VRF recovery questions; a chain-specific RPC alternative exists but has no accepted tier. | [Platform/provider review](../platform-provider-gate-20261120/REVIEW.md),15 primary references. No provider account, order, platform onboarding or RPC capacity test. |
| P16: publication scope | Corrected the plan's ambiguous artwork count:1,000 mint inventory entries,542 distinct selected base looks,2,784 supported renderer SVG states. | Existing inventory/packed catalogue and [publication procedure](../../docs/ARTWORK_PUBLICATION.md). No image changes, regeneration, upload, CID, pin or retrieval test. |

## Compiler result: a bounded subtask is complete

The exact accepted configuration is0.8.26/Cancun, via-IR, EVM optimizer enabled
with runs1, **`optimizer.details.yul:false`**. An advisory requiring the disabled
Yul passes is not automatically applicable just because the compiler version
matches. The fresh assessment also inspects named custom-error require syntax,
recursive struct types, internal call cycles and storage-end conditions.

The previous assessment's “no Yul functions” statement cannot be copied forward:
current Oracle has two nonrecursive local helpers. The refreshed source graph
and explicitly limited dispositions replace that assumption without recompiling
or invalidating F6. This closes current advisory applicability review only;
independent compiler correctness, upstream compiler0.8.35 dependencies, final
release construction and independent audit remain separate work.

## Actual markets still prevent ordinary acceptance

The selected `0x501122…afe1b` pool has zero current active liquidity at the
captured block. This does not prove every distant tick is empty. Its nominal
$100 ETH diagnostic loses14.699808% gross against starting spot, above the
necessary screens; this diagnostic is not the strategy's computed swap amount.
The larger known raw-L pool passes a forward pointwise screen but fails the
tested1,000-ZZZ reverse fill. Its stored ETH-per-ZZZ price is5.811926 times the selected
pool's price, so their ordinary maximum500bps reference bands cannot overlap.
No new filtered same-core ETH/ZZZ Initialize events were found since the prior
16November anchor; bounded discovery is not global market knowledge.

Two Chainlink proxies still point to one ETH aggregator. Pyth is stale and
disagrees; API3 read reverts. A fresh chain head cannot turn stored pool spot
into recent independent trade evidence. No source was updated/admitted and no
quote was relabelled a complete PoPL operation.

The next market action is to obtain a genuinely supportable selected-destination/
reference/execution combination: compatible price and meaningful two-way depth,
plus independent valuation/publication. Restoring liquidity/price at the chosen
pool or selecting another admitted same-pair destination is a deliberate external
market/selection decision. This review performs neither, and does not widen
financial guards to conceal the problem.

## OpenSea and randomness require actual compatibility decisions

SeaDrop V1's deployment on4663 is distinct from accepting our custom collection.
Current Studio guidance describes server-signed allowlists and `multiConfigure`;
PoPL intentionally implements Merkle allowlists, typed setters and Access
governance, with no `multiConfigure` or `owner()` selector. This is a product
compatibility gap, **not** a demonstrated Studio rejection or mint exploit.
Confirm a supported custom Merkle/configuration/authority-proof transaction
builder route before adding new mint capabilities or sealing the singleton.

Chainlink's current v2.5 catalog does not list Robinhood. RH-VRF's published
permanent request invalidation after refund conflicts with PoPL's required
deliverable original request. The zero-lane example alone does not prove a
nonzero lane is rejected. D20DAO's different proof/upgrade/refund architecture
is another unqualified lead. An ABI adapter cannot recover randomness a provider
permanently refuses. No reroll, callback bypass or candidate admission was added.

QuickNode documents Robinhood archive/debug functionality, supplying a concrete
RPC candidate to evaluate. Actual account/tier, canonical-hash/withLog behavior,
32M/full20% and24M/full25% complete operations and fees remain unknown. Other
chains' advertised gas caps cannot establish Robinhood capacity. Public endpoints
remain dated observations, not selected production service agreements.

## Remaining launch inputs and sequence

The [input review](INPUT_REVIEW.json) separates known source/default decisions
from missing actual addresses, services and operating approvals. It is a dated
evidence record, not another Todo or a deployable configuration. Public signing
remains disabled; source10 remains unsigned and the shared signer Anvil-only.
OpenSea minting does not supply activation/growth/claim submission.

1. Resolve actual source/publication and executable market feasibility; confirm
   the custom OpenSea route and an acceptable original-request randomness service.
2. Select a reviewed provider tier and actual authority/user-submission approach;
   retain unknowns/null approvals until evidence exists.
3. Continue independently safe local work: cold claim/conversion and full F6
   canonical/construction proofs, paging adoption and the remaining gas refusal.
4. Freeze the supportable candidate, independently audit/remediate, then use the
   separate deployment, seal and public-opening gates. No live action is implied.

## Documentation, verification and preservation

Updated the owning Todo criteria and current compiler/market/platform/operator/
publication guidance. Fixed the plan's artwork cardinality without altering the
actual catalogue. Creator control questions now distinguish inspected fixed-token
code from still-unanswered issuer/liquidity plans. [Verification](VERIFICATION.json)
records source preservation, plan/Todo checks and exact evidence scope.

There are zero production Solidity/Python/browser changes, zero compiler runs,
zero EVM/unchanged-suite reruns, zero signed/public transactions and no deployment,
seal, site/service rollout, DB/checkpoint/journal/Anvil mutation or paused-heartbeat
restart. New compiler screen tests and fresh bounded read-only market observations
are identified separately; they are not independent release approval.
