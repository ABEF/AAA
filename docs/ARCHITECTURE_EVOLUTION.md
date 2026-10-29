# Architecture evolution and trust boundaries

This is the current change-boundary guide for the undeployed candidate, not a
second roadmap. [Architecture](ARCHITECTURE.md) explains interactions,
[components](COMPONENT_STATUS.md) maps source ownership, and the [sole Todo](../TODO.md)
tracks unfinished work. Production is NOT APPROVED.

The current profile is accounting4 / direct governance2 / fee-intake1 /
custody3 / `ZZZ_CANONICAL_SAME_CHAIN_HOLDER_EXIT_V5`. Native ETH and one fixed ZZZ are the only contribution
inputs. The current contracts contain no integrated bridge, creator-payment
inbox, remote reward intake, external-custodian exit or post-seal ZZZ replacement. Historical profiles
retain their own codecs and evidence; changing a configuration version does
not upgrade deployed storage, journals or ownership.

## What can actually evolve

| Change | Current boundary |
| --- | --- |
| Tune range, cooldown, confirmation or execution limits | Direct governance through bounded setters. Ordinary policy2 uses physical range exit or an operator width change, not the retired centre-movement trigger. Optional25%/50% keeper selection cannot coexist with enabled confirmation2 reference-exit protection; manual governed widths remain available. Physical replacement remains guarded maintenance. |
| Select another contribution pool | Admit the supported pool, preserve historical bucket identities and deliberately switch the one enabled contribution pool. Admission alone does not move liquidity or qualify routes. |
| Move LP to another local fee tier | `Migration.moveFunds` atomically redeploys the same actual ordered pair, preserving NFT shares and the captured maintenance floor. |
| Change ETH to WETH accounting or another pair | Not supported by this deployment's principal-pool admission or `moveFunds`. Separate reward-conversion routes do not expand LP admission. |
| Add another hookless static-fee local v4 pool | Supported only for native ETH/the same fixed ZZZ on the pinned Robinhood dependencies, before collective exit starts. |
| Add an arbitrary hook, new DEX algorithm or native token | Unsupported by configuration. Requires separately reviewed compatible code and an appropriate replacement plan. |
| Replace the ZZZ token contract | No setter or issuer-exchange call exists. Governance may return actual ETH/ZZZ to holders; any later token exchange/new deployment is separate, without automatic continuity. |
| Return LP principal to NFT holders | Governance starts irreversible collective retirement while paused. Operator closes/allocates bounded batches and directly pays current NFT owners. Normal recipients take no action; rejected payouts remain backed for retry or exceptional owner-only fallback. |
| Hand assets to an operator/custodian for external work | Removed. No external custody address, all-ZZZ conversion exit, arbitrary transfer or funded local return path remains. |
| Replace the complete collection on this chain | Before collective exit only: compatible accounting4/canonicalV5 handoff carries ownership, both ledgers, shares and backing, with checked retirement/activation or funded abort. Replacement is permanently blocked after LP exit begins. |
| Relocate canonical ownership/rewards to another chain or recover after chain halt | Not implemented. Moving tokens externally is not movement or revocation of the original NFT/accounting system. |

Native ETH and WETH are distinct assets. Reversed currency slots, unrelated
pairs and an old schema cannot bypass their explicit admission/import guards.
The removed Migration `movePool` alias is not a current operator entry point;
use the exact [function reference](CONTRACT_FUNCTIONS.md).

<a id="three-layers-with-two-distinct-trust-domains"></a>
## Trust boundaries

| Domain | Enforced locally | Remaining trust |
| --- | --- | --- |
| Ownership and accounting | Current-owner claims; nonredeemable per-NFT shares; separate funded LP and royalty ledgers; fixed 80/10/5/5 allocation; exact backing | Correct deployment and dependency behavior, canonical-chain availability |
| Configuration | Fixed core bindings and ZZZ; typed calls; bounded policy; separate guardian/keeper roles | The selected immediate governance quorum, honest feeds, safe configuration and suitable operating rules |
| Collective holder return | Irreversible lifecycle; exact raw principal, frozen shares, cumulative allocation, current-owner direct payout, isolated failures and one-time payment | Operator transaction/gas availability, functioning venue/token, and recipient ability to receive funds |
| Pre-exit canonical replacement | Exact classified backing and one canonical retirement/activation | Reviewed compatible replacement code and safe governance approval |

Governance has no protocol timelock, generic executor or hidden role-grant path.
Its wallet/Safe applies its own signatures and nonce policy. Sealing removes
bootstrap and rebinding powers; it does not make immediate governance trustless.
A compromised governance wallet can approve unsafe prices/parameters or reviewed-
but-unsafe replacement code before retirement. Collective holder return cannot
select an operator beneficiary. No normal holder redemption, universal rescue,
principal sweep or arbitrary allocation change is added.

## Permanent destination capacity: bounded repair

The Vault admits at most four historical/reserved bucket identities. A
reservation permanently occupies one slot; aliases and returns for the same
bucket reuse that slot. A reserved `None` entry has no shares or principal and
must be skipped by upkeep before price or venue reads. All 1,000 NFTs may still
share a single funded bucket: bucket count is not the number of NFTs or funded
pools. Distinct buckets do not merge, and unsafe slot recycling is not supported.

