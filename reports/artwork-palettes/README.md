# Eight-color artwork and immutable trait inventory

This is scoped local development verification for the undeployed contract candidate. It does not authorize deployment or establish production readiness. The prior `reports/website-alignment/` evidence remains historical and unchanged.

## Implemented behavior

- Eight base colors: Cyan, Blue, Violet, Emerald, Amber, Crimson, Ivory and Onyx. The approved composition rules produce eight monochrome, 22 bicolor and 28 tricolor palettes.
- The finite 1,000-entry visual inventory has 200 monochrome, 500 bicolor and 300 tricolor entries. Every color style independently retains the 60/30/10 rarity composition. Four circuit patterns (Flowing arcs, Segmented panels, Orbital rings and Vertical ribs) provide 542 distinct finished palette/pattern/rarity looks: at most four identical copies, with all 100 Legendary looks unique. This final four-pattern inventory supersedes the earlier unpublished five-pattern checkpoint.
- The first authenticated VRF word retains the existing rarity-quota draw. The second selects an entry without replacement from that rarity's fixed inventory, using a bounded sparse Fisher-Yates mapping. Mint-order finalization, fixed coordinator, callback authentication and absence of owner/admin rerolls remain intact. Preview seed/order is not mint randomness.
- Immutable palette/pattern traits and component-color metadata select `palette-pattern-rarity-evolution.svg`. The renderer and production publication gate support 2,784 states. Palette, color style and pattern never change LP shares, collective membership or royalty weights.
- Vault, fee, membership, royalty, migration and custody source remain unchanged. No public-chain contract deployment, signature, funding or transaction occurred.

## Evidence

The source-bound [verification summary](verification-summary.json) records hashes and exact checks:

| Check | Result |
| --- | --- |
| Full offline Solidity unit/fuzz/default-invariant suites | **336 passed / zero failed / one expected opt-in fork setup skip**, 337 total across 24 suites. [Log](solidity-tests.log). |
| NFT reveal/metadata suite | **20 passed**, including 1,000 fuzz cases and two complete 1,000-mint inventory consumptions. Exact style/rarity quotas, no-reroll ownership/transfer behavior, duplicate limits and Legendary uniqueness passed. |
| Portable Windows Python | **327 passed / zero failed/errors/runtime skips**, from 331 tests. Four unchanged Unix-only cases await Ubuntu CI. [Log](python-portable.log). |
| Generated catalogue and cross-language checks | Solidity byte tables match the committed packed catalogue. Python validates all 1,000 entries, 58 palette masks, quota/copy bounds and all 2,784 publication paths. |
| Normal compiler and runtime/initcode objects | Standard offline `forge build --sizes` exited zero. All **20** module/helper objects pass EIP-170/EIP-3860 size bounds. NFT is 18,519 runtime / 42,004 initcode-object bytes; Vault remains 24,407 runtime bytes with 169 bytes available. [Log](forge-build-sizes.log). Constructor arguments still require deployment-time allowance. |
| Fresh static analysis | **179 source-bound findings**, individually reviewed internally as 110 false positives / 42 accepted risks / 27 informational / zero unresolved. Coverage, split/merged matcher replay and seven adversarial mutations pass. [Separate report](../artwork-palette/README.md). This is not an independent audit. |

Native Windows log copies use LF line endings; native/copy hashes and paths are recorded in [provenance](log-provenance.json). The final normal size command used the local Foundry signature-cache filesystem access established during the earlier checkpoint; this changed no compiler flags or Solidity source. Superseded five-pattern receipts remain in external local verification evidence and are not presented as verification of this final four-pattern source.

The fresh live-dependency fork and extended 256×256 accounting profile were not rerun for this artwork-only contract change. The offline suite uses mocks for VRF and LP custody. Actual production VRF availability/configuration, native-ETH/Pons market integration, production bridge/authorities/oracles, staging, immutable artwork publication and an independent audit remain open gates. Website publication is tracked separately and is not contract deployment evidence.
