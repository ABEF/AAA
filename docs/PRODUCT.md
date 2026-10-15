# PoPL product specification

ZZZ Collection — Proof of Permanent Liquidity turns an NFT into transferable economic rights associated with permanently locked liquidity. A dormant NFT costs **0.05 ETH** to mint. Its owner activates it by contributing at least **$500 of actually deployed LP**, then may add more permanent LP to that same NFT.

The user-selected market is ZZZ / native ETH on Robinhood Chain, Uniswap v4 pool ID `0x6538e2c223ed70228114983afecbe5e69fe627e2fafdf367bdd6bdeff2ad391f`. Its native asset and Pons hook are unsupported by the current liquidity adapter. Pool integration and the project's source of rewards are deferred decisions; see [verified pool details](ROBINHOOD_POOL.md). Supported candidate pools currently use conventional ERC20/ERC20 assets, subject to registry, token, oracle, and deposit checks.

NFTs activated into the same approved pool hold nonredeemable internal shares in **one shared LP position**. Owner fees follow pool shares; collective rewards follow lifetime contribution Power. Maintenance and whole-pool migration never iterate over NFT holders. Deposits, compounding and market movements can change the value of a share independently of historical Power.

## Holder rights

A holder owns the NFT and can transfer it. The current owner can claim funded individual fees and Power-weighted collective rewards, including balances earned before the NFT was transferred. Approved NFT operators do not acquire a direct reward-claim right.

Holders cannot redeem underlying principal. Authorized maintenance can move attributed capital between liquidity, idle custody, and approved migration destinations without creating a redemption entitlement. Permanent locking does not fix token amounts, USD value, or revenue.

## Position lifecycle

1. On the canonical chain, `mintDormant()` requires exactly `0.05 ether` and issues one dormant NFT with no LP, no contribution Power, and no earned LP fees. Minting changes NFT supply only.
2. Mint proceeds are forwarded to the immutable recipient selected in the vault constructor. They are separate from LP principal and reward budgets. If issuance or forwarding fails, the mint reverts atomically.
3. Only the NFT's current owner can call `activate(...)`. The vault validates, values, balances, and deploys the contribution into an approved position. At least `500e18` USD of LP must actually be deployed, excluding idle assets; input value alone is insufficient. Activation retains the existing NFT identifier and does not mint another NFT.
4. The owner of an active home-chain position can use `increase(...)` to add more permanently locked LP to the same NFT. Activation and increases raise associated capital; the mint payment does not. Satellite holder top-ups are not implemented.
5. For supported fee-earning pools, measured collected fees enter the candidate's 50/30/10/10 allocation. This is not a claim that the selected Robinhood pool grants those fees to PoPL liquidity providers; its revenue integration remains undecided.
6. Eligible keeper operations can compound or replace the underlying LP position. NFT transfers carry rights to the new owner while principal remains non-redeemable.
7. Timelocked governance can onboard additional approved routes after sealing, and attributed custody can make repeated hops between compatible vaults, including returning home. The economic NFT and claims remain on the canonical chain; an import neither remints the NFT nor adds contribution Power.

The keeper discovers shared buckets automatically and polls every ten minutes by default. New contributions require home custody, no scheduled migration, and complete funding of any earlier remote owner/collective rewards. Eligibility checks, available funds, network conditions, transaction costs, and operator availability govern execution; the polling interval is not an execution guarantee.

## Proposed attributes

The PoPL NFT #444 illustration in the [README](../README.md) shows pool, associated LP value, unclaimed fees, and an Enhanced status. The monetary figures are examples. Levels, rarity, Enhanced status, and a hosted product interface are future features.

## Implementation boundary

The paid dormant mint and separate owner activation are implemented in the development candidate. They are not deployed product guarantees. The current adapter supports conventional ERC20/ERC20, static-fee Uniswap v4 pools without hooks. It accepts WETH rather than native ETH and cannot use the selected native ETH / ZZZ Pons pool without further integration work. A reward source or revenue-sharing mechanism for that pool has not been selected.

The development candidate now implements the requested route-onboarding and repeated-custody migration redesign. Individual route identities remain append-only, while new routes require the governance timelock after sealing; module bindings stay fixed. Each move also has an additional two-day migration delay. Version-2 messages preserve canonical identity and token provenance across hops, with separate source-completion and canonical-location acknowledgements.

This is not a deployed multichain service or a general proxy upgrade. Migration supports equivalent assets at identical decimals and nominal units, rather than arbitrary asset conversion or moving the NFT to another chain. Satellite user deposits and cross-chain holder top-ups remain absent. A reviewed production transport and compatible destination deployments are still required. Governance must review new destination code, tokens, and provider semantics: a timelock gives notice but cannot prove that future custody preserves permanent-principal intent. See [current implementation evidence](../reports/IMPLEMENTATION_UPDATE.md).

Read the [economic rules](ECONOMICS.md), [component status](COMPONENT_STATUS.md), and [release checklist](RELEASE_CHECKLIST.md) before interpreting product goals as implemented guarantees.
