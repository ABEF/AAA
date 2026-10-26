# Rights, random draw and reporting partition

This is static adversarial review of ten assigned concrete contracts and their
transitive helpers at baseline`c3289a8`, not a new execution campaign, independent
audit or universal security guarantee. [Function matrix](rights-review.json) and
[reproducible matrix builder](build-rights-review.py).

The matrix covers249catalogue rows:235functions,10constructors and4receive hooks.
Every row has at least three relevant edge/adversarial family scenarios, source
locations, purpose/authority and an explicit static assessment. Scenario families
are shared where the implementation/property is shared; the number of rows or
cases is not a test count. Constant/mapping reads are deliberately distinguished
from existence-sensitive owner/claimable views, ordinal arrays, route lookups and
metadata rendering. Reviewed source/helper hashes match the prior closed AST.
No unchanged test was rerun and no production source was changed by this partition.

No new reproducible theft, double-claim or rights-dilution defect was found here.
The review traces ordered one-time request fulfillment and quota consumption,
ERC721 callback/approval semantics, current-owner payout, exact liability/fraction
updates, deferred royalty cohorts, fixed-ledger conversion and canonical cutoff/
import/backing/retirement interactions. The matrix explicitly retains provider,
governance, asset, gas and escrow liveness limits rather than treating them as
proven safe.

## Composition detail: claim previews and contract owners

An exact pre-read`claimable`/simulated payout equality check is conditional.
With an inert EOA owner and unchanged same-block state, both LP checkpoints and
royalty pending/cohort preview use the same arithmetic as their eventual claims.
But a contract owner can legitimately return ETH to the royalty receiver during its
payout callback, or claim another ledger before a later router entry. The later
entry may therefore return more, less or zero compared with the initial preview.
Router reentrancy and per-entry current-owner checks still apply; a callback
transfer of a later NFT correctly reverts the whole batch.

Do not harden observation integrity by silently forbidding those supported owner
callbacks. A stronger exact-output policy would need an explicit callback-free
scope or separately reviewed semantics. Existing
[callback-refund fixture](../../test/ClaimRouter.t.sol) already documents that a
new recipient refund remains pending and backed; it was not rerun as new evidence.

## Backend read/history addendum

[File-pinned addendum](backend-rights-review.json) reviews the production projection,
raw SQLite history, exact indexed earnings, current-price valuation, wallet chunks,
predecessor lineage, royalty eligibility/conversion reporting and indexer log/reorg
composition. No further reproducible defect was found in that read-only pass.

- Unknown/unreadable positive values remain unavailable; a genuine zero amount
  can still be worth zero without a price. Source symbols never authorize inputs
  or justify adding raw amounts of different assets.
- Fee allocation, claims, conversion denomination and returned/imported backing
  remain separate; reserved compound/buyback money is excluded from NFT income.
- Lifetime earnings follow the NFT across owners, while wallet summaries mean
  current holdings at one confirmed block, not personal wallet tenure. Chunks
  cannot safely be summed across inventory hashes or blocks.
- Replay checks source emitters, creation/ancestry/cutoff anchors, exact funded
  credit/dust pairs, indices, shares, membership and deferred royalty cohorts.
  These checks are not a cryptographic proof that no authentic log was omitted.
- A failed optional royalty token may make complete historical earnings
  unavailable. The currency-isolated NFT balance view can still present healthy
  ETH separately. This is an explicit availability limit, not permission to
  invent zero history or clear another token's liability.

## Primary references consulted

Installed dependency code and pinned candidate source determine the actual
implementation. The primary standards/service references clarify the requirements:

- [ERC721](https://eips.ethereum.org/EIPS/eip-721): existence, approvals and receiver
  semantics; approval to transfer does not itself authorize this protocol's claims.
- [ERC2981](https://eips.ethereum.org/EIPS/eip-2981): requested royalties are voluntary
  marketplace payments in the sale currency, not automatic collection revenue.
- [VRF security](https://docs.chain.link/vrf/v2-5/security): request identity,
  confirmations, no cancellation/reroll, bounded callbacks and subscription funding.
  This reference does not establish Robinhood support or a qualified live provider.

Existing release blockers and accepted risks remain: real VRF/feed/route/OpenSea
qualification, maximum-state gas/operations, immediate governance and trusted
custody, unsupported/broken currencies, lost/incompatible NFT owners, and independent
audit/remediation. Preserve the existing configuration, deployed test state and
economic rules; no service, website, signer or public transaction was changed.
