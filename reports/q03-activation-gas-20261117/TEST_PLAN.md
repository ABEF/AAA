# Q03 activation gas: independent test and consumer review

Baseline: `23be8c9`. This is a source review and proposed selection, not executed
verification. No source, default, admitted currency, entitlement, deployment or
existing environment is changed by this review.

## What must remain true

`ZZZRoyaltyRewards.activate` first fixes the opening cutoff, settles each healthy
currency against the old cohort, and only then appends the permanent rarity
tickets. A faulting optional currency retains its own prior cohort. ETH is not
an optional ERC20. A later successful synchronization credits that older cohort
before enrolling waiting activations. The one-hour opening cohort is a separate
rule: pre-cutoff activations retain their initial entitlement even if a currency
was unreadable during the opening window; a first transaction at or after the
cutoff must not include its new activation in that opening cohort.

The exact allocator distributes indivisible units to permanent tickets, using
quotient plus rotating remainder. Claims remove units from the outstanding tree;
they are not a lifetime balance. Unit1, unit2 and unit3 books can coexist when a
homogeneous cohort later gains another rarity. An optimization must preserve
their combined rights, claim ordering independence, current-owner authority,
backing and the canonical flatten/export/import result.

Reducing the configured currency allowance, skipping healthy allocation,
enrolling the entrant before old receipts settle, changing the opening cohort,
deferring a healthy entitlement merely to fit gas, increasing20M or removing
full20% padding is not an acceptable gas optimization.

## Finite new complete-operation selection

Each case below measures a NEW combined accounting/Entry state, rather than
rerunning an unchanged existing method. Build coherent actual NFT owners,
rarities, activation ordinals and royalty tickets. The actual600/300/100 rarity
inventory bounds the1000-NFT collection at1500 tickets. A999-incumbent case can
have1499 tickets; a fabricated2997-ticket launch is not the selected collection.

| Case | Setup and measured operation | Independent financial oracle |
| --- | --- | --- |
| A:811 rotated healthy |811 active NFTs, weight1023,16 ERC20 currencies plus ETH. Credit513 units, claim the first513 Commun tickets, then leave `2*1023-2` pending units per currency. Measure a real ETH Entry activation of a Rare entrant. | Enumerate every permanent ticket in the test model. Compare every incumbent's whole units, sum to exactly2044 per currency, entrant's older share0, cursor wraps from513 to511. Independently reconcile actual marginal deployed LP, net added NAV/shares, owner, unchanged main ID/range/clock and all reserves. |
| B:999 rotated healthy |999 incumbents, weight1499 and a final Commun entrant. Use the same drained/rotated setup, pending2996 units per currency, real ZZZ Entry activation with exact prior allowance. | All1000 NFT activation metadata and stock remain valid. Independently total all incumbent payouts to2996, final entrant0 old units, future receipt apportions to all1500 tickets, and every raw unit can drain. Verify exact token pull/allowance and Entry/Vault residual balances. |
| C:811 one full-budget fault |Case A, with one balance-read fault consuming the configured1M optional-currency allowance. Select first, middle and last ERC20 positions as separate frozen starting states if execution order is changed. | Only that currency defers the entrant. All16 healthy currencies, including ETH, settle fully and enroll it. After token recovery, pending older units still go only to the incumbent cohort; a later receipt includes the entrant. Claim in a different order and transfer an NFT before claim. Sum paid plus liabilities plus explicitly unallocated units to actual backing. |
| D: opening boundary |A large coherent pre-cutoff cohort, openingPool already credited and additional raw receipts unsynchronized. Measure a late Entry activation exactly at `royaltiesOpenAt()`, including a currency that was faulty during grace. | Fix the cutoff before appending the late activation. The original grace cohort receives openingPool+raw units; the late entrant receives0 initial units. The previously faulted grace activations are included on recovery. Finalization must not depend on which asset synchronizes first. |
| E: full fault boundary |Large coherent cohort with all16 optional currencies exhausting their allowances, then a real Entry activation at the unchanged20M cap. | Record success or atomic refusal honestly; no assertion that existing policy must admit this state. Failed complete calls must restore ETH/ZZZ, LP ownership/liquidity, approval effects, shares, all royalty metadata, and scope state. A larger diagnostic ceiling never qualifies20M or its margin. |
| F: post-optimization large-state growth |A current activated NFT in the large predecessor state receives a real$5 growth contribution while optional royalty currencies fault. | Growth must not append rarity tickets or loop through royalty enrollment. Preserve older royalty rights and prove actual marginal LP/net shares, current-owner linkage, unchanged geometry/clock and exact reserves. This is a new large-state interaction, not a repeated prior simple growth test. |

Use exact per-ticket arithmetic in test code, not `claimable`, allocation library
preview functions or a second copy of the tree algorithm as the expected result.
For amountA, old weightW and old cursorC, increment the independent ticket vector
by `A/W`, then increment exactly `A%W` tickets starting atC with wrapping. Sum
per-NFT ticket intervals only afterward. Keep already-paid units separate.

