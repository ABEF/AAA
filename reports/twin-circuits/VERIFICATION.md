# Twin circuit routes artwork replacement

Scope: 2026-10-20 user-approved replacement of **Vertical ribs**, explicitly
confirmed after distinguishing it from Orbital rings. This is an internal visual
and metadata consistency check, not a production approval or economic audit.

## Change

- Two groups of four continuous static traces, no chips or animation. All eight
  colors, 58 palettes, three rarities and four evolution states are supported.
- Stable pattern ID `ribs`, index 3 and every image path are retained. Fixed
  inventory JSON, packed draw bytes and generated `ZZZArtwork.sol` are byte-identical.
- Exactly **696 SVGs and 696 reference metadata files** change; **2,088 other
  artwork states** retain exact image hashes and catalogue records. Every replaced
  SVG embeds the same approved WebP texture bytes. No new raster generation.
- `ZZZNFTMetadata.sol` changes one label string only. Its getter/URI logic, all
  storage and all economic code are unchanged. The matching existing metadata
  assertion now expects the approved label while retaining the ribs URI assertion.

## Verification

- 11 existing website artwork tests pass (zero failures/skips).
- 13 existing catalogue/inventory tests pass (zero failures/skips).
- Website checker verifies all 2,784 SVG/JSON pairs and hashes, 1,000 inventory
  entries, maximum four identical finished designs, 89 HTML IDs and five routes.
- Static website build contains 5,590 files. Browser review covers Cyan Rare
  Enhanced and Cyan/Amber/Onyx Rare Enhanced with the unchanged original texture.
- All 696 new SVGs have exactly two four-path groups, one continuous path per
  lane, no animation/scripts, and original embedded texture bytes.
- Two focused existing Solidity metadata cases pass under pinned solc 0.8.26,
  normal Cancun/via-IR profile: pending/revealed valid metadata and the
  Ivory/Onyx/bicolor/tricolor label/path/royalty-weight case. No unchanged
  custody/rewards/fork/full-contract suite was rerun for this string-only change.
- Generated immutable artwork-library check passes without changing its source.

[Source hashes and unchanged-scope assertions](source-verification.json).
The complete IPFS bundle is regenerated and all 5,571 archive members verified; see [bundle receipt](bundle.json). Normal-profile metadata runtime/initcode object is 12,448/12,772 bytes and NFT is 23,502/43,287, within the existing limits. Website commit: `21d6117328dacf9e434765f2a1d159f3641a915a`. publication/pinning/provider
selection remain open. Older archives retain their original scope. Website
publication is separate from deploying the revised, still-undeployed metadata
contract candidate. The central Todo, feature reference and operator manual are
updated; no new management permission or procedure is introduced.
