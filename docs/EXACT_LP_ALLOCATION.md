# Exact-unit LP rewards: accounting7 integration

The internal [Solidity engine](../src/libraries/ExactLPAllocation.sol) is wired
into fresh [accounting7](POSITION_V7.md) Rewards, claims, same-NFT conversion and
lossless canonicalV9. Current-owner rights, fixed80/10/5/5 and separate original-
currency rarity royalties are preserved. Historical6/V8 indices and checkpoints
remain explicit; existing runtimes/journals are never reinterpreted or upgraded.
See [integration evidence](../reports/exact-lp-integration-20261106/REVIEW.md).

## What the engine does

- One tree has1,024leaf slots, of which immutable NFT mint ordinals1..1,000are
  valid. Random ERC721 IDs are not leaf indices. Never derive a slot by modulo.
- Leaf weights are exact uint256 shares. A harvest adds whole units to a root
  in constant tree work; it does not write1,000NFT balances.
- There are exactly two logical books: ETH and fixed ZZZ. Both old pending paths
  settle before a weight changes; a caller cannot omit the second currency.
- Claims and previews follow at most ten levels. A no-op weight change preserves
  all pending units and phase; reducing a generic tree weight to zero does not
  erase its previously assigned whole claims.
- Outstanding money is bounded by uint256, without a lifetime receipt counter
  that would eventually overflow after funds have already been paid.

The individual80%ledger uses one tree per logical bucket, not one per
physical main/residual. The10%collective ledger uses global equal activated
weights, separately from LP size and rarity. Compound/buyback reserves and royalty
tickets do not become tree weights. A royalty ticket shortcut using enormous
raw LP share intervals would be unsuitable.

## Rounding phase: improvement over the initial design

The earlier [design](../reports/harvesting-audit-20261106/EXACT_LP_DESIGN.md)
proposed resetting split carry on genuine weight changes. Repeated growth
between tiny receipts can repeatedly disadvantage the other branch. The engine
instead preserves a high/low, bounded fairness phase; it is not owed money:

```text
Q = 2^128
phase = high/Q + low/(Q*subtreeWeight)
0 <= high < Q; 0 <= low < subtreeWeight when weight > 0
```

Each split conserves whole units exactly: left+right=input. Full-precision
`mulDiv`/`mulmod` and safe carry folds avoid overflowing intermediate products
or sums. At fixed weights, batching and materialization order preserve the exact
rational split behavior. Before a genuine weight change, old whole money is
settled using old weights. The high phase remains; only the low remainder is
rebased with full precision. Empty transitions also preserve high, with low0.

Rebasing loses less than2^-128of one phase unit per changed node. That is a
phase-error bound, **not a cash-loss or payout-distance bound**: arbitrarily close
to a rounding boundary, a tiny phase difference can delay an indivisible unit.
Whole money remains assigned and conserved. Tree placement/hierarchical rounding
also differs from flat largest-remainder allocation; no optimal fairness,
manipulation immunity or fixed lifetime error is promised.

## Internal developer interface

These are internal functions compiled into Rewards, not explorer/operator
write targets. The allocator itself is internal code. Its fixed canonical codec is a separate constructor-created companion, without ordinary payout or arbitrary execution authority.

| Function | Inputs | Output / effect |
| --- | --- | --- |
| `setWeight` | Tree storage, ordinal1..1000, new uint256weight | Settle BOTH old books; update leaf/ancestors; return new total. |
| `credit` | Tree storage, ETH/ZZZ enum, whole amount | Add root pending/outstanding; positive amount rejects an empty cohort. Zero is a no-op. |
| `claimable` | Tree storage, asset enum, ordinal | Read exact whole claim without writes. |
| `take` | Tree storage, asset enum, ordinal | Remove and return whole claim; it does not pay a token/recipient. |
| `totalWeight`, `weightOf`, `outstanding` | Relevant tree/book/ordinal | Read typed accounting totals. |
| `split` | Whole amount, left/total weights, uint128high, low | Pure full-precision child amounts and next phase. |

The library does not authenticate owners, actual token receipts, mint ordinals,
bucket count, canonical lifecycle or the source of a weight update. It makes no
external calls and transfers nothing. The host must enforce all those boundaries.
Generic weight reduction in this primitive does not authorize normal PoPL
principal withdrawal or deactivation.

## Host and canonical integration

Vault writes actual new shares/totals, then calls its typed `syncShares` hook.
The engine settles both old asset paths using stored OLD weights before installing
the new value. NFT ordinal/bucket identity and exact aggregate totals are checked.
Membership similarly writes eligibility/count before one-time `syncMembership`;
top-ups never create another collective share. All changes roll back with a failed
contribution. Neither physical residual liquidity nor rarity becomes an LP weight.

`claimableComponents` reports whole individual/collective rights plus direct
credits. Claims take only the current owner's NFT rights; a failed payment rolls
back every debit. LP conversion takes exact historical ZZZ components and credits
ETH only to the SAME NFT/components, without another cohort allocation or income.
Principal, compound, buyback and royalty backing remain separate.

Rewards owns funds/books. Its immutable constructor-created RewardsCanonical
companion handles V9 capture/import/backing. The parent accepts only three closed
typed record domains from that child; there is no delegatecall, arbitrary storage
writer, ordinary operator recipient or new custody-exit address. All weights seed
before raw pending/high/low nodes. Exact per-book outstanding, direct liabilities,
source identities and prefund-excluding backing reconcile before activation.
Source books remain unchanged for a fully funded abort. See [record layout](POSITION_V7.md).

### Consumers and remaining qualification

Original profile7/schema16/source9 consumers use explicit synchronization events
and exact-phase replay. Fresh mint2 adds schema17/canonicalV10 with explicit
backend flag2 read/claim/lineage support; default1 remains V9. Conversion, claims
and import are not new income. Old checkpoint1 is profile6-only; profile7 has
complete admitted raw history or explicit reviewed checkpoint2. Actual lifetime
workload/archive/restore qualification remains open. Do not relabel old artifacts.

Normal real-host size gates and scoped EVM/producer-consumer evidence are recorded
in the [integration verification](../reports/exact-lp-integration-20261106/VERIFICATION.md).
Earlier [engine measurements](../reports/exact-lp-engine-20261106/VERIFICATION.md)
retain their own source scope. Count limits/harness gas are not target-chain
qualification. Fixed2023node records cost253 eight-row pages for any nonempty
collection, plus headers/NFT/other domains; sparse optimization is deferred.

Target gas/economics, long-lived checkpoint/storage/recovery, actual dependencies
and independent audit remain open. No deployment, sealing, website/service change,
old-chain reset or signing capability change accompanies source publication.
