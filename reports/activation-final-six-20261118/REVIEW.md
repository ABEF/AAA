# Six remaining activation cases — resolved in the controlled workload

18 November 2026. Baseline main: `963e039caa163a4921d08ed4bfc6b3a44cb79d42`.
Production remains undeployed and NOT APPROVED.

**All six previously refused activation cases now fit 20M with the complete
20% padding. All thirteen affected cold scenarios pass the financial checks,
the actual 20M calls and their exact padded calls.** Worst opening ZZZ/all-slow
falls from18,612,697 to16,460,899 raw gas, and from22,335,237 to19,753,079 padded.
The worst tested call therefore has246,921 gas remaining after the full margin.
Every matched complete-call estimate decreases, by725,596–2,151,798 gas.

The [comparison](BASELINE_COMPARISON.json) proves identical sender, destination,
amount, calldata, NFT/bucket,20M cap,20% padding and controlled block anchor for
all thirteen baseline/current cases. See the [complete gas table](GAS_TABLE.md)
and [cold results](full-flow-final/full01/local-rpc/SUMMARY.json). This closes
the six measured refusals, not every Q03 workload or a production release gate.

Offline [retained-trace attribution](TRACE_ATTRIBUTION.json) confirms where the
worst case improves. Both selected traces use20M; exclusive gas excludes nested
callee work, so these are separate observations, not component-budget sums:

| Contract's own frame work | Previous gas | Current gas |
|---|---:|---:|
| Royalty |3,807,396|2,520,133|
| Contribution Pricing |617,747|259,487|
| Oracle |2,781,155|2,539,948|
| Rewards |2,168,745|1,979,609|

## Implemented changes and preserved rights

Six production source files change. There is no new authority, custody
recipient, permission, helper deployment or operator action.

| Component | Improvement | What remains exact |
|---|---|---|
| Royalty status | Count, weight, cursor and initial-allocation flag share one private word. Metadata fields use16bits; production bounds remain1,000 NFTs/3,000 tickets. | Full monetary balances/liabilities, per-currency eligibility, fault recovery, one-hour opening and current-owner claims. |
| Royalty Book | Common round coefficient and cursors share a word; a tagged second word holds every larger uint256 coefficient. | All lifetime coefficients remain modulo2^256; receipt/liability arithmetic stays checked. Original currencies, unit allocation and flattened canonicalV10 rows remain. |
| LP carry | MAX128 marks the full-width low spill; normal and zero-phase reads avoid an unnecessary second-slot load. | High128/low256 logical phases, all pending units, split/rebase algorithms, two-slot footprint and canonical wire rows. |
| Contribution Pricing | Basis, captured marks and bounded asset list use contract-local transaction storage; each operation still explicitly clears them. | Every immediate write/callback boundary, typed value, phase, captured source/policy comparison and atomic rollback. Maintenance bucket remains persistent. No balance or holder ledger becomes temporary. |
| Oracle | Direct canonical partial projection and masked static hash encoding avoid repeated generic ABI work. | All15 quote/control words, strict49-word record length, typed sole writer, pending-swap rejection, live controls and full mutable-boundary proofs. |
| Optional native-v4 feed | Encode the exact seven-word nested pool identity directly. | Every round ID, signed tick, quote, source/configuration/freshness/liquidity/fee check and outer hash. No price source, TWAP or policy change. |

The generic enrollment/birth library wrappers retain their original validation.
The production host uses specialized paths only after its existing bounded,
strictly increasing eligibility/positive-ordinal proofs. No public financial
or authorization guard is removed. The zero-book simplification is proven for
the host's positive receipts and authenticated cursor sequence; it is not a
general equivalence claim for a fabricated zero-credit/arbitrary-cursor caller.
The [royalty domain review](engineering/ROYALTY_REVIEW.md) gives the detailed
proof; the [lossless engineering archive](engineering/MANIFEST.json) preserves
all source stages and failure evidence.

