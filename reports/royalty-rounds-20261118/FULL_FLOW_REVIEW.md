# Original round-engine full Entry workload and engineering follow-up

This is finite local evidence for an explicit historical source stage. It is
**not qualification of the later Manager/Pricing edits or production approval**.
The source-stage and raw hashes are in the [manifest](full-flow-baseline/MANIFEST.json).

## Actual workload

One new Solidity method,
`RoyaltyRoundsCapacity20261118Test.testRoundsFull1000DenseCurrenciesOpeningRotationsAllFaultsAndGrowth()`,
passes after657.953seconds. It mints1,000 actual NFTs through the verified SeaDrop
fixture and activates999 through actual Entry→Vault→Uniswap-v4→Membership→Royalty
calls. The incumbent cohort is599Common/300Rare/100Legendary, weight1,499; the
last Common remains dormant until each activation case. Contributions select
ETH or fixed ZZZ from the actual target/reference price imbalance during setup;
there are no price overwrites or raw membership/accounting grafts.

Sixteen six-decimal royalty currencies are admitted after activation8. The later
991 activations create dense enrollment histories. Before activation1,000, each
ERC20 has992 enrollment ends and appending opens another packed storage word;
ETH has999 ends. Tested intake is2,996 units per currency, with cursor0 or513.
The test verifies allocation to incumbents, newcomer exclusion, every incumbent's
claims across all17currencies, empty backed liabilities after drainage and the
next1,500-unit receipt split across all1,000 activated NFTs. Funded actual LP
trades/harvesting preserve nonzero incumbent LP rights during entry and growth.

Controlled feeds, VRF, market depth, test currency behavior and verified SeaDrop
remain fixture assumptions. Aggregate setup/drain/assertion tracing and gas
metering are paused; the measured Entry calls are natural complete calls. The
aggregate test harness uses its recorded large resources. These do not raise the
actual call's20M cap or the32M local block cap used by the cold verifier.

## Cold20M result

All ten cold read-only actual20M calls and their financial/royalty trace checks
succeed. The full20% padding rule passes only the two growth cases. **None of
the eight activation cases qualifies for the reviewed20M profile at this stage.**
Cold RPC estimates, rather than partially warm aggregate-test call counters,
decide this table.

| Case | Cold estimate | Full20% ceiling | Profile result |
|---|---:|---:|---|
| First opening, ETH |18,938,057|22,725,669|Blocked|
| First opening, ZZZ,16faults |17,858,433|21,430,120|Blocked|
| Rotated, ZZZ |18,895,429|22,674,515|Blocked|
| Rotated, ETH,1fault |18,025,307|21,630,369|Blocked|
| Rotated, ETH,16faults |17,006,844|20,408,213|Blocked|
| Rotated, ZZZ,16faults |17,757,752|21,309,303|Blocked|
| Rotated, ZZZ,16slow successful reads |19,541,445|23,449,734|Blocked|
| Rotated, ETH |18,145,302|21,774,363|Blocked|
| Growth, ETH |12,469,850|14,963,820|Pass|
| Growth, ZZZ,16faults |13,220,627|15,864,753|Pass|

The [summary](full-flow-baseline/full02/local-rpc02/SUMMARY.json) links the exact
per-case observations. The checker authenticates the exported state, exact
source/compiled metadata, all runtime pins, population, source/value/calldata,
currency fault controls and the two-way full financial trace. Each of the16slow
reads consumes at least45k from its50k allowance and returns the real balance;
the state is not merely labelled slow. Faulted currencies defer atomically,
while healthy currencies allocate to count999/weight1,499 before newcomer entry.
Growth performs no royalty intake. Ceiling calculation is
`ceil(estimate*120/100)` and successful exact padded calldata is mandatory when
the ceiling fits; no estimate-only admission occurs.

At most three isolated loopback nodes run concurrently, with per-case256request,
600second work and bounded response/trace budgets. The native Windows listener
table proves each exact127.0.0.1port belongs to the owned node PID before RPC.
Every owned node is stopped afterward. No public RPC, send, account unlock,
transaction, signer or existing chain is used. Complete Robinhood fees/provider
or market acceptance is not established by this local workload.

