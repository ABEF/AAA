# Security model and invariants

Fresh accounting6 supports [governance-triggered collective holder return](HOLDER_COLLECTIVE_EXIT.md).
After LP closes, each NFT retains unpaid proportional ETH+ZZZ principal, old
rewards and future royalty eligibility. Direct payouts are separate from income;
no holder principal withdrawal exists during normal operation. LP cannot reopen
after exit starts. Historical deployments keep their original rules.


**Undeployed development candidate; production NOT APPROVED.** This describes the
current native-ETH, fixed-ZZZ, local-LP design. Source-scoped internal evidence
verifies particular revisions and scenarios; it does not establish a fresh full
regression, qualified live services or an independent audit. Use the
[feature/evidence reference](IMPLEMENTATION_STATUS.md), [audit plan](SECURITY_AUDIT_PLAN.md)
and [release approval record](RELEASE_CHECKLIST.md) for their exact boundaries.

## Custody and authority

- The Vault owns the main and optional single same-pool residual plus attributed idle principal.
  All-leg valuation/harvest/close must authenticate actual IDs/keys/ticks/custody/liquidity;
  no third leg or hidden auxiliary may be created or omitted. A new hybrid main
  must be active and satisfy 60% main/40% residual value guards at captured prices.
- Each NFT has
  independently accounted, nonredeemable shares. Fees separates funded dust,
  compounding and buyback reserves; Rewards holds LP claim liabilities. The NFT's
  separate royalty ledger accounts for actual marketplace receipts. Principal,
  LP income, royalties, donations and mint proceeds must not subsidize each other.
- Holders and keepers cannot redeem principal during normal operation.
  **Governance can irreversibly stop LP and return actual ETH/ZZZ to NFT owners.**
  There is no configurable external custodian, all-ZZZ conversion exit, generic
  Vault executor or principal sweep. A terminal exit cannot reopen after unpause.
- The current governance wallet directly configures reviewed feeds, routes,
  pools, roles and bounded parameters; Access authenticates it without a
  timelock, queued operation or forwarding executor. Sealing fixes
  module bindings and the single ZZZ contribution/buyback/principal-return identity.
  Guardians may pause; governance resumes ordinary operations. Governance starts
  collective retirement only while paused; later unpause cannot undo it. See the [operator manual](OPERATOR_MANUAL.md).
- Native ETH is the actual zero-address currency, not WETH. Optional conversion
  routes may depend on a wrapper; native LP custody and holder return do not.
  Only ETH and the fixed reviewed ZZZ are contribution inputs. Other admitted
  royalty/conversion currencies do not become contribution or principal-pool options.

## Contributions, shared accounting and execution

1. Direct minting currently requires exactly **0.05 ETH**, creates one dormant
   NFT and adds no LP or reward eligibility. OpenSea primary minting, including
   the agreed 0.05 ETH buyer total net of platform fees to the recipient, is not
   integrated or qualified. Mint proceeds are not royalties or LP backing.
2. Activation requires at least **$100 of original source value**; growth requires
   at least **$5**, subject to pool limits. These are contribution thresholds,
   not a current market-value floor. An activated NFT stays eligible after value
   losses. The same NFT keeps its revealed rarity, palette and pattern.
3. Two independently reviewed USD sources per priced asset must be fresh, valid
   and within the selected **3% agreement tolerance**. Disagreement fails closed;
   there is no pool-spot, stale-price or assumed-stable-peg fallback. Two matching
   addresses or answers do not establish independent price discovery.
4. Contribution prices and limits are frozen before external token/conversion
   callbacks. The current **2% contribution** default requires marginal deployed
   LP to satisfy the captured conservative upper-input/lower-LP floor. It cannot
   be met using incumbent LP, unrelated idle, donations or historical compound.
   Reviewed Entry also binds the caller's maximum loss before funds move.
