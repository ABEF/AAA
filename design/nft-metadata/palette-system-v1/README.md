# PoPL eight-color artwork catalogue

This catalogue records the accepted color-combination rules and a balanced finite inventory for the 1,000-NFT collection. Color, color style and circuit pattern are purely visual. Rarity alone determines the separate activated NFT-sale royalty weight; these artwork traits never change LP fee shares.

## Accepted color rules

The eight base colors are Cyan, Blue, Violet, Emerald, Amber, Crimson, Ivory and Onyx. Amber is the project's yellow, Crimson its red, Ivory its warm white and Onyx its black. The six established color values are preserved.

- **Monochrome:** one of the eight base colors.
- **Bicolor:** any two distinct base colors where at least one is Ivory, Amber, Crimson or Onyx. This includes the complementary-inspired Cyan–Crimson, Emerald–Crimson, Violet–Amber and Blue–Amber families.
- **Tricolor:** start with an allowed bicolor pair, then add Amber, Crimson or Onyx if that added color is not already present. All three colors must be distinct.
- Color order does not create an additional palette. The catalogue uses the fixed base-color order to identify each unordered combination.

These rules produce **8 monochrome, 22 bicolor and 28 tricolor palettes**, or **58 palette families**. For example, Cyan–Ivory can add Amber, Crimson or Onyx. Cyan–Amber can add Crimson or Onyx. Cyan–Blue–Amber is not admitted: Cyan–Blue is not an allowed starting pair, and Blue is not an allowed third-color addition.

## Collection balance and repetition

| Color style | Commun | Rare | Legendary | Total |
| --- | ---: | ---: | ---: | ---: |
| Monochrome | 120 | 60 | 20 | 200 |
| Bicolor | 300 | 150 | 50 | 500 |
| Tricolor | 180 | 90 | 30 | 300 |
| Total | 600 | 300 | 100 | 1,000 |

Each palette is available in every rarity. Within each style and rarity, palette counts differ by at most one. Four circuit patterns add visible variation: Flowing arcs, Segmented panels, Orbital rings and Vertical ribs. Hexagonal mesh and Branching circuits are excluded from this final catalogue.

The fixed inventory contains **542 distinct complete palette/pattern/rarity looks** across the 1,000 NFTs. A complete look occurs at most four times; all 100 Legendary finished looks are distinct. Multiple NFTs can share a palette while differing in circuit pattern or rarity finish. Different token numbers alone are not counted as different artwork.

Four evolution states remain views of the same NFT, not additional minted NFTs: Dormant, Activated, Enhanced at $1,000 marked attached LP and Singularity at $10,000. Evolution follows current marked LP value. Activation and reward eligibility remain separate economic state. Enhanced keeps one bright border; Singularity has the brightest double border and background light.

## Files and contract interface

- `palette-system.mjs` is the canonical browser-safe rule module.
- `art-catalog.js` is its generated single-file browser copy.
- `inventory.json` records 1,000 balanced entries. Its deterministic token ordering is a simulation fixture, not a production randomness source.
- `packed-catalog.json` groups the same entries by rarity, preserving their fixture order. Each entry is a big-endian `uint16`: `paletteIndex * 4 + patternIndex`. SHA-256 hashes cover the raw byte sequence for each rarity.

Base-color bit positions and component ordering are Cyan 0, Blue 1, Violet 2, Emerald 3, Amber 4, Crimson 5, Ivory 6 and Onyx 7. Palette indices enumerate 8 monochrome palettes, then 22 bicolor palettes, then 28 tricolor palettes, using combinations in that base-color order. Pattern indices are arcs 0, panels 1, orbits 2 and ribs 3. The stable `ribs` slot is displayed as **Twin circuit routes** after the user-approved 2026-10-20 replacement of Vertical ribs. The name/appearance changes without regenerating or reordering the fixed inventory; original textures and the other three patterns remain unchanged.

Production assignment must consume the fixed entries **without replacement**, using authenticated verifiable randomness and the contract's ordered-reveal controls. The fixture seed and JavaScript PRNG are explicitly noncryptographic and must never select real mint traits. Independent random draws with replacement would not enforce exact quotas or artwork repetition limits.

The complete render catalogue has 58 palettes × 4 patterns × 3 rarities × 4 evolutions = **2,784 visual variants**. Some are not selected by the fixed mint inventory. The variant count is separate from the 1,000-NFT supply cap.

Regenerate the exported catalogue from the repository root:

```sh
node design/nft-metadata/palette-system-v1/export-inventory.mjs
node --test design/nft-metadata/palette-system-v1/palette-system.test.mjs
```

No deployment or transaction is performed by these commands.
