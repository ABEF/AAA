# LP holder rewards settled in ETH

The user approved a **1% maximum execution loss, network gas separate**, on
2026-10-20. This applies to LP reward conversion, separately from contribution
and maintenance limits. Production routes, feeds, operating qualification and
independent release approval remain required. See [the central task](../TODO.md#task-lp-eth-settlement).

## Accounting and claims

The existing 80/10/5/5 allocation runs first. Only whole units already earned in
the **80% individual and 10% equal collective ledgers** can be converted.
Principal, compound/buyback reserves, orphaned receipts, index dust and other
NFT balances are not conversion inputs. Checkpointing uses the NFT's historical
share and membership indices before spending anything; source fractions remain.

`Rewards.convertBatch(address,uint256[],bytes32,uint256,uint256)` accepts 1-32
sorted, distinct minted NFT IDs and one admitted non-native source asset. It
converts their earned balances once, then credits the same NFTs in native ETH.
Cumulative integer allocation conserves every output wei across individual and
collective components; individual rounding may differ by less than one wei.
Neither current shares nor royalty rarity redistributes those credits. Transfers
carry source balances and converted ETH to the new owner.

The dedicated [LP converter](../src/ZZZLPRewardConverter.sol) reuses the fixed-ledger
[royalty conversion executor](../src/ZZZRoyaltyConverter.sol), as a **separate
deployment and custody path**. Reviewed WETH unwraps exactly without a swap or
USD oracle. Other admitted currencies use a reviewed typed V3 route, fresh
independent oracle quote, at least 99% of quoted output, a stronger supplied
minimum if present, and a deadline no more than ten minutes ahead. Source spend,
wrapped output, unwrapping and ETH delivery are measured exactly. Approvals are
for the exact batch and reset to zero. Network gas is paid separately by the keeper.

Any failed swap, oracle check, unwrap, balance delta, callback guard or minimum
reverts the whole batch, restoring source balances and liabilities. Native ETH
is asset `address(0)` at Rewards asset index zero; there remain at most 32 ERC20
assets, for 33 total. Native credits never enter share/membership indices.
Unsolicited ETH does not become a claimable reward.

The standard website claim selects native ETH from both LP and royalty ledgers.
Unconverted balances are displayed separately as **awaiting ETH conversion**.
`Rewards.claim(id, sourceToken)` remains an explicit source-currency recovery
option, and ClaimRouter can prepare it when explicitly selected. It pays the
current owner directly and prevents a later second payout through conversion.
Claims remain available during an ordinary strategy pause. Canonical locks still
apply, and a recipient rejecting ETH reverts its claim without losing the balance.

## Operator procedure

| Step | Authority, operation and verification |
| --- | --- |
| Install before sealing | Bootstrap deploys `ZZZLPRewardConverter(controller,rewards,wrappedETH)`; governance calls `Rewards.bindConverter(candidate)` once. Verify `ledger()`, `access()`, `wrapper()` and `Rewards.converter()`, addresses, code and implementation dependencies. This binding cannot be added or replaced after sealing. Core sealing alone does not certify that it was configured: require it in the product release inventory. |
| Review the wrapper | Governance calls `configureWrapper((bytes32,address,address,address,bytes32,bytes32,bytes32))` with code/admin/implementation/owner pins and review hash, then `setEnabled(true)`. Follow the same proxy-risk review as [royalty conversion](ROYALTY_SETTLEMENT.md); a ticker or runtime hash alone is insufficient. |
| Admit a swap | Governance calls `addRoute((address,address,address,address,uint24,bytes32,bytes32,bytes32,bytes32,bytes32))` for source/router/factory/pool/fee and their hashes/review. Verify returned route ID, pair, exact routing interfaces, liquidity and independent feeds; simulate full conversion. No arbitrary calldata or output recipient is configurable. |
| Change or stop a route | `setRouteEnabled(routeId,false)` and `setEnabled(false)` stop without querying failed dependencies. For replacement routes, admit and verify a new immutable route record, switch the keeper configuration, then disable the old route. Re-enabling performs dependency checks. Governance is immediate through the AccessController; no waiting period is introduced. |
| Run a batch | An authorized keeper uses confirmed balances, sorted IDs, minimum output and fresh deadline. Simulate, submit through the existing serial sender, wait for confirmed receipt, and verify `LPRewardsConverted`, source/native liabilities, zero allowances and unchanged principal/shares. Conversion is not `Claimed`. |
| Recover a failure | Inspect sanitized failure logs and confirmed transaction/nonce state first. Repair/review the route, price or wrapper before retrying. Do not weaken the 1% floor. While conversion is stopped, earned source balances and already-settled ETH remain backed; an owner can explicitly claim the source asset. Broken source tokens can also prevent that fallback. |
| Stop/restart services | Disable `lp_conversion.enabled` and reconcile any pending transaction before switching workers/hosts. Preserve the serial keeper state, nonce, receipt anchor and scan cursor. Re-enable only with reviewed configuration and fresh simulation; do not reset the state to bypass an uncertain submission. |

The route fields above follow their Solidity structs exactly. The fixed converter
algorithm and wrapper address cannot be replaced after binding; unsupported
venues/wrappers require a reviewed successor deployment and the supported handoff.
Immediate governance can admit harmful dependencies; the accepted governance trust
and independent-review requirement remain.

## Keeper configuration and scheduling

`lp_conversion` is disabled by default. It has the same bounded settings as
`royalty_conversion`: `enabled`, `max_nfts_per_cycle` (1-32),
`max_gas_to_output_bps`, and `assets` entries containing `asset`, `route_id`,
`minimum_source_units`, `minimum_output_wei`. Asset zero is never an input;
WETH uses the zero bytes32 route. Add runtime-pinned `rewards`, `lp_converter`,
`lp_nft`, `lp_wrapper`, `oracle` entries alongside the existing keeper contracts.

The worker checks module bindings, code, route, limits and balances at one confirmed
canonical block hash. It scans a bounded NFT window, rotates currencies even on a
currency failure and sends at most one transaction through shared pending/nonce/gas
recovery. A persistent three-way priority rotates LP conversion, royalty conversion
and maintenance; fees must be economical under separate absolute and relative gas
budgets. `conversion_turn` is 0-2; each stream retains its own scan cursor. Existing
`next_first` fields are retained for state compatibility but no longer choose
conversion priority. With 1,000 NFTs and multiple source currencies, a complete scan takes many cycles; qualify conversion latency and economical batch thresholds before launch. Polling is not a promise of immediately claimable ETH. Error logs use `lp_conversion_deferred` or
`lp_conversion_uneconomic` without keys, RPC secrets or raw signer errors.

## History, replacements and qualification

`LPRewardsConverted` records source and native amounts for both reward components.
The indexer/API reports `lp_conversions` separately from `royalty_conversions`
and actual lifetime `Claimed` events. Earnings remain the original processed
LP/royalty allocations, valued at today's reviewed prices; conversion credits,
claims and imported balances are never new earnings. Reconciliation subtracts
source conversions and adds native credits before comparing current claimables.
Missing complete predecessor history remains unavailable, not zero.

Same-chain handoff exports native and source Rewards balances, both component
ledgers, fractions and indices with exact classified backing. Vault/Fees domains
skip the native settlement slot, which belongs only to Rewards. Native index and
fraction fields must be zero on import. Funding, recipient failure, abort and
prefund checks apply equally to ETH. This changes the Rewards domain inventory;
review source/successor schema compatibility, converter bindings and full backing
before sealing. It does not implement different-pair or cross-chain migration.

The named local fixture now deploys this converter, processes real allocated local
LP fees into reserve-backed test ETH, and prepares native LP-plus-royalty claims.
Its $1 mock prices and deterministic venue do not qualify Robinhood routes.
Never restart an existing user's fixture implicitly; start a separate session.

See [scoped verification](../reports/lp-eth-settlement/VERIFICATION.md),
[operator manual](OPERATOR_MANUAL.md) and [release approval](RELEASE_CHECKLIST.md).
