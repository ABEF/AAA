# Security model and invariants

**Status: uncompiled review candidate. These are intended invariants and review observations, not formally verified guarantees.**

## Assets and authorities

The vault controls Uniswap LP NFTs and separately recorded idle principal. The fee controller holds only collected fees and segregated compounding/buyback/remote-reward budgets. The rewards contract holds funded claim liabilities. The migration receiver/vault can hold bridged principal awaiting activation.

Governance selects eligible pools, oracle sources, keepers and routes before sealing. After sealing, module addresses and route identities are fixed. Governance can update bounded pool parameters, oracle configurations and operator/pause roles through the timelock. Those remaining configuration powers can still create economic risk. The guardian can pause, not unpause. The keeper has no redemption entitlement.

## Intended invariants

1. No owner/admin/keeper principal-redemption function, arbitrary vault call, delegatecall, module replacement or vault LP-NFT transfer entrypoint exists.
2. The canonical NFT is never replaced by range rebalancing; LP identity can change. Satellite deposits cannot mint another collection.
3. Every idle token amount is attributed to one economic position and included in an aggregate custody ledger. Donations do not mint rights or become the next depositor's balance.
4. After liquidity placement, at least 95% of the position's validated oracle value is deployed. This is an execution-time check, not a continuous valuation guarantee.
5. Only separately collected fees enter 50/30/10/10 accounting. Deposit principal and liquidity-removal proceeds do not become distributable rewards.
6. Fees are collected before position changes and again after a same-pool balancing swap that can earn fees on an existing LP.
7. Fee allocation is partition-independent in ten-raw-unit batches; remainder is carried. Final sub-ten-unit migration dust is explicitly credited to the canonical NFT.
8. Published reward indexes are checkpointed before Power changes. Fractional entitlements and already-earned balances follow the economic NFT, not a mutable wallet identifier.
9. Each claim is funded and consumes its entitlement before token transfer. A strategy pause does not disable claims.
10. All module-originated transfers use specific amounts/recipients. Temporary ERC20/Permit2 allowances are reset. Exact sender and recipient deltas reject ordinary transfer taxes.
11. Oracle freshness, decimals, reference price, spot deviation, minimum outputs and deadlines are checked independently of keeper-supplied advice.
12. Bridge messages authenticate a configured route and origin, are consumed once per origin nonce, and are atomically backed by the declared token amounts.
13. Failed destination activation preserves attributed assets for retry. A timeout alone never authorizes a withdrawal or proves source cancellation.
14. Remote NFT rewards are credited on the canonical chain only through an authorized remote-vault/token path. No second NFT or duplicate source principal claim is issued.
15. Off-chain services are not custody authorities. Indexer records can be rebuilt; ambiguous keeper broadcasts halt resubmission.

## What this does not guarantee

No code structure guarantees original token amounts, USD value, yield, constant LP deployment, honest oracle data, permanent bridge solvency, chain availability, future token behavior, or a safe migration to any arbitrary future chain.

A malicious/compromised price feed, approved bridge, governance process, token implementation or Uniswap dependency can violate the economic intent without a literal `withdraw()` call. Immutable custody also makes coding mistakes difficult or impossible to repair. Token/address/provider selection and deployment verification are part of the security boundary.

Use canonical, reviewed token/feed/provider addresses. Do not permit taxed/rebasing/blacklistable/upgradeable tokens merely because a one-time transfer test passed. “ERC20-compatible” is not an economic safety certificate.

## Secrets and operations

Never paste production keys into this repository. Keeper signing is delegated to `cast` with an encrypted keystore; its password file must be private. Use a dedicated, minimally funded keeper account. RPC providers are trusted for observed chain data; confirmations and chain-ID checks are not cryptographic proofs against a malicious provider.

Do not expose simulation RPCs, transport test mocks, bootstrap privileges or deployment configuration endpoints to users. The local deployment script cannot target public-chain IDs and does not call `seal()`.
