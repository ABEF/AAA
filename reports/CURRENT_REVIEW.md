# Current project review

Reviewed 27 November 2026; F6/provider follow-through against contract baseline `4ecfadf3` and website baseline `cccaa5fb`. Earlier wallet-read implementation used `bf5c91fc` / `89a8219b`. Earlier documentation reconciliation retains baseline `fdd599c7`. PoPL is an undeployed production candidate. **Production is NOT APPROVED.** Publishing source or this consolidation authorizes no deployment, seal, public transaction, signer adoption, website rollout, service restart or chain reset.

This is the current cross-project assessment. [Findings](../docs/AUDIT_FINDINGS.md) owns defects, accepted trust and unresolved limits; [the task ledger](../docs/project-todo.json), [generated Todo](../TODO.md), [qualification sequence](../docs/ROADMAP.md) and [release checklist](../docs/RELEASE_CHECKLIST.md) retain their distinct roles. Technical instructions remain in their owning guides and the [operator manual](../docs/OPERATOR_MANUAL.md).

## Source, architecture and financial rights

The trusted normal Solidity build is `activation-final-six-20261118`: factory payload6/allocation2, accounting7/LP-allocation1, custody5, portfolio2, maintenance3, confirmation3, compound4, emergency2, LP-routing3/execution-price1, pricing2, direct Entry3/review2, governance2 and fee-intake1. Fresh mint2/schema17/reporting5 uses canonicalV10; earlier profiles, codecs, deployments, checkpoints and journals retain their original identities. Equal tuple length is not compatibility. Use [current identities](../docs/POSITION_V7.md) and [architecture](../docs/ARCHITECTURE.md).

There are 1,000 transferable NFTs with fixed draw quotas of 600 Commun, 300 Rare and 100 Legendary. Contributions and LP principal use native ETH and one fixed ZZZ. Ordinary holders cannot redeem principal. At most four logical historical buckets are admitted; each has one main or an optional main plus one residual in the same pool, both owned by the Vault. Entrants fund the main only and cannot consume incumbent/residual/compound backing. Replacement main/residual limits of 60%/40% are admission conditions, not continuously maintained allocations.

Actual LP receipts retain the fixed 80% individual shares / 10% equal activated collective / 5% compound / 5% buyback split. Rarity weights only separate royalties. Claims and exact same-NFT earned conversion preserve original entitlement and current-owner rights; principal returns, conversions and imports are not new income. Whole-unit pending/high/low phases, direct rights, reserve classifications and dust must survive canonical transfer. See [economics](../docs/ECONOMICS.md), [LP allocation](../docs/EXACT_LP_ALLOCATION.md), [royalties](../docs/EXACT_ROYALTY_ALLOCATION.md) and [history](../docs/EARNINGS_HISTORY.md).

One human governance/operator and a separate restricted keeper key remain the selected trust model. Direct governance has no timelock. Paused manual emergency operations can explicitly bypass selected financial guards and risk nearly all principal; this is an accepted governance risk, never an automatic keeper fallback. Sealed implementations and token/parent identities cannot be patched in place. Same-pair movement and parking preserve protocol custody; irreversible collective exit returns actual ETH and ZZZ to current NFT owners, with transfers and royalty/old reward rights retained. There is no external custody-address exit, bridge, cross-chain recovery or post-exit LP reopening. Authenticated same-chain canonical replacement is separate and pre-exit. [Controls](../docs/CHANGE_AND_RECOVERY.md), [manual emergency](../docs/EMERGENCY_REBALANCE.md), [holder return](../docs/HOLDER_COLLECTIVE_EXIT.md).

## Limits, build and workload qualification

Default activation/growth minima remain $100/$5, subject to a higher pool minimum. Default contribution/conversion/maintenance loss limits remain 3%/1%/3%, bounded governance ceilings 10%, with gas separate. The default contribution floor is 97% actual marginal LP. Independent swap, spot, caller, NET, fee, funding, additional execution-loss and idle limits remain distinct.

