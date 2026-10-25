# VRF and OpenSea primary mint compatibility - 25 October 2026

This is a dated capability investigation, not a provider selection, independent
audit, verified cryptographic proof replay, marketplace approval or deployment.
No key, signature, submitted transaction or service change was used.

## Actual implementation boundary

The current PoPL Vault takes exactly 0.05 ETH, issues its canonical token identity
to `msg.sender`, records issuance and forwards the complete payment to the
immutable mint-proceeds recipient. Only Vault can call NFT.mint. NFT issues one
authenticated subscription-style request for two words, stores the original
request identity and finalizes revealed traits strictly in mint order. Its
one-time provider configuration rejects zero lanes, uses 3-200 confirmations
and 200,000-10,000,000 callback gas. Economic activation requires a revealed NFT.
No mint-to forwarding, public burn, SeaDrop interface or administrator reroll is
implemented. These facts were checked against the current source, not inferred
from a collection logo, chain compatibility page or mock successful transaction.

## Current randomness candidates

| Candidate | Concrete compatibility and security consequence |
| --- | --- |
| Chainlink VRF v2.5 | Its current supported-network catalog has no Robinhood entry. An address from another chain cannot qualify this deployment. |
| RH-VRF | Its documentation specifies native payment and the current-key sentinel `keyHash=0`; that conflicts with PoPL's fixed nonzero lane. It describes same-result callback retry, but a request can become permanently unfulfillable after refund. PoPL has no replacement draw. Source/proof/key/admin review is still missing; the public operator monitor currently has no configured status host. |
| D20DAO | The documented Robinhood API differs from subscription v2.5. Its published security model includes owner-controlled UUPS upgrades, operator liveness and a 60-second refund deadline. Delivery/refund/retry semantics need exact original-request review. A proof service can be cryptographically sound while its API, expiry or authority model remains unsuitable for this NFT. |

References: [Chainlink networks](https://docs.chain.link/vrf/v2-5/supported-networks),
[RH-VRF integration](https://rh-vrf.com/docs),
[RH-VRF refund FAQ](https://rh-vrf.com/),
[RH-VRF operator monitor](https://rh-vrf.com/operators),
[D20DAO security model](https://d20dao.org/docs/security).

A fixed adapter could translate a separately approved provider API without
changing the prepared artwork draw, but it would be new trusted code and must
preserve original request association, two words, callback authentication and
same-result recovery. No adapter is implemented or selected here. A refund
does not supply missing randomness, reveal the NFT, refund the NFT's mint price
or authorize a reroll. A permanently unanswered first draw blocks later reveals,
activation of those NFTs and collection-contract replacement; ordinary LP pool
maintenance/movement does not depend on these draws.

Required provider evidence must include complete source and deployment/admin
bindings, positive and corrupted-proof replay, exact request ABI and cost,
subscription funding/authorization, actual two-word fulfillment, worst-case gas,
failed-callback recovery delivering the same original words and final outcome
after an unserved-request deadline. There is no honest production pass yet.

## OpenSea requires a distinct primary-mint integration

OpenSea's mint endpoint documents ERC-721 SeaDrop V1 drops. The source protocol
calls the collection's nonpayable `mintSeaDrop(minter,quantity)` and subsequently
splits the transaction payment between platform and creator. Its quantity checks
read `getMintStats`. This is incompatible with forwarding an unpaid call to
Vault.mintDormant: Vault expects the whole 0.05 ETH and mints to its caller.
Forwarding a paid call instead can charge twice or mint to the integration.

The integration must preserve canonical PoPL token IDs and per-token economic
records. Copying the current ERC721SeaDrop template wholesale would introduce
different issuance/ID conventions and its public `burn(tokenId)` behavior.
Neither is an authorized replacement for PoPL. OpenSea's general chain support
and a secondary NFT listing do not qualify a custom primary drop.

References: [mint API](https://docs.opensea.io/reference/build_drop_mint_transaction),
[custom contract guidance](https://docs.opensea.io/docs/deploying-a-seadrop-compatible-contract),
[SeaDrop interface](https://raw.githubusercontent.com/ProjectOpenSea/seadrop/main/src/interfaces/INonFungibleSeaDropToken.sol),
[payment and mint implementation](https://raw.githubusercontent.com/ProjectOpenSea/seadrop/main/src/SeaDrop.sol),
[ERC721SeaDrop template](https://raw.githubusercontent.com/ProjectOpenSea/seadrop/main/src/ERC721SeaDrop.sol).

The user selected **0.05 ETH as the buyer's gross mint price**; the mint recipient
receives the remainder after the actual OpenSea platform fee, with gas separate.
The actual fee and supported drop product remain unverified. This is an explicit
integration requirement; current Vault direct mint still forwards all 0.05 ETH
and no SeaDrop integration is implemented. A subsequent design needs exact native
payment conservation; a fixed authorized mint caller/recipient path; one canonical
record and one VRF request per NFT; bounded batch gas; pause/lifecycle/reentrancy
controls; supply/receiver-failure rollback; immutable royalty receiver; and actual
OpenSea end-to-end acceptance. Website primary mint remains demonstrative and
public signing remains disabled.

## Dated on-chain observations

The separate [observation](observation.json) records 16 successful read checks
against the documented public Pinax endpoint, with genesis and a canonical
block-hash recheck. Block 97,232,131 has hash
`0x6c51c63c869220412a0aa04b8ab880a494d2f92cce3897c84a906a857614f25b`.
The three documented RH-VRF addresses have nonempty runtime, as does OpenSea's
commonly documented SeaDrop address. Exact byte counts, hashes and EIP-1967
implementation/admin-slot reads are retained. Empty standard proxy slots do
not establish immutability or absence of other authorities. One provider's
bytecode read does not establish source equivalence, proof verification,
administrator safety, OpenSea registration, chain finality or service uptime.

The first sandbox transport attempt failed before obtaining a reference block;
the explicitly authorized network-capable run succeeded. No failure was treated
as absence of a contract or a successful qualification. Blockscout's source API
could not be accessed by the research tool, so RH-VRF source verification remains
explicitly incomplete. No authenticated OpenSea API key or drop slug was used.
