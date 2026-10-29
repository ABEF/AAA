# Simplified release boundary

The fresh undeployed [accounting4/custody3 profile](POSITION_V4.md) accepts only
native ETH and one fixed ZZZ for contributions and LP custody. It replaces
external custody exits with [collective principal return to NFT holders](HOLDER_COLLECTIVE_EXIT.md).
Production is **NOT APPROVED**; existing deployments and journals are unchanged.

## Kept, removed and why

| Component | Current purpose |
| --- | --- |
| Vault / Liquidity / Strategy | Shared native ETH/ZZZ LP, per-NFT shares, actual placement/harvest and constrained range maintenance. |
| Fees / Rewards / Membership | Actual80/10/5/5 fee allocation, share-weighted individual and equal activated collective rights; separate compound/buyback reserves. |
| NFT / royalty ledger / converters | Fixed trait draw, transferable ownership and separate rarity-weighted actual royalties, including admitted currencies and guarded conversion. Future royalties continue after LP exit. |
| Migration / parking helper | Same-pair moves/parking, separate paused-governance manual emergency redeployment with explicitly optional financial checks, or terminal collective holder return. No arbitrary recipient; bypassed financial guards can permit near-total loss. |
| Canonical handoff | Same-chain ownership/accounting/backing replacement with funded abort, only before collective LP exit. |
| External principal and royalty custody exits | Removed, including all-ZZZ consolidation, chosen custody recipients, return/completion ingress and royalty drains. |
| Generic ERC20 LP pools | Removed from production admission so every funded bucket can return ETH+ZZZ. Separate ERC20 conversion venues/royalty currencies remain. |
| Creator inboxes, bridges and remote ledgers | Removed; the hookless LP earns actual venue fees directly. No remote transport, synthetic LP or bridge operator is configured. |

Separate ledgers and bounded helpers preserve economic domains and deployment
size. Historical codecs/event readers remain where needed to inspect real old
state; they do not re-enable removed current selectors. Earlier
[cleanup](../reports/obsolete-code-20261025/REVIEW.md) and
[Position3](POSITION_V3.md) evidence retains its recorded scope.

## Authority and configuration

The selected governance wallet calls modules directly. There is no timelock,
scheduler or generic executor. Governance replacement is proposal/acceptance;
sealing fixes modules and erases bootstrap. The sole human operator may control
all project accounts, but the automated keeper key retains limited authority.

Before sealing, bind the same reviewed ZZZ in source assets, Buyback and
Migration. After sealing, supported source/route/feed/range/role settings remain
configurable within guards; ZZZ identity and80/10/5/5 do not. Defaults remain
contribution2%, conversion1%, maintenance3%, each bounded at10%, gas separate.
Use [post-seal policy](POST_SEAL_POLICY.md) and the [operator manual](OPERATOR_MANUAL.md).

## Choosing the action

1. To change fee tier while keeping LP active, admit the reviewed native ETH/ZZZ
   destination, use `Migration.moveFunds`, verify actual destination LP and
   deliberately switch contributions/routes. Shares and accrued rewards remain.
2. To wait through an outage, use exact approved paused parking. Principal stays
   attributed inside Vault; resuming requires fresh same-pair execution guards.
3. To permanently stop LP, use `beginCollectiveExit`, close all buckets, allocate
   1-32 ordinals per call and distribute 1-32 NFTs per call. The operator pays
   current holders automatically; rejected recipients retain an owner fallback.
4. Pending compound joins returned principal. Earned LP rewards, royalties and
   the designated buyback reserve remain separate. No reset/sweep erases them.
5. NFTs remain transferable and royalty-eligible; LP earnings end at closing.
   Unpause cannot reopen LP, minting or canonical replacement after exit starts.
6. An issuer token exchange or new chain is no longer an operator-custody path.
   Holders receive actual old ETH/ZZZ; a new token/project requires fresh review
   and does not automatically import the old collection or its rights.

## Explicit compatibility boundary

The source requires accounting4, custody3, governance2, fee intake1, pricing2,
routing2, reviewed Entry1 and canonical
`ZZZ_CANONICAL_SAME_CHAIN_HOLDER_EXIT_V5`. Position remains eight words; statuses
are None0, Active1, reserved Outbound2, Dormant3, Parked4, Exited5. Canonical group
rows retain twelve words; V5 peers must match exactly and cannot hand off after
LP exit because that importer does not carry terminal principal liabilities.

No automatic historical profile migration exists. Old Anvil deployments,
nonces/journals, published website artifacts and historical verification keep
their original identities. Read the [function reference](CONTRACT_FUNCTIONS.md),
[feature evidence](IMPLEMENTATION_STATUS.md) and [sole Todo](../TODO.md) for actual
implementation/verification and remaining release work. No public deployment,
transaction, signing extension or service rollout is authorized by this document.
