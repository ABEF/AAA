# PoPL product specification

ZZZ Collection — Proof of Permanent Liquidity turns an NFT into transferable economic ownership of permanently locked liquidity. Users contribute ZZZ paired with WETH or USDC, subject to approved pools, token behavior, price feeds, and deposit limits.

## Holder rights

A holder owns the NFT and can transfer it. The current owner can claim funded individual fees and Power-weighted collective rewards, including balances earned before the NFT was transferred. Approved NFT operators do not acquire a direct reward-claim right.

Holders cannot redeem underlying principal. Authorized maintenance can move attributed capital between liquidity, idle custody, and approved migration destinations without creating a redemption entitlement. Permanent locking does not fix token amounts, USD value, or revenue.

## Position lifecycle

1. A canonical-chain deposit is validated, valued, balanced, and deployed into an approved Uniswap position.
2. The vault records its liquidity and attributed idle balances, and the owner receives an economic NFT.
3. Collected trading fees fund individual rewards, collective rewards, compounding, and buybacks in the 50/30/10/10 proportions.
4. Eligible keeper operations can compound or replace the underlying LP position. The economic NFT keeps its identifier.
5. NFT transfers carry economic rights to the new owner.
6. An approved one-hop migration can move custody to a configured satellite while NFT issuance and claims remain canonical.

The keeper polls every ten minutes by default. Eligibility checks, available funds, network conditions, transaction costs, and operator availability govern execution; the polling interval is not an execution guarantee.

## Proposed attributes

The PoPL NFT #444 illustration in the [README](../README.md) shows pool, associated LP value, unclaimed fees, and an Enhanced status. The monetary figures are examples. Levels, rarity, Enhanced status, and a hosted product interface are future features.

## Implementation boundary

The current adapter supports conventional ERC20/ERC20, static-fee Uniswap v4 pools without hooks. Native ETH is represented by WETH. A custom Uniswap v4 hook is proposed future work. Bridging requires an additional reviewed production transport.

Read the [economic rules](ECONOMICS.md), [component status](COMPONENT_STATUS.md), and [release checklist](RELEASE_CHECKLIST.md) before interpreting product goals as implemented guarantees.
