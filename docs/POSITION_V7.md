# Accounting7: exact-unit LP rewards

This is the fresh source candidate, not an upgrade of deployed accounting6.
Production **NOT APPROVED**. Preserve old runtimes, wallets, journals and
[profile6](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/docs/POSITION_V6.md) readers under their original identities.

## Identity and unchanged economics

| Boundary | Fresh identity |
| --- | --- |
| Vault share/accounting behavior | `ACCOUNTING_VERSION() = 7` |
| Rewards whole-unit allocation | `LP_ALLOCATION_VERSION() = 1` |
| Canonical peers | `ZZZ_CANONICAL_SAME_CHAIN_EXACT_LP_SEADROP_V10` |
| Production inventory / read consumer | schema17/mint2; explicit backend flag2 adds V10 read/claims, default1 retains V9 |
| LP geometry, custody and maintenance | portfolio2, custody5, maintenance3, confirmation3, compound4 |
| Entry and pricing | direct Entry3, reviewedEntry2, pricing2, ProtocolPolicy1 |
| Royalties | settlement4/reporting5; fresh allocation2/payload6 round books, original currencies and one-hour opening; payload5 stays historical |

Position remains the native eight-word principal record. Its equal shape is not
runtime/accounting identity. LP custody is one logical share account per bucket,
with one main or an optional main/residual pair in the same native ETH/fixed-ZZZ
pool. Physical ranges never become separate NFT reward weights.

Fixed actual-receipt 80/10/5/5 is unchanged. The individual 80% uses bucket LP
shares; the collective 10% uses one share per activated NFT across buckets.
The 5% compound and 5% buyback reserves stay outside Rewards. Rarity affects
only separate royalties. Engine rounding phase is not money or a reserved
fractional claim. See [exact allocation](EXACT_LP_ALLOCATION.md).

See [OpenSea mint2](OPENSEA_MINT.md) for the V10 original-recipient/phase extension,
20th callable helper and predeployed metadata renderer. LP/royalty economics and
flattened accounting-domain formats are unchanged; royalty private books require fresh allocation2/runtime pins and must not load historical tree storage. Original V9 evidence retains its
source scope. Explicit mint2 backend reads/claims and per-peer lineage pins are
implemented; source9 website and installed consumers are not upgraded. Actual
V10 consumer/operating qualification remains open.

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
The [integration report](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/exact-lp-integration-20261106/REVIEW.md) owns
verification and remaining limits. Source publication does not deploy, seal,
restart a service, change a website or authorize public signing.


The fresh `activation-final-six-20261118` / payload6 build preserves public accounting7/LP-allocation1/schema17/canonicalV10 logical records. LP phase uses a MAX128 sentinel/full-width spill; Royalty status and Book coefficients use new private encodings without narrowing money or lifetime coefficients. Pricing basis/marks/list are transaction-scoped and explicitly cleared after each atomic operation. Public selectors/types/rights remain; three getter address-input names become `asset`. Use fresh exact source/runtime/data pins and logical canonical import, never old raw slots or relabelled snapshots/journals. The [current verification](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/activation-final-six-20261118/REVIEW.md) qualifies all13 controlled cold cases within20M/full20%; real markets/providers/fees and wider workloads remain separate.

## Historical profile boundaries

These rows preserve inspection compatibility, not operating instructions for the
fresh release. The explicit declared profile, exact code/configuration/dependency
pins and chain/deployment identity select the codec. Never infer a generation
from an eight-word tuple, failed getter, shared version suffix or website name.
Historical journals, checkpoints, receipts and private storage remain unchanged.

