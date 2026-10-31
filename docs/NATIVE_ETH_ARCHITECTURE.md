# Native ETH and holder-return architecture

<a id="adversarial-design-review---2026-10-24"></a>

The fresh undeployed candidate uses `Vault.ACCOUNTING_VERSION()==6`, custody4,
direct governance2 and canonical
`ZZZ_CANONICAL_SAME_CHAIN_ADAPTABLE_POLICY_V6`. [Profile6](POSITION_V6.md) is explicit;
older native/wrapped deployments and journals are not upgraded. Production is
**NOT APPROVED**. Earlier [native-port evidence](../reports/native-eth-port/VERIFICATION.md)
retains its original source scope.

## Asset identities and backing

- Native ETH is `address(0)`, eighteen decimals, with no ERC20 runtime hash.
  USD valuation still requires independently reviewed dual-source pricing.
- One fixed ZZZ is configured before seal. Contribution identity, immutable
  Buyback target and Migration's settlement identity must match. No replacement
  token setter exists after seal.
- ETH and fixed ZZZ are the only contribution inputs **and the only admitted LP
  pair**. New static hookless fee tiers on the pinned native venue may be admitted;
  generic ERC20/WETH LP admission is removed. Separate conversion venues and
  admitted marketplace currencies do not expand principal pool support.
- Principal/idle, compound reserve, buyback reserve, earned LP liabilities and
  royalties are separately classified. Forced ETH, donations and old prefunds
  cannot satisfy an operation's declared funding or become fabricated income.
- Exact payable budgets, token deltas, approval resets, ownership, lifecycle and
  reentrancy checks apply. Failure reverts rather than inventing a receipt.

## Bounded physical portfolio

Default custody is one main Uniswap LP. Governance can enable a main plus at most
one residual in the same native ETH/ZZZ pool. Both actual NFTs belong to Vault.
The physical executor is a fixed typed contract child, not a new human operator
or an external custody address. Its parent/core/state/PosM/Permit2/router wiring,
Balancer arithmetic child and standalone fixed-controller companions require
exact runtime/reciprocal checks. Sealing fixes the Access module parents.

Per-NFT value and share pricing use aggregate physical token amounts plus
attributed idle and applicable classified compound, not a sum of liquidity across
ranges. New contributions deploy entrant funds into the current main only;
incumbent residuals are still valued/checkpointed. Ordinary adjustment closes
both old legs and rebuilds the selected portfolio atomically. A disable request
keeps a live residual accounted until safe merge, with no hidden third leg.

The configured main floor(default60%, governed6000–9999bps) and complementary
residual ceiling(default40%) apply after an ordinary hybrid replacement at the
captured price vector, separately from governed idle(default5%) and loss caps. Market drift
can later change both assets/values. It does not force a 40% residual allocation.
[Mode and timing procedure](OPERATOR_MANUAL.md#optional-main-and-residual-mode).

## End-to-end actions

| Action | Native accounting boundary |
| --- | --- |
| ETH activation/growth | Exact ETH through Entry/Vault into native settlement, without wrapping. Original value floors default100/5USD and are governed for future contributions; captured default2% contribution loss applies; actual marginal LP, venue/caller minima and gas remain separate. |
| ZZZ activation/growth | Exact allowance and measured ZZZ input; guarded balancing into ETH/ZZZ. New assets cannot be subsidized by incumbents' LP, idle or compound. |
| Harvest | Actual ETH/ZZZ receipts from both live legs enter fixed80/10/5/5 allocation. ETH holder fees need no conversion; fees are separated before principal close. |
| Earned-fee conversion | Only earned source balances become the same NFTs' ETH credits. Default 1% loss, governance maximum 10%, gas separate. The selected pool's observed fee requires a cheaper route at that default. |
| Royalties | Separate actual-receipt rarity-weighted ledger; optional currency faults preserve earlier cohorts. Royalties remain live after LP exit; no external custody drain exists. |
| Compound/buyback | Only classified reserves fund each job; keeper pays gas. LP shares are not minted by idle reinvestment. Claims do not trigger these jobs. |
| Rebalance/move/resume | Guarded native ETH/ZZZ LP, same actual pair. Default 3% maintenance cap uses starting prices and includes released compound; stronger venue/caller and idle limits still apply. |
| Reversible parking | Approved paused close of both legs into Vault idle, without USD prices or swaps. No external recipient. Fresh guarded same-pair deployment is required to resume. |
| Collective holder return | Governance permanently stops LP; close each bucket, include pending compound, apportion exact actual ETH/ZZZ by shares and pay current owners. No conversion or USD-loss promise. Rejected payouts remain backed. |
| Canonical replacement | Same-chain V6 carries ownership/accounting/backing only before LP exit starts. Both physical legs must be closed before parked export; complete funding and atomic retirement/activation or funded abort are required. |

WETH is unnecessary for native principal, harvesting, closing or holder payout.
A separately reviewed v3/unwrap conversion route can still depend on a wrapper;
its explicit runtime/admin/settlement checks are not removed by native LP support.
ETH/WETH are never silently treated as the same asset.

## Terminal principal and continuing NFT rights

Position6 keeps the eight-word holder-return layout, including `Exited=5`; old `Outbound=2` is reserved.
`Access.lpExitStarted` is a separate irreversible lock, not canonical retirement
or a reversible global pause. Contributions, minting, LP maintenance and new LP
placement cannot resume after it. Each bucket stops earning when closed; the
last close ends LP earnings for the collection.

Shares, collective membership and rarity eligibility remain to preserve earned
rewards and future royalties. Closed NFTs have known zero attached LP and
explicit `LP exited` metadata, using existing activated artwork. Unpaid principal
follows the current owner; payment marks it permanently paid before callbacks.
Principal return is neither a fee earning nor a previously claimed reward.
[Full settlement procedure](HOLDER_COLLECTIVE_EXIT.md).

## Compatibility and remaining work

Versioned API/keeper/inventory readers must explicitly select accounting6,
custody4, portfolio2, LP routing2, maintenance3, confirmation3, Budget4 and
canonical V6; production inventory is schema8 with 21 helpers. Eight-word length alone does not select the profile.
Historical profiles, deployment addresses and receipt/pending journals keep their
original semantics. The served accounting3 poplint artifact and existing local
chains do not acquire new payout controls from source edits; popldemo stays a
separate simulation, public DEPLOYMENT null and browser signing Anvil-only.

Current source/runtime gates, scoped offline checks and local actual-v4-core
integration pass within their [recorded scope](../reports/optional-portfolio-20261030/VERIFICATION.md).
Actual feed/route/VRF qualification, authorities, OpenSea, permanent artwork,
accounting6 service/wallet acceptance, target-chain gas and operating/receiver
failure rehearsals plus independent review remain [open](../TODO.md). No public
transaction, deployment, service restart or release approval follows from this page.
