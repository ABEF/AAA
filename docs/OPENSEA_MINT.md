# OpenSea primary mint: fresh source profile

This is a source candidate, not an approved or deployed OpenSea collection.
The website Mint page remains demonstrative. Existing sites, Anvil deployments,
wallet signer and journals retain their original profiles.

## Sale rules

| Phase | Initial allocation | Buyer payment | Unused supply |
| --- | --- | --- | --- |
| Team | 20 NFTs | Free; gas separate | Remains reserved |
| Allowlist | 500 NFTs; one per listed address | Governed mint price, initially0.05ETH total | Released to public FCFS |
| Public FCFS | Initially480 NFTs | Same governed mint price | Cannot consume unminted team reservations |

The total collection cap remains1,000. Governance may review future allocations,
price, wallet/batch limits and sequential sale windows. Counts never reset;
allocations cannot be reduced below issued NFTs or reserve already-sold supply.
Set `releaseUnusedTeamToPublic=false` for the selected launch policy. Changing
allocations or proof terms requires reviewing and publishing the matching proofs.

Team and allowlist addresses are distinct in the maintained proof builder.
SeaDrop's wallet limits count **lifetime original mints across all phases**, not
current balances or one allowance per phase. Transferring an NFT does not restore
allowance. Choose the public cumulative wallet limit explicitly, including any
earlier team/allowlist mints; it is not a per-human or Sybil-resistance guarantee.

All three windows are inclusive and strictly disjoint: team, then allowlist,
then public. A reserved team NFT is not publicly sold after its team window;
it also does not become mintable outside a valid team window. Reopening or
rescheduling must respect the still-open official sale end. The existing mint-end
rule forbids reopening after that final end has passed. Under-subscription is
valid: neither royalties nor protocol operation wait for a1,000-NFT sellout.

The official final public end must match `NFT.royaltyRewards().mintEnd()`.
The **one-hour** royalty activation window starts after that end. Free or paid
minting creates a dormant NFT with zero LP and no royalty entitlement; activation
still follows the separate contribution policy.

## Actual platform boundary

