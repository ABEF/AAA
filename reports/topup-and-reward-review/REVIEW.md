# October 19 contract and integration review

Internal source review dated 2026-10-19. **Production NOT APPROVED.** This is not
an independent audit or a guarantee that no vulnerability exists.

## Scope and findings

Reviewed the published contract delta from `485a089` through `742b15b`, plus the
current Entry/contribution-budget floors. Today's changed production surfaces
are NFT mint pause, PoolRegistry stop/selection controls, RoyaltyConverter,
RoyaltyRewards, and the two contribution minimum checks. Existing authority,
lifecycle, custody, quote and frontend boundaries were inspected where they
interact with these changes. Unrelated unpublished route/artwork drafts are not
promoted by this review. [Verification](VERIFICATION.md) distinguishes fresh
checks from earlier evidence.

| Surface | Review result and practical boundary |
| --- | --- |
| $5 top-ups | Entry checks original-source value; direct Vault contributions check the fixed helper. Both retain the $100 activation floor and higher configured pool minimum. Six-decimal/depegged input, exact threshold, direct bypass attempts and 99% marginal LP guards have focused tests. No new role, recipient or withdrawal function. |
| One contribution pool | Both configuration paths share selection enforcement. Dependency-free stops clear only the selected pool when deposits stop. Historical custody/maintenance remain supported; operations-only stops do not silently select a different pool. Full validation is needed to reopen. |
| Mint-only pause | Governed mint switch checks before mint and after receiver callbacks. Pending original reveals and separate existing economic rights retain their independent guards. No new randomness reroll/provider override. |
| Royalty conversion | Only the fixed ledger can call the converter; bounded sorted NFT batches checkpoint source entitlements before conversion. Exact source/wrapper/ETH deltas, reviewed routes, deadline, caller minimum and 99% oracle floor remain. Converted ETH is credited to the same NFTs rather than redistributed through the native receipt index. Conversion is not earnings or a claim. |
| Optional royalty outages | Earlier eligible cohorts retain unseen receipts before waiting NFTs join. Activation and healthy currencies continue; exact unreadable backing can still block replacement. This behavior follows the user's accepted recovery rule. |
| Concurrent backend | Existing finite worker/connection admission, request deadlines, immutable snapshot reads, cleanup quarantine and unsigned typed preparation prevent shared wallet context or unbounded request queues. Actual Linux/RPC load qualification remains open. |
| NFT display | Earned totals now combine the NFT's individual LP, equal collective allocation and royalties. Gross pool fees, principal, conversion credits and payouts are not added as new earnings. Current claimable remains separate. Local totals require matching NFT, chain and confirmed block; a missing component/price is unavailable, not zero or a partial total. |

No new unauthorized principal-withdrawal path, hidden payout recipient or
reproducible double claim was identified within this reviewed scope. Governance
can still immediately approve harmful dependencies or replacement code; that
accepted trust is not described as cryptographically eliminated.

## Improvements made in this change

- Enforce the requested floor in both contract paths, backend preparation and new
  website actions; preserve the 1% execution budget and legacy preview holdings.
- Treat optional local history RPC errors as unavailable history instead of losing
  otherwise confirmed ownership and claimable balances. Do not retry a terminal
  `WorkLimit`, hide a core/lifecycle failure or log sensitive exception text.
- Skip expensive historical replay for dormant NFTs. They have no earned-reward
  rows; their core ownership/activation data is still checked.
- Remove misleading gross NFT-card earnings. Saved demo history has no dated net
  receipt series: its missing 24h value stays unavailable, not gross fees/70 or a
  fabricated 90% share. Each NFT's collective allocation depends on membership.

The follow-up [reward calculation audit](REWARD_CALCULATION.md) verifies the complete NFT income sum and fixes an oversized-input display failure without changing economic rights.

Approval review confirms the typed production preparer requests the exact raw
source amount for the pinned Entry, or a zero-reset step for insufficient nonzero
allowance, then requires fresh preparation. Native ETH bypasses token approval.
Entry pulls exactly `amountIn` and clears bounded router/Vault allowances. Existing
sufficient allowances are reused, not automatically reduced; cancelled/reverted
contributions can leave approvals. The 64-case Python run includes exact approval,
reset, lifecycle, owner and distinct local confirmation coverage. No production
browser-wallet execution is claimed from this source review.

Separately, the user requested fresh local claim balances. One operation on the
existing port-8892 Anvil chain funded 100 TEST-1 venue fees and 0.01 test ETH
royalties, processed in four successful local transactions. Active NFT claimable
balances increased and the dormant NFT retained zero; no claims, resets or
new deployment were performed. See [local funding receipt](local-funding.json).
This older deployed fixture does not prove the new $5 binary is deployed.

## Remaining review obligations

These remain in the existing central task ledger, not a second status checklist:

- [Asset/route qualification](../../TODO.md#task-activation-assets): complete $5
  routes within 1%, pricing/depegs, exact on-chain addresses, venue and gas costs.
- [Strategy risk](../../TODO.md#task-security-strategy): oracle manipulation, MEV,
  liquidity/range behavior and repeated permitted per-operation losses.
- [Dependency review](../../TODO.md#task-security-dependencies): wrappers, token
  upgrades, marketplace receipts, creator terms, funded services and VRF.
- [Integration review](../../TODO.md#task-security-integration): real concurrent
  users, provider failure/recovery, complete history and independent audit.
- [Governance](../../TODO.md#task-security-governance) and
  [chain recovery](../../TODO.md#task-security-chain-recovery): immediate authority
  trust, replacement admission and still-unfinished future-chain handoff.

Vault runtime has only **19 bytes** of normal-build headroom. Preserve module
boundaries and actual deployment-size checks, including dynamic constructor args.
No public contract deployment, public transaction, server update, existing local
chain restart or paused-monitor restart was performed.

## Subsequent ETH-only payout clarification

The [payout-currency audit](ETH_PAYOUT_AUDIT.md) identifies a material functional
gap: LP claims pay source ERC20; royalty conversion does not cover LP liabilities.
A read-only local trace confirms the behavior without submitting a claim. The
central Todo, feature reference, operator manual, roadmap and release record
retain this open pre-seal requirement. No additional production code changed.

## Contribution failure boundary

Entry conversion, range-aware balancing, LP deployment and share accounting are
one atomic production transaction. Reverts undo their transfers/state; gas and
previous separate approvals are not refunded/revoked. Successful LP followed by a
read/API failure is still successful custody, not a refundable contribution: the
website requests confirmed-state recovery rather than submitting again. Native
local wrapping is an explicit prior step, leaving backed WETH in the wallet if
Entry fails. The local fixture does not imply automatic unwrap/refund UI.

The strategy targets range-dependent token requirements, not an unconditional
50/50 split. It can be one-sided outside range. Contract minimum-output and 99%
original-source deployed-value checks remain in force. They depend on reviewed
prices/dependencies; internal rollback evidence is not a universal no-loss claim.
