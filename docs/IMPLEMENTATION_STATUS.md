# Implemented and Todo

Updated 2026-10-15 for the bounded metadata notification and keeper release-hardening candidate, based on contract revision `5febe7065856749345010ecca23dcd368b472c9e`. Current source hashes and executed checks are in [release hardening](../reports/release-hardening/README.md). The separate website remains revision `9eaa9e67917240112dd402d27fc8b2980c7b79fa`.

**Checked means implemented in the undeployed development candidate, with local test evidence. It does not mean deployed, independently audited or approved for real funds.** Unchecked items identify missing implementation, integration or production qualification. The separate [release checklist](RELEASE_CHECKLIST.md) remains NOT APPROVED.

## Implemented in the contract candidate

- [x] Exact **0.05 ETH dormant mint**, forwarded to the fixed mint recipient; minting adds no LP or reward eligibility. [Vault](../src/ZZZVault.sol).
- [x] Owner activation with at least **$100 of net, actually deployed LP**, followed by permanent additions to the same NFT. LP principal is nonredeemable; attached shares and unclaimed/future reward rights follow NFT ownership.
- [x] **One physical LP position per approved pool/strategy**, with individual NFT shares. Rebalance, harvest and compounding operate per shared bucket, rather than once per NFT. The intended initial collection uses one pool; the defensive cap is 16 historical buckets, including imports.
- [x] **80% individual / 10% collective / 5% compounding / 5% buyback and burn** funded allocation. The individual share follows LP shares; the collective share is equal per activated NFT. No Power or rarity multiplier changes LP rewards. [Fees](../src/ZZZFeeController.sol), [rewards](../src/ZZZRewards.sol).
- [x] Immutable creator-payment receivers, funded processing and current-owner claims, with segregated reserves and incumbent entry settlement. The receiver accepts actual payments; it does not establish a creator's payment obligation. [Funding rules](EXTERNAL_REWARDS.md).
- [x] Separate **5% ERC-2981 royalty request** and distribution of **100% of eligible royalty receipts** at activated Commun ×1 / Rare ×2 / Legendary ×3. Dormant NFTs have zero weight; pre-admission/prefund/no-member receipts remain quarantined. Marketplace payment is voluntary. [Royalty ledger](../src/ZZZRoyaltyRewards.sol).
- [x] **1,000 NFT cap** and exact final quotas of **600 Commun / 300 Rare / 100 Legendary**, with authenticated randomness callbacks and mint-order draws without replacement. No administrator trait selection, reroll or cancellation. Actual production VRF remains an integration gate. [NFT](../src/ZZZNFT.sol).
- [x] Immutable visual traits: **eight colors, 58 palettes, monochrome/bicolor/tricolor and four patterns**. A fixed 1,000-entry artwork inventory limits identical palette/pattern/rarity looks to four; all 100 Legendary finished looks are unique. [Catalogue](../design/nft-metadata/palette-system-v1/README.md).
- [x] **2,784 rendered artwork states**, retaining the approved egg material. This is a rendering library, not additional NFT supply. Production immutable hosting remains pending.
- [x] Dynamic metadata selects the current marked attached LP evolution: Dormant, Activated, **Enhanced from $1,000**, **Singularity from $10,000**. Market losses can lower the stage without removing activation rights. Remote/stale valuation is explicitly unavailable. Reveal and contributions emit ERC-4906 notifications. [Metadata](NFT_METADATA.md).
- [x] Constrained keeper rebalancing, harvesting, compounding and direct buyback/burn, plus guardian pause and timelocked governance roles. This does not eliminate impermanent loss. [Operations](OPERATIONS.md).
- [x] Repeated whole-bucket migration framework, equivalent-asset accounting and timelocked onboarding of future chains/pools/providers after sealing. Real transport wrappers are not supplied. [Migration framework](../src/ZZZMigration.sol).
- [x] Bucket-discovering dry-run keeper, confirmed/reorg-aware event indexer, and an intentionally blocked offline production-configuration validator. These tools are not a hosted frontend API or an approved live operating service.
- [x] Permissionless bounded metadata notifications for at most 50 inclusive mint ordinals, resolving actual hashed token IDs. An optional disabled-by-default watcher detects confirmed evolution/availability/reveal changes through the keeper's existing simulation, budgets, serial signing and durable pending recovery. Production operation and external marketplace refresh remain unqualified.

## Todo to turn the website flows into real transactions

