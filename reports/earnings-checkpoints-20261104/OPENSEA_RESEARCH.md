# OpenSea primary mint: compatibility investigation

Reviewed November5,2026. Read-only official documentation/source inspection;
no target-chain probe, contract change, mint authority or marketplace approval.
Mutable upstream main/documentation must be pinned and rechecked before release.

## Established versus still unknown

OpenSea lists Robinhood Chain among supported marketplaces. That is not proof
of support for this custom collection's primary drop.
[Official chain guide](https://support.opensea.io/en/articles/8867082-which-blockchains-are-compatible-with-opensea).

The inspected SeaDrop deployment table does not list Robinhood. This is absence
of deployment evidence in that table, not proof that no deployment exists.
Do not reuse a familiar deterministic address without actual chain/runtime and
product confirmation. [Official repository](https://github.com/ProjectOpenSea/seadrop#deployments).

OpenSea's generic drop-settings guide currently states a10% primary platform fee.
The exact Robinhood/product terms are not verified or selected here. Preserve
the user's gross buyer-price rule(default0.05ETH), with actual platform fee
deducted before net proceeds and network gas separate. Primary platform charges
are separate from the NFT's5% secondary-sale royalty request.
[Official drop settings](https://docs.opensea.io/docs/part-4-edit-drop-settings).

## Actual code mismatch and required design

| Reviewed boundary | PoPL consequence |
| --- | --- |
| SeaDrop calls `mintSeaDrop(minter,quantity)` on the NFT contract. Its `getMintStats(minter)` uses minted-by-wallet, total supply and maximum supply; stats must be committed before receiver callbacks. | Current ZZZNFT has neither interface and accepts issuance only from Vault. Current wallet balance is not a lifetime mint counter. A separate wrapper NFT would change canonical identity and is unsuitable. [Official interface](https://github.com/ProjectOpenSea/seadrop/blob/main/src/interfaces/INonFungibleSeaDropToken.sol). |
| SeaDrop validates payment, mints, then splits its received ETH between creator and fee recipient. | Current payable Vault direct mint charges the full price, mints to msg.sender and forwards all proceeds. Routing unchanged through an intermediary gives wrong ownership/payment behavior; do not charge twice. The new path needs authenticated recipient-aware issuance and conserved marketplace payment semantics. [Official execution source](https://github.com/ProjectOpenSea/seadrop/blob/main/src/SeaDrop.sol). |
| PoPL's Vault and NFT already use reentrancy guards; NFT mint requests the original two-word VRF draw before safeMint. | A naïve NFT→Vault→NFT mint wrapper can collide with those guards. Preserve one canonical sequence/ID, one original draw, supply/ordinal accounting, mint-only pause, terminal/canonical locks, receiver rollback and pre/post policy validation. Review the complete call graph rather than adding a broad external minter. |
| Future PoPL price/payee/VRF policies remain governed. | A qualified marketplace path must agree with the captured PoPL sale/VRF terms, actual configured fee recipient and payout address. A price/recipient/runtime change must not revive a stale review. |

## Concrete next dependency and work

First obtain OpenSea's confirmation of the supported Robinhood primary-drop
product and its exact verified SeaDrop implementation/configuration/caller path.
Then design and implement the narrowly authenticated interface on the existing
canonical NFT/Vault graph, including accurate wallet statistics and bounded
quantity. Do not substitute ERC721A/sequential IDs or introduce unrelated mint,
burn, upgrade or custody authority merely to inherit a template.

Verify buyer/payment/receiver/VRF/callback/pause/last-supply cases locally before
any separately authorized real marketplace rehearsal. A generic primary-drop
guide, secondary listing or ABI presence does not close this gate. The production
inventory stays blocked; public website minting remains demonstrative.

Current source references: [Vault](../../src/ZZZVault.sol),
[NFT](../../src/ZZZNFT.sol), [issuance validation](../../src/ZZZVaultCanonical.sol),
[owning task](../../TODO.md#task-opensea-mint).
