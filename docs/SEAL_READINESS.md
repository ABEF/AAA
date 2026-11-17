# Irreversible setup and sealing

Use this alongside the [operator manual](OPERATOR_MANUAL.md),
[deployment preparation](DEPLOYMENT_PREPARATION.md) and
[complete source inventory](../reports/test-seal-deep-review-20261117/SEAL_INVENTORY.json).
This guide explains irreversible boundaries, not a separate Todo or permission
to deploy or seal.

## OpenSea still needs the NFT's metadata

The selected primary mint is **OpenSea → pinned SeaDrop → PoPL NFT/Vault**.
SeaDrop handles the reviewed primary-sale payment/proof path. Our ERC-721 still
issues the NFTs, records their permanent rights, requests their draw and returns
their metadata. OpenSea reads `NFT.tokenURI(id)`; that metadata points to the
artwork root and shows traits and lifecycle. Minting on OpenSea therefore does
not remove our artwork-publication requirement.
[OpenSea metadata standard](https://docs.opensea.io/docs/metadata-standards),
[custom SeaDrop guidance](https://docs.opensea.io/docs/deploying-a-seadrop-compatible-contract).

A configured root can still point to missing or wrong content. The contracts
reject an empty sealed root and bare `ipfs://` / `ar://` identifiers; they cannot
prove content completeness, immutable publication, marketplace retrieval or
availability. Verify every catalogued evolution path using the
[artwork publication procedure](ARTWORK_PUBLICATION.md). Metadata update events
notify indexers; they do not guarantee an immediate OpenSea cache refresh.

Requalify the exact chosen root's length and cold `tokenURI` read cost. The older
41-byte controlled fixture is not a universal budget for every URI, provider or
marketplace. None of these metadata checks creates LP or changes financial rights.

## Review the whole dependency graph before any irreversible write

The unsigned pre-seal planner includes `seal_boundary_review`:

- All **39 construction instances**, their exact ABI input names/types and
  assigned values, including internally created helpers. Inert code parts use
  byte-length/hash commitments; their exact bytes stay in the authenticated
  construction plan rather than being duplicated in this review.
- Explicit reads for chain, module graph, artwork, SeaDrop, LP converter, fixed
  ZZZ, native venue, randomness, launch role and sale-end dependencies.
- Every live identity/readiness flag remains **unverified**. Unknown addresses
  remain null; no RPC, content check, seal transaction or seal calldata is made.

Complete offline configuration inputs are not complete live readiness. Perform
the reads on one reviewed canonical snapshot, compare actual deployed code and
creation/immutable evidence with the exact current build, and recheck mutable
state before committing. Preserve those observations and simulate the final
reviewed operation separately. Do not infer an address's owner, correct code or
external product acceptance from a nonzero address or successful getter.

| Boundary | Exact input/read before commitment | What becomes permanent; real remedy |
| --- | --- | --- |
| Controller deployment | Constructor governance/keeper/guardian; read `governance()`, `bootstrap()`, `keepers(address)`, `guardians(address)` | Controller and factory identities are fixed. Governance can rotate governed roles during their permitted lifecycle; lost governance has no hidden recovery key. |
| Module slots | `Access.bind(moduleId,implementation)`; read all `module(bytes32)` and each reciprocal `access()`/companion parent | Each slot binds once. Wrong code/parent requires reconstruction before use; sealing erases bootstrap and cannot be undone. |
| Protocol policy | `bindProtocolPolicy(policy)`; read `protocolPolicy()`, policy `access()` and version | The policy implementation/controller is fixed. Its supported future settings remain governed; implementation replacement is not a setter. |
| Vault chain | Constructor `nftHomeChain`; read `canonicalChainId()` | Current same-chain-only construction requires the executing chain. A different chain ID is rejected, rather than producing a permanently unusable Vault. |
| Budget/canonical helpers | Constructor/binding addresses and exact reciprocal parent/getter evidence | Typed child implementations and parents are fixed. Matching tuple shapes or a version number do not authenticate runtime code. |
| Native venue graph | Manager/core/state/PositionManager/Permit2/Balancer and fixed child getters; compare exact native admission pins | A coherent but wrong venue graph can never admit this release's native pools. Pool-ID changes after sealing cannot replace those parent contracts. Reconstruct before use. |
| Fixed ZZZ | `ActivationAssets.zzz()`, `Migration.currentZZZ()`, `Buyback.zzz()`, `Rewards.isAsset(ZZZ)`, actual token code/decimals | Exactly one deployment ZZZ. Token migration uses terminal holder return and redeployment; there is no retarget setter or integrated bridge. |
| LP converter binding | `Rewards.converter()` equals the reviewed converter; converter `ledger()` and `access()` match | Must bind before seal. Omitting it permanently removes this deployment's ZZZ-to-ETH LP settlement path. Existing raw backing is not destroyed; ordinary ETH-only preparation can fail. Routes are a separate later-configurable choice. |
| OpenSea helper binding | `NFT.seaDropMint()` equals the reviewed helper; helper `nft()`, `access()`, `seaDrop()` and `seaDropCodeHash()` match | Must bind before seal/first mint for the selected OpenSea release. A zero-helper local direct-mint test is not OpenSea qualification and cannot be converted into this release after sealing. |
| SeaDrop singleton | Exact external runtime, helper code hash, supported chain and actual onboarding | The bound singleton cannot be rotated through `updateAllowedSeaDrop`. A future incompatible platform requires a separately reviewed deployment/transition, not an assumed repair call. |
| Artwork and renderer | `NFT.artworkBaseURI()`, `metadataRenderer()`, all published paths/content | Empty constructor setup is allowed; bootstrap may call `setBaseURI(nonemptyRoot)` once before seal. A nonempty constructor already consumes that choice. Wrong-but-nonempty content has no in-place URI repair. |
| Randomness initial setup | NFT randomness getters, policy settings, coordinator code, subscription consumer/funding/callback evidence | Initial configuration is pre-seal. Later provider rotation requires all previous draws finalized. A permanently unanswered request cannot be rerolled or assigned by governance. Qualify the provider before first mint. |
| Standalone versus importer | `canonicalState()`, `preparationActive()`, Handoff `incomingSource()`/phase and exact schema | A replacement importer is deliberately prepared before seal and stays inert until authenticated backing/activation. A sealed standalone deployment cannot later be relabelled as that importer. |
| Sale terms and proofs | Helper `configured()`, `mintConfig()`, actual NFT-keyed SeaDrop public drop/root/recipient/fees/payers and `NFT.mintedCount()` | Review future-only changes and lifetime counts. Transfers never reset original-recipient allowances. A Merkle root does not prove that its off-chain leaves use approved terms. |
| Official final mint end | `NFT.royaltyRewards()` then royalty `mintEnd()`/revision; match final OpenSea phase | Governance can revise while the prior sale is open. After closing, reopening is forbidden; the one-hour initial royalty window follows that final end, even below 1,000 sales. |
| Bootstrap timing | Compare `mintEnd()`, `royaltiesOpenAt()` and `royaltiesOpen()` with the canonical block timestamp; retain authenticated `RoyaltyOpeningFinalized` event/state history | Finalization has no public getter; `royaltiesOpen()` only tests time. If a configured end expires during bootstrap, the current setter cannot reset it even with zero NFTs. Do not assume zero mints permits reopening; reconstruct and review a viable schedule. |
| Revealed traits | Finalized ordinal/artwork and original VRF request evidence | Rarity/design assignment is permanent. Activation changes economic/lifecycle state, not the original rarity draw. |
| Royalty admission/capacity | Exact token, code/behavior, gas/outage review and capacity getter | Admitted currencies cannot simply be deleted; capacity only increases within its engineering bound. A malicious or failed token cannot be made transferable by a sweep promise. |
| Opening/recovery allocation | Opening status, current active weights and exact unallocated currency/amount | Initial opening and explicit recovery allocations are irreversible economic writes. `reviewHash` does not freeze a pending recovery's cohort. Preserve already earned liabilities. |
| Pool/residual configuration | Exact pool identity, retained history and both physical LP IDs before changes | Desired mode can change; backing cannot be dropped. Disabling residual mode does not itself close it. All actual positions remain valued/harvested until a reviewed close/merge succeeds. |
| Permanent bucket reservation | Read `VaultCanonical.bucketIdentity(pool)`, `Vault.bucketCount()`, `bucketAt(index)` and `poolBucket(pool)` | New reservations use the calculated ID; aliases may use an existing registered bucket. Wrong fresh IDs reject before capacity is consumed. Valid reservations remain permanent and the four-bucket limit is not increased by cancelling a plan. |
| Parking | Both-leg custody/ledger fingerprints, principal/reward separation and actual parked balances | Reversible only through supported guarded or explicit emergency recovery. Healthy validation or explicit permitted bypass is still required; external token transfers may fail. |
| Collective principal exit | Confirm governance/paused state, final fees, all bucket backing and current owner/share allocations | Terminal. Unpause does not restart principal or canonical replacement. NFTs retain transfer/royalty/old-reward rights. Failed isolated payouts retain backing; broken tokens/receivers can still delay delivery. |
| Canonical freeze/funding/retirement | Reviewed notice/peer, complete ledgers, no live residual, exact backing and phase/cursors | Abort requires the transferred backing returned before source reopening. Final retirement cannot be undone. Unavailable currencies, pending draws or incompatible escrow may prevent the assumed transition. |

The complete inventory includes additional fixed constants and adapter-specific
immutables. A replaceable price adapter's fixed pool/call budget is different
from a fixed Vault implementation: an admitted Oracle source may be replaced
through its existing guarded configuration, without pretending its old runtime
changed.

For `Vault.reservePool(pool,bucket)`, finish the complete Migration/validator
bindings first. Read `Migration.validation()` and its `access()`/`migration()`;
then `CustodyValidation.validReservationIdentity(pool,bucket)` can corroborate
the identity. A true predicate does not prove pool admission, authority, remaining
capacity or that a fresh activation is possible. In particular, an alias to an
empty other-pool reservation is preserved, but first activation still needs its
own canonical domain. Use an existing initialized LP bucket for a pool move;
do not use empty aliases as arbitrary new contribution destinations. Spot swaps
do not change a bucket ID, whereas replacing the contract target/lifecycle still
requires a fresh operation review.

## Missing bindings are release blockers even if raw seal succeeds

`Access.seal()` checks selected structural invariants. It is **not a complete
production-release validator**. In particular, this source still permits explicit
zero-helper direct-mint/local configurations and does not require the LP converter
binding. The selected OpenSea/ETH-settled release must reject those omissions in
its actual deployment review before sealing. Neither an unsigned plan nor the
new metadata-only seal checks close those omissions automatically.

If a pre-seal one-time slot is wrong, reconstruct before accepting real mints or
funds. After deployment, compatible same-chain replacement is conditional, not
a universal escape hatch. Terminal holder exit does not repair the old
implementation, pending randomness, a failed token or an unavailable chain.

Separate **binding** from **launch timing**: the SeaDrop helper and LP converter
must bind before sealing, but sale terms, an initially unset `mintEnd` and
reviewed conversion routes can be configured afterward within their normal
guards. An unset end is not an expired end. Delay the initial deadline write
until the launch schedule is viable; the sale stays blocked until the complete
SeaDrop/NFT-end configuration agrees. Do not falsely describe these future
settings as permanently fixed by sealing.

## What remains configurable

Supported policies retain their existing bounds: future entry/sale terms and
recipient, role grants, pause, price sources, reviewed routes/pools, loss caps,
ranges/residual settings, confirmation/compound intervals and selected operating
gas policies. See [future operating settings](OPERATOR_MANUAL.md#future-operating-settings).
Changing those policies never resets ownership, lifetime mint counts, sealed
module identities, earned rights, finalized artwork or terminal retirement.