The selected contribution candidate is 32M gas with full 20% padding, maximum admitted estimate 26,666,666; backend decimal string and website integer must match. Keeper/manual maintenance remains 24M with full 25%; claims remain 12M with full 20%; historical defaults and source-specific evidence are not relabelled. All 13 controlled F6 cold cases fit their original 20M/full20% profile. In the expanded 1,000-NFT/64-ERC20-plus-ETH/two-LP fixture, 11/12 contributions fit 32M; the worst direct estimate remains 476,135 above admission. A separately paid preparation option does not remove that direct shortfall. Never substitute receipt/trace gas for a required fresh estimate.

The source inventory is 193 Python files / 2,161 named definitions / 281 lambdas. Frozen Solidity maps remain 61 project sources / 39 dependencies / four build controls and 1,021 ABI rows. The workload plan covers 187 scenario classes with service partitions; this is an obligation map, not dynamic full coverage. The [current source-bound inventory](../evidence/wallet-f6-20261127/FUNCTION_INVENTORY.json) includes the wallet-read/bundle changes; [the current anonymous-code inventory](../evidence/wallet-f6-20261127/ANONYMOUS_CODE_INVENTORY.json) binds its exact source and line locations without claiming execution coverage. Tight EIP-170/initcode headroom remains a constraint; source size gates are not real constructor/provider approval.

## Markets, prices and execution

Production-pool selection is operator-deferred. The recorded native ETH/ZZZ integration target `0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b` remains authorized for isolated testing, including explicitly synthetic depth; it is not a launch choice or independent market-depth proof. Preserve its configuration and the original empty-state observations. No replacement pool, WETH principal route or hook may be admitted automatically.

The operator selected spot for both placement and independent valuation; do not introduce TWAP automatically. Two ETH feeds using the same ZZZ pool are not independent ZZZ sources. Qualify two independent source paths, external depth excluding PoPL LP, actual directional fees, slippage, complete execution costs and same-core reference exclusions. Latest recorded route screens do not qualify a complete production route/source pair. Solidity's reviewed manual v3 earned-conversion capability is distinct from the current zero-wrapper graph and worker; configuration alone cannot enable it. [Prices](../docs/POOL_SPOT_PRICE_SOURCE.md), [routes](../docs/TYPED_V4_ROUTES.md), [reference swaps](../docs/REFERENCE_SWAP_EXECUTION.md), [services](../docs/PRODUCTION_SERVICES.md).

## Mint, randomness, metadata and irreversible setup

The selected mint design remains custom Merkle qualification: initial 20 free team / 500 same-price allowlist, one per listed address / 480 public FCFS, variable future windows/counts, original-recipient lifetime restrictions, unused allowlist rollover and reserved unused team slots. Paid price is 0.05 ETH gross by default, actual platform fee deducted, recipient receives net and gas is separate. Standard signed-stage adaptation was not selected. Actual OpenSea custom-drop onboarding, singleton/helper compatibility and fee terms remain unqualified.

The one-hour royalty opening supersedes the earlier 24-hour draft. The final OpenSea end must match the NFT end; claims open at end+3,600 seconds. Initial-cohort activation must finish strictly before the cutoff. Unset/past ends reject minting; once the old end has passed, there is no administrator extension or clock pause. Future currency admissions and pathological-token costs require separate gas/operating review.

Randomness still needs a qualified live coordinator/service, funding, callbacks, confirmations and unresolved-request response; a candidate address is not qualification. Administrator rarity selection, rerolls and silent provider rotation with unresolved requests remain excluded. Artwork distinguishes the 1,000-entry inventory, 542 selected base looks and 2,784 supported renderer states. Actual immutable content/root, hosting, cold tokenURI, marketplace cache/ERC4906 and sound/display behavior remain release checks. LP-exited differs from Dormant and retains royalties. [Mint](../docs/OPENSEA_MINT.md), [qualification](../docs/MINT_INTEGRATION_QUALIFICATION.md), [artwork](../docs/ARTWORK_PUBLICATION.md), [lifecycle](../docs/METADATA_LIFECYCLE.md).

## Backend, history and website consumers