5. Conversion defaults to **1%** and maintenance to **3%**. Governance may set
   each category within a hard **10%** maximum; stronger caller/venue minima and
   captured operations remain binding. Network gas is separate. The default
   1% conversion budget requires a cheaper qualified route than the selected
   pool's observed combined swap fee; no route or cap increase is invented.
6. Idle is attributed share-backed principal, not sweepable dust. Placement and
   guarded maintenance enforce the 5% idle ceiling at execution, not continuously.
   Compounding issues no new shares. Bounded balancing/reinvestment must preserve
   other buckets, existing fractions, ownership and fee reserves.
7. At most one pool accepts new contributions at a time. Up to four permanently
   admitted/historical buckets bound settlement work. Pools are static hookless
   v4 with native ETH/fixed ZZZ only; admission pins the selected chain/dependencies. Same-chain
   pool moves require identical ordered actual currencies; ETH and WETH differ.
   Local fixtures do not qualify worst-case real token, venue or keeper gas.

## NFT rights, receipts and claims

1. Only physically received local Vault LP fees enter the fixed **80% holder /
   10% collective / 5% compound / 5% buyback** allocation. There are no creator
   inboxes, integrated bridge receipts or remote-fee liabilities in this release.
   Deposits and LP-removal proceeds remain principal. Uniswap protocol fees are
   not PoPL revenue.
2. Holder LP rewards follow NFT shares. Collective rewards give every activated
   NFT one equal membership, independent of rarity, LP size or current evolution.
   Dormant NFTs do not dilute it; growth, transfers and maintenance add no membership.
3. Twenty-raw-unit batches implement 16/2/1/1, with carried remainder. Funded dust
   settles to incumbent owner indexes at entry/move barriers; up to 19 raw units
   per settlement are an explicit rounding exception, not a lifetime dust cap.
   Current-pool fees settle before new shares, including entry-generated fees;
   new membership cannot take previously indexed or locally pending rewards.
   Unharvested venue fees retain collection-time membership policy, not a claimed
   historical venue-earning-time allocation. Late compound belongs to incumbents.
4. Royalty weights are **1/2/3** for activated Commun/Rare/Legendary NFTs and zero
   before activation. They never alter LP or collective weights. ERC-2981 requests
   a fixed **5%** payment to the royalty receiver but cannot force marketplaces
   to pay. Distributions require actual receipts; no periodic income is promised.
5. Healthy royalty currencies settle before a new NFT joins. A failed optional
   ERC20 balance/synchronization call defers only that currency's new eligibility;
   recovery assigns previously unseen receipts to the earlier cohort before
   enrolling waiting NFTs. Native ETH has no token balance-read failure or
   external-custody deferral in accounting4/5. Gas bounds and full backing checks
   remain. Not every technical activation failure is isolated.
6. LP/royalty conversions debit the selected NFTs' source entitlements and credit
   actual ETH to those same NFTs. Conversion, claim, transfer and principal return
   are not new earnings. No backing can be counted both as raw funds and as
   converted credit. Retired-currency liabilities remain backed and identifiable.
7. Current NFT ownership authorizes claims; transfer approvals alone do not.
   Whole balances, fractions and unclaimed rights follow the NFT. Debiting before
   payout and exact amount/destination checks protect against double claims and
   callbacks. Ordinary strategy pause does not disable funded claims, although
   canonical lifecycle locks or broken dependencies can. LP exit does not remove
   previously earned claims or future rarity-weighted royalty eligibility.
8. There is no burn/reset, dead-address rescue or administrator sweep of funded
   liabilities, unsupported assets or prefunds. An NFT sent to an unusable owner
   can strand its rights. Exact token deltas reject ordinary transfer taxes;
   rebases, blacklists, proxies and no-op transfers need independent admission review.

## Reveal, metadata and replacement

- The maximum supply is **1,000**. Ordered draw without replacement yields exactly
  **600 Commun / 300 Rare / 100 Legendary** if all are revealed. The current request's authenticated VRF
  coordinator alone fulfills each known request once; finalization consumes the
  existing artwork inventory in mint order. No new image generation, cancellation,
  reroll or administrator-selected traits exists.