The80/10/5/5 LP split, rarity1/2/3 royalties, exact activation-time rights,
source/fault cohorts, original-currency royalty claims, marginal deployed LP,
entrant-only funds and net-NAV share issuance are unchanged. Contributions
still do not recenter incumbent LP or reset its clock. Default loss budgets,
oracle agreement, idle/caller floors, source freshness/code pins, rollback,
roles and all other financial controls stay unchanged.

Keep the12M default, reviewed20M/full20%,50,000 activation balance-read cap,
1M isolated currency sync allowance and120,000 funding reserve. No budget,
headroom, compiler setting or safeguard is raised or weakened.

## Fresh source, payload and compatibility

The trusted normal build is `activation-final-six-20261118`. Its exact closed
100-source graph passes all48 unchanged runtime/initcode gates and the strict
artifact importer. The [normal evidence](build/final/normal-size-evidence.json)
records Oracle23,406/1,170 runtime bytes/headroom; Rewards23,983/593;
Royalty24,562/14; Manager24,459/117 and Vault24,544/32. Access full initcode is
48,580/49,152; Oracle full initcode is47,710/49,152. Tight Royalty/Manager/Vault
space remains a maintenance constraint.

All public selectors, argument/output/tuple types, mutability and economic
rules remain. Three former mapping getters now name their address input
`asset`; this cosmetic ABI difference is explicitly recorded, not called
byte-identical. Callable documentation remains40 contracts/968 functions/
40 constructors/13 receive hooks and1,021 unchanged operator example rows.

Royalty creation changes, so fresh configuration explicitly selects
**payload6**, allocation2, in unchanged code-storage FORMAT2. Creation length
is25,533 and hash is
`0xbb0f8ce9cf2c332313c08da26f70174276182fd2202e7b308d4352525207c9e4`;
the two inert data runtimes are24,576 and963 bytes. Exact old payload3/4/5
identities remain separate. The old F5 helper/artifact and the preserved
`production.schema17.payload5.example.json` are byte-identical. See
[consumer review](consumer/REVIEW.md) and [generated pins](consumer/GENERATED_PINS.json).

These are fresh private layouts/codecs. Never hot-copy old Royalty or LP carry
slots, replace old runtime labels, rewrite pending journals or silently adopt
old checkpoints. Use reviewed logical canonical records and exact fresh pins.
The [layout acceptance](build/final/LAYOUT_ACCEPTANCE.json) admits only the two
reviewed private layout changes and three cosmetic ABI names. Pricing has no
legitimate cross-transaction contribution context; its transaction-only state
matches the existing atomic Entry/Budget and Oracle execution model.

## What actually ran

The [plan](PLAN.md) and engineering archive keep source stages separate.
Do not sum executions or overlapping scenarios into a whole-project pass.

| Scope | Evidence |
|---|---|
| Exact normal graph |100 sources,48 normal size gates, canonical ABI comparison and explicit private-layout admission. The final admission reuses its captured output without another compilation. |
| LP codec |8 affected/new isolated methods: full-width boundaries, spill/compact transitions, mutable shares, claims and logical rows. Funded owner/collective components save185,917 gas; zero-fee components save105,301 versus the immediately previous codec. |
| Royalty codec/host |9 new methods:223-bit/full256 boundaries, modular wrap/zero cursor, late first cursor, generic validation, normalized2/3→1, opening/fault/current-owner payouts, flat import/prefunds/future income and funded abort. |
| Pricing |11 distinct host methods, including8 affected checks and3 new width/phase cases. Actual baseline/candidate production Pricing with controlled callers checks STATIC callbacks, immediate visibility, sequential operations, exact basis hash/shares, rollback and retry. Paired component saves356,135 gas. |
| Oracle / feed identities |10 new quote/hash methods and5 new feed identity methods cover canonical/dirty narrow words, signed extremes, lengths, repeated save/clear, sentinels and exact hash bytes. These component timings do not substitute for complete-call estimates. |
| Actual Rewards recovery |2 affected existing methods re-execute against the new codec: all2,029 logical export rows, ETH/ERC20 backing release/accept or abort/restore, current-owner rights and future receipts. Typed dependency seams are not the complete coordinator. |
| Consumers |12 distinct passing controls:7 new F6 methods and5 affected historical-loader/build controls. Historical archives remain hash-authenticated without pretending they match current source. |
| Static CI closure | Actual Slither0.11.6/crytic0.4.2 consumes the admitted100 ASTs without another compilation. All601 records are covered:147 current assessments and454 exact referenced-source reuses. The former default rejects current drift; the unchanged matcher passes after its review default points to the fresh record. Two new default-admission regressions pass. [Scope and limits](STATIC_REVIEW.md). |
| Complete workload |One affected existing method rebuilds999 actual incumbent Entry contributions at1,000 minted NFTs, then exports13 states. Each cold owned-node check validates source/runtime/anchor, actual marginal LP/accounting and pre-join royalty events/read caps, exact20M success and successful full20%-padded simulation. All13 owned nodes are stopped. |

