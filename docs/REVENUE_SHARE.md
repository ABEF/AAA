# Proposed creator-revenue share measurement

`zzz_ops/revenue_share.py` implements two deterministic proposed policies plus a
read-only collector for an actual local shared LP position. It does **not**
transfer funds, change the Pons creator payout address, authorize PoPL to debit
the creator, prove an agreed percentage, or create an NFT-holder claim before
PoPL receives and processes real funds. Creator agreement and production
measurement/source review remain open.

## Proposed baseline

Prefer **fee-weighted sampled active-liquidity share** when complete, verifiable
raw hook/creator-fee observations exist. It weights a busy trading interval more
than a quiet interval. Use **time-weighted active-liquidity share** as a simpler
alternative only if explicitly agreed with the creator; it gives each second
equal weight. Neither method is canonical protocol economics until approved.

For each confirmed end-of-block sample:

```text
active share = PoPL in-range LP liquidity / total current active pool liquidity
```

The numerator and denominator are the actual Uniswap liquidity units for the
same pool, not USD principal, total value locked, total supplied out-of-range
liquidity or the website's example 34%. If the PoPL range does not contain the
current tick, its active numerator is zero. With no active pool liquidity and
zero PoPL active liquidity, the proposed share is zero. A positive PoPL numerator
larger than the total pool numerator is rejected.

For time weighting over exact boundary snapshots covering `[start,end)`:

```text
time-weighted share = sum(sample active share × interval seconds) / total seconds
```

The left sample is held constant until the next sample. Every interval is
reported. Missing start/end boundaries, excessive sample gaps, unordered blocks,
overlapping/duplicate samples, wrong pool/chain and insufficient confirmations
are rejected rather than silently interpolated or renormalized around gaps.

For fee weighting, **separately for each raw fee asset**:

```text
fee-weighted share(asset) = sum(prior sample active share × raw fee observation)
                           / sum(raw fee observations in that asset)
```

For example, a quarter active share during 100 raw fee units and a three-quarter
share during 300 units produces `(25 + 225) / 400 = 62.5%`, compared with 50%
for equally long intervals under the time-weighted policy. Native ETH and ZZZ
amounts are never added or converted to assumed dollars. An asset without
positive fee observations has an **unavailable** fee-weighted share; the
calculator refuses to allocate its creator receipts using another asset's share.

Fee records must name their immutable prior snapshot `record_id`, actual
block/hash/time, transaction hash and log index, and an admitted raw asset. A
sample is an end-of-block state, so an event in that same block cannot use that
sample. An event in the next sample's block uses the previous sample: internal
intervals are `(left block,right block]`, while the full period excludes fee
timestamps at `end`. Duplicate events, conflicting block/time provenance,
transactions assigned to different blocks, out-of-window events and wrong
chain/pool/assets are rejected. The complete event inventory is canonically
hashed and all output fractions use exact rational arithmetic.

**These are sampled sharing policies, not actual Uniswap fee accounting.** A
single swap can cross ticks and change active liquidity several times, and
intra-block changes are hidden by end-of-block samples. Exact conventional v4 LP
fee attribution would need the appropriate fee-growth/inside-range accounting
and full transaction state/trace replay. Pons hook creator revenue is separate
from conventional LP fees and needs its own agreed attribution basis. Do not
present this calculator as proof that a 34% value share earns 34% of hook revenue.

## Actual payments and rounding

For an independently reconciled **creator receipt in one admitted asset**, the
calculator proposes:

```text
proposed PoPL amount = floor(actual creator receipt × measured share)
creator retained amount = actual creator receipt − proposed PoPL amount
```

It reports the exact fractional raw-unit remainder separately. That fraction is
already included in the creator's retained amount; do not add it again or turn
it into an unfunded PoPL liability. There is no automatic cross-window carry
policy. Consolidate creator receipts once per asset/window to avoid repeated
per-receipt floors. The input is the agreed post-deduction creator-revenue base,
not automatically gross pool volume, pool conventional fees or the entire hook
fee. How protocol deductions, refunds and payout timing define this base needs
creator approval.

The creator still sends the real agreed amount to PoPL's reviewed canonical
reward receiver. The receiver must support the payout asset, receive the actual
funds, and synchronize them before the NFT LP-reward ledger distributes its
80/10/5/5 allocations. Calculator output and a promised creator amount are not
funding, a transferable claim, or a source of retroactive rewards. No payout
contract, signing key or creator authority was added.

## Measurement data interface

`Snapshot` has these exact fields:

| Field | Meaning |
| --- | --- |
| `chain_id`, `pool_id` | Reviewed chain and actual v4 PoolId |
| `block_number`, `block_hash`, `timestamp` | Immutable block identity and chain timestamp |
| `observed_head` | Head observed when collecting; required depth is checked |
| `pool_active_liquidity` | Pool's current active uint128 liquidity |
| `popl_active_liquidity` | Vault-owned position's in-range uint128 liquidity |
| `source_id` | SHA-256 identity of reviewed collector configuration/source receipt |

Its `record_id` is SHA-256 of canonical JSON for these fields. The dataclass is
frozen and input is revalidated even if constructed directly. Preserve source
records and raw RPC receipts in append-only evidence storage. Hashes bind content;
they do **not** prove that an untrusted input producer queried the canonical
chain. The offline calculator labels this limitation in every report.

`FeeEvent` adds exact `chain_id`, `pool_id`, `block_number`, `block_hash`,
`timestamp`, `transaction_hash`, `log_index`, `asset`, `raw_amount` and
`sample_id`. A reviewed hook-event/trace indexer must produce these from complete
canonical evidence, including a raw receipt archive and admitted emitter/ABI
review. The offline calculator requires `events_complete: true` as an explicit
**operator attestation**, not a proof; it cannot detect a deliberately omitted
log. The Pons-specific complete fee-event parser, authenticity/completeness
checks and reconciliation to actual creator receipts remain open. Periodic
creator payout transfers alone do not locate when trading fees were generated
and must not be silently treated as per-swap fee events.

## CLI: deterministic offline calculation

```sh
python -m zzz_ops.revenue_share calculate --input measurement-window.json --output proposed-share.json
python -m unittest tests_python.test_revenue_share -v
```

The input is strict schema 1 with these common keys:

```text
schema: 1
policy: "time_weighted_active" or "fee_weighted_sampled_active"
chain_id, pool_id, start, end, max_gap_seconds, min_confirmations
snapshots: complete ordered Snapshot records including exact start and end
admitted_fee_assets: reviewed distinct address list (address zero denotes ETH)
creator_receipts: [{"asset": address, "raw_amount": integer-or-decimal-string}]
```

Fee weighting additionally requires `fee_events` and `events_complete: true`.
Unknown fields/policies, invalid integers, floats, booleans, oversized uints and
unadmitted receipt assets are rejected. All reported amounts/fractions are exact
decimal strings; no float enters accounting. Reports bind the complete input
dataset and output with SHA-256 identities and always say
`policy_status: proposal_not_creator_approved` and `moves_funds: false`.

## CLI: read an actual confirmed shared position

```sh
python -m zzz_ops.revenue_share snapshot --config collector.json --block 123456 --output snapshot-123456.json
```

The collector JSON has only `rpc_urls` and `measurement`. RPC URLs are private
operator configuration, never part of a public report. `measurement` has:

```text
chain_id, pool_id, bucket_id, min_confirmations
contracts:
  state_view:       {address, code_hash}
  position_manager: {address, code_hash}
  pool_manager:     {address, code_hash}
  vault:           {address, code_hash}
```

`code_hash` is Ethereum Keccak-256 of independently verified **deployed runtime
bytecode**, not initcode/SHA-256. Addresses must be distinct and nonzero. The
collector checks chain/depth, runtime pins, StateView/PositionManager core
bindings, canonical pool-to-bucket mapping, actual `Vault.group` custody, actual
PosM owner, full physical PoolKey hash, packed tick bounds and current slot0.
It reads official v4 `StateView.getLiquidity(bytes32)` plus
`getSlot0(bytes32)` and `PositionManager.getPositionLiquidity(uint256)` plus
`getPoolAndPositionInfo(uint256)`. All state reads use EIP-1898 canonical block
hashes; providers without support fail closed. The block identity is checked
again after collection. The current approved source uses the same packed
tick decoding as `ZZZLiquidityManager._checkPosition`.

This collector handles **one existing local home-chain shared position**. It
refuses absent, imported, remote or in-flight custody rather than guessing a
remote value. Idle reserves and out-of-range position liquidity are not active
liquidity. It does not infer multi-pool shares, historical movement between
chains, payout currency conversions or fee amounts. Historical selected blocks
are allowed deliberately for window reconstruction; the configured maximum gap
and exact period boundaries control the calculator. An old historical sample
is not represented as a live current balance.

Remaining release work: creator approval of policy/base/period/sampling/rounding;
independent raw fee-source and complete log/trace parser review; two-provider
canonicality and archive/finality/reorg operating policy; receipt reconciliation;
real target-pool and staged operating rehearsals; and external review. The
offline mock-RPC tests establish implementation behavior, not these external
facts or production readiness.
