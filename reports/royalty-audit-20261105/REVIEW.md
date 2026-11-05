# Royalty receipt, recovery, conversion and claims

Reviewed5November2026 against main e007618 and the locally verified recovery1
candidate. **Undeployed; production NOT APPROVED.** This is an internal scoped
audit and implementation, not a whole-project or independent approval.
[Verification](VERIFICATION.md), [machine evidence](evidence.json),
[operator procedure](../../docs/ROYALTY_SETTLEMENT.md).

## What improved

| Finding | Resolution and boundary |
| --- | --- |
| Unsupported receipts and admitted prefunds had no usable recovery path. | Implemented governance-only `recoverUnallocated(asset,amount,routeId,minimumETH,deadline,reviewHash)`. Unsupported balances need no permanent admission slot. Admitted sources can use only explicitly orphaned units after pending settlement. ETH output stays in the royalty ledger and is first allocated at current active rarity weights. |
| A retired receiver rejected unknown late currencies. | `forwardLate` now accepts healthy exact-transfer unsupported tokens, but only after authenticated retirement and only to its one fixed immediate successor. That successor separately admits or recovers them; callers cannot choose a payout wallet. |
| A naive recovery could steal existing royalty entitlement or give newcomers old outage receipts. | Preserve ordinary synchronization, earned balances, fractions, division dust and deferred-cohort settlement. They are liabilities, not recovery inventory. Tests explicitly reject recovery of these funds. User-approved current-weight recovery applies only to value never allocated to an NFT. |
| Recovery could be counted as a second receipt/conversion/claim. | Dedicated `UnallocatedRoyaltiesRecovered` event. Earnings replay credits the native index once, distinguishes collection `royalties_recovered` from old received/quarantined amounts and preserves carried fractions. Actual claims alone increase paid totals. Semantic source changes require checkpoint rebuild/re-pin. |
| Generated event metadata was stale. | Regenerated the source schema and restored exact retired VRF/Entry descriptors from Git. All144prior descriptors remain byte-for-byte equal;175are now available. Decoder-only compatibility does not re-enable retired contracts. |
| Older isolated royalty tests omitted the current ProtocolPolicy dependency. | Explicit test-only controller/policy binding repairs those fixtures. Initial failures are retained; no production activation guard was weakened. |
| ERC2981 was being confused with guaranteed payment. | Source and new transfer regression confirm a fixed5% request to `NFT.royaltyRewards()`, not payment enforcement on transfer. Official OpenSea documentation describes a separate transfer-validator path, absent and unqualified here. No transfer restriction was silently added. |

## Entitlement rules must remain separate

1. Normal admitted receipts settle to the eligible cohort. Activation does not
   give a dormant NFT older royalties. Optional-currency outage recovery settles
   unseen funds to the older cohort before enrolling newcomers.
2. Ordinary `convertBatch` converts selected NFTs' earned balances and credits
   ETH to those same NFTs; it is neither new income nor a payout.
3. Recovery1 uses only unsupported balances or explicit `orphaned` backing. The
   user approved allocating its measured ETH by Commun1/Rare2/Legendary3 weights
   **at recovery**, not reconstructing unsupported arrival-time entitlements.
   Suspected/disputed historical entitlement still needs review; a balance alone
   is not permission to override an existing claim. Governance chooses recovery
   timing, which can affect which activated NFTs participate; that is an explicit
   policy/trust consequence, not historical compensation.
4. Current owners inherit all unpaid rights after transfer. Claims remain owner-
   authenticated. LP terminal exit does not remove royalty weights or allow
   governance to drain earned royalties.

## Recovery controls

- Current governance only, not merely a keeper. Sealed active canonical NFT,
  unpaused/no preparation, with authority/lifecycle checked before and after
  external callbacks. NonReentrant and economic checks remain.
- Positive amount, nonzero review fingerprint and ETH minimum, current deadline
  at most600seconds ahead, and a nonzero active-weight denominator.
- Admitted pending receipts synchronize before the recoverable amount is tested;
  earned/deferred backing cannot be relabelled as orphaned. No LP access, holder
  claim override, arbitrary call or recipient parameter.
- ERC20 conversion uses the fixed converter bound before sealing, exact temporary
  approvals reset to zero, reviewed enabled routes, actual source/native deltas,
  caller minimum and the converter's ordinary price/loss floor. Default1%,
  governance maximum10%, gas separate. No financial bypass was introduced.
- Native unallocated ETH needs no converter or swap. Recovery credits one lazy
  index, not an iteration sending funds to1,000wallets. Holders later use normal
  claims. The keeper's existing conversion job does not automate this authority.
- Failures revert all accounting and transfers. Operator stop/review/re-enable
  and fresh simulation/retry retain existing journals; no implicit server reset.

## Verified and remaining

The source-scoped record includes72distinct selected EVM successes, with the
current1,000-NFT mixed-state fixture and a1,000-input recovery conservation fuzz
method, plus actual local v4 conversion. Python141affected checks and103final
record/regression checks overlap and must not be summed.43normal deployment-size
gates pass;474actual static detector contexts have explicit scoped dispositions.
See verification for failed/corrected stages and limits.

No finite audit covers every token or execution path. Malicious/frozen/blacklisted,
taxed/rebasing, unreadable, worthless, unpriced or illiquid assets may remain
unconvertible. Reviewed single-hop venues and independent prices must actually
exist; there is no universal router or guessed token valuation. With no activated
NFT there is no permitted beneficiary yet. `orphaned` remains a backing
classification pending explicit recovery, not permission to sweep liabilities.
Fractional/global rounding backing remains reserved, not recoverable surplus.

ERC2981 requests5%; marketplaces/private sales can omit payment. OpenSea's
[documented enforcement](https://docs.opensea.io/docs/creator-fee-enforcement)
requires compatible transfer-validator integration and supported market flows.
That would change transfer trust/availability and needs a separate decision and
Robinhood qualification before sealing. [ERC2981](https://eips.ethereum.org/EIPS/eip-2981)
itself makes payments voluntary.

Real feeds/routes/tokens, converter binding, actual marketplace payment behavior,
matching source services/site, operator gas/hosting/recovery and independent
audit/remediation remain open in the sole Todo. No deployment, sealing, public
transaction, service/site/Anvil/journal/signer or heartbeat change was made.