Current source10/schema5/mint2/V10 read and unsigned-review support is implemented locally. Source9/V9, historical native/current profiles and actual served environments retain distinct identities. Public deployment/signing is null/disabled; the shared browser signer remains Anvil-only. A future production submission path needs separate review rather than silently extending that signer.

Complete ownership assembly requires every fixed-block page with exact owner/chain/NFT/configuration/block/digest/count and order; at most 16 IDs per page means 63 pages for 1,000 NFTs. A final page or eight cards is not a full wallet. The controlled source9 80-GET wallet/cards run finished in 98.834 seconds; final age 116.018 left only 3.982 seconds under 120. This is thin synthetic evidence, not robust provider/HTTP/full F6/V10 qualification. Profile1's 1,000-by-66 earnings cross-product remains outside the120-second envelope. Optional profile2 replaces that cross-product with separate63 ownership/LP plus17 full-wallet earnings slices:80 coreGETs before protocol/cards/final provenance. This is a source improvement; actual provider/F6/V10/maximum-lineage/freshness qualification remains open. Keep explicit incomplete/unavailable states, 1,024-read/1 MiB limits, ingress/concurrency budgets, and cache encoded key+JSON bounds of 64 KiB/entry and 8 MiB total.

Claim planning retains fresh complete validation and first-success safe prefixes; 32 is a count ceiling, not gas or optimal packing. Historical data requires canonical lineage, reorg rollback, exact raw amounts and the complete 86,400-second suffix. Changes to checkpoint semantic source require separately reviewed rebuild/re-pin for the matching consumer; preserve original checkpoint/review/DB/WAL and explicit codec generations. [API](../docs/FRONTEND_API.md), [claims](../docs/CLAIM_PLANNING.md), [checkpoint](../docs/EARNINGS_CHECKPOINTS.md), [history recovery](../docs/HISTORY_RECOVERY.md), [ingress](../docs/API_INGRESS.md).

## Complete-wallet financial read improvement

The optional API configuration `wallet_read_batch:1` selects wallet view profile2
only with accounting7 and configured complete earnings. Omitted/zero retains
profile1. Source9/source10 consumers independently prove all16-ID ownership/LP
pages, then assemble four-currency earnings for the complete current-owner NFT
inventory. Every slice binds the same block/configuration/IDs/count/digest and
complete currency coverage. Legacy compact-reader logic remains byte-identical;
unknown capability or a failed advertised endpoint cannot silently fall back.

Per-NFT whole-unit earnings and paid/converted balances are reconciled before
wallet aggregation. Claims/conversions/transfers/imports are not extra income;
lifetime earnings follow the currently held NFTs, including earlier owners.
Currency filtering reduces account bookkeeping without dropping global ledger
events, tree state, faults, cohorts or exact rounding. The complete86400-second
raw suffix remains mandatory and boundary semantics stay unchanged.

A separately pinned constructor-only STATICCALL program runs through canonical
creation eth_call. No helper is deployed, transaction signed, state override
used or wallet gas paid. Each call covers at most3NFTs/4royalty currencies and
uses fixed24M total virtual gas,50k plain/500k LP/1M royalty getter bounds;
successful wrong-size replies are integrity failures. Requests still decode and
authenticate individual raw getters. Explicit failed getters are retained only
inside the request, with no uncapped retry or cross-request financial cache.
The existing25s/1024RPC/2048POST/1MiB,64KiB-entry/8MiB cache and120s freshness
limits remain. A legitimate expensive view or long lineage may still refuse.

Review found and fixed three related issues: bind live mint ordinals to replayed
immutable mint history; classify contradictory prefetched replies as fatal
integrity errors; index each NFT's conversion history once and avoid creating
unselected zero paid-currency rows. ETH conversion credits retain all source
currencies, including those outside the current slice.

