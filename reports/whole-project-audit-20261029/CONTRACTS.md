# Contract-wide source and accounting review

Final prompt: SHA256 `5cd040ace83c4865dd1cc7aac9e85373b4142603b0ca7af07f4c46d3f7f44206`. Baseline main `781fcc9d224f77a4a54d278878ffc3b002b71e26`. This report is one contract partition of the whole-project review, not production approval or proof that every inherited/getter/callable body has no defect. The phase1 map and source hashes are in `UNDERSTANDING.md` and `understanding.json`; the independent second challenge is retained separately.

## Result and actual scope

No independently reproduced contract defect requiring a source repair was established in this pass. Zero Solidity, ABI, storage, economic, rights, authority or dependency/toolchain changes were made. The review reconstructs all33 concrete components and46source files, with deep cross-module tracing of principal entry, current-NAV share issuance, actual fee intake, reward/royalty entitlement, conversion, maintenance, holder return, and especially the six-domain canonical snapshot/backing/abort/multi-hop state machine. `coverage.json` distinguishes component/critical-path review from interface navigation and pending exhaustive function-body coverage.

New execution evidence is deliberately limited to **five current-source canonical composition methods:5passes,0failures/skips,258.0seconds including compilation, exact selected method set and no source drift**. Prior217affected Solidity passes and39normal object gates are reused only at exact matching source/dependency/build pins; those217methods do NOT include CanonicalHandoff or NativeCanonical suites. Reading existing test scenarios is not a new pass. Older canonical reports retain their original topology/compiler/source identities.

## Financial invariants reconstructed

- FeeController raw custody >= accounted; accounted comprises designated compound, buyback and carried dust. A complete20rawunit basket credits16individual/2collective/1compound/1buyback. At a membership/share boundary, the sub20 remainder belongs entirely to incumbents' individual rewards. Exact lifetime80/10/5/5 after arbitrary boundary flushes is not the implemented policy.
- LP Rewards raw custody >= liabilities + orphaned. Whole claimables alone do not equal liabilities: uncheckpointed indexed accruals, both per-NFT fraction classes and global index division residue matter. Current-owner claims lower only actual paid liability; they never rerun the split, compound or buyback. Donations are funded balances without automatic principal/reward attribution.
- Royalties accounted = liabilities + orphaned; raw custody >= accounted, with raw-accounted pending receipt. A recovered optional payment currency first credits its earlier eligible cohort and only then admits waiting activations at a new baseline. Current-NAV tier changes do not remove activation or royalty weight.
- Contributions use a frozen original price vector and original input budget. Existing LP is repriced after an entry swap; issued shares use net added NAV against incumbent physical LP+idle+compound. Only entrant-budget amounts can pass marginal deployed-LP guards. Unclassified raw donations cannot subsidize the contribution. Cumulative contributed USD, current marked NAV, deployed-retention floors and idle ceilings are distinct.
- Compound is designated incumbent principal backing. Buyback is separate reserve. Claims and ETH conversion do not create earnings; conversion consumes earned whole source units and distributes every native wei to the same NFTs/components with cumulative floors. Source fractions/global residue stay backed.
- Terminal return pays only principal+pending compound, not earned liabilities or buyback. During Closing/Allocating, partially materialized principal rows are not the whole settlement. Once Ready, remainingETH/ZZZ equals all unpaid per-NFT allocations; cumulative share floors allocate each raw unit of every bucket exactly once. An ETH/token failure rolls back both payments and paid/liability flags for that NFT.

## Deep canonical findings and rejected concerns

