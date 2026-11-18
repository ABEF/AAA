# Royalty activation: source-backed optimization limits

Baseline: `23be8c9b01211b0732b2bcb64c227f0e05151e0a`. This is source and
arithmetic analysis, not a new EVM gas measurement or a claim that the full
activation fits its reviewed20M envelope. No production source is edited by this
analysis and no unchanged test is rerun.

Subsequent scope expansion investigates the explicitly identified representation
redesign as an isolated experiment. See [the complementary allocation proof and
measurements](complement/PROOF.md). Its meaningful gas savings do not erase the
initial size-gate failure or establish production compatibility by themselves.

## Actual work

`ZZZRoyaltyRewards.activate` finalizes the official opening cutoff, authenticates
the NFT, and synchronizes native ETH plus every admitted ERC20 before assigning
the new activation ordinal and permanent rarity tickets. Each ERC20's complete
`_sync` runs in a separate self-call with the existing governed1M allowance.
Successful currencies enroll the new NFT; a reverted/OOG currency retains its
previous cohort. Recovering that currency distributes previously unseen receipts
to that previous cohort before enrolling waiting activations. Native ETH cannot
be deferred through an ERC20 balance-read fault.

`_sync` performs actual balance/backing checks, opening-pool or ordinary receipt
allocation, accounted/liability writes and eligible-cohort recovery. The1M budget
covers all of those steps, not merely `balanceOf`. An expensive healthy tree may
therefore consume much of that allowance. The bound must not be silently reduced
or bypassed to make a launch measurement look smaller.

`_distribute` chooses the applicable unit1/2/3 ticket book and passes captured
eligible weight and rotation cursor into `ExactRoyaltyAllocation.credit`.
The allocator represents outstanding whole units with positive dyadic range
tags. Exact captured prefixes prevent a future activation from receiving past
royalties. Claims drain those tags along one ticket path; paid units do not
accumulate in a lifetime index. Canonical export flattens the exact ticket rights.

## Why the existing demanding component is expensive

The previous controlled rotated cases intentionally drain earlier credit, then
credit `2×weight−2` units with cursor513 into cold books. This requires a quotient
prefix plus two remainder intervals; it is not an unnecessary double conversion
or duplicated oracle read.

| Eligible weight | Intervals and deltas | Tag updates | Distinct storage tags |
| --- | --- | --- | --- |
|1023|1→1023:+1;514→1023:+1;1→511:+1|35|27|
|1499|1→1499:+1;514→1499:+1;1→511:+1|33|26|

These counts follow the current inclusive cover algorithm directly. A cold
zero-to-nonzero tag requires real storage work; repeated updates to an already
dirty tag are much cheaper. Simply expressing the same positive allocation as
three disjoint constant-value intervals keeps the same number of distinct tags.
It can remove some cheap repeated writes but does not remove the dominant cold
storage work. The earlier11.8M/11.46M component measurements must retain their
own source/fixture scope; they cannot be added to a separate LP measurement to
assert a complete current transaction cost.

## Rejected shortcuts

- Crediting a single global tag without settling future entrants would allocate
  old receipts to their new tickets. A fractional global index also reintroduces
  the indivisible-unit issue that the exact-unit engine was built to solve.
- Skipping an admitted healthy currency or enrolling the entrant before its
  old receipts are settled changes entitlement timing and is outside this work.
- Lowering the1M allowance changes the admitted fault/healthy-read boundary.
  Sixteen deliberately gas-burning reads can each consume that allowance before
  failing. Their aggregate cost cannot be eliminated generically while preserving
  exactly those token semantics and execution limits.
- Signed/modular difference tags, a new lifetime index or a different lazy tree
  would be an accounting representation redesign. They require their own
  overflow, claim, canonical and source-profile review; they are not a safe small
  optimization justified by this measurement alone.

Caching the immutable-for-this-call asset list/length, reusing the36-byte call
buffer, or suppressing intermediate duplicate cohort writes may save modest gas.
The last option must preserve recovery events and every old-cohort allocation.
None is evidence of solving a multi-million-gas deficit, so no cosmetic Solidity
change is shipped without a measured whole-flow benefit.

## Existing operational route

Permissionless `sync(asset)` can materialize healthy pending receipts separately
before activation. It preserves exact old-cohort rights; the later activation
still checks for receipts that arrived afterward. Calling individual healthy
currencies avoids `syncAll` reverting due to one broken currency. This is an
existing operation, not permission to skip checks in activation, guaranteed
liveness under continuous new receipts, or a solution for sixteen permanently
gas-burning currencies. Full naturally cold, nearly1000-NFT activation evidence
must determine what fits20M with the complete required headroom.
