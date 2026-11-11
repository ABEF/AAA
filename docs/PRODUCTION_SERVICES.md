# Production service decisions

A dedicated direct ZZZ/USD provider is not mathematically required: the optional
[spot composite reader](POOL_SPOT_PRICE_SOURCE.md) composes reviewed native-v4
ETH/ZZZ spot with ETH/USD. Prefer the largest qualifying external market and
preserve two independent ZZZ paths. No pool, source age/liquidity policy or
production source pair is selected; the dated provider findings below retain
their original scope.


Reviewed2026-11-09. [Latest read-only qualification](../reports/market-followup-20261109/REVIEW.md) records shared-anchor20:04:50UTC observations and a separate20:18:44UTC feed follow-up, not selected live configuration. This records required capabilities and actual selection limits;
[Todo](../TODO.md) alone owns status. **No production deployment is approved.**

## Dependency inventory

| Dependency | Required capability / current boundary | Procedure/evidence |
| --- | --- | --- |
| ETH and fixedZZZ USD prices | Two independent reviewed USD sources per asset, exact original age/round/decimals, runtime/upstream controls and300bps agreement. No usable pair: Chainlink proxies share one aggregator; Pyth is stale; API3 ETH is inactive/direct-ABI incompatible; no two fixedZZZ sources are established. Exact-token CEX books are USDT market leads, not USD feeds. | [Price security](PRICE_SECURITY.md), [latest findings](../reports/market-followup-20261109/feeds/FINDINGS.md) |
| Optional Pyth reader | Existing immutable reader preserves original publishTime and hard86400s age ceiling. Captured age229537s and546.2675655bps disagreement fail unchanged guards. Live on-chain update-fee getters are0; authenticated data access, funded updates, gas, upstream controls and recovery remain unqualified. | [Reader policy](PYTH_PRICE_SOURCE.md), [feed evidence](../reports/market-followup-20261109/feeds/FEED_FINDINGS.json) |
| Sequencer liveness | Chainlink lists no Robinhood uptime feed and says expansion to additional networks has stopped. Review an actual correct-chain outage/recovery policy; never copy another chain or synthesize always-up data. | [Primary-source findings](../reports/market-followup-20261109/feeds/FINDINGS.md), [operator procedure](OPERATOR_MANUAL.md#configure-stop-and-recover-usd-pricing---2026-10-24) |
| Contribution/conversion markets | Actual full-input/direction/size/spot/fee/depth and gas qualification, then whole operation with independent prices. Latest696quote calls include23overlapping gas rechecks; tiny favorable reverse outputs are not economically useful conversion acceptance. Selected and alternative10018 cannot jointly pass ordinary principal reference bands at the anchor. Native-v4 principal and optional v3/WETH earned conversion stay separate. | [Route evidence](../reports/market-followup-20261109/routes/ROUTES_FINAL_v2.md), [pool](POOL_SELECTION.md), [typed conversion](TYPED_V4_ROUTES.md) |
| RPC/archive | Canonical hashes/ancestry, complete logs, durable historical state, trace/simulation/gas and recovery. The official endpoint retained an anchor header but refused its state roughly11minutes later; a bounded alternate-provider read recovered it. This is not provider approval. | [RPC qualification](RPC_PREPARATION_QUALIFICATION.md), [current failures](../reports/market-followup-20261109/VERIFICATION.md), [history](HISTORY_AUDIT.md) |
| Randomness | Exact original subscription-v2.5 two-word request, proof-verifying actual coordinator, immutable lane/subscription/payment policy, funded consumer, same-request recovery/no reroll. No qualified provider yet. | [Mint/provider qualification](MINT_INTEGRATION_QUALIFICATION.md) |
| OpenSea | Mint2 source implements free TEAM and governed-price AL/public dormant minting(default0.05ETH gross), recipient net after the actual platform fee, gas separate. The pinned SeaDrop runtime is observed; actual custom-drop onboarding, fees/payers, VRF and operating acceptance remain open. Secondary listing support is different evidence. | [Marketplace qualification](MINT_INTEGRATION_QUALIFICATION.md) |
| Authorities | One human operator/governance wallet (type still unselected), separate guardian/keeper capabilities, current accepted mint recipient, bootstrap and VRF owner/funder; actual addresses deferred. No external custody recipient exists: collective principal return pays current NFT owners. | [Address inventory](DEPLOYMENT_ADDRESSES.md) |
| Artwork | Matching2,784-state content-addressed root, independently verified manifest/CID, redundant retention/retrieval and marketplace cache rehearsals. Prepared bundle is not uploaded/pinned. | [Publication](ARTWORK_PUBLICATION.md) |
| Read/API/indexer | Backend and local source10 website support explicit mint2/accounting7/V10 reads and owned unsigned reviews; source9/V9 remains separate. Actual hosting/configuration/providers/history/concurrency/restore acceptance remains open. Served current3 poplint stays unconfigured and no public signing is enabled. | [API](FRONTEND_API.md), [source10](SOURCE10_WEBSITE_PROFILE.md), [recovery](INDEXER_RECOVERY.md) |
| Keeper/monitoring | Supported Linux host, exact source/provider/signing-fee policy, gas funds, original journals, logs/alerts and off-host restore/rehearsals. Paused desktop heartbeat is not continuous monitoring. | [Operations](OPERATIONS.md), [rehearsals](KEEPER_REHEARSALS.md) |

## Cost and qualification rules

Ordinary push-feed contract reads have no extra per-read LINK transfer in PoPL;
transactions still consume gas. RPC plans, data publishing/updater fees, VRF,
pinning/hosting and keeper gas require actual provider/product quotes and budgets.
A call gas ceiling is not a flat charge. Dated references are not live configured
PoPL prices or a service agreement; two labels behind one upstream do not prove
independence. Do not invent addresses, quotes or evidence to pass inventory gates.

No creator-payment agreement, inbox operator, integrated bridge provider or remote
proof service is needed for this hookless local release. Those removed features
are historical research, not launch requirements. Token-issuer powers, source
quality and actual fixedZZZ burn support still require review with the ZZZ team.

Select and independently review actual services/configuration, bind observations
to exact source/block/chain, run the appropriate rehearsals, then obtain independent
audit/remediation and named release sign-off. Publishing these decisions or an
unsigned transaction does not authorize deployment, sealing, signing or spending.

## Concrete provider requests

For fixedZZZ `0x7dbf38976f6d3b9c529e7d9484a71898b409ee6a` on4663, request exact
USD source/product addresses, market/publisher coverage, source and administrative
independence, original timestamps/decimals, heartbeat/latency/outage terms, upgrade
controls, authenticated update ownership and full data/gas/funding costs. If a
market uses USDT, require defensible USD normalization and depeg behavior.

API3 is a concrete ETH alternative to discuss, with authenticated published offers,
but its observed base/name are uninitialized. A compatible immutable reader would
be separately reviewed work; do not remove round checks to accommodate the native
proxy. Offers are native-wei duration-funding parameters, not guaranteed payable
amounts or an active SLA. All observed offers have86400s heartbeat; do not presume
that a heartbeat at the Oracle hard maximum leaves update/confirmation headroom.
No provider was contacted, selected or paid by this qualification.
