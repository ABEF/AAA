# NFT ownership and revenue review

2026-10-16. Internal review of the undeployed working candidate. **Not an
independent audit or approval for real funds.** See the [revised execution
prompt](REVISED_PROMPT.md), [original prompt](original-prompt.txt) and
[baseline identities](baseline.json). Results are recorded separately from
source inspection; an existing historical report is not a fresh test run.

## Prompt challenge and second check

The first check compared the request with accepted economics. The second used
independent source reviews of accounting, ownership/royalties and scale tests.
The resulting corrections were checked against actual call paths:

- Economic identity is a hashed canonical NFT ID with shares of a shared bucket;
  venue LP token IDs can change during maintenance. There are not 1,000 LPs.
- The 1,000 cap and exact 600/300/100 quotas are fixed. No supply expansion,
  deactivation, reroll or new governance upgrade power is implied by this work.
- Activation persists through falling market value and custody transitions.
  Eligibility and artwork evolution are different state machines.
- Pending local receipts settle to incumbents; unharvested/remote revenues retain
  the accepted processing-time membership policy. Generation-time entitlement
  cannot be reconstructed from a later unlabelled creator payment.
- Full groups of 20 raw units split 16/2/1/1. Up to 19 raw units per settlement
  can instead go to incumbent owners at entry/migration boundaries. This is a
  documented exception, not exact 80/10/5/5 at every denomination or granularity.
- Separate royalties request 5% and use activated rarity weights 1/2/3. No
  marketplace payment is assumed until funds actually arrive.
- A complete local test is useful evidence, but not a proof that all bugs,
  adverse market outcomes, external failures or unsafe future routes are absent.

## Identity and ownership

`ZZZVault.mintDormant` hashes chain ID, Vault address and the monotonically
increasing issuance sequence. `ZZZNFT` records the issuance ordinal separately.
It binds a coordinator request to that ID; ordered quota and artwork-inventory
draws finalize traits once. `ownerOf(id)` is the canonical owner.

`Vault.nftBucket(id)` selects a stable custody group. `sharesOf(id)` records that
NFT's nonredeemable fraction, and `bucketTotalShares(bucket)` is its denominator.
Physical LP custody lives in `group(bucket).lpTokenId`, owned by the Vault.
Rebalance closes/replaces that physical token; it does not remint the collection
NFT or change its rarity or share identity. Compounding increases bucket NAV
without minting more shares. New contributions buy shares at current incumbent
NAV after pre-entry fee checkpoints and reserve settlement.

LP individual indexes are keyed by bucket and asset; the collective index is
global per asset. Each NFT owns its paid checkpoints, accrued whole balances and
fractions. The separate royalty ledger uses per-asset indexes and NFT-specific
checkpoints/accruals with immutable rarity weights. No transfer needs to move
balances between wallets.
Both claim ledgers authenticate `ownerOf(id)` at execution and pay that owner.
Approval to transfer an NFT does not authorize claiming its revenue.

The NFT-created claim router bounds batches to 32 unique NFT/asset/ledger entries.
It checks ownership before any payouts and again before each entry. Each ledger
also authenticates the owner, consumes entitlement before paying and guards
reentrancy. There is no caller-selected target or payout address.

**Sale ordering matters:** a valid seller claim mined before the sale consumes
that amount. A transfer mined first revokes the seller's claim authority. The
buyer inherits the then-unclaimed balances, not a guarantee of an old listing or
API snapshot. A purchase promising a minimum included claim balance would require
an atomic marketplace-specific condition. No such promise or new sale mechanism
is added here.

Safe transfer updates ownership before calling the receiver. The receiving
contract may therefore claim as the new owner during its callback. If that
callback rejects the transfer, ownership and all nested claims revert together.
An approved marketplace operator cannot claim merely through approval. An escrow
that actually becomes `ownerOf(id)` is the holder and may claim if its code allows.
A payout callback can also transfer the NFT onward after entitlement was consumed;
event ordering alone must not misidentify that valid earlier payout as theft.

## Three distinct funding paths