If predecessor setup uses typed privileged test writers instead of999 real
historical Entry contributions, disclose that boundary. The measured operation
can still traverse the real Entry/Vault/NFT/royalty and v4 graph, but it is not
proof of999 historical physical-LP contributions or live SeaDrop acceptance.
Do not transplant arbitrary private tree storage and call it a real setup.

## Targeted optimization-sensitive companions

Run only newly added/changed relevant methods, with preserved baseline failures.

1. **Book transition:** all-Rare or all-Legendary cohorts within their actual
   stock limits, with outstanding and partially claimed unit2/unit3 credits;
   append another rarity and verify old compressed-book units plus new unit1
   units, rotated cursors and exact current-owner payouts. The large mixed
   cases alone do not exercise this representation transition.
2. **Underfunding and external-token boundary:** a successful but expensive
   token read, reverting read, oversized revert, malformed balance reply and
   read-only callback attempt must not corrupt other currencies. Caller gas
   starvation must not turn a healthy settled currency into an enrolled
   newcomer with older income. Any lower complete-call cap must either preserve
   the defined deferred cohort or revert atomically, not silently drop work.
3. **Canonical continuity:** after mixed books, partial claims, deferred recovery
   and a transfer, use actual royalty canonical capture/settle/export/import
   with authenticated backing. Compare independently expected whole-unit rows,
   cursor, orphaned funds and future rights. A faulted/unopened initial cohort
   must keep its existing blocking semantics; do not flatten it away to pass.

## Complete gas measurements and admission

Current activation schema2 uses the explicitly configured cap, reduced by the
gas limit of the SAME confirmed block hash. For the20M profile, the exact final
estimate must satisfy `ceil(estimate*120/100) <= 20,000,000`. Thus16,666,666
passes this arithmetic boundary and16,666,667 does not. Body gas deltas are not
complete transaction estimates; same-test SSTORE original-state effects and
warmth remain separate from a fresh RPC call.

The backend first traces a probe, freezes tighter output/LP floors, traces the
actual returned calldata and estimates that same exact transaction at the
confirmed hash. It rejects differing same-snapshot economic results and checks
the final canonical anchor and original expiry. Approvals remain separate,
exact-amount reviews requiring preparation again after confirmation. Request
payloads cannot override the configured gas policy. Gas and native fees remain
separate from the3% total contribution floor.

For each new exported state, the isolated RPC qualification must record the
actual20M call, capped estimate, exact full-padding call, caller, calldata/value,
chain/block/time, complete materialized code graph and exact baseline/delta
hashes. Trace the real empty-code sender into production Entry, not a test
harness. Capture failures as failures. Do not add independent gas components,
infer target-chain fees from chain31337 or relabel old launch-workload results.
The existing backend's advisory unsigned transaction omits gas/nonce; wallet
execution still needs a fresh review. Its `_gas` helper does not itself perform
the separate exact-padded-call experiment, so RPC evidence must state that
additional measurement explicitly.

## Source and consumer impact before accepting an optimization

- `ExactRoyaltyAllocation` is internal code. A layout-preserving algorithm change
  may retain ABI/storage/royalty4/canonical semantics, but this must be proved;
  changing representations or economic timing is a different accounting change.
- `ZZZRoyaltyRewards` creation bytes are embedded by `ZZZRoyaltyFactory` in two
  immutable authenticated code-data children. Changed creation code changes the
  payload hash, child part hashes and factory construction/transitive metadata.
  Current `factory_code_v3.py` and `config/factory-code-storage-v3.json` enforce
  source-owned payload3; current production_v14→production_v15 consumers inherit
  that identity. Preserve its historical meaning and prepare an explicit new
  reviewed payload/consumer selection when required. Do not accept arbitrary
  bytecode or rewrite old observed pins to fit a new build.
- The unsigned deployment/pre-seal planners use the trusted build's complete
  compiler input/output hashes, constructor graph and48 normal size gates.
  Rebind a new accepted stage only after current normal compilation, exact
  constructor lengths, immutable data parts and relevant current static review.
  Existing reports, deployed profiles and runtime pins stay source-scoped.
- Reassess exact-runtime configurations for API/website/keeper/observer and the
  factory-code verification path. Do not automatically enable signing, deploy,
  seal, admit assets, expand capacity or adopt a provider/budget.
- ABI/function-reference regeneration is needed only for actual ABI changes;
  source/runtime identity and factory payload still change without a new ABI.
  Keep historical readers/codecs/journals unchanged. Track source-bracketed
  methods and overlapping baseline/final stages without inflating test counts.

## Remaining limits

The finite cases above are not all possible token code, market paths or maximum
64-currency capacity. An arbitrary malicious token can remain unreadable or
untransferable permanently; no gas optimization can guarantee delivery of a
token whose own transfer semantics fail. These controlled calls do not qualify
independent feeds/routes, Robinhood provider/block admission/complete fees,
launch authorities, real contract wallets, OpenSea/VRF/content or operations.
Any state still above20M/full margin remains explicitly unqualified; disclose
the real admission consequence rather than weakening safeguards or hiding it.
