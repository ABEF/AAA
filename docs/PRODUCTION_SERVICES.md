# Production service decisions

Reviewed2026-10-29. This records required capabilities and actual selection limits;
[Todo](../TODO.md) alone owns status. **No production deployment is approved.**

## Dependency inventory

| Dependency | Required capability / current boundary | Procedure/evidence |
| --- | --- | --- |
| ETH and fixedZZZ USD prices | Two independently reviewed sources per asset, exact decimals/original timestamps, source runtime/proxy/upgrade controls, age/round agreement 3%, sequencer policy. No qualified live pair or automatic fallback. | [Price security](PRICE_SECURITY.md), [dated references](../reports/price-reference-20261025/OBSERVATION.md) |
| Optional Pyth reader | Immutable bounded price-ID/confidence/time/exponent reader is implemented. Actual product/updater/source independence and operating cost remain unqualified; reader code is not a live feed selection. | [Reader policy](PYTH_PRICE_SOURCE.md) |
| Contribution/conversion markets | ETH/fixedZZZ only for user input. Review actual single-hop v3/v4 routes, depth/fees, exact LP placement and independent prices. Default 1% reward conversion needs cheaper actual routing than the selected pool's recorded effective fee. | [Routing](TYPED_V4_ROUTES.md), [pool](POOL_SELECTION.md), [preparation](ACTIVATION_PREPARATION.md) |
| RPC/archive | Same-block/hash canonical reads, authentic complete logs, trace/simulation/gas capabilities, bounded latency, reorg and backup provider behavior. Read-only probe success is not independent production approval. | [RPC qualification](RPC_PREPARATION_QUALIFICATION.md), [history audit](HISTORY_AUDIT.md) |
| Randomness | Exact original subscription-v2.5 two-word request, proof-verifying actual coordinator, immutable lane/subscription/payment policy, funded consumer, same-request recovery/no reroll. No qualified provider yet. | [Mint/provider qualification](MINT_INTEGRATION_QUALIFICATION.md) |
| OpenSea | Intended primary mint gross buyer0.05ETH, recipient net after actual platform fee, gas separate; canonical buyer/NFT/reveal integration. Current direct mint does not implement this. Secondary listing support is different evidence. | [Marketplace qualification](MINT_INTEGRATION_QUALIFICATION.md) |
| Authorities | Named governance wallet/quorum, guardian, keeper gas signer, current accepted mint recipient, bootstrap and original VRF reserve owner/funder; actual addresses deferred. No external custody recipient exists: collective principal return pays current NFT owners. | [Address inventory](DEPLOYMENT_ADDRESSES.md) |
| Artwork | Matching2,784-state content-addressed root, independently verified manifest/CID, redundant retention/retrieval and marketplace cache rehearsals. Prepared bundle is not uploaded/pinned. | [Publication](ARTWORK_PUBLICATION.md) |
| Read/API/indexer | Qualify fresh accounting6/custody4/portfolio2/V5 runtime/profile, authentic predecessor/history coverage, bounded concurrency/deadlines, ingress identity, persistent storage/backups and verified recovery. Served poplint remains the separate unconfigured current3 build; no fresh6 hosted acceptance yet. | [API](FRONTEND_API.md), [ingress](API_INGRESS.md), [recovery](INDEXER_RECOVERY.md) |
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