```text
Conventional v4 LP fees -> LiquidityManager.collect -> Vault fee deltas
                                                         |
Creator's actual payment -> immutable RewardReceiver.sync |
                              -> FeeController.allocateExternal
                                                         |
                                              FeeController
                      +----------------+-----------------+-------------+
                      |                |                 |             |
                    80%              10%                 5%            5%
             bucket owner index   equal NFT index    bucket compound  buyback
                      +------ Rewards ------+          reserve        reserve
                                  |                       |             |
                        current-owner claims        permanent LP   swap + burn

Marketplace royalty actually received -> NFT.royaltyRewards()
                                      -> separate 1/2/3 index
                                      -> current-owner royalty claim
```

The selected native-ETH/Pons market has zero conventional LP fees in the reviewed
configuration. Its creator/hook revenue is a distinct stream. Holding liquidity
does not itself authorize PoPL to debit the creator or receive that revenue.
The agreement's basis, share, assets and frequency remain to be finalized.

FeeController allocates only pulled, funded assets. Native creator payments need
the admitted wrapper and become the canonical pair asset. Ordinary pair receipts
are forwarded through the fixed bucket inbox. Mint proceeds, old idle principal,
LP removal proceeds, unattributed donations and royalty balances are not LP fees.
Satellite owner/collective reserves return as already allocated 90% funds, with
provenance and funded-liability checks; they are not split a second time.

The 80% owner index is bucket-specific and proportional to LP shares. The 10%
collective index gives each activated canonical NFT one equal share. Rarity has
no influence on either. Funded dust and pending local creator inboxes settle
before new membership. Top-ups checkpoint old shares first and add no membership.

The 5% compound reserve belongs to the earning bucket. Only the Vault may consume
it into its attributed idle/deployed principal. The keeper cannot receive it.
The 5% buyback reserve is segregated by asset; the fixed Buyback module obtains
only its recorded budget, uses an admitted direct pair or burns ZZZ directly,
then checks both supply reduction and its remaining ZZZ balance. Failed execution
must atomically restore reserves and keep unrelated funded claims available.
Price/slippage/deadline checks limit execution; they do not eliminate MEV or IL.

Royalties are allocated separately when admitted funds are observed. Pending
receipts synchronize before activation or claim. Prefunds, pre-admission balances
and receipts with no eligible NFTs remain quarantined. Fractional and global
division dust stays backed; no administrator can sweep it. Native ETH and
admitted exact-transfer ERC20 assets have independent accounting and units.

## Marketplace verification

ERC-2981 signals a recipient and percentage; it does not enforce payment or tell
whether a transfer was a sale. Current OpenSea documentation describes separate
ERC-721-C/transfer-validator integration for enforcement. This NFT uses ordinary
ERC-721 plus ERC-2981, so that enforcement must not be advertised. No marketplace
sale of this undeployed collection was executed or verified. Production must
configure the actual `NFT.royaltyRewards()` address and stage a real paid sale
and claim for each supported asset and chain.

