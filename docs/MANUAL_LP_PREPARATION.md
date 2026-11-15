# Typed unsigned manual LP preparation

Two read-only preparers cover explicit Migration operations for the current
accounting7/custody5 source. Both write a new unsigned review artifact. Neither
reads or updates a keeper journal, chooses floors/routes, loads a signer,
broadcasts, approves assets, extends an expiry, changes pause state, or changes a
guarded request into a forced request.

| Preparer | Scope |
| --- | --- |
| `scripts/prepare-operator-management.py` | Park, resume, raw residual close and each collective-exit step below. |
| `scripts/prepare-manual-lp.py` | Schema1 Active B/C/D, plus explicit schema2 Parked emergency D below. |

The [current manual reference-swap fix](../reports/manual-reference-swap-fix-20261115/REVIEW.md)
allows a reviewed external price reference to execute the exact supplied manual
swap while retaining selected financial guards. The
[earlier controlled rehearsal](../reports/manual-recovery-rehearsal-20261115/REVIEW.md)
at `da24f65` covers mint2/V10 C/D, Parked recovery and park-to-recovery through the
production CLIs; its former reference-swap rejection and gas remain historical.
Matching production deployments, target providers/fees, contract-wallet execution
and operating acceptance remain unqualified. No existing service, site, signer
or chain is changed.

This adapter supports **direct empty-code governance EOAs only**. It checks the
governance address's code at both pinned snapshots. Contract wallets, including
Safe/multisig wallets, and delegated EOAs are explicitly refused with
`unsupported_contract_wallet_envelope`, before network-funding review. Their
outer transaction/gas payer is not the governance address's direct transaction.
The existing manual Explorer/Safe procedures and on-chain governance authority
remain available; this tool neither constructs their envelope nor guesses a payer.

## Custody and terminal management selections

The new management selection has exactly `schema`, `action`, `parameters`,
`expires_at`, `review_notes_sha256`, `evidence_sha256`. Schema is integer1; action
is one of the seven names below. ABI numbers are canonical decimal **strings**,
including NFT IDs. No unknown parameters, duplicate keys/IDs or floats are
accepted. Use the same exact read configuration and manual policy described
below; the five extra runtime pins and fee policy are required for both tools.

The `parameters` column lists **all** permitted keys. Values here are descriptions,
not executable JSON. Bucket IDs identify shared custody, not individual NFTs.

| Action | Exact parameters | State and effect |
| --- | --- | --- |
| `park` | `bucket`, `minimum0`, `minimum1` | Paused, Active, before terminal exit. Closes both legs into attributed Vault idle; preparation-time draining is permitted while canonical state remains operating. |
| `resume` | `bucket`, `destination_pool`, `minimumLiquidity` | Unpaused, Parked. Deploys into the same or another admitted native ETH/fixed-ZZZ pool under normal financial guards. Destination operations must be enabled; deposit admission is separate. |
| `close_residual` | `bucket`, `minimum0`, `minimum1` | Paused, Active, registered residual, no preparation notice. Closes only the residual into attributed idle; main, desired mode, shares and rebalance clock stay. |
| `collective_exit_begin` | `confirm_terminal_exit: true` | Paused, operating, no preparation notice. Explicitly confirms irreversible LP shutdown; does not close every bucket or pay holders in this call. |
| `close_bucket` | `bucket`, `minimumETH`, `minimumZZZ` | Paused, Closing. Closes one snapshotted Active/Parked bucket into holder-return backing. |
| `allocate_principal` | `maximum` | Allocating; either pause state. Processes1–32 mint ordinals from the on-chain cursor at inclusion; never choose a separate start cursor. |
| `distribute_principal` | `nft_ids` | Ready; either pause state. Exactly1–32 distinct explicit NFT IDs. Pays each actual current owner through isolated calls; caller supplies no recipient. |

`bucket`, `maximum` and every `nft_ids` element are positive uint256 strings;
`maximum<=32`. `destination_pool` is the complete lowercase bytes32 pool ID.
`minimumLiquidity` is positive uint128 **new position L**, not token amounts or
USD. `minimum0`/`minimum1` are uint128 raw ETH/ZZZ close-delta floors;
`minimumETH`/`minimumZZZ` are uint256 raw **total returned principal** floors,
including attributed idle and designated compound. Explicit0/0 close floors are
permitted by the current source and accept the actual returned mix; they are not
a default recommendation. The operator must review every floor. No solver chooses
or weakens it. Healthy market changes may alter quantities; simulation is the
check against those exact supplied floors.

