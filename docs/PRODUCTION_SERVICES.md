# Production service decisions

[Expanded20November market/route review](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/market-route-qualification-20261120/REVIEW.md)
checks additional native candidates and actual WETH/v3 discovery. No complete route
or independent source pair is approved. A documented market or deployed Pyth
contract does not supply a qualified source/publication operation; the fixed
native profile does not automatically support WETH/v3/hooks. No service selected. Final production-pool selection is operator-deferred.
The [conversion scope correction](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/market-route-qualification-20261120/ERRATA.md)
distinguishes implemented manual v3 capability from current graph/worker support.

[20 November actual feasibility](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/readiness-gate-a-20261120/REVIEW.md)
refreshes prices/markets and identifies exact OpenSea/VRF/provider questions.
No dependency is admitted or selected. Current-source compiler applicability is
[reviewed separately](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/compiler-applicability-20261120/REVIEW.md).

The [16 November refresh](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/real-market-refresh-20261116/REVIEW.md) adds current
same-anchor source/pool state and directional quotes, plus two bounded discovery
intervals. It does not repeat the earlier13-check provider qualification or admit
a source/route/provider. No independent ETH/ZZZ pair or full operation is qualified.

A dedicated direct ZZZ/USD provider is not mathematically required: the optional
[spot composite reader](POOL_SPOT_PRICE_SOURCE.md) composes reviewed native-v4
ETH/ZZZ spot with ETH/USD. Prefer the largest qualifying external market and
preserve two independent ZZZ paths. No pool, source age/liquidity policy or
production source pair is selected; the dated provider findings below retain
their original scope.


The [13 November provider qualification](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/predeployment-qualification-20261113/REVIEW.md)
independently establishes genesis, passes all13 paced RPC checks and verifies
specific history/logs/tiny nonpersistent simulation. Full provider capacities/
plan/SLA/archive, exact real-market PoPL fees and operator spending approval
remain open. Current market/source failures are retained; no live endpoint,
source/route, zero-tip policy or operating service is selected.
[Operator procedure](OPERATOR_MANUAL.md#robinhood-rpc-fees).

Current guide reviewed2026-11-20. Dated [9November feed/market read-only qualification](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/market-followup-20261109/REVIEW.md) records shared-anchor20:04:50UTC observations and a separate20:18:44UTC feed follow-up, not selected live configuration. This records required capabilities and actual selection limits;
[Todo](../TODO.md) alone owns status. **No production deployment is approved.**

## Dependency inventory

| Dependency | Required capability / current boundary | Procedure/evidence |
| --- | --- | --- |
| ETH and fixedZZZ USD prices | Two independently reviewed paths per asset, original rounds/ages/decimals, controls and300bps agreement. At20November block119107223 checked ETH proxies share one aggregator; Pyth is stale/disagreeing and API3 read reverts with cause unrefreshed. No fixedZZZ pair approved. | [Price security](PRICE_SECURITY.md), [current capture](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/market-route-qualification-20261120/REVIEW.md) |
| Optional Pyth reader | Immutable reader preserves original publishTime and hard86400s age ceiling; the20November stored ETH observation fails age/agreement. Robinhood is absent from the documented sponsored EVM list: a compatible authenticated own publisher or another qualified service needs an operator, data access, gas funds, age alerts and recovery. Prior zero on-chain update-fee observations do not establish free data/operation. | [Reader policy](PYTH_PRICE_SOURCE.md), [current research](../reports/market-feasibility-20261120/PRIMARY_SOURCES.json) |
| Sequencer liveness | Chainlink lists no Robinhood uptime feed and says expansion to additional networks has stopped. Review an actual correct-chain outage/recovery policy; never copy another chain or synthesize always-up data. | [Primary-source findings](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/market-followup-20261109/feeds/FINDINGS.md), [operator procedure](OPERATOR_MANUAL.md#configure-stop-and-recover-usd-pricing---2026-10-24) |
| Contribution/conversion markets | Final production pool is deferred. Qualify both directions, complete input/output/marginal LP, compatible reference prices, external depth and gas/fees. Current native low-fee diagnostics do not qualify; v3 positive outputs are finite discovery, not prepared graph/worker adoption. | [Current diagnostics](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/market-route-qualification-20261120/REVIEW.md), [scope correction](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/market-route-qualification-20261120/ERRATA.md), [pool](POOL_SELECTION.md) |
| RPC/archive | Canonical hashes/ancestry, complete logs, durable historical state, trace/simulation/gas and recovery. The official endpoint retained an anchor header but refused its state roughly11minutes later; a bounded alternate-provider read recovered it. This is not provider approval. | [RPC qualification](RPC_PREPARATION_QUALIFICATION.md), [current failures](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/market-followup-20261109/VERIFICATION.md), [history](HISTORY_AUDIT.md) |
| Randomness | Exact original subscription-v2.5 two-word request, proof-verifying actual coordinator, immutable lane/subscription/payment policy, funded consumer, same-request recovery/no reroll. Current Chainlink catalog omits Robinhood; candidate permanent refund/expiry rules can conflict with original-request recovery. No qualified provider. | [Mint/provider qualification](MINT_INTEGRATION_QUALIFICATION.md) |
| OpenSea | Mint2 source implements free TEAM and governed-price AL/public dormant minting(default0.05ETH gross), recipient net after the actual platform fee, gas separate. The pinned SeaDrop runtime is historically observed; current Studio signed-allowlist/multiConfigure/authority-proof compatibility with PoPL Merkle/typed setters remains unverified. Actual onboarding/fees/payers/VRF/operation remain open. Secondary listing support is different evidence. | [Marketplace qualification](MINT_INTEGRATION_QUALIFICATION.md) |
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

For the ETH secondary, compare compatible authenticated Pyth Core publication
with API3 activation plus a separately reviewed round-compatible reader. The
current API3 read reverts;13November zero base/name observations remain historical.
Do not remove Oracle round checks. API3 documentation describes mainnet plan
expiry after three months and a standard86400s heartbeat; actual current offers,
renewal, update/confirmation headroom and cost need review. An old offer is not
a payable quote or active SLA. Pyth Core/Pro interfaces are separate products;
the existing Core reader is not automatically compatible with Pro updates.

Name the operator, choose the actual product, record data/API access and renewal
responsibility, fund only reviewed operating costs, configure age/outage alerts
and rehearse publication/recovery before admission. [Primary references](../reports/real-market-refresh-20261116/PRIMARY_SOURCES.json).
No provider was commercially engaged, selected, installed, funded or paid by this qualification.
