# Packed LP phase accounting — exact logical rights, bounded engineering evidence

The parent accepted the source candidate after its normal/source review. Source publication is not deployment or release approval. No existing chain, journal, service, public signer or budget was changed by these checks.

## Representation and invariants

Carry remains two storage slots. Its first uint256 packs high128 and a compact low128; nonzero second-slot wide holds every low>=2**128. Reading returns the original logical high128/low256. Writing clears an old spill when low returns to compact form. No weight, phase, balance or monetary domain is narrowed. Split math and setWeight ordering are unchanged; private packing changes no economic rights or authority.

The logical LP-allocation1 algorithm, high/low canonical rows, public ABIs, Book96/Tree224-byte footprints and all top-level slots/offsets remain. Private raw EVM carry storage is incompatible with the old high/low representation: use exact fresh runtimes/source pins and logical canonical import, never a hot code replacement or raw old-slot copy. No new authority, external getter or profile flag is introduced.

## Evidence stages — do not sum executions into features

| Stage | What actually ran |
|---|---|
| [Engine differential](engine/differential01/RESULT.json) | Six affected/new isolated methods pass: all2047 logical nodes/both books, mutable weights, claims, MAX/zero/noop/overflow, reachable spill→compact→spill, boundary128/MAXlow encoding, deterministic128-step sequence and extracted999-state component comparison. |
| [Zero-fee component](engine/zero-fee01/RESULT.json) | ONE additional new method passes. Both assets have zero earned fees/outstanding; logical node equality remains. The prior six method bodies stay exact and were not rerun. |
| [Actual host final](canonical-project/actual03/RESULT.json) | TWO distinct new actual final Rewards+immutable RewardsCanonical methods pass. Exact29-source closure and project sources are stable; ROOT foundry.toml is neither used nor bracketed. |
| [Adapter compile](canonical-project/adapter-compile/RESULT.json) | Two exact copied current test adapters compile under normal settings; ZERO old test methods execute. Logical ABI tuple order is proved against the baseline, and the frozen old adapter remains unchanged. |
| [Source-copy size](normal-host01/RESULT.json) | Actual Rewards24,218→24,072runtime bytes (504headroom); canonical child18,609unchanged length. Two selected objects, not full release build acceptance. |

Actual host stages01/02 retain the failed test-only raw-slot inspector experiments. Stage01 explicitly reports MemoryLimitOOG; stage02 reports a generic revert near the aggregate fixture limit, with no financial assertion failure established. Neither is counted as a pass or diagnosed as a production defect. Final03 uses actual canonical export rows instead of the raw VM inspector and succeeds. Its full test transaction is an intentionally large verification workload (~998M aggregate gas under the predeclared1B test ceiling), not a permitted operating transaction or canonical page-gas qualification. No production/default/headroom limit changed and no gas metering was disabled.

## Measured component tradeoff

| Controlled component | Original | Packed | Difference |
|---|---:|---:|---:|
| Funded999 owner enrollment |1,303,448|1,062,543|240,905saved|
| Funded999 collective enrollment |1,140,048|975,668|164,380saved|
| Zero-earned-fee999 owner |218,230|270,767|52,537extra|
| Zero-earned-fee999 collective |218,026|270,580|52,554extra|

Funded component total saves405,285gas. Zero-fee component total costs105,091more because reading the logical phase checks the second slot. This is a real conditional regression, not universal savings. Standalone hosts/inlining differ from actual Entry; never subtract these numbers from a complete-operation estimate. Final whole-operation20M/full20% qualification is recorded separately by the parent campaign.

The extracted state uses the committed999-NFT openingZZZ/allslow fixture. Normal storage metadata authenticates owner/collective bases and logical restoration; no old full-state exports are duplicated. The initial fixture has zero materialized carry values but funded pending money. Separate full-width methods explicitly exercise nonzero compact and wide carries. All touched engine slots/accounts are cooled before component calls.

## Actual canonical lifecycle scope

The production final Rewards and its constructing immutable canonical child perform the operations. NFT/Access/Vault/Membership/token identities are explicit typed test seams; the full ZZZCanonicalHandoff coordinator, actual NFT minting, Uniswap, price feeds and real deployment are not qualified here. Huge weights beyond ordinary priced-entry examples deliberately exercise the uint256 spill domain and do not establish their admissibility under full protocol price/cap checks.

Three identically seeded ledgers provide source, target and unmigrated control. NFT1 has already claimed; NFT2 transfers fromB toC; NFT3 remains dormant. Both ETH and exact ERC20 receipts create compact collective phases and wide individual phases. The actual immutable codec exports/imports all2029rows (header,2assets,3NFTseeds,2023nodes). Real backing is released from source parent, accepted through target child and returned to its parent. After activation a legitimate fresh target capture reproduces every source/control export row. Current owners receive exactly the remaining rights, dormant rights stayzero and subsequent funded income matches control before complete drainage.

The second method releases and accepts backing, then uses actual state4 release→source restore to return both assets. Source export rows remain exact; original current-owner claims and future income match control. The aborted target remains locked and holds no backing. These direct codec flows use typed lifecycle-control seams, not an assertion that a complete coordinator cutover/abort is production-approved.

Current NativeFee.rawTreeDigest and ExactLPAllocationHarness.node/digest were copied exactly into isolated compile probes. [Adapter proof](canonical-project/ADAPTER_SOURCE_PROOF.json) verifies typed logical order, source hashes and the unchanged frozen adapter. The initial selected Forge file did not compile that unimported probe; the separate standard-JSON codegen supplies the actual compile evidence. [Metadata bindings](canonical-project/ACTUAL_METADATA_BINDINGS.json) bind real host/test dependencies and disclose any compiler line-ending normalization.

## Remaining work

Keep exact entitlements, all safeguards and the20M contribution profile with full20% headroom. Component and canonical functional evidence do not approve final constructor/runtime adoption, whole Entry gas, maximum64-currency/two-leg/all-order state, target providers/fees, actual operating batches, market/VRF/OpenSea services or independent release audit. No unchanged historical suite was rerun by this slice.