1. **One captured cutoff, not moving export balances.** Freeze locks source before external observations and captures all six domains before settlement. Royalty pending cutoffs are recorded once. Later receipts cannot alter row roots/backing. Fee dust settlement transfers funds into LP Rewards and updates that already-captured reward manifest; fee backing decreases consistently. No export/funding occurs before all six ordered settles complete.
2. **Partial settlement abort is valid.** Before royalty settlement, reopening leaves original incoming amounts pending. After settlement, reopening preserves the already-credited cutoff rather than indexing it again. No source activation/transfer can alter denominators while frozen. An aborted source may later recapture; only snapshot delivery/import caches reset, rights remain.
3. **Funding is not inferred from a prefund.** Source and importer agree on exact asset and amount per slot/index. The source transfers first, coordinator checks actual destination delta, and only then a zero-value authenticated acknowledgement forwards funds from companions. Destination/source companion prefunds remain independent. Fund/return flags and controller phases prevent replay, partial activation or arbitrary recipients.
4. **Funded abort has no unfunded override.** Only actually transferred legs must return, exactly once, then source module backing validation precedes reopening. A token or receiver that fails can keep an abort frozen; no administrator bookkeeping shortcut deletes the obligation. This is an explicit recovery dependency, not repaired by inventing a sweep or custody receiver.
5. **Commit is an atomic authority transition.** Every row/root/count and funding leg must match. Source retires and destination validates/activates in the same transaction. Receiver/token callbacks are within locked coordinator phase/identity guards. The importer is inert and does not copy ERC721 approvals. A same-chain reorg reverts both sides, though consumers still require finality.
6. **Multi-hop late receipts are not exported twice.** A retired admitted royalty address forwards only remaining post-cutoff receipts to its immediate successor. If that successor has frozen for a later handoff, forwarded late receipts remain outside its snapshot and are forwarded after its retirement. Each link is an explicit operation, not recursive gas growth. Unknown post-retirement ERC20 currencies have no admission/rescue; operator must inventory marketplace cached receivers/currencies before cutover.
7. **Fraction/identity rows preserve the real right.** NFT rows preserve owner, original draw words, mint ordinal and sparse finite draw inventory, while a new epoch separates future VRF requests. LP rows preserve both fraction classes/paid indices; royalty rows flatten delayed-join baselines at cutoff without awarding earlier money to new activations. Source-authenticated rows are still subject to exact destination dimensions/order/semantic checks.
8. **Contract ownership remains an operational compatibility gate.** Inert import `_mint` intentionally avoids receiver callbacks. Preserving escrow's address does not ensure an escrow tied to the old collection can release a replacement NFT. No code-only universal receiver test solves this; holder preflight/marketplace cutover remains required.

## Other critical paths reviewed

Setup/sealing fixes the module graph, source/fixed-ZZZ/buyback/holder-return identity and canonical companions; bootstrap disappears. Direct governance, pause, principal exit and canonical lifecycle checks stay distinct. Runtime/source independence pins cannot make malicious governance or a proxy/upstream dependency trustless.

NFT mint proceeds stay outside LP, pending VRF has no reroll fallback, ordered finalization preserves quotas, and one missing fulfillment can block full collection replacement but not pool maintenance. Tier fall does not deactivate entitlement. Metadata unavailable values stay unavailable; terminal artwork4 is separate from accounting Exited5.

Native LP operations use typed periphery actions, exact input/debt/receipts, Vault NFT ownership, explicit Permit2 approval reset and final position/range/liquidity/price checks. The Balancer compares bounded actual-core quotes after withdrawal and executes zero/one swap. Bounded search is not global optimum. Oracle upper/lower spread, actual directional fees, additional loss and total/caller/venue/captured limits are independent; their combination may legitimately make a trade unavailable.

Rebalance raw eligibility is physical range exit or reviewed width change after hard interval, not a centre displacement. Sampled readiness holds side/physical identity/control with max300second selected gaps; it cannot detect every between-sample excursion. Compound has its independent clock, yields to raw due rebalance, and cannot reset the rebalance clock. Jitter is only service scheduling, not on-chain authorization or MEV protection. Manual keeper invocation cannot bypass the on-chain guards.

Holder-return start/close stays governance-only while allocation/delivery is permissionless and cannot redirect amounts. Current-owner lookup is per payout; a callback can legitimately transfer later NFTs, which are subsequently paid according to current ownership. One rejecting recipient is isolated; owner-only fallback can choose a compatible recipient. Partial exit cannot reopen LP or start canonical replacement, while future royalties/old reward claims remain.

## Lifetime alias/workflow cost: concrete operating improvement

Let N=minted NFTs, B=permanently registered bucket slots (including reservations, at most4), L=registered pool aliases, A=LP reward assets (at most33), R=royalty currencies including native (at most17). Exact source row formulas are:

| Domain | Records |
| --- | --- |
| NFT | 1001+N |
| Vault | 1+B+L+N+A |
| Membership | 1+N |
| LP Rewards | 1+A*(1+B+N) |
| Royalties | 1+R+N*(1+R) |
| Fees | 1+A+B*A |