- [ ] **Selected pool integration:** implement and review native-ETH settlement and Pons-hook compatibility, or explicitly choose a supported alternative market. The current adapter deliberately rejects the selected Robinhood native-ETH/hooked pool. Creator-payment intake does not make custody compatible. [Pool boundary](ROBINHOOD_POOL.md).
- [ ] **ZZZ/USDC activation routing:** implement and review any conversion from USDC into the target pool's assets. Existing entry can balance the pool's own currencies; it is not an arbitrary-input router. The live UI must quote enough gross input to leave at least $100 of net deployed LP after costs/slippage. Exactly 100 USDC input is not a guaranteed successful activation.
- [ ] **Production randomness:** establish a supported proof-verifying VRF service, immutable coordinator, funded subscription, finality/callback parameters and a rehearsed fulfillment/outage procedure. A compatible interface and MockVRF tests do not prove live availability. Earlier missing fulfillment can block later ordered reveals.
- [ ] **Metadata operation:** publish/pin and independently verify the complete artwork manifest at its immutable IPFS/Arweave root. Stage the implemented bounded watcher with actual feeds, NFT bytecode pins, RPC/confirmation limits and budgets. Test actual marketplace rendering/cache refresh.
- [ ] **Live frontend and metrics:** host confirmed ownership/position/fee-history API projections, current valuations and funded claimable balances; wire wallet approvals, quotes, mint, activation, additions and claims to the reviewed deployments. Define receipt-versus-earned history and token/USD pricing. The website's example balances and 24-hour/all-time USD fees are simulations; the current indexer does not compute those financial projections or serve HTTP.
- [ ] **Royalty UI:** display and claim the separate NFT-sale royalty balances by asset. The existing website previews royalty weights but its reward balances/claims cover only simulated LP individual and collective rewards.
- [ ] **Bulk-claim integration:** choose and review wallet batching or a bounded contract batch path. Existing LP and royalty claim entrypoints claim one NFT and one asset at a time; the demo's bulk button is not evidence of a native batch function.
- [ ] **Revenue and pricing:** finalize the actual Pons/creator payment terms or alternative revenue market; review ZZZ and other asset USD feeds, denominations, decimals, wrapping and outage policy. The website's assumed 0.30% fee does not apply to the selected 0%-conventional-fee pool.

Production NFT labels also need a display-number decision: current token IDs hash chain/vault/sequence and metadata names use that raw number. Sequential labels can use the existing mint ordinal, with a reviewed metadata/UI change if desired, without changing stable custody IDs. The demo's short labels such as #444 are examples.

## Todo before a funded initial launch

- [ ] Choose and independently verify governance multisig, guardian, keeper, mint recipient, feeds, admitted assets/pools and every module/helper binding. The user has not selected these public authority addresses and requested keeping the gates open.
- [ ] Stage actual entry, top-ups, reward funding/claims, royalties, transfers, real keeper signing/recovery, rebalances, indexer backfill/reorgs and alerts on the reviewed chain/dependencies.
- [ ] Qualify worst-case gas for the actual venue, assets and inboxes, including the 16-historical-bucket bound; backtest strategy costs, volatility, slippage and MEV. Vault runtime currently has only 169 bytes of EIP-170 margin. Constructor arguments still need initcode allowance.
- [ ] Obtain an independent external audit, remediate findings, complete deployment/configuration review and satisfy the [release checklist](RELEASE_CHECKLIST.md). Local tests and internal Slither triage are not this audit.
- [ ] Fill and independently authenticate the [production inventory](../config/production.example.json), including release-specific code, asset, randomness and staging evidence. Its current blocked state is intentional; an offline pass would still not authorize deployment.

## Todo before enabling real bridging

- [ ] Implement and independently review actual provider SDK wrappers, authentication, finality, equivalent-token backing, delivery fees, failure/recovery and retained historical routes.
- [ ] Stage canonical → satellite → satellite → home → revisit, including delayed/forged/reordered receipts, ACK epochs, pauses and old reward liabilities with the actual providers.
- [ ] Review each future destination and onboard its immutable policy/routes through the timelock before approving an economic migration.

An independently reviewed initial deployment can keep migration disabled with no provider policies or routes. The existing framework allows later onboarding after sealing; no arbitrary future chain, asset conversion, bridge recovery or satellite user top-ups are automatically supported. See [migration-disabled launch](OPERATIONS.md#migration-disabled-initial-launch).

## Verification evidence

- Current local Solidity: **342 passed, zero failed, one expected opt-in fork setup skip**, across 24 suites. The new 50-token notification workload uses **318,466 gas**, below its 500,000 regression budget.
- Current portable Python: **372 passed** from a **376-test inventory**, zero failures/errors/runtime skips. The focused keeper run passed **109** cases, including 45 metadata cases. Four unchanged Unix-only cases remain reserved for supported Ubuntu verification. Exact source hashes are in [release-hardening verification](../reports/release-hardening/verification-summary.json).
- All **20 module/helper runtime and initcode-object size gates** passed; source-bound compiler records cover 26 Solidity files.
- Fresh internal Slither: **179 findings**, individually triaged as 110 false positives / 42 accepted risks / 27 informational / zero unresolved review entries. Accepted risks and the independent audit remain release considerations.
- Current local receipts: [test/size summary](../reports/release-hardening/verification-summary.json) and [static-analysis review](../reports/release-hardening/static-analysis/README.md). Older artwork/alignment reports remain historical evidence for their exact sources.
- Earlier [Ubuntu CI for source revision 5febe70](https://github.com/ABEF/AAA/actions/runs/38793910449) passed **local-checks, static-analysis and robinhood-fork**. Check all three jobs for the new published revision separately; earlier green CI does not validate subsequent source changes or close production integration, configuration or audit gates.

The detailed [component map](COMPONENT_STATUS.md) describes implementation boundaries. The [roadmap](ROADMAP.md) orders the remaining work; the [release checklist](RELEASE_CHECKLIST.md) records independent production qualification.