The unchanged workload body is source-pinned; these are13 scenarios, not13 new
test methods. It includes ETH/ZZZ activation/growth, pending opening receipts,
rotated receipts, healthy/one-fault/all-fault and slow successful currencies.
Its16 ERC20 currencies plus ETH, full cold enrollment append and fixed entrant
order are deliberate controlled cases. It does not establish universal64-
currency, two-physical-LP, every-order, real-provider or real-market capacity.

### Corrections and rejected work remain visible

- Fifteen finite new royalty object probes include rejected oversized designs.
  The previous four unchanged rejected probes were not rerun. Only final10 is
  adopted; hypothetical savings are not reported as measurements.
- Two royalty canonical fixtures initially validated before transferring backing;
  the financial guard rejected them. Only the corrected two methods were rerun;
  one diagnostic failure is retained. Nine distinct methods have twelve executions.
- An initial feed gas probe had cold/warm call imbalance. The corrected matched
  probe saves962 gas/identity; the biased figure is rejected.
- Normal final01 completed compiler output but its report checker wrongly rejected
  duplicate inherited error ABI rows. Its raw output/failure remains. The corrected
  checker preserves multiplicity and captures compiler exit before postprocessing;
  final02 is the admitted normal run. No test suite was rerun for that tool fix.
- A new archive fixture initially used an integer-only input decoder on a pinned
  report's elapsed-time float. Only affected archive controls were rerun. Consumer
  count corrections and a discarded workflow-only probe are excluded from coverage.

## Remaining limits and operating boundary

The six measured gas refusals are resolved. Actual independent ETH/ZZZ prices,
usable routes/depth, selected currencies, complete target fees/provider capacity,
expanded maximum workloads, current constructors/operations, VRF/OpenSea/
authorities, service/site rollout and independent audit remain open.

One editorial residual is recorded for the next source revision: the inline
Royalty status comment still describes an earlier10/12/12-bit sketch. Actual
getters/writes and reviewed layout use16/16/16 with the initial bit at48. Operator
guidance is correct and requires public reads, not private-word decoding. The
frozen code is not changed after qualification for a comment-only rewrite;
correct it with fresh source/artifact pins at the next source revision.

The source and documentation update does not deploy, seal, sign, adopt a service
or modify existing Anvil8902/NFTs/LP/balances, journals/DB/WAL/dist, websites,
browser signer/public-null configurations or the user-paused heartbeat. Four
unrelated dirty files and historical report bytes remain preserved. Todo and
the operator guide distinguish this controlled improvement from release approval.

Technical basis: the pinned [Solidity0.8.26 assembly/memory conventions](https://docs.soliditylang.org/en/v0.8.26/assembly.html#memory-safety)
require explicit narrow-word cleaning and safe temporary memory. [EIP-1153](https://eips.ethereum.org/EIPS/eip-1153)
defines contract-local transaction storage, revert rollback, STATIC reads and
explicit caution about stipend-based assumptions. Existing authority/phase
checks remain; transaction-end clearing alone is not used between operations.