Sources checked 2026-10-16: [ERC-2981](https://eips.ethereum.org/EIPS/eip-2981),
[OpenSea enforcement](https://docs.opensea.io/docs/creator-fee-enforcement),
[Uniswap v4 architecture](https://developers.uniswap.org/docs/protocols/v4/concepts/architecture).

## Findings and dispositions

| ID | Finding / assessment | Disposition |
|---|---|---|
| Q1 | No direct integration execution coverage for `ZZZBuyback.execute` existed; a token-only burn fork test was insufficient. This was a verification gap, not a demonstrated theft exploit. | Add real-module success, failure, rollback, retry and conservation regressions; actual venue qualification stays separate. |
| Q2 | Existing 1,000-NFT gas tests used one wallet and one final claim; full-supply artwork tests did not establish combined reward correctness. | Add varied owners/LP/rarities, all-NFT multi-stream payouts and per-asset conservation with cold-operation gas checks. |
| Q3 | Isolated transfer tests did not combine real custody with immediate receiver claims and safe-transfer rollback across both ledgers. | Add explicit ordered transfers, operators, pending receipts, callback claims/rollback and dual-ledger stateful invariants. |
| R1 | An admitted broken royalty token can block new activations because incumbent settlement must read every admitted asset. Skipping it would change eligibility economics. | Known liveness risk; fail closed, test healthy-asset claims independently, retain token/upgrade/blacklist review gate. |
| R2 | Destination reservation currently reserves identity, not an available capacity slot. Later unrelated arrivals can prevent delivery. | Existing unresolved migration blocker; preserve rejection/retry evidence and keep real bridging disabled. |
| R3 | Canonical creator-funded compounding reserves cannot automatically follow permanently remote principal. | Existing limitation; reinvest on compatible return or implement/review a separately funded remote top-up design. |
| R4 | Sub-20-unit dust exception is bounded per settlement, not over the protocol's lifetime. Low-decimal/high-unit-value assets can make it material. | Retain policy; qualify raw-unit economic value and entry frequency for every admitted asset. |
| R6 | Migrating LP does not migrate canonical NFT ownership, membership, per-NFT shares or claim ledgers. Permanent home-chain loss has no implemented canonical recovery. | Explicit pre-seal architecture decision and separate audited recovery design; do not promise universal chain failover. |
| R5 | A pre-sale balance snapshot can become stale after the seller claims. | Document execution-time ownership and buyer verification; no false minimum-entitlement guarantee. |

No production rewrite is justified merely because the prompt says "implement" an
already implemented feature. Record any demonstrated new defect and its repair
in the final verification report rather than counting a test as a source fix.

Severity and prerequisites: Q1-Q3 are medium-priority verification gaps, not
demonstrated asset-theft vulnerabilities. R1 is a medium liveness risk conditional
on a previously admitted token failing; healthy assets remain claimable. R2 is a
high-priority blocker **before enabling real cross-chain movement**: competing
admissions can consume capacity before delivery. Migration remains disabled for
initial launch. R3 is a medium functionality limitation when custody stays remote.
R4 requires economic review for low-decimal/high-value assets; repeated boundary
settlement can make a small raw-unit exception material. R5 is execution-order
behavior, not unauthorized claiming. No newly demonstrated critical/high exploit
in the enabled local ownership/reward paths was found; this is not an absence proof.

## Accounting assertions and coverage boundaries

For each asset separately, tests reconcile funded receipts against paid claims
plus remaining reserves/liabilities/quarantine and executed reinvestment/burn.
Backing balances and their liabilities are two descriptions of the same money,
not two additive obligations. Raw native, 6-decimal and other token amounts are
never summed as if they had the same value.

Shared-bucket principal equals attributed venue/idle/compound assets in the
fixture, while unallocated donations remain excluded. NFT share sums equal the
bucket share supply; membership counts match activated NFTs; royalty weights
match immutable rarity; all pending and claimed entitlements stay funded.
These are accounting checks. They do not promise market-value conservation.

Existing suites additionally cover zero/one membership, fractions and dust,
multiple pools, parked/remote custody, historical reward delivery, disabled assets,
oracle failures, entry callbacks, migration replay/epochs, reserve roles and
access sealing. The coverage matrix and executed test receipts identify the
precise cases. Local mocked venues are never presented as a live trading test.

## Open release gates

1. Independent audit/remediation and final frozen-source/configuration approval.
2. Real selected-market integration, independent USD feeds, funded supported VRF,
   authority addresses and finalized creator payment terms.
3. Actual input routes, complete execution costs, strategy/MEV/IL analysis and
   target-chain gas limits across admitted tokens, venues and inboxes.
4. Robinhood Testnet wallet/API/indexer/keeper and marketplace sale rehearsals;
   live frontend transaction/history integration and permanent artwork hosting.
5. Complete sustained operating observation, independently hosted alerts/backups,
   redundant RPC and fee qualification, physical host loss and key rotation.
6. Before enabling bridging: permanent capacity admission, reviewed provider and
   destination safety/backing, remote compounding and adversarial multi-chain runs.

7. Before sealing: resolve the canonical home-chain failure model, lost-key policy
   and any required full NFT/ledger migration design. See the seven workstreams
   in the [security audit plan](../../docs/SECURITY_AUDIT_PLAN.md).

No component in this review receives unconditional production approval. A
perpetual right to funded fees is not a promise of perpetual revenue, capital
value, service availability or recovery from every external failure.
