# Exact-unit LP allocator: implemented engine, pending ledger integration

The internal [Solidity engine](../src/libraries/ExactLPAllocation.sol) implements
bounded whole-unit allocation for the approved LP reward upgrade. It is not yet
used by the current Rewards/Vault/canonical graph. Current accounting6 still
uses LP indices/fractions; royalty4's exact tickets are a separate completed
implementation. The [owning task](../TODO.md#task-lp-exact-unit-allocation) remains
open until the ledger, canonical and consumer integration is verified.

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

The future individual80%ledger needs one tree per logical bucket, not one per
physical main/residual. The10%collective ledger needs global equal activated
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

These are internal functions compiled into a future host, not explorer/operator
write targets. The current deployment has no new module, authority or setter.

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

## Next integration steps

1. Authenticate NFT.mintOrdinalOf, actual bucket shares and global membership.
   Settle old weights and synchronize new Vault shares/denominator atomically.
   The current pre-update checkpoint alone cannot install a changed tree weight.
   Evaluate moving/adapting the existing typed hook rather than adding redundant
   calls or a generic executor. Current normal runtime margins are107bytes for
   Vault and3,265for Rewards; the actual integrated replacement must fit after
   removing obsolete fraction code, not by retaining two active accounting
   algorithms or assuming the library shell measures inlined code.
2. Preserve funded current-owner claims and exact per-NFT conversion outputs.
   Conversion must credit the same component/owner right, never allocate by
   current cohort a second time.
3. Design explicit new accounting/LP-allocation/canonical/event/API/checkpoint
   identities. Current6/V8 and all existing runtimes/journals remain unchanged.
   Do not silently reinterpret old fractional rights as these whole books.
4. Rebuild/authenticate weights before restoring canonical pending/phase records;
   enrollment after restoring money would mutate imported allocation. Validate
   node/leaf bounds, outstanding sums and phase invariants in the new format.
5. Update earnings replay/reconciliation, claims, inventory/runtime pins and the
   keeper conversion consumer. Initial/growth, main/residual transitions and
   terminal return must retain the same logical rights.
6. Measure the integrated host at maximum state. Library-shell size, internal
   harness gas and the32-entry count limit do not qualify full activation,
   claim/conversion/canonical gas or the existing12Mwork envelope.

See the [implementation and review record](../reports/exact-lp-engine-20261106/REVIEW.md)
and [verification](../reports/exact-lp-engine-20261106/VERIFICATION.md).
No deployment, sealing, website/service change, old-chain reset or signing
capability change is implied by this source component.
