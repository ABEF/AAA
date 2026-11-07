# Accounting7: exact-unit LP rewards

This is the fresh source candidate, not an upgrade of deployed accounting6.
Production **NOT APPROVED**. Preserve old runtimes, wallets, journals and
[profile6](POSITION_V6.md) readers under their original identities.

## Identity and unchanged economics

| Boundary | Fresh identity |
| --- | --- |
| Vault share/accounting behavior | `ACCOUNTING_VERSION() = 7` |
| Rewards whole-unit allocation | `LP_ALLOCATION_VERSION() = 1` |
| Canonical peers | `ZZZ_CANONICAL_SAME_CHAIN_EXACT_LP_V9` |
| Production inventory / read consumer | schema16 / explicit profile7 |
| LP geometry, custody and maintenance | portfolio2, custody5, maintenance3, confirmation3, compound4 |
| Entry and pricing | direct Entry3, reviewedEntry2, pricing2, ProtocolPolicy1 |
| Royalties | royalty4, reporting5; original currencies and one-hour opening |

Position remains the native eight-word principal record. Its equal shape is not
runtime/accounting identity. LP custody is one logical share account per bucket,
with one main or an optional main/residual pair in the same native ETH/fixed-ZZZ
pool. Physical ranges never become separate NFT reward weights.

Fixed actual-receipt 80/10/5/5 is unchanged. The individual 80% uses bucket LP
shares; the collective 10% uses one share per activated NFT across buckets.
The 5% compound and 5% buyback reserves stay outside Rewards. Rarity affects
only separate royalties. Engine rounding phase is not money or a reserved
fractional claim. See [exact allocation](EXACT_LP_ALLOCATION.md).

## Atomic weight and claim flow

1. Activation/growth harvests and checkpoints incumbents before issuing new
   shares. The Vault writes the new share/total values, then calls
   `Rewards.syncShares(id)`. Rewards settles old whole rights with its stored
   old weights before installing the authenticated new weight.
2. Activation records eligibility/count, then Membership calls
   `Rewards.syncMembership(id)`. This adds exactly one collective share;
   growth never adds another. Both hooks reject unauthorized callers or
   inconsistent NFT ordinals/buckets/totals. Failure rolls back the contribution.
3. `claimableComponents(id,asset)` returns whole individual/collective amounts;
   `claimable(id,asset)` returns their sum. There are no fresh SCALE/index/
   fraction getters. `allocationTree(0)` describes the collective tree; a real
   bucket ID describes its individual tree. `directLiabilities(asset)` tracks
   separately allocated whole conversion/import credits.
4. Holder `claim` or the NFT's fixed claim router takes only that NFT's rights,
   debits liabilities and pays its current owner. Pausing LP operations does
   not pause ordinary funded claims. Failed payout reverts all debits.
5. LP conversion consumes exact existing ZZZ components and credits ETH to the
   same NFT/components. It never redistributes by today's shares/membership,
   touches principal/reserves or creates new income.

LP currency admission is native ETH plus one reviewed fixed ZZZ, bound before
sealing. Other marketplace royalty currencies are handled by RoyaltyRewards,
not additional LP trees. Earlier zero-participant LP collective funds remain
separately orphaned under the existing rule, not gifted to a later activation.

## Lossless canonical boundary

Rewards owns funds and books. Its immutable constructor-created
`Rewards.canonicalModule()` companion holds the bounded canonical codec and
authenticated transfer coordination. Its only parent writes are fixed typed
asset/seed/node records; there is no arbitrary storage, call or delegate executor.
Both parent and child addresses/runtimes must match the reviewed graph.

Import order is NFT, Vault, Membership, LP Rewards, royalties and fees. Every
LP weight is authenticated/seeded before any pending node or phase is restored.
The LP domain uses:

| Rows | Record |
| --- | --- |
| Header | Eight words: version, asset/bucket/NFT counts, four ordered bucket IDs. |
| Each LP currency | Ten words: identity, liability, orphan, backing, direct total, five tree totals. |
| Each minted NFT | Eight words: identity/bucket/shares/eligibility and two-currency direct components. |
| Each node1..2023 | 31 words: node ID plus ten pending/high/low entries for at most five trees × two currencies. |

Maximum LP rows are 3,026 for 1,000 NFTs and two assets. An empty collection
omits the node domain. Existing bounded handoff pages remain required; no
one-shot 1,000-NFT reconstruction or distribution is introduced. Exact gas must
be measured for the full host and selected page.

Raw pending amounts, high/low phases and direct rights are preserved. Flattening
claim previews while retaining old stored phase would be incorrect. Validation
checks exact outstanding totals, authenticated weights and funded backing;
prefunds are not migrated backing. Abort preserves source books and requires
returning transferred backing before reopening source operation. Old6/V8 peers
are rejected, rather than converting their fractions implicitly.

## Consumers and operating boundary

Matching consumers replay explicit share/membership synchronization events and
exact whole-unit allocation. Claims, conversions and import are not income.
Old checkpoint1 is incompatible with profile7; use explicit reviewed checkpoint2
or the admitted raw-history path. Keep operator approval, source/anchor pins and
the complete raw rolling-day suffix. Do not relabel an old checkpoint or journal
to bypass validation. [Procedure](EARNINGS_CHECKPOINTS.md).

The [operator manual](OPERATOR_MANUAL.md) owns exact caller/input/recovery steps.
The [integration report](../reports/exact-lp-integration-20261106/REVIEW.md) owns
verification and remaining limits. Source publication does not deploy, seal,
restart a service, change a website or authorize public signing.
