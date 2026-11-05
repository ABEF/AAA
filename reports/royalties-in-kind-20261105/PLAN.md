# Original-currency royalty settlement

User decision5November2026: holders claim royalties in the received currency;
remove royalty swaps. LP reward conversion remains separate. Baseline main
bce897c; no deployment, signer/site/service/Anvil/journal change is authorized.

1. Remove fresh royalty conversion/binding/approval entrypoints and converter
   deployment surface. Preserve weighted per-currency indices, eligibility,
   fractions, backing, current-owner claims and fixed ERC2981 recipient.
2. Replace swap recovery with governance-only original-currency allocation of
   admitted unallocated backing at current active weights; protect existing
   earned/deferred/fraction liabilities. Unsupported tokens require review and
   admission, within the existing16ERC20 limit. No arbitrary recipient or sweep.
3. Explicit fresh royalty capability/profile; retain old runtime readers,
   receipts/events/journals and historical conversion tests separately. Fresh
   inventory/keeper/API reject accidental royalty conversion configuration.
4. Mixed claim preparation/reporting returns separate raw currencies; missing
   metadata/prices stays unavailable. Never present tokens as pending ETH.
5. Verify changed paths with independent multi-currency accounting, simultaneous
   activation/claims/transfers, recovery/outages/rounding and negative selectors.
   Rebuild normal size/static/reference evidence; no unchanged broad reruns.
6. Update operator procedures/all call examples, owning docs, sole Todo,
   feature/evidence, roadmap/release and repository memory. Preserve earlier
   reports and four unrelated tracked dirty files. Main/source publication only.
