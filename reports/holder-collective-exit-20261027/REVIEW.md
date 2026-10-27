# Collective holder exit: internal review

Reviewed 2026-10-27. This is an internal source/design review of the fresh
accounting-V4/custody-V3 candidate, not an independent audit or release approval.
Use [verification](VERIFICATION.md) for exact executed commands, source identities,
results and limitations. Historical custody-V2 evidence does not verify this change.

## Requirement and behavior change

The user replaced principal exit to a governance-selected external custody
address with governance-triggered collective ETH + fixed-ZZZ return to NFT
holders. During ordinary operation holders still cannot redeem principal.
Starting the collective exit irreversibly ends minting and new LP contributions,
maintenance, resume and pool movement. Each actual bucket closes without swaps;
current owners receive proportional principal, while NFT transfers, previously
accrued rewards and future rarity-weighted royalties remain available.

The old recipient/approve/conversion-exit/recovery/completion paths are removed.
Native ETH/fixed ZZZ is the only newly admitted LP pair, including compatible
fee-tier changes. This avoids admitting a future funded bucket whose actual
currencies cannot be returned by this ETH/ZZZ settlement implementation.

## Reviewed safety boundaries

| Concern | Implemented boundary | Remaining condition |
| --- | --- | --- |
| Start during a contribution/maintenance callback | Migration validates all funded buckets before entering the Vault's nonreentrant barrier; Access sets a permanent flag. Principal operations check that flag before and after callbacks. | The ordinary pause and the terminal exit flag are separate. Unpausing cannot restart LP. |
| Governance-selected payout theft | No external custody recipient or sweep. Permissionless pushes resolve the current NFT owner; only that owner can select a fallback recipient. ERC-721 approval alone grants no payout power. | Governance can still choose when to initiate the collective shutdown. Reviewed canonical replacement remains a separate pre-exit authority. |
| Principal/reward mixing | Final harvest allocates actual fees through the existing fixed 80/10/5/5 system. Dust is settled, pending 5% compound joins principal, and exact close deltas plus attributed idle reach settlement. | The holder's earned 80%/10%, royalty balances, 5% buyback reserve and unsolicited prefunds are not principal distributions. |
| Share dilution/rounding | Mint/contribution lock freezes denominators. Per-bucket cumulative floor allocation in immutable mint order preserves every raw unit. Final allocation checks all snapshotted shares and both output totals. | Individual rounding can differ by less than one raw unit from the ideal rational allocation. This is not a new USD valuation. |
| Paying an incomplete inventory | No payouts before every funded bucket closes and every captured mint ordinal is processed. Dormant NFTs have no principal. | A malformed/incomplete inventory fails closed; it is never repaired by guessing zero. |
| Rejection, gas griefing or reentry | Automatic pushes use bounded self-calls; each ETH+ZZZ payout is atomic, marks paid before external calls and checks exact transfers and remaining backing after payment. Failure defers that NFT only. | A receiver requiring more than the automatic gas budget can use owner-authenticated fallback. A failed ZZZ token may prevent all corresponding payouts. |
| Double payment or stale owner | One per-NFT paid marker survives transfers; each push resolves ownership immediately before payment. Claimed funds do not travel with a subsequent NFT transfer. | A legitimate owner can claim before selling; a listing's earlier unclaimed balance is not guaranteed. |
| Broken prices or unavailable conversions | Raw exit has no USD-oracle or swap leg. Caller raw minima and actual venue/token settlement checks still apply. | Raw return is not a 3% value-retention promise and cannot fix a broken venue or token. Network gas is separate. |
| Reopening through canonical handoff | Access preparation/transition and handoff freeze reject the terminal exit flag. Canonical V5 and accounting V4 are explicit new profiles. | This candidate does not migrate terminal principal ledgers into a successor. Old deployed profiles/journals are not relabeled. |
| Stale marketplace metadata | Exited LP reports known zero NAV and a terminal lifecycle trait while royalty activation remains. Bounded principal allocation emits ERC-4906 notifications for the actual funded NFT IDs. | Marketplace cache/provider behavior still requires live qualification. Exited artwork uses the existing activated visual, not a fifth evolutionary artwork. |

## Liveness and operational limits

Governance must pause, review and initiate the irreversible transition, then
close every funded bucket with its reviewed raw minima. Losing governance access
or encountering a failed venue/token before the last close can leave the
collection in Closing. No unsafe administrator bypass, guessed output,
forfeiture, unreviewed conversion or arbitrary-address rescue is introduced.
Already closed principal remains classified and backed while settlement waits.

Once all buckets close, anyone can advance at most32mint ordinals per allocation
call and push at most32NFTs per payout call. Failed pushes remain retryable without
an expiry. The current owner may choose an acceptable recipient using the
fallback claim. There is no operator reimbursement from holder backing.

Exact source-token behavior, venue/runtime qualification, live price/conversion
routes for ordinary operations, actual target-chain gas and service rehearsals,
marketplace integration, and independent audit/remediation remain release gates.
This review does not establish that every possible exploit or failure is absent.
