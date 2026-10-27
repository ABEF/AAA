# Native ETH and holder-return architecture

<a id="adversarial-design-review---2026-10-24"></a>

The fresh undeployed candidate uses `Vault.ACCOUNTING_VERSION()==4`, custody3,
direct governance2 and canonical
`ZZZ_CANONICAL_SAME_CHAIN_HOLDER_EXIT_V5`. [Profile4](POSITION_V4.md) is explicit;
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

## End-to-end actions

| Action | Native accounting boundary |
| --- | --- |
| ETH activation/growth | Exact ETH through Entry/Vault into native settlement, without wrapping. Original value floors$100/$5 and captured default2% contribution loss apply; actual marginal LP, venue/caller minima and gas remain separate. |
| ZZZ activation/growth | Exact allowance and measured ZZZ input; guarded balancing into ETH/ZZZ. New assets cannot be subsidized by incumbents' LP, idle or compound. |
| Harvest | Actual ETH/ZZZ venue receipts enter fixed80/10/5/5 allocation. ETH holder fees need no conversion; fees are separated before principal close. |
| Earned-fee conversion | Only earned source balances become the same NFTs' ETH credits. Default1% loss, governance maximum10%, gas separate. The selected pool's observed fee requires a cheaper route at that default. |
| Royalties | Separate actual-receipt rarity-weighted ledger; optional currency faults preserve earlier cohorts. Royalties remain live after LP exit; no external custody drain exists. |
| Compound/buyback | Only classified reserves fund each job; keeper pays gas. LP shares are not minted by idle reinvestment. Claims do not trigger these jobs. |
| Rebalance/move/resume | Guarded native ETH/ZZZ LP, same actual pair. Default3% maintenance cap uses starting prices and includes released compound; stronger venue/caller and idle limits still apply. |
| Reversible parking | Approved paused close into Vault idle, without USD prices or swaps. No external recipient. Fresh guarded same-pair deployment is required to resume. |
| Collective holder return | Governance permanently stops LP; close each bucket, include pending compound, apportion exact actual ETH/ZZZ by shares and pay current owners. No conversion or USD-loss promise. Rejected payouts remain backed. |
| Canonical replacement | Same-chain V5 carries ownership/accounting/backing only before LP exit starts. Complete funding and atomic retirement/activation or funded abort are required. |

WETH is unnecessary for native principal, harvesting, closing or holder payout.
A separately reviewed v3/unwrap conversion route can still depend on a wrapper;
its explicit runtime/admin/settlement checks are not removed by native LP support.
ETH/WETH are never silently treated as the same asset.

## Terminal principal and continuing NFT rights

Position4 keeps eight words and adds `Exited=5`; old `Outbound=2` is reserved.
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

Versioned API/keeper/inventory readers must explicitly select accounting4,
custody3 and canonical V5. Eight-word length alone does not select the profile.
Historical profiles, deployment addresses and receipt/pending journals keep their
original semantics. The served accounting3 poplint artifact and existing local
chains do not acquire new payout controls from source edits; popldemo stays a
separate simulation, public DEPLOYMENT null and browser signing Anvil-only.

Actual feed/route/VRF qualification, authorities, OpenSea, permanent artwork,
accounting4 service/wallet acceptance, target-chain gas and operating/receiver
failure rehearsals plus independent review remain [open](../TODO.md). No public
transaction, deployment, service restart or release approval follows from this page.