Governance must review destination alias ownership and capacity before moving.
Reservation protects local admission, not venue liveness or a capital-value
guarantee. Arbitrary reservations by governance can exhaust
capacity; the bounded set is not a recovery guarantee.

<a id="different-pair-migration-proposed-composition-epochs"></a>
## Principal retirement and accounting separation

Different-pair conversion, the bridge/message stack and external custody exits
are removed. Current LP admission is native ETH/fixed ZZZ only. Pool movement
before retirement preserves the same actual pair and bucket identity; it cannot
exchange the token contract or turn ETH into WETH. Historical profile readers
retain old composition/claim records without re-enabling those operations.

| Value | Required treatment |
| --- | --- |
| Principal and attributed idle | At collective exit, return actual ETH/ZZZ proportional to frozen bucket shares, never another bucket's assets. |
| Designated compound | Pending5%compound joins that bucket's returned principal; already reinvested compound is already inside LP. |
| Owner/collective LP claims | Preserve existing liabilities and fractions. Guarded reward conversion credits the same NFTs without recognizing new income. |
| Royalties | Preserve eligible cohorts, existing liabilities, future receipts and current-owner claims; no external royalty-custodian drain. |
| Buyback reserves, donations and quarantines | Keep their existing classifications; exclude them from holder principal and newcomer LP execution budgets. |

The terminal Exited5 status reports zero remaining LP and preserves NFT shares
for existing reward indices. Unpaid principal belongs to the NFT's current owner.
Deterministic bounded allocation precedes all payout; direct payout batches mark
each NFT paid once, with reverting receiver calls isolated. A receiver cannot be
forced to accept ETH: retry or an owner-authorized fallback is exceptional recovery.
Actual venue/token faults can still prevent closure/payment. LP earnings end after
all LP closes; NFT transfers and future rarity-weighted royalties continue.

## Accepted migration execution budget

The default contribution / conversion / maintenance loss caps are **2% / 1% /
3%**, with gas separate and governance hard maxima of 10%. Captured operation
policy, signed caller maxima and stronger venue minima still apply. A caller does not gain three fresh budgets for
close, swap and redeployment.

Atomic maintenance values starting principal plus released compound and final
LP plus attributed idle at one starting price vector. Contributions additionally
require actual marginal deployed LP at the captured floor, excluding incumbent
capital; the default is 98%. The separate 5% idle ceiling remains. Governed
parking and collective closure use independently reviewed raw output minima,
without swaps or oracle-valued aggregate loss promises. They do not claim one
cached price vector across separate operator transactions.

Repeated permitted losses can compound. At the default 3%, ten worst-case
operations retain about 73.74% before market changes and gas. There is no
cumulative hard cap; profitability, turnover and strategy review remain required.
See [loss policy](EXECUTION_LOSS_POLICY.md), [migration safety](MIGRATION_SAFETY.md)
and [idle classification](IDLE_AND_DUST.md).

<a id="canonical-chain-continuity-requires-a-separate-decision"></a>
## Controlled canonical migration

Compatible [same-chain canonical handoff](CANONICAL_HANDOFF.md) freezes ownership
and accounting, exports/imports all required domains and exact backing, and
activates exactly one successor when the source retires. Source and successor
must use accounting4 and the compatible holder-exit V5 schema; old remote/home
fields are not filled with invented values. Collective exit permanently blocks
canonical replacement because the transport does not import principal-return
liabilities. Before retirement, pending draws, missing backing or
incompatible contract holders must be resolved under the checked procedure.

External bridging alone cannot transfer canonical ownership or revoke source
claims. No complete cross-chain import/finality system or post-halt recovery
exists in this release. A new chain or token deployment must not be advertised
as automatic continuity for existing holders. Preserve rights and liabilities
through a separately reviewed cutover plan while the original chain works.

## Operating and release boundary

Local tests and Anvil rehearsals do not qualify real feeds, conversion depth,
VRF, authority wallets, OpenSea primary mint, target-chain gas or operating and
recovery services. The two-source price policy still needs independently
qualified observations with the selected 3% disagreement tolerance. Public
website deployment remains null and its signer Anvil-only; old native-2 views
are not accounting4 wallet integration. The served unconfigured poplint artifact
retains its accounting3 reader until a separately reviewed frontend update.

The [operator manual](OPERATOR_MANUAL.md) owns stop/restart and exact call
procedures. Release requires actual dependency/service qualification and an
independent audit with remediation. Documentation changes perform no deployment,
public transaction, service action or existing-state migration.

## Historical evidence

The October 16 design and later superseded bridge/pair/inbox work remain in
[source-scoped architecture review](../reports/architecture-evolution/REVIEW.md),
[verification](../reports/architecture-evolution/VERIFICATION.md) and its
[review brief](../reports/architecture-evolution/REVISED_PROMPT.md). Later
[pair-composition evidence](../reports/pair-composition/VERIFICATION.md),
[custody evidence](../reports/custody-handoff/VERIFICATION.md) and
[current-profile pruning review](../reports/architecture-pruning-20261025/REVIEW.md)
retain their own recorded source identities. They do not re-enable removed
selectors or prove later code. Current procedures above supersede obsolete
operating instructions; historical reports are preserved unchanged.