| Declared generation | Position and principal/canonical boundary | Other exact recorded capabilities |
| --- | --- | --- |
| Accounting1/2 | Historical15-word codecs and their original status maps; never interpreted as local8-word rows. | Explicit legacy readers only; no automatic import or journal upgrade. |
| Accounting3 | Eight local words; None0/Active1/Outbound2(external custody)/Dormant3/Parked4; no Exited5. Canonical `ZZZ_CANONICAL_SAME_CHAIN_NATIVE_LP_ONLY_V4`. | Direct governance2, fee-intake1, pricing2/routing2/review1; HTTP schema2 is a separate envelope. Retired external-custodian procedures must not run on fresh7. |
| Accounting4 | Eight words; Outbound2 reserved and Exited5 added; custody3, canonical `ZZZ_CANONICAL_SAME_CHAIN_HOLDER_EXIT_V5`, pre-exit only. | Maintenance1 or2 must be explicit; policy2 uses Strategy2/compound3. LP routing0/1 and execution-quality0/1 are separately declared. Confirmation2's recorded900-second window/300-second maximum gap differs from fresh confirmation3. Inventory schema6 observes17helpers; API/config schemas remain separate. |
| Accounting5 | Eight-word main/residual profile; custody4/emergency2, portfolio1, maintenance3/confirmation3/compound4; canonicalV5 retained only with both legs closed/parked. | Entry routing2/pricing2/review1, LP routing2, position-executor1/math1, governance2/fee1/execution-quality1; inventory schema7 has17modules/20helpers. Residual-exit1 requires matching actual binaries, not tuple compatibility. |
| Accounting6 | Eight-word policy-aware profile; custody5/emergency2/residual-close1, portfolio2, maintenance3/confirmation3/compound4; ProtocolPolicy1. Canonical `ZZZ_CANONICAL_SAME_CHAIN_EXACT_ROYALTIES_V8`; older V6/V7 peers incompatible. | Direct Entry3/pricing2/review2, LP routing2/position1/math1. Inventory schema15 has17modules/18callable helpers plus2inert Factory children, with exact royalty4/recovery2/reporting5. Reinvest1/raw-exit1 require exact reviewed capability/runtime pins; schema14 and earlier do not gain them. |
| Accounting7/source9 | Eight-word principal format with LP-allocation1 whole-unit books and exact raw LP V9 domain; source9/schema16/V9 consumer profile. | Explicit historical consumer; checkpoint1 remains accounting6-only. Matching checkpoint2 and original source/configuration pins are required. |
| Accounting7/source10 | Current mint2/schema17/canonicalV10; exact LP V9 domain retained inside V10 plus original-recipient/phase mint records. | Current LP routing3/execution-price1;20callable helpers plus2inert Factory children. F6 explicitly selects factory payload6/allocation2/code-storage2; payload3/4/5 remain distinct historical inputs. |

Inventory schema, read API envelope, activation configuration, Entry routing,
LP routing, accounting, custody, royalty settlement and canonical wire are
independent version families. Schema10's royalty-converting/custody5 profile,
schema9's custody4/direct Entry3/20helpers and schema8's routed Entry2/21helpers
remain historical inspection inputs. Source8 named custody5/direct Entry3 while
ACCOUNTING_VERSION stayed6; served current3 names the separate older website,
not an installed source8/source9/source10 adoption.

The exact eight local fields are poolId, lpTokenId, idle0, idle1, depositUSD,
centerX96, lastRebalance and status. lpTokenId is an actual main Uniswap NFT;
physical amounts and both-leg backing establish custody/NAV, not tuple length or
summed raw liquidity. Current statuses are None0/Active1/reservedOutbound2/
Dormant3/Parked4/Exited5. Whole-collection handoff requires the exact compatible
canonical schema and funded ordered records; legacy/trailing rows reject.
Do not relabel fractional accounting6 or checkpoint1 data as exact accounting7,
flatten raw pending/high/low phases, copy old private slots, reset a journal or
roll older software over newer pending fee records.

For complete historical configuration, geometry, timing, custody and codec
semantics, use the frozen original guides at the pre-consolidation revision:
- [Accounting3](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/docs/POSITION_V3.md).
- [Accounting4](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/docs/POSITION_V4.md).
- [Accounting5](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/docs/POSITION_V5.md).
- [Accounting6](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/docs/POSITION_V6.md).
