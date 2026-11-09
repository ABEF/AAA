# Typed unsigned manual LP preparation

Two read-only preparers cover explicit Migration operations for the current
accounting7/custody5 source. Both write a new unsigned review artifact. Neither
reads or updates a keeper journal, chooses floors/routes, loads a signer,
broadcasts, approves assets, extends an expiry, changes pause state, or changes a
guarded request into a forced request.

| Preparer | Scope |
| --- | --- |
| `scripts/prepare-operator-management.py` | Park, resume, raw residual close and each collective-exit step below. |
| `scripts/prepare-manual-lp.py` | Existing Active-state B/C/D consolidation/full emergency requests; unchanged. |

This is a source implementation. Actual matching deployment/configuration,
provider support, gas/fee semantics, wallet execution and operator rehearsal
remain qualification work. No existing service, site, signer or chain is changed.

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

All three adapters currently require an **Active** source bucket. Parked full
emergency recovery is explicitly unsupported by this tool, although the contract
has a separate supported state space. There is no automatic recentering or
fallback. B/C preserve the main and do not include designated compound funds;
D closes both legs and may include designated compound. Rewards and royalties
remain separate from operation principal.

Use the [complete B/C/D matrix](../reports/moving-market-flows-20261106/INPUT_MATRIX.md)
and the maintained [operator procedure](OPERATOR_MANUAL.md#same-main-residual-consolidation).

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

The existing **B/C/D** selection has exactly `schema`, `action`, `bucket`, `checks`, `lower`,
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
For D, observed physical/idle/already-designated compound is a lower bound that
excludes the operation's future harvest. It is not a preflight spending ceiling.
Both exact full simulations must authorize the unchanged explicit amount using
the source's real harvest/release/accounting; the tool forecasts no extra funds.

<a id="procedure-and-review-boundaries"></a>

## B/C/D procedure and review boundaries

1. Reconcile actual pending operations and conflicting signer/keeper work using
   the maintained recovery procedure. This tool neither examines that journal nor
   proves that no other pending transaction exists. Pause separately from the
   governance wallet before capturing manual inputs.
2. Select B, C or D explicitly and obtain the exact current main ticks, intended
   positive added/new-L floor, retained mask and any explicit swap input/floor.
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