Total records = **1006+4N+N*(A+R)+3A+2AB+B+R+L**. Direct export and import calls require at least **2*sum(ceil(domainRecords/8))**, since each domain cursor is independent. Funding legs = **3A+R**, including zero-valued manifest legs; commit checks flags for them too. Add freeze1, settle6, completeImport1 and commit1. Destination preparation, source notice, parking, deployment, retries, abort/returns, metadata and late-forward operations are additional. A direct call count is not necessarily a transaction count if a separately reviewed bounded relay later batches calls; no such batching is assumed here.

For N=1000,B=1,L=1,A=2,R=1:8019records,2012export/import calls,7funding legs and9control calls =2028direct calls before the additional setup/drain/retry work. For N=1000,B=4,L=4,A=33,R=17:55394records,13856export/import calls,116funding legs and9control calls =13981direct calls. These are arithmetic workload counts, not target-chain gas/fee quotes or execution results. Existing1000-NFT and maximum-asset fixtures are separate dimensions; neither proves their full Cartesian maximum gas campaign.

Aliases are permanent and grow through repeated same-pair moves even when the same bucket is reused. No on-chain loop in capture/commit scans every alias: their row relay work is bounded, but total lifecycle work grows linearly. The useful improvement is documenting/planning actual counts, budgets, resumption cursors and relay automation before cutover. Arbitrarily capping aliases or deleting history would alter approved recovery behavior and is not justified by this review.

## Fresh Entry v3 cleanup candidate: intentionally not changed

Under the fresh nativeETH/fixed-ZZZ principal pair, a successful typed v3 Entry route has no reachable useful currency combination: v3 route admission requires distinct nonzero ERC20 source/output; source must be ETH/ZZZ, and execute requires output to be a principal pair member. ETH fails nonzero source, ZZZ->ETH fails nonzero output, ZZZ->ZZZ fails distinctness. ZZZ->anotherERC20 can be admitted but execution rejects it before moving user funds. Direct/native-v4 Entry paths remain usable.

This is a fresh-profile simplification candidate, not a found drain. Removing its selectors/storage/routeKind requires an explicit new source/API routing profile and all backend/test/legacy codec consumers to be mapped. Do not remove v3 converters: optional royalty ERC20->WETH->ETH remains a valid separate route and does not make WETH a principal input. This audit preserves historical ABI/journals and records the candidate rather than performing a broad unverified interface change.

## Verification status and limits

Five current-source composition methods were selected to close the newly recognized gap: abort before cutoff settlement, abort after royalty settlement, multi-hop late receipts during successor freeze, actual-native principal/full handoff accounting, and native partial-funded abort. They use real current controller/Vault/NFT/reward/royalty/fee/canonical modules, with explicitly mocked venue/prices/VRF/admission. They do not qualify real oracle, VRF, Uniswap market execution or target-chain services.

The first harness attempt exited0 but selected zero tests because the anchored filter omitted signature parentheses. Its raw files are retained in attempt1. An independent exact method-ID check rejected that vacuous result; it is not counted as a pass. The filter was corrected to exact escaped signatures and the same five methods retried using isolated compiled artifacts. No fixture, guard, gas/size bound or source policy was relaxed.

Final execution result is in `canonical-composition-summary.json` and independently required exact-selection result in `canonical-selection-check.json`: both pass; expected/actual five-method sets are identical, no duplicates, no missing/unexpected methods and no source drift. Final stdout SHA256 is `e1f29acdff882eea9deed88dce7896226911e794b04720215b8fdcc315773d26`; empty stderr SHA256 is `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. The run is pinned Forge1.4.4 commit05794498 and solc0.8.26, default Cancun/viaIR/runs1/Yul-off, isolated output/cache/home, noFFI/RPC/wallet/broadcast. Current source hashes before/after are retained.

Unqualified production routes/feeds/VRF/authority addresses/OpenSea integration, artwork hosting/retrieval, exact constructor initcode/gas, maximal-catalog gas, strict-cadence sustained operating rehearsal, current website acceptance, escrow cutover, economic attacker profitability, broken dependencies and independent audit/remediation remain open. No new safety guarantee, deployed state or publication/deployment claim follows from this review.
