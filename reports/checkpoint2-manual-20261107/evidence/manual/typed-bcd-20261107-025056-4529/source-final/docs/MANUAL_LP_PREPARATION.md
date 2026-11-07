# Typed unsigned manual LP preparation

`scripts/prepare-manual-lp.py` prepares one explicitly selected, paused-governance
Migration call for the current accounting7/custody5 source. It performs read-only
RPC calls and writes a new review artifact. It never reads or updates a keeper
journal, chooses a floor or route, loads a signer, broadcasts, approves assets,
extends a deadline, or changes a guarded request into a forced request.

This is a source implementation. Actual matching deployment/configuration,
provider support, gas/fee semantics, wallet execution and operator rehearsal
remain qualification work. No existing service, site, signer or chain is changed.

## Supported selections

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
automatically. Contract-wallet execution envelopes and actual fee sponsorship
need separate qualification; this artifact prepares the Migration call itself.

The action selection has exactly `schema`, `action`, `bucket`, `checks`, `lower`,
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

## Procedure and review boundaries

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
the backstop. A successful manual operation stays paused; unpause and post-state
verification remain separate steps in the operator manual.
