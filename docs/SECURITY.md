# Security model and invariants

**Status: development security-review candidate. These are intended invariants and review observations, not formally verified guarantees or funded-deployment approval.** Current build/test evidence is separate from historical reviews in [the implementation update](../reports/IMPLEMENTATION_UPDATE.md).

## Assets and authorities

The vault controls Uniswap LP NFTs and separately recorded idle principal. The fee controller holds only collected fees and segregated compounding/buyback/remote-reward budgets. The rewards contract holds funded claim liabilities. The migration receiver/vault can hold bridged principal awaiting activation.

Governance selects eligible pools, oracle sources, keepers and initial routes before sealing. After sealing, module addresses and the adapter's transport endpoint remain fixed. Existing route contents remain immutable, but new append-only route identities and future destinations can be added through the governance timelock. The canonical registry may authorize remote-only graph edges for onward hops. Governance also controls bounded pool parameters, oracle configurations and operator/pause roles through the timelock. The guardian can pause, not unpause. The keeper has no redemption entitlement.

Route onboarding is a material trust power. Review every new destination's runtime code, custody rules, proxy/administrator authorities, token mappings, and provider semantics. The timelock creates a notice period; it cannot verify remote code or prove that future custody preserves permanently locked principal. Fixed local module bindings do not remove the economic risk of migrating to an unsafe approved destination.

## Intended invariants

1. No owner/admin/keeper principal-redemption function, arbitrary vault call, delegatecall, module replacement or vault LP-NFT transfer entrypoint exists.
2. Exactly 0.05 ETH mints a dormant canonical NFT with no LP or Power. Proceeds go to its immutable constructor recipient and do not enter principal accounting. Activation keeps that NFT and requires at least $500 of actually deployed LP. Rebalancing and repeated custody imports do not remint it or add contribution Power.
3. Every idle token amount is attributed to one economic position and included in an aggregate custody ledger. Donations do not mint rights or become the next depositor's balance.
4. After liquidity placement, at least 95% of the position's validated oracle value is deployed. This is an execution-time check, not a continuous valuation guarantee.
5. Only separately collected fees enter 50/30/10/10 accounting. Deposit principal and liquidity-removal proceeds do not become distributable rewards.
6. Fees are collected before position changes and again after a same-pool balancing swap that can earn fees on an existing LP.
7. Fee allocation is partition-independent in ten-raw-unit batches; remainder is carried. Canonical migration dust is credited to the NFT. Satellite migration dust remains funded in its remote-individual budget until delivery home, without reducing accounted custody prematurely.
8. Published reward indexes are checkpointed before Power changes. Fractional entitlements and already-earned balances follow the economic NFT, not a mutable wallet identifier.
9. Each claim is funded and consumes its entitlement before token transfer. A strategy pause does not disable claims.
10. All module-originated transfers use specific amounts/recipients. Temporary ERC20/Permit2 allowances are reset. Exact sender and recipient deltas reject ordinary transfer taxes.
11. Oracle freshness, decimals, reference price, spot deviation, minimum outputs and deadlines are checked independently of keeper-supplied advice.
12. Version-2 bridge messages authenticate the configured route and origin, preserve previous custodian and canonical identity/token mappings, are consumed once per origin nonce, and are atomically backed by declared token amounts. Remote token-to-canonical identities cannot be rebound for an NFT.
13. Failed destination activation preserves attributed assets for retry. A timeout alone never authorizes a withdrawal or proves source cancellation.
14. Source-completion ACKs match frozen departure snapshots; canonical location ACKs require the next global epoch and recorded previous custodian. Accepted ACK snapshots survive later moves; historical retries cannot regress location. Revisited satellites require a strictly newer local custody epoch and a drained old position. Canonical return records location atomically during import.
15. Off-chain services are not custody authorities. Indexer records can be rebuilt; ambiguous keeper broadcasts halt resubmission.
16. Remote NFT rewards reach the canonical chain only through an authorized vault/token path. Historical paths can drain funded old budgets after principal moves, using persistent asset provenance rather than the current pool. No second NFT or duplicate source principal claim is issued.

## What this does not guarantee

No code structure guarantees original token amounts, USD value, yield, constant LP deployment, honest oracle data, permanent bridge solvency, chain availability, future token behavior, or a safe migration to any arbitrary future chain.

A malicious/compromised price feed, approved bridge, governance process, token implementation, future destination vault or Uniswap dependency can violate the economic intent without a local `withdraw()` call. Immutable custody also makes coding mistakes difficult or impossible to repair. Token/address/provider selection, destination review, and deployment verification are part of the security boundary.

The adapter defines an authenticated, funded transport boundary with an immutable endpoint; it is not a complete production bridge. Equivalent-asset migration is not arbitrary asset conversion, and the canonical NFT does not move chains. Satellite user deposits remain absent. The requested Robinhood native-ETH/Pons-hook pool and its reward source remain outside supported integration; see [pool research](ROBINHOOD_POOL.md).

Use canonical, reviewed token/feed/provider addresses. Do not permit taxed/rebasing/blacklistable/upgradeable tokens merely because a one-time transfer test passed. “ERC20-compatible” is not an economic safety certificate.

## Secrets and operations

Never paste production keys into this repository. Keeper signing is delegated to `cast` with an encrypted keystore; its password file must be private. Use a dedicated, minimally funded keeper account. RPC providers are trusted for observed chain data; confirmations and chain-ID checks are not cryptographic proofs against a malicious provider.

Do not expose simulation RPCs, transport test mocks, bootstrap privileges or deployment configuration endpoints to users. The local deployment script cannot target public-chain IDs and does not call `seal()`.