The [pinned official deployment registry](https://github.com/ProjectOpenSea/seadrop/blob/d368f55f609a7f4b2245f89ff49c1a933fbeff83/docs/Deployments.md)
lists Robinhood Chain4663 as a standard SeaDrop V1 drop network. The independently
read runtime at `0x00005EA00Ac477B1030CE78506496e8C2dE24bf5` matches the
[verified deployment](https://robinhoodchain.blockscout.com/address/0x00005EA00Ac477B1030CE78506496e8C2dE24bf5?tab=contract):
21,081bytes, Keccak
`0x53e4b9339cf624803c9a7d0195576cca5b917920813508d86b3eb93dcbabeb5c`.
The verification record binds the observation block and original responses.

Protocol compatibility is separate from OpenSea accepting this custom PoPL
collection into its primary-drop/API product. No actual collection onboarding,
platform fee, fee recipient, payer/router permissions, provider funding or live
wallet execution is approved. Do not substitute a generic secondary-sale address
or fee guide for those exact launch terms. The
[custom-contract guidance](https://docs.opensea.io/docs/deploying-a-seadrop-compatible-contract)
does not make an arbitrary custom contract an accepted Studio collection.

The reviewed path is:

1. The buyer calls the pinned SeaDrop `mintAllowList` or `mintPublic` with exact
   gross ETH. Team proofs specify zero; paid proofs/public settings use the same
   reviewed governed price. Network gas is additional.
2. SeaDrop checks proof/window/payment, recipient lifetime allowance, fees and
   approved payer, then calls `NFT.mintSeaDrop(minter,quantity)` with **zero ETH**.
3. The fixed `ZZZSeaDropMint` reserves the complete batch's lifetime/phase counts
   before receiver callbacks. The Vault records canonical hashed IDs; the NFT
   requests one original two-word VRF result per NFT and safely mints to the buyer.
   Final policy/runtime/end checks must still match.
4. SeaDrop pays its actual fee and the creator's net proceeds. Failure anywhere
   reverts the complete mint, payment and request bookkeeping. The NFT/helper
   never holds the sale proceeds or receives LP custody authority.

The NFT's checks finish before SeaDrop's fee/creator callbacks. SeaDrop caches
the current payout address and payment amounts before those transfers; subsequent
authorized configuration changes affect future operations. There is no invented
post-payment NFT callback or persistent settlement lock. This differs from the
historical direct-Vault review's post-payee fingerprint boundary.

SeaDrop's buyer calldata also does not carry PoPL's custom expected-policy hash.
It enforces the actual gross payment, but a governance change before inclusion
can change the current fee/net/payee while leaving that gross price unchanged.
The helper reviews current configuration within the NFT callback; it does not
claim to freeze earlier OpenSea UI settings. Pause and reconcile before live
configuration changes, and qualify the actual platform review experience.

`Vault.DormantMinted.mintPrice` records what the **Vault received**: zero on the
SeaDrop path, including paid mints. Use authenticated `SeaDropMint` receipts and
balance deltas for gross/platform/net revenue; never label that zero as a free
primary mint or treat mint proceeds as LP/royalty income.

## Deployment and compatibility

The fresh graph uses canonical **V10**, mint integration2/helper1 and inventory17.
V9/16 and source9 tools remain explicit historical profiles; no runtime, receipt
or journal is relabeled. Fresh deployment order includes:

1. Deploy/bind Access and ProtocolPolicy as usual.
2. Separately deploy `ZZZNFTMetadata(controller)`; deploy
   `ZZZNFT(controller,baseURI,renderer)`. The constructor validates its fixed
   renderer/controller. Predeployment avoids embedding another large creation
   object inside the NFT's initcode.
3. Deploy `ZZZSeaDropMint(controller,NFT,SeaDrop,expectedRuntimeHash)` and have
   bootstrap call `NFT.setSeaDropMint(helper)` once before seal and any mint.
4. Configure the reviewed plan, NFT-keyed SeaDrop settings, actual royalties end
   and all ordinary protocol modules. Authenticate the whole final inventory.

Once bound, direct paid `Vault.mintDormant` attempts cannot bypass the primary
sale: the NFT's direct mint rejects them. The unbound direct path exists only as
an explicit local test configuration, not approved OpenSea production setup.
The SeaDrop implementation/helper cannot be rotated after seal. Signed and
token-gated minting, changing max supply or changing the allowed singleton through
`updateAllowedSeaDrop` are unsupported and revert.

V10 records both **current owner** and **original recipient/phase**. Imports
rebuild lifetime counters from original recipients, never current owners. Peers
must match the mint configuration and implementation policy; old V9 NFT records
are rejected. The fixed NFT codec also binds the helper/runtime/configuration
into the deployment commitment. Ordinary LP accounting and reward economics are
unchanged. Actual complete handoff, service and marketplace cutover qualification
must match this exact release.

## Backend consumers

The read/claim API and lineage verifier support explicit
`mint_integration_version:2` on accounting7 with pinned `seadrop_mint` and
`seadrop` roles. They authenticate the NFT/helper/controller/runtime at the same
canonical block and select V10. Omission remains mint1/V9, including on each
lineage peer; never inherit the successor setting into an older peer.
Direct mint preparation returns Use OpenSea before RPC or simulation. Protocol
status reports the OpenSea channel with stage availability unknown until actual
proof/platform eligibility is verified. Mutable sale-price or phase drift does
not disable unrelated LP/reward claims. See [API](FRONTEND_API.md),
[transactions](FRONTEND_TRANSACTIONS.md) and [lineage](FRONTEND_LINEAGE.md).
Source9 website, live services, configs and signer are unchanged.

## Prepare the plan and proofs offline

From the repository root:

```text
python scripts/prepare-opensea-drop.py profile
python scripts/prepare-opensea-drop.py prepare REQUEST.json --output NEW_MANIFEST.json
python scripts/prepare-opensea-drop.py check NEW_MANIFEST.json --output NEW_CHECK.json
```

Use exact decimal strings for ABI integers and fresh output names. Supply the
actual NFT/SeaDrop/payee, explicit fee recipient/BPS, cumulative public wallet
limit, batch limit, team quantities, allowlist addresses, windows and payer list.
Include reviewed source hashes and review-notes hash. The builder binds the
complete Solidity/dependency/tool closure and emits the combined Merkle root,
each proof and complete `configure_arguments`.

The proof leaf is **one** `keccak256(abi.encode(minter,MintParams))`, with sorted
Merkle pairs. Default double-hashed StandardMerkleTree leaves are incompatible.
The combined root includes only free-team and same-price allowlist leaves in
their proper windows. The helper independently caps the allowlist allocation;
SeaDrop's own stage ceiling is cumulative collection supply, not500 independent
allowlist mints. Public supply excludes unused reserved team slots.

The artifact is not a live snapshot, simulation, signature, transaction or
OpenSea acceptance. Its review hash is an audit fingerprint, not an on-chain proof
of opaque root contents. Initial roots and historically reused roots still need
review. `configure` additionally takes the **expected current mint price** so a
price change between preparation and execution cannot silently rebind old proofs.

## Governance calls and recovery

| Call | Required input | Effect |
| --- | --- | --- |
| `Mint.configure(config,expectedMintPrice,reviewHash)` | Complete15-field plan, exact current price in wei, nonzero reviewed hash | Review future sale configuration |
| `NFT.updatePublicDrop(SeaDrop,publicDrop)` | `Mint.expectedPublicDrop()` tuple, reviewed singleton | Match public price/window/fee |
| `NFT.updateAllowList(SeaDrop,data)` | Manifest root, actual proof-publication URI metadata | Publish team/allowlist eligibility |
| `NFT.updateCreatorPayoutAddress(SeaDrop,payee)` | Current accepted Policy recipient | Select creator net recipient |
| `NFT.updateAllowedFeeRecipient(SeaDrop,recipient,allowed)` | Actual platform recipient, boolean | Match singleton approved recipient |
| `NFT.updatePayer(SeaDrop,payer,allowed)` | Reviewed payer address, boolean | Match exact reviewed payer set |
| `NFT.updateDropURI(SeaDrop,uri)` | Actual OpenSea drop metadata URI | Update drop metadata |
| `NFT.setMintEnd(publicEnd)` | Reviewed official final end | Match one-hour royalty launch |
| `NFT.setMintPaused(true/false)` | Boolean | Stop/resume new mint requests |

These configuration calls use governance after seal, bootstrap before seal.
They do not require a keeper restart and never transfer LP or sale proceeds.
Helper-only callbacks are not operator entry points. The maintained operator
tables expand every tuple and distinguish management, reads and module callbacks.

Partial setup or drift intentionally blocks minting until public settings, root,
payee, singleton fee recipient, exact bounded payer set, price and final end agree.
Before changing a live sale, pause new mints, reconcile submitted transactions,
review/publish new proofs where terms changed, apply matching settings, simulate
the exact platform transaction and then deliberately unpause. Changing only the
Policy price does not update an existing proof root. A completed transaction must
never be resent because a later read failed.

New settings cannot repair a failed original VRF request or reset minted counts.
Follow [original-result recovery](MINT_INTEGRATION_QUALIFICATION.md) for provider
outages. LP claims, royalties, transfers and independent maintenance keep their
own existing guards. No public deployment, signing or service change is
authorized by this procedure.
