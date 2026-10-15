# Selected-pool creator revenue observation

Read-only verification on 2026-10-15 through Robinhood's official public RPC and
Pinax agreed at block **89,525,289**, hash
`0xb191eb4fecde14faf513bc06f4c44fff52a29640dce7b1ce69b555d38dc5e19b`.
No transaction or signature was made.

For pool `0x6538e2c223ed70228114983afecbe5e69fe627e2fafdf367bdd6bdeff2ad391f`,
the hook `launches(poolId)` returned base hook fee **100 bps**, protocol share
**3,000 bps**, creator tax **0**, buyback allocation **5,000 bps**, and
`buybackEnabled=false`. Creator recipient was
`0x698084856f65bf1b4740e3d0dba0b57a5b1deba9`. Runtime SHA-256 was
`dc18643fcd12fa11efe76c23b212f54417779d65b4351fdb354e56a744a3a1b6`,
matching the retained source/runtime identity.

The base hook fee is 1% of the swap's unspecified-currency amount. Pons gets
30% of that base fee; with buybacks disabled and no additional tax, the creator
gets the remaining 70% after quote-asset conversion/distribution. This is
approximately **0.70% of traded value**, not an exact fixed USD-volume return.
Token fees may need conversion, rounding applies and future buyback policy can
change cash proceeds. Hook earnings first accrue and are swept to escrow;
they are not automatically ordinary LP fee growth.

The user reports the creator agreed to share revenue in proportion to PoPL's
pool liquidity share. Exact measurement, payment frequency/asset and sender
configuration still require agreement. The proposed calculator in
[REVENUE_SHARE.md](../../docs/REVENUE_SHARE.md) does not grant a debit right over
the creator or turn estimated revenue into a funded NFT claim.

For illustration only, $848,000 volume x 1% x 70% x 34% is **$2,018.24** before
PoPL's 80/10/5/5 allocation. The website's old 0.30%-swap-fee numbers remain
separate hypothetical examples, not actual selected-market receipts.

Primary material: [hook contract](https://robinhoodchain.blockscout.com/address/0xE5e702641Ea86F4ae6cC3cDaeD2B886f976Be044?tab=contract),
[Pons hook and sweep mechanics](https://docs.ponsfamily.com/v2#uniswap-v4-pools).
Raw matched observations are retained externally in this task's evidence directory
at `revenue-terms-20261015/latest-hook.json`.