## Source identity and retained failed attempts

The successful stage compiles a closed198-source dependency graph. All compiler
metadata source identities match the captured pool, with Forge's CRLF-to-LF
normalization recorded separately from filesystem SHA256. Source brackets stay
stable and the original Foundry configuration is restored exactly. The important
filesystem hashes are:

| File | SHA256 |
|---|---|
| Manager |`237cdabac5ecd33399f5ef90d585569853ee4bd676d5730fa8aa2b4a79330ac4`|
| ContributionPricing |`c22ceebcd9f3c3d8f6c998fdef86a3af675718d7447ee03bb68325f5c0a05bfb`|
| RoyaltyRewards |`aa55a0fbe5d0ab652c42b7d32151c18f3159f8ddf56d59d1fe270dd272f7afc5`|
| ExactRoyaltyAllocation |`d2e761e976697aadae10c731914c017e5a0a200edfdf16a7e9258302d708e0fe`|
| ProtocolPolicy |`1806cedcaa524b21c0c2323f3bc765fbff30944d29936cee75d328ddc687e0cc`|
| Full workload test |`123492acdbf7e2696f8a8bdca6580a6ccde7267f7cba863e851d211f251e0fdf`|

The producer's first selector matched zero methods; its [failed execution
record](full-flow-baseline/full01/EXECUTION.json) is retained and is not a test
pass. The corrected unique selector checks the exact returned method identifier.
The initial cold-node attempt failed before any RPC because CIM listener
inspection was unavailable; its known records and
[scope limitation](full-flow-baseline/full02/INITIAL_INFRASTRUCTURE_FAILURE.json)
are retained. Its in-memory helper had not been frozen independently at launch,
so no reconstructed helper identity or financial execution is claimed. The
successful checker freezes its own exact source before all ten cases.

The published compressed source pool, raw producer JSON, artifact, exact state
exports and RPC transcripts retain their original hashes. Genesis allocations
are reconstructible from those exports and the authenticated merge recorded in
each verification; the second duplicate genesis image is omitted. Evidence
hashes establish integrity and finite provenance, not independent audit or
universal coverage. Copying/compressing this evidence executes zero tests.

## Cost investigation and Manager-only engineering probe

The recorded allslow ZZZ trace contains11full `Oracle.validateExecution` calls
(inclusive2,786,934gas), two Manager scope starts and ends, one actual swap proof
and the final Entry proof. The openingETH Royalty activation costs4,015,221gas;
`Rewards.syncShares` and `syncMembership` together cost2,569,735exclusive gas.
Nested inclusive costs overlap, and exclusive frame subtraction can be negative
because of refunds. The [call-cost summary](full-flow-baseline/full02/local-rpc02/CALL_COST_SUMMARY.json)
and [ordered boundaries](full-flow-baseline/full02/local-rpc02/rounds-999-rotated-zzz-allslow/ORACLE_BOUNDARIES.json)
are trace analysis only, with zero transaction replays.

The later Manager-only engineering probe supplements core probe02 with AST and
immutable locations, changing output selection only. Its runtime object matches
that probe byte-for-byte. All seven immutable addresses are obtained from the
old deployed runtime's actual getters and reciprocal graph checks. Only the
Manager's code changes in a copied authenticated allocation; every storage word
and other contract code remain byte-identical. New getters/controls are checked
again, and exact financial plus16slow-read traces pass.

The estimated allslow ZZZ cost falls519,727gas to19,021,718, but the full20%
ceiling remains22,826,062. This **does not qualify**. The Manager runtime is24,459
bytes, with117bytes headroom. Both owned engineering nodes stop. This is an
explicitly unqualified runtime transplant: it proves neither a fresh constructor
graph nor the later combined Manager/Pricing/other source. See the
[probe result](full-flow-baseline/manager/engineering01/PROBE_RESULT.json).

Additional opening+slow composites, final combined source sizing and a fresh
full graph/cold verification remain necessary before any new qualification
claim. No default, financial safeguard, entitlement or resource margin is
weakened to turn the recorded failures into passes.