For park/residual close, the tool fetches the complete14-word request from the
same pinned state: pool, main ID, shares, gross contribution, custody epoch,
parking nonce, ordered currencies and authenticated physical portfolio hash.
It generates the source-bound `reviewHash`; these hashes are not interchangeable.
Resume's actual function has no `reviewHash` or custody-hash argument; its review
hash remains provenance only. Raw close does not require USD feeds or ordinary
operations readiness. Resume deliberately retains normal prices, routes,
deployment/idle/loss guards, and has no keeper cooldown/buffer scheduling gate.

### Prepare one management action

The following is a complete **shape example**, not a usable review: its bucket,
floors, fixed timestamp and evidence hashes are illustrative. Replace them with
your original reviewed values; never copy these numbers into a real operation.

```json
{
  "schema": 1,
  "action": "park",
  "parameters": {
    "bucket": "7",
    "minimum0": "1000000000000000",
    "minimum1": "1000000000000000000"
  },
  "expires_at": "1794189600",
  "review_notes_sha256": "1111111111111111111111111111111111111111111111111111111111111111",
  "evidence_sha256": [
    "2222222222222222222222222222222222222222222222222222222222222222"
  ]
}
```

```text
python scripts/prepare-operator-management.py --read-config READ_CONFIG.json --policy MANUAL_POLICY.json --selection SELECTED_ACTION.json --output NEW_REVIEW.json
```

1. Reconcile existing pending work separately. Select one exact action and meet
   its pause/lifecycle requirements. The tool never pauses/unpauses or submits it.
2. Choose the original absolute `expires_at` within600seconds of the confirmed
   snapshot, plus your explicit floors/IDs/counts and1–15 distinct nonzero evidence
   SHA256 values. Notes likewise require a nonzero SHA256. The returned expiry can
   be earlier under the original snapshot-age limit (at most120seconds).
3. Inspect the exact Migration target, chain/governance, ABI arguments, source /
   runtime/configuration hashes, untouched original selection and false readiness
   flags. It captures controls first at configured confirmation depth, then at a
   later canonical tip explicitly labelled **not confirmed**. Each snapshot uses
   a bounded probe/estimate followed by exact-gas verification. The two exact
   calls use identical calldata and frozen transaction gas; controls or custody
   changes require a new review, while healthy price/amount/target updates are
   re-evaluated without recentering, weakening floors or extending expiry.
4. The shared manual fee policy requires full25% estimate headroom, its original
   gas-price/network-fee ceilings, observed direct-governance funding and both
   block gas limits. This is separate from unsigned activation policy2's20% rule.
   Distribution uses the explicitly configured block-bounded gas budget, not an
   artificially small estimator result: the contract can return after a low-gas
   early break. No budget or batch increases automatically.
5. `expires_at` is an on-chain deadline **only** for `park`, `resume`,
   `close_residual` and `close_bucket`. Begin/allocation/distribution have no
   contract deadline; their artifact expiry is an off-chain review boundary.
   Their cursor/current owner can change after the final review. Allocation uses
   the cursor and distribution pays the current owner **at inclusion**.
6. Distribution simulation reports a successful count, possibly partial. It does
   not prove which IDs succeeded and is not a paid-prefix guarantee. After any
   separately authorized wallet execution, inspect actual receipt events and
   `principalOf` before preparing remaining explicit IDs. No automatic queue,
   holder redirect, skipping decision, resend or journal adoption is performed.

Known local refusals expose a stable `reason` code and `stage`: for example pause
state, missing residual, incompatible bucket state, disabled/reserved destination,
changed controls, insufficient gas/funding or no simulated payout progress. An
opaque provider revert remains unavailable; the tool does not invent its cause.
No failed review produces a replacement transaction or force fallback. Output is
exclusive/atomic; preserve existing artifacts and inspect any durability failure.
`ready_for_submission` and `production_approved` stay false. These reviews do not
prove absent pending work, future inclusion, provider honesty or universal payout.

