# Production mint venue

User decision, 2026-10-22: **production minting is intended for OpenSea**. The
website Mint page demonstrates the product. Local Anvil minting remains an
integration tool, not the production launch flow.

The production website profile refuses mint preparation and presents an inactive
OpenSea action until its exact collection URL/integration is qualified. Activation,
LP growth, ownership reads and claims remain website responsibilities. No public
signer has been enabled.

This decision does not establish OpenSea compatibility. Before sealing, verify
the intended chain and mint-product support, required interfaces/caller path,
collection administration and exact URL. A listing or secondary sale does not
prove primary-mint compatibility. Do not substitute a different NFT collection
for the canonical PoPL identity and ledgers.

The selected integration must preserve 1,000 supply, 0.05 ETH price/recipient,
fixed draw and rarity quotas, original randomness, mint pause/canonical lifecycle,
atomic failure and zero LP at mint. Verify the NFT recipient even if an intermediary
calls the contracts. Review any required adapter/contract change before sealing;
then rehearse a supported marketplace mint and verify recipient, proceeds, supply,
events and reveal. Direct local `Vault.mintDormant()` tests do not close this gate.

Operators use existing `NFT.setMintPaused(true/false)` controls for incidents and
restart. Hiding a website button cannot pause external callers. See the
[operator manual](OPERATOR_MANUAL.md) for provider outages and replacement rules.
Publish only the verified collection URL after chain/address checks.

Task status: [OpenSea primary mint](../TODO.md#task-opensea-mint).
