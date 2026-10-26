# Native ETH and local Position3 architecture

<a id="adversarial-design-review---2026-10-24"></a>

The undeployed current candidate uses native ETH/ZZZ through contributions, LP
settlement, rewards, maintenance and custody. `Vault.ACCOUNTING_VERSION() == 3`
selects the eight-word [local Position codec](POSITION_V3.md). The same-chain
handoff schema is `ZZZ_CANONICAL_SAME_CHAIN_NATIVE_LP_ONLY_V4`; direct governance
is `AccessController.GOVERNANCE_VERSION() == 2`. Native accounting2 evidence is
historical and does not qualify these later storage/ABI/governance changes.
**Production is not approved.**

## Asset identities and backing

- Native ETH is `address(0)`, eighteen decimals and no runtime hash. It requires
  independently reviewed dual USD pricing. Zero is never a contract destination
  or the configured ZZZ identity.
- There is one fixed ZZZ contract. Bind its source policy once before any pool
  admission, bind immutable Buyback with the same ZZZ, then configure Migration's
  exit identity once before seal. Seal rejects omitted/mismatched bindings.
  No post-seal ZZZ replacement or third activation currency exists.
- Native ETH and ZZZ are the only user contribution inputs. A future accounting
  pool may contain WETH and the same fixed ZZZ, but WETH remains a distinct ERC20;
  admitting a pool does not add WETH as an external input or make wrapping implicit.
- Vault principal/idle, Fees compound/buyback/dust, LP-reward liabilities and
  royalty liabilities are independently classified custody domains. Forced ETH,
  donations and prefunds cannot satisfy a contribution, loss floor or funded
  obligation merely because a contract balance increased.
- Payable input equals the declared native amount; ERC20-only operations require
  zero unrelated ETH. Exact transfer deltas, ownership, lifecycle and reentrancy
  guards apply. Rejecting callbacks revert the operation, not a fabricated receipt.

## End-to-end behavior

| Operation | Current native boundary |
| --- | --- |
| ETH activation/growth | Entry forwards exact ETH; Vault funds typed native settlement. No WETH deposit/approval/withdraw step. |
| ZZZ activation/growth | Exact ZZZ allowance and reviewed conversion. Actual marginal LP must meet the captured contribution floor: default98%, or a stronger venue/caller floor. Activation minimum remains$100; top-up minimum$5; gas is separate. |
| LP fees | Actual ETH enters the fee ledger directly with80/10/5/5 allocation. Current NFT rights follow shares plus equal active membership. Already-native fees need no conversion. |
| ZZZ fee conversion | Default maximum1% loss, captured with actual route/source/price controls; governance may set future category limits up to10%. A cheaper qualified route is still required at this default when the selected LP fee alone exceeds it. |
| Royalties | Admitted marketplace currencies have separate rarity-weighted funded accounting. Native royalty receipts and guarded ETH conversion credits coexist without double-counting income. This is not creator-hook revenue. |
| Compound/buyback | Spend only their classified reserves; retain NFT principal/fee separation. Idle reinvestment issues no new shares. Keeper funds network gas externally. |
| Pool change | `Migration.moveFunds` moves between supported same-ordered-pair local pools under the captured maintenance floor, default97%. The retired Migration `movePool` alias is absent. |
| ETH/WETH pair change | Not atomic: the ordered-pair check rejects it. A reviewed externally custodied conversion/actually funded local completion may use an admitted pool with the same fixed ZZZ. No implicit1:1 normalization. |
| Normal external custody exit | Reviewed paused exit consolidates attributed principal to fixed ZZZ under preserved aggregate/output floors, then sends it to the approved source-chain custodian. |
| Raw external custody exit | Explicit separate approval closes/sends actual native ETH and ZZZ without swaps or USD reads. Reviewed raw minima still apply; no USD-loss guarantee. No WETH dependency. |
| Return/completion | Exact actual assets must return, or actually fund/deploy the admitted local destination. No timeout write-off, synthetic remote LP or automatic reopening. |
| Whole-collection handoff | Local V4 carries ownership, shares, LP/royalty indices and exact classified backing once, with terminal retirement/activation or fully funded abort. No older-schema or cross-chain import. |

## Local position and governance boundary

Position3 stores only pool ID, LP token ID, attributed idle0/idle1, cumulative
contribution USD, range center, last rebalance and status. None0/Active1/
Outbound2/Dormant3/Parked4 have no satellite/remote location meaning. Pinned chain,
Vault identity and canonical lifecycle establish local custody. Native currency
zero must never be interpreted as missing backing.

After seal, the selected governance wallet calls approved module functions
directly. Access has no operation scheduler, role arrays or generic executor.
Module bindings and fixed ZZZ cannot be retargeted. Guardian pause, keeper
maintenance and two-step governance replacement remain separate authorities.
External custody is expressly trusted: its recipient can divert or lose funds;
source contracts cannot enforce their return. This is distinct from holder
redemption, which is not available.

## Services and compatibility

Read responses remain schema2, with explicit accounting3/fee-intake1/native
routing2/pricing2 profiles and current runtime/parent pins. Historical accounting1/2
readers and event decoders retain original semantics, including old status codes.
Do not upgrade a saved journal, alter the existing Anvil deployment, or guess a
codec from returned length. V4 handoff and current lineage reject cross-codec
predecessors. The separate website integration requires the exact reviewed
profile; public DEPLOYMENT remains null and signing stays Anvil-only.

## Review and remaining release gates

Earlier [native-port verification](../reports/native-eth-port/VERIFICATION.md)
and [native readiness](../reports/native-readiness-20261025/VERIFICATION.md)
retain their own source/profile scope. [Current pruning evidence](../reports/architecture-pruning-20261025/REVIEW.md)
records later changes separately. Prior WETH/native2 passes do not prove current
provider compatibility, actual route liquidity, maximal operating gas or safety.

Qualified independent feeds/routes/VRF, production authorities, OpenSea primary
mint integration, native operating/recovery rehearsals and independent audit
remain open in the [sole Todo](../TODO.md). Preserve actual failure/rollback,
native fraction/backing, callback, current-codec handoff/abort and code-size
verification when those paths change. Repeat unchanged suites only for a concrete
reason; no fresh full regression or deployment is claimed by this document.