- Artwork base remains fixed after sealing; planned coordinator/subscription/payment rotation requires all old draws finalized. Initial provider policy is reviewed at
  seal. Bounded confirmation/callback-gas changes affect future requests only.
  An unanswered earlier request blocks later finalization and activation; whole-
  collection capture also requires completed reveal. Provider authenticity,
  funding and actual fulfillment remain release gates, not ABI assumptions.
- Artwork follows current marked attached LP/idle/compound value and can downgrade
  across governed display-only tiers(default$1,000/$10,000). Valuation can be unavailable while parked or during
  dependency faults. Metadata grants no financial permissions and claims do not
  depend on a successful metadata price read. Exited5 reports verified zero LP;
  terminal `LP exited` uses the existing Activated image, preserving rarity/traits.
- The retained **same-chain** whole-collection handoff freezes ownership and both
  ledgers, exports authentic complete rows, transfers exact classified backing,
  and atomically retires/activates one compatible successor. Full funded abort,
  donation quarantine and terminal-state guards remain. Collective LP exit blocks
  canonical replacement permanently; the schema does not transport principal-return
  liabilities. Unreadable backing can prevent ordinary pre-exit capture. Governance's
  choice of reviewed replacement code remains a trust assumption.

## Exit, operations and remaining limits

The current profile is accounting6/custody4/portfolio2/canonical
`ZZZ_CANONICAL_SAME_CHAIN_ADAPTABLE_POLICY_V6`. Governance starts collective retirement
while paused. Every funded bucket must be actual native ETH/fixed ZZZ before the
irreversible lock. Final collection classifies fees normally; pending 5% compound
joins principal. Exact close deltas and raw minima protect that bucket's returned
assets. No swap or oracle-dependent USD-loss promise is part of holder return.

All buckets close before bounded deterministic ordinal allocation and payout.
Cumulative rounding assigns every raw unit against frozen bucket shares, without
an administrator dust recipient. Shares/membership remain to preserve prior
reward indices and royalty rights. Separate direct-payout batches authenticate
each current NFT owner, mark paid before transfers and isolate failed recipients.
One failed owner cannot block other owners. An owner-only fallback recipient is
exceptional recovery, not a required holder claim. A contract that rejects ETH
cannot be forced to receive it; failed venue/token behavior can still stop
closure or settlement. Exact backing, reentrancy and duplicate-payment guards
must hold throughout, including recipient callbacks and NFT transfers.

There is **no external-custodian exit, integrated bridge, issuer exchange, remote
proof intake or cross-chain NFT/reward-ledger handoff**. No administrative call
can reopen LP or import a replacement after retirement begins. The source cannot
recover a halted chain, replace sealed code or override lost governance keys.
See [holder-return procedure](HOLDER_COLLECTIVE_EXIT.md) and
[recovery boundaries](CHANGE_AND_RECOVERY.md).

Keepers execute authorized upkeep within on-chain range/cooldown/output/loss
guards and pay gas. Optional switching between reviewed +/-25% and +/-50% widths
follows governance's approved rules in ZZZ-price-in-ETH orientation; it is not an
arbitrary keeper policy change. Polling does not guarantee a rebalance time or continuous
in-range liquidity. MEV, impermanent loss and losses within authorized caps remain
possible. Off-chain services are not custody authorities; stale/partial data must
remain unavailable. Ambiguous broadcasts require same-hash recovery rather than
blind resubmission or journal deletion. Keep production keys outside Git and
use the [keeper recovery runbook](KEEPER_RECOVERY.md).

Actual feeds/routes/VRF, token and proxy powers, authorities, OpenSea, native
wallet/service acceptance, worst-case gas/strategy economics, operating rehearsals
and independent audit/remediation remain open. Source hashes and agreeing RPCs
do not eliminate dependency or governance trust. No return, USD value, original
token quantity, continuous availability or yield is guaranteed.
