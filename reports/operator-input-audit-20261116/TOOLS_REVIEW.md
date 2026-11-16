# Unsigned operator tools: source and input-validity review

This is the tool portion of the operator-function audit, starting from
`72e519797659158eb48cfe5da582fb8c88b90bfa`. It is not a live deployment,
contract-wallet, market/provider, gas-profile or production acceptance report.
Contract authorization and inclusion-time safeguards remain authoritative.

## Confirmed corrections

### TOOL-01 — reported manual gas was neither called nor frozen

**Classification:** medium operational verification/envelope defect; no
demonstrated unauthorized movement or on-chain accounting defect.

`zzz_ops/manual_lp_review.py:simulation` previously called each selected B/C/D
operation at the configured cap, obtained an estimate, and reported 25% padded
gas. It did not call at that reported limit. The returned transaction omitted
`gas`; the second anchor could report a different padded estimate. The existing
source-bound local rehearsal performed its own exact-gas call, so its historical
receipts retain their original scope; they did not supply the missing check in
the production preparer. See [baseline reproduction](tool-baseline.json): two
1,000,000-gas calls, a reported 125,000-gas result, no transaction gas field.

The preparer now probes at the unchanged cap, estimates, then calls at the
exact initial 25%-padded gas. That gas is frozen in `transaction.gas` and
rechecked at the later canonical anchor. A higher final estimate must still
fit the original envelope with 25% headroom; otherwise preparation refuses
with `frozen_gas_insufficient`. A lower estimate does not reduce the frozen
envelope. Final funding and fee ceilings use the frozen gas, not the smaller
new minimum. Caller calldata, floors, expiry, checks and roles do not change.

Fresh output adds `transaction_gas` and `gas_strategy` to the simulation/network
gas records. `padded_gas` remains the observed per-anchor minimum; it is not
the submission gas when that estimate falls. Schema1 Active and explicit
schema2 Parked selections retain their existing input formats. Old artifacts
are not rewritten or retroactively declared exact-envelope reviews.

The owned-chain rehearsal helper now selects explicit `transaction_gas` when
present, validates consistency with `transaction.gas`, and retains the explicit
historical `padded_gas` fallback. Its strict reference wrapper is rebound to the
exact changed helper bytes. Import/helper checks passed; no rehearsal is run.

### TOOL-02 — management dangling outputs caused unnecessary reads

**Classification:** low operational preservation/diagnostics defect.

`management_review.main` used `Path.exists()`, which misses dangling symlinks.
Exclusive hard-link publication already prevented overwriting them, but the
tool could read inputs and perform RPC work before discovering the occupied
output. It now uses `os.path.lexists()` before any input/RPC preparation and
reports `existing_output_preserved`. Existing artifact bytes remain protected.

## Operation and input review

These are source assessments, not a claim of fresh execution for every row.
Every live preparer remains unsigned, direct-empty-code-governance-only,
bounded, source/runtime-pinned and unapproved. Safe/contract/delegated-wallet
execution requires a separate outer envelope; refusal is a tool boundary,
not removal of on-chain governance rights.

