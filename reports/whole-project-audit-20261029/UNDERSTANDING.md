# Understanding established before the final audit prompt

Baselines: contract`781fcc9`, website`e5bb216`, main,2026-10-29 Paris. Phase1
performed source/requirement/dependency/guide reconstruction, with no tests,
browser actions, source behavior changes, signing, services or deployment.
Raw maps/pins are preserved externally under `whole-project-audit-20261029`.

## System and scope

The source inventory contains46Solidity files and33concrete contract roles,
including six-domain canonical codecs and fixed factory/companion instances.
The generated reference lists665functions/33constructors/13receivers. All are
mapped to components; this is navigation, not proof all bodies newly audited or
executed. Operations maps include563Python callable rows across65files, likewise
not test counts. Website and API are separate source graphs and versioned modes.

| Feature family | Ownership, flow and important distinction |
| --- | --- |
| Mint/reveal/metadata | Direct0.05ETH dormant mint, original two-word VRF request, ordered finite exact600/300/100 draw among1000NFTs.58palettes/fourpatterns/fourvisual states are not extra minted NFTs. Rarity affects royalties only. Actual OpenSea-compatible primary mint/VRF and immutable IPFS publication remain unqualified. |
| Activation/growth | Exact native ETH/fixedZZZ budget through Entry/Pricing/Vault/Manager; atomic original-source/marginal-LP and caller floors.100USD activation/5growth minima, stronger pool minima and cumulative1mUSD contributions per NFT. Existing shares, fees, idle and compound cannot subsidize the entrant. |
| Shared custody/routing | One contribution destination, four bucket slots, independent NFT shares of a physical LP. Manager/Balancer use actual core quotes, zero/one swap and reviewed destinations separate from LP target. Historical aliases can grow separately from funded bucket count. |
| Maintenance | Physical outside/manual width change, hard12h minimum, sampled900/300condition, post-ready60-600jitter; separate compound clock and hourly harvest. Amount/price/range/cooldown policies do not promise yield or continuous in-range liquidity. |
| Harvest/accounting | Actual received LP fees split by20raw units16/2/1/1; individual share index, equal activated member index, compound and fixedZZZ buyback reserves. Dust/fractions and membership boundary residuals are explicit. Harvest is permissionless while otherwise allowed; keeper is the normal automated scheduler, not sole call authority. |
| Royalties/conversion/claims | Actual eligible receipts100% rarity1/2/3, optional ERC20 outage cohorts and native ETH. Earned-only aggregate source conversion credits the same NFTs; original fractions stay backed. Current owner claims unclaimed rights, including prior-owner accrual; transfer approval does not grant claim authority. |
| LP movement/parking | Governance-reviewed same ordered native ETH/fixedZZZ pool movement or reversible paused parking, exact guards/backing. Different from whole-collection handoff or terminal holder return. No integrated bridge/external-custody executor. |
| Terminal principal return | Governance pauses/starts irreversible exit and closes all buckets. Actual LP+idle+pendingcompound returns proportionally by cumulative floors to current NFT owners in bounded isolated batches; receiver fallback is owner-only. Old rewards/future royalties/transfers survive, LP never reopens. |
| Whole-collection replacement | Pre-exit same-chain six-domain capture/settle/sequential rows/funding/commit; exact ownership/shares/indices/fractions/classified backing and fully funded abort. Source retirement/successor activation atomic; late admitted receipts forward hop by hop. Post-exit/future-chain import not implemented. |
| Keeper and recovery | Dedicated limited service key, one serial pending lane, durable intent before send, original fee review/nonce/receipt/spend checkpoints, no blind resend. Files/locks/health/watchdog/jitter/cursors are operational state, not entitlement. One human operator also controls direct governance; no extra committee/timelock. |
| Indexer/API/history | Authentic complete operator-maintained logs plus pinned confirmed reads; typed lifecycle, holdings, NAV, claims, conversions and original-currency today's-USD history. Reorg/backfill transactions, bounded events/predecessors, HTTP/process/admission budgets and unavailable states. Consistency is not finality/provider proof. |
| Website/wallet/user flows | Demo simulation, preserved local profiles/signing, served unconfigured current3 poplint and absent fresh4browser profile are separate. Account/network/provider/intent revisions, exact approvals, recovery and confirmed LP-only image/audio matter; card snapshots and complete aggregate snapshots have different semantics. |
| Build, content and release | Locked packages/actions/compiler, normal size/initcode gates, explicit local-only deployment, independent read-only fork harness, CI selections, static builds/root identities, content manifest and operator procedures. Local publication does not qualify production or roll out services/sites. |

## Financial classes and clocks

Actual principal/attributed idle/deployed+pendingcompound, holder LP liabilities,
royalty liabilities, designated buyback, index fractions, carried fee dust,
quarantine/unclassified prefunds, principal-return liabilities and operating gas
have distinct owners/purposes. USD marks do not move assets. Claim/conversion/
handoff/return is not newly generated income. Collection allocations can include
ledger division dust, so immediately payable whole NFT sums may differ.

Activation remains permanent when current NAV falls. Activated artwork cannot
silently become unactivated rights. Metadata stage4`LP exited` and enum Exited5
are distinct. Market losses/IL are not automatically an accounting error.

Wall/monotonic clocks, latest/confirmed block time, request/draft expiry,
observation receipt gap, service poll, cooldown, compound/harvest interval, retry
backoff and actual inclusion are different. A successful batch need not pay every
receiver. Exactly300sec max observation gap may repeatedly restart with delay;
it is a settled liveness tradeoff, not hidden continuous-price evidence.

Claim side effects differ by ledger: LP claims do not harvest or rerun the split;
royalty claims call synchronization and can index previously received pending
royalties before payout. The payment itself is not income. This distinction was
confirmed against source during the first prompt challenge.

## Requirements, evidence and genuine unknowns

Current code and explicit user decisions control behavior; historical examples
do not reintroduce old tokens, custodians or remote ledgers. Accepted immediate
governance/dependency/successor-code trust must remain explicit. Raw prefunds and
hash labels do not establish honest backing, market data or running-code identity.

Actual independent feed pairs, feasible1%conversion routes, token issuer/burn
behavior, supported VRF, OpenSea primary integration, production addresses,
fresh4browser/services, exact constructor/maximal target gas, authentic histories,
Linux/host/key/backup/alert/soak and independent audit remain real release gates.
Unknown configuration is a blocker to that operation, not an assumed value.

Phase1 found factual drift to evaluate during execution: outdated no-extra-RPC
prose despite the final conversion head check; hourly/historical versus fresh300
sampling wording; dedicated keeper runner selection missing newer suites; old
fork workflow versus current harness. Demo example wording/fresh4gap and mixed
card/inventory snapshot meaning require careful classification, not automatic
profile relabeling or public signer changes.

The [knowledge assessment](KNOWLEDGE.md) ties primary standards and available tools
to actual questions. The [new prompt](../../docs/WHOLE_PROJECT_AUDIT_PROMPT.md)
must be challenged twice before its execution; those challenge records and
coverage distinguish mapped facts, findings and real verification.
