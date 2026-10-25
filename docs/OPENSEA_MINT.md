# Production mint venue

## Approved buyer price and unimplemented mint path - 2026-10-25

Buyer pays **0.05 ETH total mint price**. Any actual primary-mint platform fee is
deducted from that amount; the immutable proceeds recipient gets the remainder.
Network gas stays separate. No particular platform percentage is assumed.

This is the required OpenSea integration behavior. The current direct Vault mint
still forwards the entire0.05ETH and mints to msg.sender. It has no mintSeaDrop
interface, recipient-aware payment path or OpenSea primary-drop approval. These
are pre-seal implementation/acceptance requirements, not configuration claims.
See [the exact integration requirements](MINT_INTEGRATION_QUALIFICATION.md).

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

The selected integration must preserve 1,000 supply and0.05ETH gross buyer price with actual platform fees
deducted before net recipient proceeds,
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

## Interface research - 2026-10-23

OpenSea's [chain guide](https://support.opensea.io/en/articles/8867082-which-blockchains-are-compatible-with-opensea)
includes Robinhood, while its [primary-drop documentation](https://docs.opensea.io/docs/seadrop)
describes SeaDrop-compatible NFT methods. These establish neither a supported
Robinhood primary-drop product nor the required deployment pins. Verify those
exact details before implementation; do not infer them from general chain support.

Current source has no SeaDrop interface. `Vault.mintDormant()` charges 0.05 ETH
and calls `NFT.mint(msg.sender, id)`; NFT minting admits only Vault. An intermediary
using that path unchanged would own the NFT. Any integration must explicitly
preserve the buyer recipient, proceeds/fee handling and original NFT/accounting
identity. No adapter or mint permission was added by this research.
