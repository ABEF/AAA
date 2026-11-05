# Last24-hour royalty and integration audit

Internal source candidate; **production NOT APPROVED**. No deployment, sealing,
public signing, service/site rollout, Anvil reset or journal migration occurred.

The fixed interval is2026-11-04T19:04:18Z→2026-11-05T19:04:18Z. It covers11
contract commits through967370f and3website commits through5674487. Subsequent
corrections below belong to this audit, not the original interval. See the
[plan](PLAN.md), [verification](VERIFICATION.md) and [evidence](evidence.json).

## What changed

| Finding | Correction and consequence |
| --- | --- |
| Scaled royalties stranded whole raw units even when ideal shares were whole | User-approved settlement4 assigns every allocated unit through GCD-normalized rarity tickets and a rotating remainder cursor. Three Legendary NFTs receiving3units now get1each. Fixed-cohort split receipts equal one combined receipt. This is an accounting-policy change, not merely refactoring. |
| First exact candidate assigned adjacent rarity tickets unfairly in integral cases | Normalize each captured eligibility prefix by its GCD(1/2/3). Keep earlier books after the cohort expands. True indivisible mixed-cohort remainders still rotate; they are not nearest-rounded individual quotas. |
| Synthetic backend models used zero-based starts while the real source used one-based starts | Rename internal coordinates to `ticket_offsets`; explicitly convert source `ticketStart=offset+1`, with0only dormant. Actual EVM logs/getters/V8 rows verify producer/consumer agreement. Model-only passing tests were insufficient. |
| Valid zero-amount canonical settlement telemetry was rejected by replay | A zero eligible `RoyaltiesReceived` acknowledges no income. Require matching generic credits for positive allocation telemetry; only `RoyaltiesAllocated` credits new income once. |
| Checkpoint builder could access nonexistent state | Correct its source state/serialization handling and compare bounded raw replay against checkpoint plus suffix; retain original fractions for LP/legacy profiles and exact current royalty books/cursors. |
| Opening flags could contradict their confirmed timestamp | Backend and website authenticate configured/end/open-at/status against the SAME confirmed snapshot. Reject inconsistent flags and positive locked royalty amounts. LP balances remain separate; dormant cards still show no deadline. |
| Sale changes could invalidate a reviewed mint after NFT returned, during the Vault's payee callback | Fresh Vault review hashes core sale/VRF policy, NFT, receiver, mintEnd and its monotonic revision. Check again after callbacks. End changes, including restoring a former end, cannot revive an old review. Preparation expires at the sale boundary. |
| Royalties arriving at a cancelled replacement had no usable onward path | After all abort backing returns, the CURRENT verified active target governance can review recovery of one admitted original currency. Authenticate retired lineage one bounded hop at a time. Sync before/after and recheck cohort/authority/lifecycle. Existing target unallocated funds stay separate. No arbitrary recipient or royalty swap. |
| New ledger creation bytes made the embedded factory exceed normal runtime size | Store only constructor-derived fixed creation bytes with immutable hash, verified before typed CREATE. No code/recipient/salt input or setter. High one-time storage/constructor gas remains an explicit target-chain release gate. |
| Initial recovery coordinator exceeded normal runtime size | Move only the read-only no-input lineage proof to the existing immutable Access-bound VaultCanonical companion. Coordinator retains restoration, permissions, route storage and transfers. Direct operator calls to the proof helper are rejected. |
|250k optional sync gas was insufficient for healthy cold exact allocation | Fresh default becomes1m, within unchanged governed100k–1m bounds. It is a forwarding ceiling, not a fixed charge. Smaller claim batches and actual maximum-state gas qualification remain necessary. |
| Expanded royalty capacity conflicted with the observer's old33-record inventory limit | Fresh schema13 shares97total token-record limit between validator and observer. Preserve historical profile bounds; exceeding the reviewed fresh bound still fails before reads. This does not approve admission or gas. |
| Current documentation mixed superseded royalty conversion, V6/V7 and fractional rules | Reconcile current guides, profiles, sole Todo, features, roadmap, operator call tables and repository memory. Preserve historical reports, old codecs/configs and original evidence. |

## Current financial rule

The fixed80/10/5/5 LP allocation is unchanged. LP indices/fractions, principal
shares, entrant/incumbent separation, both-leg valuation, harvest, conversion,
compounding, buyback, terminal holder return and emergency permissions are not
replaced by this royalty redesign. Original-currency royalties are separately
weighted Commun1/Rare2/Legendary3 and follow the current NFT owner.

Settlement4 uses outstanding units rather than a lifetime monetary index. An NFT
reads/consumes at most four effective tickets across normalization books. There
is no per-receipt1,000-holder loop and no allocated fractional royalty reserve.
The cursor advances only on remainder allocation, never claims/transfers.
Tiny mixed-cohort receipts can favor a particular ticket temporarily. Activation
order, public allocation timing and donations can affect the next indivisible
recipient. Review a token's raw-unit value; this policy cannot divide a unit.

