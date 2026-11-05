# One-hour royalty opening and reviewed currency capacity

User decision5November2026; baseline c7dad14. Source candidate only, production
NOT APPROVED. Earlier24-hour drafts were superseded by the explicit one-hour
instruction; their artifacts/failures remain external and are not current passes.

| Change | Final behavior |
| --- | --- |
| Sale close | Governance NFT.setMintEnd(uint64) mirrors final OpenSea stage. Future end required; can revise while the OLD end has not passed. Mint rejects unset/past end. Mid-mint callback change rolls back mint/provider/request state. No automatic OpenSea configuration. |
| Initial pool | Admitted receipts during mint/grace stay in separate openingPool. Fixed3600seconds after close, strict pre-cutoff activated NFT cohort gets original-currency rarity-weighted rights. A late first transaction cannot enlarge the cohort. Normal sync/claim/activation materializes allocation; no keeper or opening transaction prerequisite. |
| No initial participants | Funds become unallocated, with no automatic first-late-activation windfall. Governance later chooses current-active-weight allocation. No beneficiary exists if nobody ever activates. |
| Prefunds and rights | Constructor/preadmission prefunds retain separate explicit recovery. Earned/fraction backing, current-owner transfers, initial/outage cohorts and original currencies remain separate. Growth adds no royalty weight. LP rewards/80-10-5-5/maintenance stay independent. |
| Full unallocated allocation | allocateAllUnallocated(asset,reviewHash) allocates every eligible unallocated whole unit of ONE admitted currency at current active weights. No swap/payout/arbitrary recipient. Locked initial pool and earned/fraction liabilities are excluded. Partial allocation remains supported. |
| Capacity | Operating16ERC20+ETH; governance can increase to64ERC20+ETH with review hash. Only increases, no currency removal or dropped entitlement. Admission remains separate. Review hash is not a gas proof; cold/faulted activation, full service/history/checkpoint/canonical workload qualification precedes expansion. |
| Explicit compatibility | Settlement3/recovery2, inventory12/reporting4/keeper royalty3/canonicalV7. V7 royalty header includes closed sale/capacity and rejects old peers. Capture requires the initial window finalized and every admitted initial allocation synchronized; emergency/terminal LP paths stay independent. No old runtime, journal or checkpoint is relabeled. |
| History/API/UI source | Opening status, effective eligibility and pending initial-pool claim reconciliation; first allocation credited once. Existing180event descriptors include four new events and retain176prior records. Fresh bounded inventory/read limits expanded without relaxing work budgets. Dormant NFT cards intentionally show NO deadline. Signing/public/live-site boundaries unchanged. |

## Risks and operating requirements

Register actual reviewed marketplace currencies before sale. Unsupported receipts
cannot be reconstructed at receipt-time eligibility; their separately approved
review/admit/current-weight allocation rule remains. A freeze, tax, rebase,
blacklist or malicious token can still prevent that currency's payout. Fractional
units remain backed and carry; they are not unallocated sweepable money.

One activated NFT at cutoff legitimately gets the whole initial pool if no other
NFT activated. Time continues during pauses/outages; finishing approval alone
does not count as activation. A late activation receives future royalties only.
After sale closure governance cannot extend/reopen the window. The actual
OpenSea integration, provider latency and all mint-path bindings remain open.

64currencies is a hard engineering ceiling, not unlimited lifetime support or a
gas guarantee. Future compatible code/qualification is needed beyond it. Current
bounded work/claim limits stay; use selected currencies/batches. A64-currency
expansion has NOT been qualified on Robinhood or running services.

The [operator procedure](../../docs/ROYALTY_LAUNCH_WINDOW.md), sole Todo, feature,
profile, release, source-bound callable notes/examples and repository memory are
updated. Existing contracts, sites, services, Anvil8902, holdings, journals and
shared signer are unchanged. [Verification](VERIFICATION.md) owns exact scope.