| Entry point/action | Exact operator input and authoritative reads | Moving-state/failure boundary |
| --- | --- | --- |
| Offline `Catalog.prepare/check` | Current contract-qualified ABI, exact nested argument shapes, canonical decimal integers, chain/controller/target/runtime/snapshot and evidence hashes | No RPC or authority proof. `reviewHash` binds the reviewed manifest; it does not make stale custody or unsafe floors valid. Source/catalog changes refuse. |
| Manual B: guarded same-main | Exact bucket, existing main ticks, checks14, no explicit swap, positive added-main-L floor and original deadline. Reads current main/residual geometry, physical fingerprints, custody hash, policy, sources and automatic venues | External swaps change current price/composition, not existing bounds. Healthy price rounds may change; custody/control changes or inactive main reject. New frozen exact-gas review applies. |
| Manual C: explicit same-main | Same fixed bounds; caller chooses mask, optional exact swap and output floor; residual+attributed idle only | Main principal and unrelated compound are not an allowance. Forced financial bypass is explicit; authority/pair/custody/deadline remain. Main geometry is preserved; successful consolidation atomically completes modeOFF. |
| Manual D: Active replacement | New aligned ticks, selected mask, exact optional swap and new-position-L floor; current physical custody and both legs are captured | Full-source call proves post-harvest spendability. Pre-harvest amounts are not a fabricated ceiling. Trading before inclusion still faces original floors and custody checks. |
| Manual schema2 D: Parked | Explicit Parked status, same fixed pool, exact attributed idle/designated compound, zero live IDs, nonce/epoch/hash | Bits1/16 require Active LP and refuse; other bits stay explicitly selected. No automatic mask clearing, new pool or unpause. |
| `park` | Bucket and uint128 raw close floors; complete14-word request auto-read from pinned custody/portfolio/nonce/epoch | Paused Active before exit; preparation draining allowed by source. No USD/decimals/ordinary-operation dependency. Both legs become attributed idle; unpause does not reopen LP. |
| `resume` | Bucket, destination bytes32 pool ID and positive uint128 new-L floor | Unpaused Parked; valid admitted same pair, reservation, routes, prices, normal financial guards. Current strategy target/spot may move and are re-simulated. No ordinary keeper timing gate. |
| `close_residual` | Bucket and uint128 raw residual close floors; current physical custody/portfolio request auto-read | Paused Active/no preparation, residual required. Main and desired mode stay; principal becomes attributed idle, not automatically reinvested. |
| `collective_exit_begin` | Explicit irreversible confirmation; source graph, minted count, registered buckets and physical inventory | Paused idle exit phase. Off-chain artifact expiry only; actual function has no deadline. It authorizes terminal shutdown, not all later closure/distribution calls. |
| `close_bucket` | Bucket and uint256 raw total ETH/ZZZ returned-principal floors, original deadline | Closing phase; both legs/idle/designated compound inspected. Principal/rewards remain separate. Raw close does not require healthy USD or automatic swap routes. |
| `allocate_principal` | Canonical decimal maximum1–32; current settlement/cursor, mint ordinal IDs, shares and principal rows read | Allocating phase; included transaction uses cursor at inclusion. Tool refuses changed captured progress; no separately frozen start cursor or on-chain artifact expiry is invented. |
| `distribute_principal` | Explicit1–32 distinct full NFT IDs; ordinal identity, current owners, allocated/paid status, backing and payout gas | Ready phase. Success result is a count, not a paid prefix or fixed beneficiaries. Partial failures remain backed; actual receipt/ledger reconciliation is required. Uses configured batch gas, not cheap estimated prefix. |
| Offline deployment planner | Exact trusted build, constructor inputs/addresses, native dependency and size gates, module binding order | Missing inputs stay blocked. Addresses are assignments, not live code/authority proofs; no deployment or seal. |
| Conditional deployment sequence | Explicit direct-EOA sender and canonical nonce; exact fixed CREATE/binding sequence | Nonce capacity and closed graph are checked offline. Insertions, failure, delegation, replacement and live nonce/control state remain outside the prediction; no nonce adoption. |
| Offline pre-seal planner | Twelve fixed configuration families, trusted ABI/build, exact native dependency pins, source identities, orientation, route, VRF and SeaDrop artifacts | Null own/dependent values retain null calldata. Completeness never marks authority/state/market/provider/seal approval. No RPC, signing or adoption path. |

## Cross-cutting input findings retained

- Raw ETH is wei; fixed ZZZ uses its authenticated decimal descriptor; USD and
  liquidityL are different units. Positive minima, unsigned widths and signed
  ticks are parsed as canonical decimal strings rather than floats.
- Existing lower/upper ticks are geometry. `getSlot0` current tick/sqrt price
  and portfolio token quantities are mutable market observations.
- Main/residual LP IDs, bucket IDs, full PoPL NFT IDs and bytes32 pool IDs are
  distinct. Array duplicate, empty, width and count checks remain explicit.
- `reviewHash`, custody/portfolio hashes and policy fingerprints have different
  domains. Manifest provenance never substitutes for on-chain revalidation.
- Initial reads use a confirmed canonical hash; the later tip is explicitly
  unconfirmed. Both exact calls preserve calldata, original expiry and frozen
  gas. Later inclusion can still revert safely; no state is reserved.
- Management begin/allocation/distribution lack contract deadlines. Their
  artifact expiry is an operator review boundary, not an on-chain guarantee.
- No tool reads/adopts a pending journal or reserves a nonce. Operator/keeper
  signing reconciliation and contract-wallet envelopes remain independent work.

## Verification scope

Ten new targeted methods passed: exact-gas verification, frozen gas under lower
and higher estimates, full-envelope fee calculation, final return shape,
block capacity, Parked mask preservation, dangling output preservation,
rehearsal historical compatibility and strict wrapper pin import. Fourteen
adapted methods passed for exact B/C/D ABI/floors, canonical read anchors,
physical/control changes, healthy market motion, guard failures, funding/
wallet boundaries, expiry, Parked execution controls and diagnostics.

The first new-test stage exposed three fixture-timing mistakes: its callback
changed gas before the first estimate returned. Those test hooks were moved
after the first exact call; the production correction was not loosened. One
later selected method name did not exist; twelve actual methods passed in that
stage, then only the two intended Parked methods were selected and passed.
Do not count the loader error as a test or sum repeated stages.

No unchanged suite, compiler, static analyzer, browser suite, public RPC,
existing chain, service or actual transaction was run. Existing Solidity,
permissions, defaults, safeguards, NFT rights, journals and environment remain.

Actual provider honesty/complete fees, market feasibility, maximum-state
operation, contract-wallet execution, real operating acceptance and independent
audit remain open. Injected wire success is not EVM/gas qualification.
