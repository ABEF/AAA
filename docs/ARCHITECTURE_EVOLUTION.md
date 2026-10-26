# Architecture evolution and trust boundaries

This is the current change-boundary guide for the undeployed candidate, not a
second roadmap. [Architecture](ARCHITECTURE.md) explains interactions,
[components](COMPONENT_STATUS.md) maps source ownership, and the [sole Todo](../TODO.md)
tracks unfinished work. Production is NOT APPROVED.

The current profile is accounting 3 / direct governance 2 / fee-intake 1 /
local canonical V4. Native ETH and one fixed ZZZ are the only contribution
inputs. The current contracts contain no integrated bridge, creator-payment
inbox, remote reward intake or post-seal ZZZ replacement. Historical profiles
retain their own codecs and evidence; changing a configuration version does
not upgrade deployed storage, journals or ownership.

## What can actually evolve

| Change | Current boundary |
| --- | --- |
| Tune range, cooldown, triggers or execution limits | Direct governance through bounded setters. An optional reviewed keeper rule selects only the 25% / 50% presets; physical LP replacement remains guarded maintenance. |
| Select another contribution pool | Admit the supported pool, preserve historical bucket identities and deliberately switch the one enabled contribution pool. Admission alone does not move liquidity or qualify routes. |
| Move LP to another local fee tier | `Migration.moveFunds` atomically redeploys the same actual ordered pair, preserving NFT shares and the captured maintenance floor. |
| Change ETH to WETH accounting or another pair | Not an atomic `moveFunds` operation. Explicitly approved external custody can perform conversion, followed by actually funded local completion into an admitted pool containing the same fixed ZZZ. |
| Add another hookless static-fee local v4 pool | Within the sealed manager's supported rules. Native pools are pinned Robinhood ETH/ZZZ; generic ERC20 pairs must contain the same ZZZ. |
| Add an arbitrary hook, new DEX algorithm or native token | Unsupported by configuration. Requires separately reviewed compatible code and an appropriate replacement plan. |
| Replace the ZZZ token contract | No setter exists. The selected approach is custody exit, external issuer exchange and a fresh reviewed deployment; continuity of existing NFT rights needs its own concrete plan. |
| Hand assets to an EOA/contract for external work | An exact approved paused custody exit. Source contracts cannot compel the recipient to return assets or prove external bridging/exchange. |
| Replace the complete collection on this chain | Compatible canonical V4 handoff carries ownership, both ledgers, shares and exact classified backing, with checked retirement/activation or funded abort. |
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
| External custody and replacement | Exact request/snapshot, raw transfers, stored floors, actual local funding and one canonical retirement/activation | Honest external recipient/replacement code and operator execution; source contracts cannot recover stolen external assets |

Governance has no protocol timelock, generic executor or hidden role-grant path.
Its wallet/Safe applies its own signatures and nonce policy. Sealing removes
bootstrap and rebinding powers; it does not make immediate governance or a
custody recipient trustless. A malicious quorum can approve unsafe prices,
a dishonest recipient or reviewed-but-unsafe replacement code. No holder
redemption, universal rescue/sweep or arbitrary change to allocation is added.

## Permanent destination capacity: bounded repair

The Vault admits at most four historical/reserved bucket identities. A
reservation permanently occupies one slot; aliases and returns for the same
bucket reuse that slot. A reserved `None` entry has no shares or principal and
must be skipped by upkeep before price or venue reads. All 1,000 NFTs may still
share a single funded bucket: bucket count is not the number of NFTs or funded
pools. Distinct buckets do not merge, and unsafe slot recycling is not supported.

Governance must review destination alias ownership and capacity before moving
or exiting. Reservation protects local admission, not external custody, venue
liveness or return funding. Arbitrary reservations by governance can exhaust
capacity; the bounded set is not a recovery guarantee.

<a id="different-pair-migration-proposed-composition-epochs"></a>
## Different-pair migration and composition epochs

The former typed pair executor and bridge/message stack are removed. A different
accounting pair is handled, when supported, by [approved external custody](GOVERNED_CUSTODY_HANDOFF.md):
exit, execute the reviewed conversion externally and actually fund/deploy the
admitted local destination. Normal completion preserves its original approved
absolute floor; explicit raw mode uses its separately approved raw minima.
Neither relabels historical claim currencies or creates remote backing.

| Value | Required treatment |
| --- | --- |
| Principal and attributed idle | Exact bucket custody and actual destination LP/funding; never borrow another bucket's assets. |
| Designated compound | Purpose-bound incumbent backing; historical currencies remain accounted through composition changes. |
| Owner/collective LP claims | Preserve existing liabilities and fractions. Guarded reward conversion credits the same NFTs without recognizing new income. |
| Royalties | Separate eligible cohorts, funding, conversion and full original-currency custody return. |
| Buyback reserves, donations and quarantines | Keep their existing classifications; they cannot pay an entrant's LP minimum or make a custody plan appear funded. |

The local composition epoch identifies a changed accounting pair and historical
backing; it is not a bridge message or a license to change fixed ZZZ. Normal
recovery requires every original actually sent asset and quantity. An issuer
exchange can make that return impossible unless a concrete continuity plan is
reviewed before irreversibly exchanging or burning the original assets.

## Accepted migration execution budget

The default contribution / conversion / maintenance loss caps are **2% / 1% /
3%**, with gas separate and governance hard maxima of 10%. Captured operation
policy, signed caller maxima, stronger venue minima and original approved
custody floors still apply. A caller does not gain three fresh budgets for
close, swap and redeployment.

Atomic maintenance values starting principal plus released compound and final
LP plus attributed idle at one starting price vector. Contributions additionally
require actual marginal deployed LP at the captured floor, excluding incumbent
capital; the default is 98%. The separate 5% idle ceiling remains. Parking and
a later custody approval are distinct transactions: preserve reviewed pre-parking
minima rather than pretending the contract cached a single cross-transaction
price vector. Explicit raw exit makes no USD-loss guarantee.

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
must use the compatible local V4 schema; old remote/home fields are not filled
with invented values. Pending draws, external custody, missing backing or
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
are not current accounting-3 wallet integration.

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
