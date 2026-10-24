# New ETH / ZZZ pool selection - 2026-10-24

## Current user decision

The user will create a new Uniswap ETH/ZZZ pool instead of using the existing
Pons venue. No pool creation, funding, admission, deployment or transaction is
authorized or claimed by this record. The former documented integration target
was the native-ETH/ZZZ Pons pool; references to that target are historical research,
not the selected new pool. A USDG market may remain a separate activation route.

## Required details - pending

- Confirm the chain and Uniswap version; do not infer them from the old market.
- Confirm native ETH versus WETH as the physical currency.
- The user supplied a target displayed breakdown: 0.25% LP, 0.05% Uniswap
  protocol, 0.30% effective fee. Record this as intent, not an observed new-pool
  setting. Confirm the version-specific calculation, actual protocol controller
  and enabled policy; the creator does not automatically control protocol fees.
- Confirm static/dynamic policy, tick spacing and any hook (including explicitly
  no hook). Version and hook choice remain undecided.
- Once created, record the exact PoolKey/pool ID or applicable pool address,
  initialization transaction, deployed dependency identities and initial price.
- Define initial seed liquidity and who provides it. Existing market volume,
  liquidity, measurements and Pons creator terms do not carry to the new pool.

The version/hook decision is pending. Recommendation, not user approval: v4
without a custom hook matches the current v4 custody/execution architecture and
native ETH requirement. The existing Vault/keeper/reward ledgers already provide
LP management and NFT revenue allocation; those functions do not require a hook.
New native hookless admission still needs implementation and qualification.

Official references checked 2026-10-24:
- [v4 versus v3](https://developers.uniswap.org/docs/protocols/v4/concepts/v4-vs-v3): native ETH support and different position/settlement interfaces.
- [Optional hooks](https://developers.uniswap.org/docs/protocols/v4/concepts/hooks): custom lifecycle behavior; hook identity cannot be changed on an existing pool.
- [Fee structures](https://developers.uniswap.org/docs/get-started/concepts/fees): the displayed 0.25%/0.05% split is documented for fee-enabled 0.30% v3 pools, not a universal v4 configuration.
- [v4 protocol-fee implementation](https://github.com/Uniswap/v4-core/blob/main/src/libraries/ProtocolFeeLibrary.sol): input protocol fee and LP fee compose sequentially; do not blindly sum or equate v3 and v4 fee fields.

Confirm the actual new pool policy and chain before implementation. A reported
Uniswap protocol fee goes to Uniswap's protocol mechanism, not the PoPL governor
or NFT royalty address. PoPL's 80/10/5/5 applies to its actually collected LP fees,
after venue-level deductions; never to all trading volume or another LP's income.

## Revenue and retained accounting

For a normal fee-charging pool, PoPL receives venue fees attributable to its own
active LP position. The existing receipt-backed 80/10/5/5 allocation remains.
NFT royalties are independent and unchanged. Neither liquidity provision nor a
new pool guarantees trading volume, active-range earnings or future revenue.

The prior Pons creator-payment agreement/measurement work is historical and
conditional; it is not automatically a launch dependency of a standard new pool.
If a new custom hook or external sharing agreement is chosen, explicitly qualify
that separate funding path. Do not retain an assumed Pons entitlement.

Collected venue fees may arrive in both pair currencies. Existing LP-holder ETH
settlement still requires the reviewed converter, routes, prices and keeper;
a native-ETH pair does not by itself make every reward an ETH-only credit.

## Actual code compatibility

`PoolRegistry.configure` admits the supported hookless ERC20/ERC20 path; it does
not admit native ETH. Current `configureNative` is pinned to the old Robinhood
native/Pons key and dependency boundary. Therefore a new native ETH/ZZZ pool is
not supported by merely substituting a pool ID. It needs narrowly scoped reviewed
admission/settlement support before sealing, plus updated inventory and evidence.
A different Uniswap version may require a separately reviewed adapter.

Preserve existing on-chain share accounting, exact contribution approvals, $100
activation/$5 growth floors, 1% contribution-loss limit, 3% ordinary maintenance
limit, one contribution pool at a time and current-holder reward rights. Do not
loosen these guards to force an unsupported venue through admission.

## Qualification work

1. Confirm the missing venue decisions and actual created-pool identity.
2. Implement only the required compatibility changes; qualify native settlement,
   fee collection, close/rebalance, adverse callbacks, donations and exact approvals.
3. Review fresh independent ZZZ pricing, asset conversion routes, wrapper policy,
   loss/gas economics, starting price and liquidity depth for this pool.
4. Update deployment inventory, operating procedures and service bindings.
5. Run focused local/fork checks for changed behavior and an isolated Anvil journey.
   Do not reset the existing 8902 fixture or reuse old-pool evidence as new-pool proof.

No contract behavior or live website/server configuration changes in this decision
record. Public signing stays disabled, monitoring stays paused, and production
remains NOT APPROVED. [Sole Todo](../TODO.md#task-pons-qualification).
