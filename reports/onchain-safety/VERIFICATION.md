# On-chain safety and cost: scoped verification

Recorded 2026-10-24. Undeployed candidate; production **NOT APPROVED**. This is
internal implementation evidence, not an independent audit, live oracle/route
qualification, public transaction or fresh full regression.

## Results and failure provenance

| Scope | Distinct passing cases | Evidence |
| --- | ---: | --- |
| New Oracle boundary and contribution encoding tests | 12 | [Focused run](root-focused-summary.json), [inputs](root-focused-inputs.json): bounded uptime gas/return/revert data, strict widths, deduplicated calls, failed-source self-quote rejection and governed recovery; maximum `1e36` price plus 1,000 fuzzed real contribution/share/basis-hash cases. |
| Affected pricing and Entry cases | 74 | [Run](pricing-affected-summary.json), [inputs](pricing-affected-inputs.json): dual policies, stale/divergent/invalid rounds, sequencer/grace, frozen prices/caps, late historical backing, actual owner rights, callback rollback and claims independent of pricing. |
| Strategy planning | 30 | [Initial 24 passes / one stale fixture failure](strategy-affected-summary.json), [two additional parity cases](strategy-additions-summary.json), [three native cases](strategy-native-summary.json), [only repaired failed case](strategy-fixture-repair-summary.json). Includes nine new cases, 21 prior cases, mixed decimals/native, both directions, reversed USD-price/source ordering, outside-range behavior and 1,000-run range fuzz. |
| Reward accounting and claims | 27 | [Six new checkpoint cases](reward-cached.json), [20 affected existing cases](reward-affected-summary.json), [one paused/pricing-independent claim](reward-pause.json). Maximum 33 currencies, no retroactive earnings, pre-top-up fractions, exact one-read contexts, current-owner/native callback checks, bounded claims and converted-output conservation. Fuzz runs retain their actual 1,000/1,001/1,000 iterations. |
| Cold scaling and capacity | 2 | [1,000-NFT / 32-ERC20 reward workload](cold-gas-summary.json), [gas readback](cold-gas-readback.log); [combined capacity activation](combined-capacity.log) with four buckets, inbox/royalty bounds and every historical reward index populated. Existing gas budgets are unchanged. |

These are **145 distinct Solidity case IDs**, including 27 new cases. Repeated
gas readbacks and fixture reruns count once. The [consolidated case record](verification-summary.json)
retains original failures and confirms no unresolved affected case.

The [prepatch Oracle control](oracle-before-summary.json) has eight expected
failures and two already-safe passes. It demonstrates the old reader/call-count
behavior; it is not a failed final candidate. The Strategy fixture reload was
refreshing its deliberately stale feeds after admission. Dual admission correctly
rejects that stale round. The fixture now refreshes first; only that failed case
was rerun. No production check or limit was relaxed.

The [83 affected backend checks](backend-affected.log) cover dual-price preparation,
preflight and the event/source schema. Functions/events/entry points are unchanged
in the [ABI comparison](abi-compatibility.json); shared price math exposes the
existing `InvalidPrice(address)` error in Strategy's ABI. No new caller authority
or event schema is added. Unchanged website and unrelated suites were not rerun.

## Cost measurements and limits

| Measured workload | Before | After | Meaning |
| --- | ---: | ---: | --- |
| Strategy planner call | 486,203 | 155,839 | 330,364 gas saved, about 67.95%. Identical warm mock-venue / real-Oracle / mock-feed fixture and compiler; only Strategy differs in [paired snapshots](strategy-gas-summary.json). |
| Owner checkpoint benchmark test | 27,360,383 | 27,190,449 | 169,934 gas saved. These are whole-test values from retained raw JSON, including identical token setup/funding; not a full activation fee estimate. |
| Collective checkpoint benchmark test | 27,323,733 | 27,194,722 | 129,011 gas saved. The two benchmark deltas total 298,945 gas. [Raw-supported comparison](reward-gas-comparison.json). |
| Cold combined-capacity activation | 11,864,627 | 11,507,856 | 356,771 gas saved; final margin 492,144 under the unchanged 12,000,000 gate. Before retains the [prior source scope](../price-security/VERIFICATION.md); final source/fixture is pinned here. |

Checkpoint fixtures deploy no Oracle, pricing companion or Strategy. Those files
also changed between concurrent snapshots but are not on that measured path;
the [input differences](reward-gas-comparison.json) remain explicit. Absolute
call-only checkpoint observations were displayed during development but their
verbosity logs were not saved. This report uses the retained raw whole-test
values instead. No extra benchmark was run to manufacture more passing cases.

All measurements use explicit local substitutes. Cold deltas exclude intrinsic
calldata gas and refunds; planner/checkpoint cases are warmed. None qualifies
actual Chainlink/other providers, selected-chain gas limits, conversion markets,
wallet fees or full real-user transaction costs. New packing adds some runtime
instructions to save recurring storage work; one-time deployment cost is not
claimed lower for every contract.

## Build and source scope

[Final production compilation](production-size-gates.json) passes **37 source
object gates**, including the new internal library's compiler object. It adds no
deployed helper address: the current inventory still has 15 helpers. Pinned
Solidity 0.8.26/Cancun/via-IR, optimizer runs1, Yul disabled and normal size limits
are unchanged. Dynamic constructor arguments still need exact release checks.

| Contract | Runtime bytes | Creation plus fixed arguments |
| --- | ---: | ---: |
| Vault | 24,551 (25-byte runtime margin) | 46,720 |
| Oracle | 11,042 | 29,267 |
| ContributionPricing | 14,945 | 15,663 |
| Strategy | 13,286 | 13,781 |
| Rewards | 21,311 | 22,364 |

[All-source ABI/typecheck](all-typecheck.json) passes for **120 source/test/script
inputs**; [final bindings](final-solidity-bindings.json) record their exact bytes.
The [per-run scope](source-scope.json) distinguishes snapshots taken during
concurrent work. In particular, early focused tests retain the prior equivalent
Oracle reference-function body; final reference/library behavior is covered by
the subsequent pricing/Strategy scopes. The final build pins current production
source. Earlier receipts are not rewritten as final-source full regression.
The [source checker](source-checks.json) is consistency-only, not exploit analysis.

Actual independent feeds/proxy review, target-chain routes/gas and operating
rehearsals, production inventory and independent audit/remediation remain open
in the [single Todo](../../TODO.md). Existing8902/Anvil/NFT/LP/balances/journals,
the dist repair overlay, Anvil-only signing, null public DEPLOYMENT and paused
monitoring were preserved. Publication is a separate [Git receipt](PUBLICATION.md).