CanonicalV8 exports frozen whole entitlements without deleting source books,
preserves actual activation order independently of mint order, validates complete
ticket/ordinal coverage and exact per-currency liabilities/backing, and retains
funded abort. V7 peers/checkpoints are not relabeled. Reporting5 and inventory13
are explicit fresh boundaries. The allocator adds no deployed helper/authority.

## Where every unit belongs

| Category | Meaning and required action |
| --- | --- |
| Allocated liabilities | Exactly assigned ticket/imported whole units. All eligible claims drain allocated liabilities with no allocated rounding remainder. Current owner receives the original currency. |
| Pending receipts | Actual balance not yet synchronized; sync/claim accounts them under the recorded cohort. ERC20 receipt arrival times cannot be reconstructed from balance alone. |
| Mint plus ONE-hour window | Held separately for strict pre-cutoff activations; lazy first successful sync allocates after opening. No royalty keeper transaction prerequisite. |
| No activated cutoff cohort | Remains explicitly unallocated until governance reviews allocation once eligible holders exist. The first later activation does not automatically capture it. |
| Constructor/preadmission/unsupported receipts | Discover/review/admit the exact currency; governance allocates eligible unallocated units at current active weights. No invented historical eligibility or arbitrary sweep. |
| Cancelled replacement receipts | Complete abort first, follow verified lineage if necessary, then target-governance reviewed recovery. Captured abort backing is not this recovery money. |
| Faulted/frozen/taxed/rebasing token or incapable owner | Exact accounting cannot compel transfer or recover lost keys. Isolate healthy claims; investigate the dependency/ownership. No universal automatic payout guarantee. |

Thus “every received unit is immediately claimable, with no unallocated funds at
any time” would contradict the selected opening, zero-participant and review
rules. The implemented promise is exact assignment of every ALLOCATED unit plus
explicit, protected handling of each other category. Currency capacity is16ERC20
plusETH initially, reviewed increases up to64; it is not unlimited safe admission.

## Scope and remaining risk

Affected tests, actual source-wire fixtures, independent bounded allocator models,
normal compiler gates and strict analyzer triage support these corrections.
Earlier failures, empty selections, source drift and corrected fixtures are
retained and distinguished in [verification](VERIFICATION.md). Existing keeper
deadline/indexer/manual-guard evidence is reused only at exact unchanged contexts;
this is not another whole-project regression or independent audit.

Runtime headroom is tight: royalty52bytes, Migration39, Budget237, Balancer360,
Handoff448, VaultCanonical511 and Vault635 in the recorded normal build. Fixed
factory deployment gas, maximum currency activation/claim/handoff work, host/RPC
budgets and target block/transaction limits remain open. A32-entry router limit
does not establish universal32-entry gas feasibility.

Actual OpenSea caller/payment/final-stage binding, feeds/routes/VRF, authorities,
matching source8 services/site, storage/restore/lifetime history, marketplace
payments and independent audit/remediation remain in the [sole Todo](../../TODO.md).
The public simulation, served poplint/current3, Anvil holdings, signer and journals
are unchanged. The website source changes do not complete or deploy native6 integration.

## Test-maintenance follow-up

The user's follow-up identified a separate maintenance obligation. Current
tests still contained old identity/rounding assertions, unopened-window claims,
post-handoff mint assumptions, old validator/template combinations and a false
16-fault/12M gas claim. These were not reasons to restore retired behavior or
weaken financial guards. [The maintenance map](TEST_MAINTENANCE.md) distinguishes
current corrections, stronger nonvacuous models and retained historical imports;
[verification](VERIFICATION.md) records the targeted follow-up stages separately.

In particular, the1M isolated budget does not prove aggregate activation fits an
existing12M envelope. That is an operating qualification gap. Insufficient gas
must reject atomically; a larger synthetic local call is not permission to
change a running API budget or to call maximum currency capacity qualified.

## Standards used in the review

ERC2981 reports a recipient and percentage; marketplace payment is separate,
and payment uses the sale currency. It does not enforce universal5% collection.
[ERC2981](https://eips.ethereum.org/EIPS/eip-2981)

External calls can reenter across contracts, and bounded loops must respect gas.
Review pre/post authority, exact backing, effects-before-payout, isolated currency
failures and atomic rollback together. [Solidity0.8.26 security considerations](https://docs.soliditylang.org/en/v0.8.26/security-considerations.html)

Normal runtime size limits apply independently of passing test profiles.
No test size override is deployability evidence. [EIP170](https://eips.ethereum.org/EIPS/eip-170)