Parking/raw residual close leave principal **idle**, not automatically reinvested.
Resume restores parked LP only while unpaused; raw residual close keeps main
unchanged and desired residual mode unchanged. Use B/C consolidation to reinvest
that idle into the same main, or a separately reviewed full replacement. Collective
exit cannot reopen LP. After each actual confirmed step, fetch fresh state before
preparing the next; reviews are not a preauthorized dependent sequence. See the
[operator controls](OPERATOR_MANUAL.md#portfolio-management-controls),
[holder-return procedure](HOLDER_COLLECTIVE_EXIT.md) and
[current source verification](../reports/operator-management-20261109/REVIEW.md).

<a id="supported-selections"></a>

## Existing Active-state selections

| Action | Exact Migration entry | Required interpretation |
| --- | --- | --- |
| B | `consolidateResidual(request,false)` | Checks14, current main ticks and zero explicit swap fields. Minimum liquidity is **added main L**. Main must be active. |
| C | `consolidateResidual(request,true)` | Explicit checks0–31, current main ticks and reviewed explicit swap or no swap. Minimum is **added main L**. An inactive main can remain inactive. |
| D | `emergencyRebalance(request)` | Explicit checks0–31, explicitly selected replacement ticks and swap or no swap. Minimum is **new position L**. |

Schema1 requires an **Active** source bucket for all three actions. An old D
selection is never reinterpreted as Parked recovery. B/C preserve the main and
exclude designated compound; Active D closes both legs and may include designated
compound. There is no automatic recentering or fallback. Rewards, buyback reserves
and royalties remain separate from operation principal.

## Parked emergency recovery: explicit schema2

Use this only for an intentional paused-governance recovery into the bucket's
**current** native ETH/fixed-ZZZ pool. Guarded unpaused `resume` remains the normal
alternative, including movement to another admitted same-pair pool. Neither
preparer switches between these actions on failure.

For `scripts/prepare-manual-lp.py`, supply the same complete selection fields
listed below, but set **integer `schema: 2`**, **`action: "D"`** and add exactly
**`expected_position_status: "parked"`**. All ABI integers remain decimal strings.
B/C, missing status, Active state and unknown fields are refused under schema2.
No schema, mask, route, ticks, output floor or expiry is inferred.

| Input | Required choice |
| --- | --- |
| `bucket` | Actual registered Parked bucket with positive NFT shares. |
| `checks` | Explicit sum of retained bits2/4/8; see the table below. |
| `lower`, `upper` | Reviewed new main ticks, ordered and aligned to current pool tick spacing. |
| `swapPool`, `zeroForOne`, `amountIn`, `minimumOut` | Exact reviewed admitted fixed-pair swap, or explicit zero pool/amount/output and false direction for no swap. |
| `minimumLiquidity` | Positive raw **new main L**, not USD or token units. |
| `deadline` | Original absolute deadline, current and at most600seconds from the initial snapshot. |
| `review_notes_sha256`, `evidence_sha256` | Original nonzero note/evidence digests; same strict rules as schema1. |

| Retained bit | Parked effect |
| --- | --- |
| 1 | **Unsupported**: ordinary trigger/cooldown requires an Active main. Reject; never silently clear. |
| 2 | Retain independent/pool-price protection using starting bounds plus full live source and authenticated own-swap proofs. |
| 4 | Retain value, execution-quality and idle guards, including required USD sources even if bit2 is bypassed. |
| 8 | Retain current main/swap venue operations-enabled flags. |
| 16 | **Unsupported**: sampled confirmation requires an Active main. Reject; never silently clear. |

For example, explicitly selected `checks: "14"` retains2/4/8 and bypasses1/16;
this illustrates the mask, not a chosen operating setting. `checks: "0"` bypasses
all five optional categories. It can accept severe loss or an inactive new range.
The schema2 artifact lists retained/bypassed categories; a selected retained bit
is not a claim that its condition passed without both exact simulations.

Mandatory governance, sealed/paused/operating lifecycle, current admitted native
pair/core bindings, exact accounting and callbacks, explicit positive caller L
and swap-output floors, deadline and atomic rollback remain. Bit8 bypass does not
admit an unknown pool. Mask0 skips optional USD-price/source-health evaluation. Oracle runtime/bindings
and explicit execution-profile source revision remain authenticated, as does the
current on-chain pool spot needed to mint.
Broken tokens, core settlement or RPC can still prevent recovery.

The reader proves zero main/residual association and the exact nonzero-domain
empty portfolio fingerprints, pool reservation and complete bucket inventory.
Only attributed bucket idle plus already-designated compound may fund recovery;
neither existing rewards nor another bucket's funds may subsidize it. It does not
invent a physical LP or call Active-only geometry reads for position0. Both
snapshots bind shares, idle, compound, custody hash, nonce/epoch and governed
controls. Changes abort the artifact rather than updating the selected calldata.

Run the same B/C/D command below with a **new** output path. Inspect schema2's
source-state/bypass disclosure, exact current Migration target, frozen calldata,
original floors/expiry and both successful simulations. The first snapshot is at
configured confirmation depth; the later canonical tip is labelled unconfirmed.
Funding,25% gas headroom, original fee ceilings and block bounds remain unchanged.
The output stays unsigned with `ready_for_submission:false` and
`production_approved:false`; it contains no nonce, gas or signing fields in the
transaction. There is no automatic route, resend, signing or unpause.

After a separately authorized successful governance transaction, verify the
receipt, bucket Active state, new Vault-owned main/no residual, remaining
attributed funds and unchanged shares/reward reserves. **The protocol stays
paused**. Review restored prices/settings and reconcile pending work before
separate governance unpause. A revert leaves Parked state/funds unchanged except
for transaction gas. Never repeat an ambiguous submitted transaction as new work.

The earlier [source review](../reports/parked-recovery-preparation-20261115/REVIEW.md)
retains its injected-RPC scope. The [actual local rehearsal](../reports/manual-recovery-rehearsal-20261115/REVIEW.md)
at `da24f65` adds CLI, gas and receipt evidence for that baseline. The
[current reference-swap record](../reports/manual-reference-swap-fix-20261115/REVIEW.md)
separately owns the updated source's verification. Neither qualifies a target
provider, production fee budget or contract-wallet envelope.

Use the [complete B/C/D matrix](../reports/moving-market-flows-20261106/INPUT_MATRIX.md)
and the maintained [operator procedure](OPERATOR_MANUAL.md#same-main-residual-consolidation).

<a id="local-manual-recovery-rehearsal"></a>

## Current manual reference swaps and historical recovery rehearsal

Current priced manual C/D capture both ETH/ZZZ source bounds before the first
emergency fingerprint, harvest or unwind whenever bit2 or4 is retained. Manager
quotes the exact selected venue/direction/amount, verifies its exact output and
full quoted core state immediately after the swap and before settlement, then
validates live source freshness/agreement, controls and callbacks through LP
placement and the final emergency fingerprint. A favorable later reference
cannot replace the starting USD loss/output/idle vector. Public Oracle reads
remain live. See the [current source/verification record](../reports/manual-reference-swap-fix-20261115/REVIEW.md).

The following gas table belongs exclusively to the earlier `da24f65` source.
Use the current report for new-source gas; do not reuse this table to approve a
new runtime, budget or route.

The [15 November record](../reports/manual-recovery-rehearsal-20261115/REVIEW.md)
covers four explicit manual flows on newly owned Anvil chains. Each actual
production CLI uses its normal wall clock and unchanged 25-second review budget,
two genuine canonical anchors, frozen caller inputs and the same exact unsigned
calldata through local inclusion. No browser signer, public transaction, existing
Anvil, keeper journal or running configuration is used.

| Explicit flow | RPC estimate | Required 25% padded gas | Actual receipt gas |
| --- | ---: | ---: | ---: |
| Active C, checks14; residual into the existing main |10,233,104|12,791,380|9,388,004|
| Active D, checks14; replace both legs with one main |10,408,641|13,010,802|9,520,341|
| Parked D, checks14; retain financial/operations guards |8,822,193|11,027,742|8,181,893|
| Parked D, explicitly chosen checks0 outage scenario |3,007,714|3,759,643|2,626,114|

Every row passes at the full 24M cap and at exactly
`ceil(estimate × 1.25)`, below the actual local 32M block limit. Estimates,
trace gas and receipt gas are separate measurements. These values do not change
the 12M defaults, approve a spending ceiling or quote Robinhood's complete fees.
Checks0 is a separately selected emergency case with broken prices/disabled
operations; its lower gas is not a reason to remove safeguards from checks14.

The same owned-chain journey also prepares and includes `park` before Parked
D14. Its estimate is 1,616,054, padded gas 2,020,068 and receipt gas 1,367,950.
The report retains all six local receipts, including an earlier confirmed park
before a rehearsal-verifier failure. C's post-receipt verifier correction was
reconciled offline without resending its transaction.

### Verify the operation's actual result

| Operation | LP and principal result | Counters and clocks | Residual policy / pause |
| --- | --- | --- | --- |
| `park` | Both legs close into attributed Vault idle. Designated compound stays in Fees; rewards/buyback stay separate. | Parking nonce +1; custody epoch unchanged. Main centre, last rebalance and last compound remain unchanged. | Desired mode unchanged; stays paused. |
| C consolidation | Close the residual; increase the existing main by at least the selected added-L floor. Preserve its ID, ticks, centre and rebalance clock. Designated compound is not released. | Parking nonce +1 and custody epoch +1; last compound becomes inclusion time. | Completes consolidation with mode OFF and advances control revisions even if already OFF; stays paused. |
| Active or Parked D | Create one Vault-owned main in the selected ticks; close any old legs. Use only attributed principal and designated compound. | Last rebalance becomes inclusion time; last compound, parking nonce and custody epoch unchanged. | Desired mode is not disabled by D; stays paused. |

For a lasting single-position policy after D, disable residual mode through
governance **before preparing** the review. A new physical main alone does not
disable future residual creation. C completes that policy change itself.
An independent pending main-range change is not cancelled by consolidation.

Inspect the confirmed receipt and both asset ledgers: current owners/shares,
active versus dormant membership, exact LP closure, attributed idle, released
compound, funded reward liabilities, buyback/dust backing, cleared allowances
and inactive execution contexts. New fees collected during a real close may
increase reward/reserve books; reconcile their events rather than requiring
balances to be numerically unchanged. The measured critical receipts had no
new fees, so they preserved existing books exactly. Reconcile pending work and
choose any later unpause separately.

### Retained guards and the execution venue

At `da24f65`, actual checks14 probes rejected after an own swap changed its live
reference fingerprint; successful baseline flows used a non-reference venue.
That evidence remains unchanged. Current matching source instead authenticates
the selected own-swap transition, so a reviewed external reference may also be
the swap venue without dropping bit2 or4. It must still be distinct from the
same-core PoPL principal destination; LP removal/minting is not an authorized
reference-liquidity change.

Bit2-only opens the price scope even without value checkpoints. Bit4-only still
requires USD sources, captured gross/additional-loss floors and idle limits;
omitting bit8 does not accidentally restore operations-enabled through a quote.
Manager-only `quoteSwap` settles nothing and keeps structural pool admission;
actual Manager execution enforces retained bit8 and ordinary price paths still
require operations enabled. Masks0/8 add no Oracle-health dependency; retained
eligibility/confirmation bits1/16 keep their independent Active-main requirements.

Quotes and captured getters grant no execution authority. Live freshness,
sequencer/source agreement, policy/source revisions, exact custody, asset flows,
caller output/L floors and selected financial guards remain. Genuine spot/loss/
idle limits or source disagreement can still reject an operation. No route,
mask, floor or expiry changes automatically, and no MEV immunity is claimed.
Bypassing financial guards can permit near-total principal loss.

The capability numbers and existing request shapes stay the same; exact changed
source/runtime pins require explicitly matching reviewed consumers and fresh
reviews. Keep old artifacts, journals and runtime profiles under their original
identities. Do not relabel the old rejection/gas evidence as new-source results.

### Reproduce only on a new owned local chain

For the current source, use fresh authenticated exports and the matching
`test/ManualReferenceSwapQualification.t.sol` artifact with
`scripts/rehearse-manual-reference.py`. It admits only explicit checks14 C/D/
Parked D reference-swap cases, preserves exact selected inputs and uses the
pinned strictly owned-node launcher. The current report records the exact
methods/build/evidence; the wrapper accepts no RPC URL, key or existing-node target:

```text
python scripts/rehearse-manual-reference.py --exports FRESH_METHOD_EXPORTS --host-artifact MATCHING_HOST_ARTIFACT --anvil REVIEWED_LOCAL_ANVIL_EXE --python LOCAL_PYTHON_EXE --case parked-d14 --new-review-deadline-seconds 500 --output NEW_OWNED_REHEARSAL_OUTPUT
```

The placeholder paths must identify that fresh controlled export, matching host
artifact and reviewed local tools. The deadline option records a **new explicit
review intent before preparation**; it never edits a prepared artifact or pending
transaction. Stale feeds, expired inputs and failed simulations still refuse.
Do not reuse an old output path or resubmit an uncertain hash.

The producer starts a new PID-verified loopback chain 31337 with `--accounts 0`,
32M blocks and a minimal child environment. Its read-only recording proxy
rejects mutation requests. Only its owned node may be mined or impersonate the
disposable governance EOA for local receipts; it records exact state/receipts and
stops its own processes. Inspect `cleanup.json` and every pending intent. It
cannot target the existing local chain or deploy to a public network.

The earlier `scripts/rehearse-manual-recovery.py` rejection probe and original
host/gas captures belong to `da24f65`. The current wrapper reuses its pinned
isolation infrastructure with current exports; running the old acceptance
command against new behavior is not current-source qualification.

This controlled graph has two active NFTs, one dormant NFT and one active bucket,
with real Access, current
mint2/V10 and Uniswap v4, but fixture token/feeds/VRF/Permit2/depth and a derived
local-network admission seam. It does not qualify actual ZZZ markets, OpenSea,
provider latency, maximum workloads, target-chain fees or production operation.
The inner offline catalogue still carries its historical V9/LP-routing2 label;
actual current profile admission comes from explicit configuration, runtime
pins and unchanged Projection/Reader checks. Do not relabel old artifacts.

## Explicit inputs

Supply three reviewed JSON files. Duplicate keys, floats, unknown fields,
oversized documents and noncanonical ABI integers are rejected. Files are bounded
by the existing operator-review decoder; ABI integer fields below are canonical
decimal **strings**, never JSON floating-point numbers.

The read configuration is the existing strict frontend `Projection` schema2
configuration for accounting7/custody5, fee-intake1, protocol-policy1 and original
royalty reporting5. It supplies the actual deployment anchor, confirmation depth,
module/runtime pins, assets and RPC endpoints. Accepted snapshot age must be at
most120seconds. The tool does not fill missing integration data with demo data.

The manual policy has exactly these fields:

| Field | Meaning |
| --- | --- |
| `schema` | Integer1. |
| `projection_sha256` | Exact configuration identity used by the matching Projection. |
| `reference_sha256`, `source_snapshot_sha256` | Exact current hashes from `scripts/prepare-operator-review.py profile`. |
| `governance` | Expected actual governance address, authenticated against Access; this field grants no permission. |
| `extra_contracts` | Exactly `oracle`, `fees`, `activation_assets`, `custody_validation`, `contribution_pricing`; each contains only lowercase `address` and nonzero `code_hash`. These addresses must be distinct from the read configuration's module/helper addresses. |
| `fee_policy` | Exactly `max_gas_limit`, `max_gas_price_wei`, `max_network_fee_wei`, `estimate_includes_all_fees`, `review_hash`. The three limits are positive decimal strings; complete-fee review must explicitly be true and review hash nonzero. |

The explicit gas cap must be21,000–64,000,000. This is an engineering bound,
not approval for a particular operation, chain or provider. Both reviews clamp
it to their actual block gas limit and require the full25% estimate headroom,
original price/network-fee caps and observed governance funding. No cap rises
automatically. Contract/delegated-wallet execution envelopes are unsupported by
this adapter. This direct-EOA artifact prepares the Migration call itself.

The **schema1 B/C/D** selection has exactly `schema`, `action`, `bucket`, `checks`, `lower`,
`upper`, `swapPool`, `zeroForOne`, `amountIn`, `minimumOut`, `minimumLiquidity`,
`deadline`, `review_notes_sha256`, `evidence_sha256`. Schema is integer1; action
is B, C or D; direction is a boolean. Evidence contains1–15 distinct nonzero
SHA256 values without a `0x` prefix. Notes likewise use a nonzero SHA256 value.
Swap pool is a bytes32 ID, including explicit zero for no swap. Other ABI numbers
are decimal strings. Supply positive minimum L and the **original absolute
deadline**; the tool never computes a weaker replacement value.

Checks retain their contract meanings:1 raw trigger/cooldown,2 independent price
agreement,4 value/quality/idle,8 operations flags,16 sampled confirmation. Forced
checks0 does not read USD feeds, require operation-enabled flags or consult the
automatic route catalogue. Mandatory custody/control/runtime checks remain.
A positive explicit swap still needs its authenticated admitted fixed-pair venue
and captured operation principal. Bit4 requires USD data even without bit2.
For Active D, observed physical/idle/already-designated compound is a lower bound that
excludes the operation's future harvest. It is not a preflight spending ceiling.
Both exact full simulations must authorize the unchanged explicit amount using
the source's real harvest/release/accounting; the tool forecasts no extra funds.

## Manual LP failure diagnostics

The same `scripts/prepare-manual-lp.py` command now reports bounded JSON errors
on stderr and returns exit1. Schema1 Active B/C/D and explicit schema2 Parked D
share this diagnostic surface. Successful unsigned reviews, their commitments,
calldata, floors, deadlines and read order are preserved.

| Field | Operator meaning |
| --- | --- |
| `stage` | Where this invocation stopped; not a transaction status. |
| `reason` | Stable local cause, sanitized RPC/work category, or explicit unknown. |
| `message` | Fixed explanatory text; never raw provider/revert/input text. |
| `error_type` | A bounded known exception family, not an arbitrary class name. |
| `read_only`, `transaction_submitted` | Always true/false: this preparer cannot send a transaction. Other wallets/processes may have pending work. |
| `output_may_exist` | Existing output was preserved, or writing/reporting started and a complete artifact may exist. False means this invocation did not reach publication, not that another process cannot create the path. |
| `rpc_method`, `rpc_code` | Optional trusted RPC metadata only; recognized read method and signed32-bit code, otherwise null. |

| Stage | Work being checked |
| --- | --- |
| `input_validation` | CLI/files/selection; preserve any existing output path. |
| `preparation` | Honest fallback when preparation started but the precise exception stage cannot be attached/read. Never mislabel it as input validation. |
| `configuration_validation` | Manual policy, exact source/configuration and runtime role setup. |
| `initial_snapshot` | Confirmed authority/lifecycle, current custody, pool, position and selected protections. |
| `manifest_preparation` | Offline exact request and review commitment. |
| `initial_simulation` | First exact call, estimate, gas/fee limits and governance funding. |
| `final_snapshot` | Later canonical tip, original deadline and unchanged custody/controls. |
| `final_simulation` | Same exact calldata and original limits at that later tip. |
| `final_canonicality` | Both anchors, last head/expiry and unchanged local inputs. |
| `artifact_rendering` | Convert the completed review to bytes; writer has not started. |
| `artifact_publication` | Exclusive creation/durability or final CLI reporting. Inspect any complete file. |

Important known causes, with no new eligibility conditions:

| Cause | Response |
| --- | --- |
| `not_sealed`, `pause_required`, `preparation_active`, `canonical_not_operating`, `terminal_exit_started`, `exit_phase_not_idle` | Inspect the exact lifecycle; use only its authorized procedure. Terminal exit cannot be reopened. |
| `governance_changed`, `governance_permission_missing`, `unsupported_contract_wallet_envelope` | Reconcile the actual authority/envelope. A configured address grants no permission. |
| `position_state_mismatch`, `same_main_ticks_changed`, `invalid_tick_spacing`, `main_outside_range` | Review the selected action and current geometry. No recenter/force fallback is selected. |
| `no_residual_or_idle`, `no_parked_principal`, `swap_exceeds_principal` | Inspect attributed operation funds; never borrow other principal/reward reserves. Active D retains its future-harvest lower-bound rule. |
| `operations_disabled`, `swap_operations_disabled`, `invalid_swap_pool`, `fixed_asset_mismatch` | Review exact admitted current assets/venue and selected guard bits. No automatic venue admission or bypass. |
| `custody_hash_mismatch`, `custody_or_controls_changed`, `local_inputs_changed` | Preserve the previous artifact; capture a new review of the changed inputs. |
| `gas_headroom_exceeded`, `gas_price_exceeded`, `network_fee_budget_exceeded`, `insufficient_governance_gas` | Review the original25% padding, approved fee limits and payer funding. No budget increases automatically. |
| `invalid_original_deadline`, `review_expired`, `original_deadline_or_head_changed`, `final_anchor_changed` | Capture fresh canonical state and an explicitly reviewed original expiry. No extension or automatic retry. Composite head/deadline failures are not misreported as proven expiry alone. |
| `parked_active_trigger_or_confirmation_incompatible` | Parked cannot retain Active-only bits1/16. Choose the mask explicitly; it is never silently cleared. |
| `existing_output_preserved` | Preserve/inspect that path, including a dangling symlink; choose a genuinely new filename. |
| `artifact_publication_uncertain` | A complete review may already exist even if durability, cleanup or final stdout failed. Inspect it; do not overwrite, delete or assume a transaction was sent. |

Other typed local codes cover exact ABI/pool/inventory/fingerprint/source/config
comparisons. The [source's `LOCAL_CODES` catalogue](../zzz_ops/manual_lp_review.py)
is authoritative. A cause names the first comparison that failed, not every
latent problem and not proof that a dependency was compromised.

For example, a final snapshot can report `stage:"final_snapshot"`,
`reason:"custody_or_controls_changed"`, `output_may_exist:false`. This asks for a
fresh reviewed snapshot, not a weaker safeguard or repeat of an already-submitted
transaction. Neither preparer examines the pending journal or reserves a nonce.

Opaque RPC, decoder or simulation failures remain
`manual_preparation_unavailable_or_invalid` (or sanitized `rpc_*` when a typed
RPC error survives). Never interpret them as a proven slippage/oracle/buffer
inequality. Transport may have retried reads within existing limits; this feature
adds no retry or force path. `work_limit_*` identifies the bounded work category.
An unavailable endpoint may be wrapped generically and have no numeric RPC code.
Credentials, endpoints, paths, raw inputs and provider messages are not echoed.

New seven-action management reviews embed the updated manual-helper source hash,
so their **source commitments change**. Where a function takes a `reviewHash`,
new calldata carries that new hash too; targets, economic inputs and contract
behavior stay. Preserve saved artifacts with their original provenance; do not
rehash old reviews, pending records or journals. No contract/runtime/profile, earnings
checkpoint or keeper-health identity is automatically refreshed by this change.

[Source review and verification](../reports/manual-lp-diagnostics-20261115/REVIEW.md)
cover these local diagnostics; actual provider, gas and operating acceptance stay
separate. No signer, service restart, deployment or setting change is performed.

<a id="procedure-and-review-boundaries"></a>

## B/C/D procedure and review boundaries

1. Reconcile actual pending operations and conflicting signer/keeper work using
   the maintained recovery procedure. This tool neither examines that journal nor
   proves that no other pending transaction exists. Pause separately from the
   governance wallet before capturing manual inputs.
2. Select B, C or D explicitly and obtain current main ticks for B/C or reviewed
   replacement ticks for D, plus the positive added/new-L floor, retained mask
   and any explicit swap input/floor. Parked D requires the schema2 selection above.
   The adapter verifies supplied choices; it is not a sizing solver.
3. Run with a **new** output path:

   ```text
   python scripts/prepare-manual-lp.py --read-config READ_CONFIG.json --policy MANUAL_POLICY.json --selection SELECTED_ACTION.json --output NEW_REVIEW.json
   ```

   These filenames are unresolved operator inputs, not a qualified configuration.
   Publication is exclusive and atomic on supported filesystems. Existing output
   bytes are preserved; Unix directory synchronization follows file creation.
   A durability failure can leave a complete artifact to inspect; do not overwrite
   or assume submission occurred.
4. Inspect the actual chain/governance/Migration target, value0, exact calldata,
   original minimum and deadline, operation-specific custody hash and source-bound
   review hash. The unsigned transaction includes chainId but no nonce, gas or
   signing fields. `network_gas` is a separate observed envelope.
5. Inspect both snapshots and simulations. The first uses the configured
   confirmation depth. The second uses the later canonical tip, which is **not
   described as confirmed**. Healthy trading/composition or new feed rounds can
   change while IDs/ticks/L/shares and governed settings remain fixed. The second
   full call and estimate use the **same** calldata, floors, deadline and review
   hash. Changed custody, authorities, policy identities/revisions, recovery
   nonces or other controls refuse preparation. A failed latest retained guard
   refuses the artifact; there is no third simulation or fallback loop.
6. Revalidate through the actual operator wallet immediately before any separate
   signing decision. The last head/deadline check follows slow RPC work, but later
   market changes, reorgs, local I/O and inclusion remain outside an atomic
   off-chain guarantee. Preserve the existing pending hash/nonce on ambiguity.

`ready_for_submission` and `production_approved` remain false. The review hash
is reproducible provenance, not an on-chain permission or custody fingerprint.
Runtime pin matching does not independently prove reviewed build provenance,
proxy immutability or provider honesty. Ordinary on-chain inclusion guards remain
the backstop. Successful B/C/D operations stay paused; unpause and post-state
verification remain separate steps. The new management actions retain their own
pause/lifecycle requirements above; none changes pause state automatically.