Checkpoint semantic source now includes the reader/helper source and artifact.
Old artifacts keep their exact original bytes and cannot be relabelled. Adoption
requires a NEW independently reviewed/re-pinned matching checkpoint and a
separately authorized worker/proxy/consumer rollout. Current protocol contracts,
public null configurations, Anvil-only signer, services/sites/chains/journals
and paused heartbeat remain unchanged. See [operator procedure](../docs/OPERATOR_MANUAL.md#optional-profile2-separate-complete-wallet-earnings).

### Focused wallet-read verification

| Partition | Actual evidence and scope |
| --- | --- |
| Exact backend |25 distinct NEW methods have staged PASS records:21 in completed receipts and four diagnostic passes retained from an interrupted campaign without a final source-stability receipt. Full-day boundaries, exact rounding/phase, claims/conversion/transfer, checkpoint source refusal and wrong live proofs are covered. This is not one final25-method suite. [Method ledger](../evidence/wallet-aggregate-20261127/BACKEND_VERIFICATION.json). |
| Maximum controlled wallet |1000 NFTs/66 descriptors complete all17 earnings slices, each under existing25s/1024RPC/1MiB bounds. Exact lost stdout measurements remain null; no invented latency/RPC maxima and no duplicate run. Deployment/getter/history/clock truths are injected. [Assertions](../evidence/wallet-aggregate-20261127/MAXIMUM_ASSERTIONS.json). |
| Read helper |Nine NEW protocol methods and two NEW actual EVM methods pass in distinct stages. The affected conflict method was rerun only after its fatal-classification fix. The EVM stage uses five compiled runtimes installed on a fresh owned node; actual constructor creation eth_call/STATICCALL executes, but normal F6/Robinhood/provider support is unqualified. |
| Browser consumer |24 NEW profile2 checks plus one affected existing future-capability assertion pass. A separate NEW actual backend-to-JS composition passes for17NFTs/five currencies, independent raw/USD/LP/ETH totals and unchanged request pacing. Its native/runtime/geometry/clock seams remain explicit. [Composition](../evidence/wallet-aggregate-20261127/consumer/composition-002/RESULT.json). |

Original nonpasses remain recorded: two read-helper receipt-setup failures ran
no EVM method bodies; the backend campaign was interrupted for repeated test
selector hashing; two many-conversion fixture failures preceded only that
corrected method's rerun. The first JS composition rejected an incomplete
controlled lifecycle. Its replacement was regenerated through actual readers
after completing the fixture truth, with no production guard weakened or DTO
edited after production. Original and replacement fixtures retain distinct hashes.
No unchanged test body or normal contract/browser/keeper suite was rerun.

The [source and helper binding check](../evidence/wallet-aggregate-20261127/FINAL_SOURCE_STATIC.json)
verifies compiled creation bytes, reviewed standard input/settings and exact raw
source pin; the compiler input normalizes CRLF to LF. It also checks Python
syntax and unchanged protected files, browser signer and public configurations.
Callable/operator generated bytes remain exact and the83 Todo IDs/statuses stay.
All source-scoped receipts are indexed by [the evidence manifest](../evidence/wallet-aggregate-20261127/RECEIPT_MANIFEST.json).
Actual current-F6/provider gas, archive/maximum-lineage, complete120s journey,
HTTP/host/concurrency and reviewed rollout remain open under CWR07/Q06/P17.

### Actual F6 and provider follow-through

The saved normal F6 fixture authenticates39 construction instances,123 runtime
roles,32 actually activated NFTs and65 royalty currencies/66 descriptors. Its
original snapshot lacks creation-time historical states; the initial restore
correctly refused them. A separate31-transaction replay reproduces every original
hash/receipt/header root. A new snapshot adds only genuine historical states30/31,
preserving the original accounts, head,446 headers and444 transactions. The fresh
Ubuntu restore passes actual creation absence/runtime checks and all123 pins.
Original files and failed attempts remain unchanged.

That actual F6 check found a valid LP component view using304,131 gas; the original
250k helper allowance refused it. The operator explicitly approved500k per LP
view and three NFTs per helper. Total virtual gas remains24M, plain50k/royalty1M,
with no transaction, fee, accounting or protocol-contract change. The sum of
maximum child allowances is19.05M, leaving4.95M for constructor/return/other work.
The compiler artifact and Python/Solidity pins match. Three affected and two NEW
focused methods have scoped passes across separate stages; the original negative
fixture timeout is retained, not accepted as proof of a revert.

Offline checkpoint construction also repeated identical pinned royalty reads
per NFT;32 NFTs by65 currencies alone imply at least6240 uncached reads, above
the existing4096 logical build default. Opt-in profile2 now uses the existing
job-local canonical cache during build. Every decoder and economic comparison
still runs; chain/head/header/final checks remain live, and scope exit clears all
raw replies. Omitted/zero remains unchanged. Defaults remain60s/4096 logical/
8192 physical POSTs, with64KiB-entry/8MiB retention; HTTP limits do not change.
Four NEW focused methods pass for the build hook, cleanup/budgets, legacy path
and old-builder source-pin refusal. Actual economic construction is separately
qualified below; hook tests do not establish it.

The affected controlled1000-NFT/66-descriptor method completes all17 independent
earnings pages within existing request limits: maximum603 logical reads,
173,175 response bytes and7.437s/page;375 constructors/page. Its121.438s total
uses injected transport and zero physical HTTP posts. This is a per-request pass,
not a120-second complete-wallet or provider pass. The older1000-NFT gas fixture
uses substitute Access/Registry and lacks complete chain history, so it cannot
be promoted to normal F6 website acceptance.

Public-provider observations comprise30 original attempts and10 NEW calls for
the changed helper. Both reviewed endpoints accept the new canonical creation
call and its45-row wire. The separate old-block witness succeeds at Pinax and
fails with unavailable historical state at the official endpoint. Cheap wrapper
execution does not prove24M work capacity, real F6 getters, sustained quotas,
archive reliability, finality or a production provider plan. No provider is adopted.

The maintained Ubuntu indexer reconciles 415 original headers and 898 financial
logs against saved actual receipts. Its closed database is copied into a fresh
lab and caught up only with new genuine headers. The current builder produces
a new 566,584-byte schema2 checkpoint at the original block445 in 5.400401s,
using 3,098 logical reads and 6,194 POSTs; database bytes stay unchanged during
construction. An independent literal-event review checks all32 NFT rights,
65 original royalty currencies,66 descriptors and exact reserve/earned-unit
conservation, while the maintained builder separately verifies live per-NFT
balances. The one-hour royalty opening and complete86,400-second suffix remain.
The32 NFTs share one owner and Commun weight1; ETH+ZZZ are two assets, not
proof of two physical LP positions. Mixed-owner/rarity/residual cases retain
their separate qualification scopes.
These old income events precede the current24-hour window; new empty headers
do not create income. This fixture does not replace recent-boundary, claim,
conversion, predecessor-lineage or full1000-NFT qualification.

The first actual Source10/proxy journey stops503 on its second GET: the isolated
source package omitted the pure physical-LP reader `keeper.compound_policy`.
The direct failed-stage diagnostic confirms ModuleNotFoundError; no gas or
economic guard was bypassed. Exactly that published helper and its empty package
initializer form a separately pinned122-file consumer closure; the original120
producer/checkpoint source generation is preserved. The original failure and all
earlier archive/export/fixture failures retain their exact results. The actual
consumer outcome is recorded separately below and in the
[source-scoped evidence index](../evidence/wallet-f6-20261127/INDEX.json).

After adding only the missing read dependency, the affected wallet page passes:
511 logical reads/1,019 POSTs,10,751 bytes and3.025s. The second strict Source10
journey remains **NONPASS**:33 API requests/261 direct RPCs/117.628s. Protocol,
both wallet pages and all17 currency slices return200 by76.450s. The sixth card's
earnings request reaches the unchanged120-second snapshot expiry; the next
queued card refuses stale input. There is no rate, connection, periphery or RPC
budget bypass. Complete financial and all-eight-card final assertions, including
the harness's independent96 raw-total reads, are not reached. Twenty successful
HTTP replies cannot be promoted to a full-wallet PASS. No third whole-journey
attempt or larger freshness/timeout allowance is used.

Next work is to reduce the card/history cost and qualify the complete current
consumer under120s, then the full normal1000-NFT/two-position/lineage workloads
and actual provider capacity. Existing current consumers, services and public
configuration are not upgraded by these finite results.

All new Node/API/proxy processes are confined to their owned Ubuntu lab. Node is
the exact official v24.13.1 Linux/x64 binary checked against the HTTPS official
checksum manifest, without separately verifying its detached signature. The
existing SSH key's forwarding restriction is retained; no tunnel or production
runtime/service is installed. Existing services, sites, Anvil8902, journals,
keys and the paused heartbeat remain preserved. Browser signing stays Anvil-only;
public configurations stay null.

## Keeper, recovery and diagnostic data

Pending-first behavior, durable intent before signer launch, one known-hash receipt recovery, nonce/spend/fee-day anchors, locks and source identities remain mandatory. Ordinary confirmation retains the sampled 85% physical plus independent-reference trigger, 600-second window / 300-second maximum gap / 240-second source polling, durable 60–300-second jitter after the initial 12 hours, and deadline-driven polling. Hourly harvest is independent; compound cadence and geometry eligibility remain separate. Future Nitro profile2 requires its exact reviewed chain4663/inclusive-fee/type2/priority0/configuration procedure; omitted/profile1 and original pending schema remain unchanged.

Current output changes compact JSON while preserving every event, field, order and flush. Two health-ID previews are capped at 32 numerically sorted IDs with full counts, completeness and full-list ASCII SHA-256; the original complete journal remains authoritative. Exact pretty-output limits are 64 KiB for selection and 1 MiB for staging export. Desktop archive reads are bounded, stable and alias-resistant; a serial collector refuses new capture at 10,000 entries while still verifying identical retained files. There is no automatic deletion, journal reformatting or live host logging/retention adoption. Updated source13/19 pins require reviewed matching tools/policy; older packages keep their exact original release.

Finite backup, scheduler, alert, off-host possession, clean-root and once-only recovery results have separate source/fixture scopes. The fresh 45-file / 808,416-byte desktop kit recovered one actual locally accepted stock harvest with zero recovery sends, three native calls and four stock processes in 2,119/6,000 RPC; included/final NFT/LP/rights/reserve vectors matched before the independently retained node stopped. The first target's pre-execution namespace failure and fresh target2 continuation remain distinct. External OS runtime and the continuously retained isolated chain were dependencies: no physical second host, complete OS/chain restoration, production signer recovery or cross-host fencing was proved.

Current fresh capture used the original 900-second allowance and real clock. The older 86,400-second synthetic review allowance is historical and changes no live freshness policy; stock 600-second head, 30-second future and original harvest 180-second calldata guards remain. Never initialize a used sender, rewrite pending/hash/config/policy/time, widen a cap, reset an outbox/clock, guess a resend or repair a failed output in place. Preserve partial attempts and signer material separately. [Recovery](../docs/KEEPER_RECOVERY.md), [native backup](../docs/KEEPER_BACKUP.md), [scheduling](../docs/KEEPER_SCHEDULING.md), [sidecars](../docs/KEEPER_SIDECAR_RECOVERY.md), [alerts](../docs/KEEPER_ALERTS.md), [operator procedure](../docs/OPERATOR_MANUAL.md#unsigned-keeper-restart-from-a-reconstructed-kit).

<a id="evidence-and-history"></a>

## What evidence does and does not establish

Retained historical successes are reused only where exact source/dependency/fixture applicability holds. Changed affected cases and missing compositions are verified explicitly; no unchanged test body is rerun merely to increase a pass count. Local mocks, direct storage/funding, synthetic depth, controlled prices/clocks, receipt-only proofs and saved-wire seams remain labelled. Estimates, padded limits, body traces, receipts and end-to-end runtime are different measurements.

Original failures stay failures: c813 lost its node before final vectors; the daemon-storage campaign retains its incorrect timing assertion and missing final physical capture; c826/c827 setup failures and the first c828 target were not relabelled. Current c828 target2 passed separately, and the original mid-observer host snapshot remains separate from the later settled five-state comparison with zero nonambient differences and one periodic observer invocation-ID change. A later correction does not rewrite a prior source's result.

Historical report narratives and superseded compatibility pages are preserved at the pre-consolidation Git revision and indexed by the consolidation manifest; retained raw/structured evidence keeps original hashes and privacy. Old relative claims such as “current” or “fresh” refer only to that report's recorded source. No unchanged test body, financial workload, server call or external qualification was rerun for consolidation. Four new focused checks verify the changed review-package behavior described below; they are not another keeper or financial rehearsal.

## Documentation consolidation and verification

This review replaces 818 historical report Markdown files. The findings register preserves current actions, accepted policies and stable-ID assessments from all 40 retired human assessment ledgers, including the original 64, 310, 24 and 57-row registries. All report text was scanned for unresolved obligations; the register distinguishes source fixes, obsolete architecture, unresolved implementation questions and external qualification. That reconciliation is not proof that every historical obligation is solved.

Nineteen additional deprecated or duplicate pages were merged or retired. Component responsibilities now live in Architecture; legacy profile boundaries remain in Position V7; instructions and current context live in AGENTS, this review and the operator manual. Required technical references remain separate from assessment. The Todo retains its 83 stable IDs, statuses, decisions and current acceptance conditions while removing accumulated report chronology.

The [retirement manifest](../evidence/documentation-consolidation-20261127/RETIRED_DOCUMENTS.json) records every removed path, original blob, SHA-256 and current owner. Original narratives and taxonomy are available at [the exact pre-consolidation revision](https://github.com/ABEF/AAA/tree/fdd599c7698d0e1c0709a4a8b50130e5557ba508). Use a separate checkout of that revision to recover retired files, then the package's recorded producing release and tools to reproduce its original validation. Old package manifests describe their original tree; they were not rewritten to pretend the reduced checkout is complete.

Compiler output, size/source maps, analyzer records, required fixtures, transaction/receipt/state evidence and recovery evidence remain byte-exact. Required structured analyzer assessments remain because verification consumes them; they are not a second human findings register. Unrelated untracked drafts, private recovery packages and the four protected dirty files were excluded.

During the earlier documentation consolidation, the application-code adjustment admitted exactly this report into schema4 auditor bundles, after the existing path and secret checks. Schemas1–3 and all other report admission rules remain unchanged. Four new focused methods passed once: exact schema admission, actual pack/verify and byte preservation, old-schema refusal, and lookalike/other-report exclusion. No old test bodies ran. Generated callable/operator text, Todo consistency, current links and source-bound workload inventory are checked as affected documentation/build inputs. Exact verification receipts accompany the retirement manifest; this work does not qualify a running service or production release.

The consolidated findings retain important limitations often lost in short summaries: V10 canonical peers cannot rotate SeaDrop transport; spend budgets are per sender journal rather than automatically global across rotated keys; a conditional late-fee callback accounting question needs real dependency reachability evidence; thin full-wallet freshness and direct cold maximum-state gas remain open. Raw forwarding of unadmitted late royalties to an authenticated successor is already implemented, so the old permanent-stuck-receiver claim is superseded.

## Remaining work and operating boundaries

The 83 stable task IDs remain 35 done / 40 in progress / seven todo / one excluded at their recorded task scopes; complete acceptance packages are not thereby approved. Q01–Q07 and the 23-package sequence still require real independent markets/prices/routes, complete provider/fee/gas/workloads, actual authorities/OpenSea/VRF/content, matching current consumer/site/submission adoption, full operating interruption/restore/alerts/durability/sustained history, and independent audit/remediation and named approval. Pool choice remains operator-deferred. Deployment, sealing and public opening are separate irreversible gates.

Keep original Anvil8902, NFTs/LP/balances, pending/nonce/receipt/spend journals, dist overlay and all existing sites/services unchanged. Popldemo remains simulation; served poplint is its own unconfigured current3 profile, not the fresh candidate. Heartbeat remains user-paused. Preserve the four unrelated dirty files listed in AGENTS and all unrelated untracked work; never publish raw operational configuration, credentials, keys, passwords, keystores or private bundles. Public authority and service changes require their own explicit authorization.
