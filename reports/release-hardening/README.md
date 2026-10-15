# Release checklist hardening - undeployed candidate

Recorded 2026-10-15, based on `5febe7065856749345010ecca23dcd368b472c9e` plus the source hashes in [verification-summary.json](verification-summary.json). **Internal development evidence, not an independent audit, deployment or approval for real funds.** The website repository and server were not changed.

## Changes and verification

The NFT adds a permissionless `refreshMetadataRange(firstOrdinal,lastOrdinal)` with a fixed 50-entry limit. Ordinals resolve to actual hashed token IDs, with individual ERC-4906 notifications and atomic bounds/ownership checks. The method has no external calls, price reads, trait changes or custody effects. Existing single-token refresh remains available.

The keeper adds an optional, disabled-by-default confirmed-block watcher. It validates the canonical NFT/controller/Vault identity and reviewed live runtime; tracks evolution, valuation availability and reveal state; and uses the existing simulation, serial signer, spending limits and durable pending recovery. It remains separate from shared-pool LP upkeep. Dry runs and failed, ambiguous, expired or reorged observations cannot establish a successful notification. Deployment and actual marketplace operation still need staging.

| Check | Recorded result |
| --- | --- |
| Full offline Solidity | 342 passed, zero failed, one expected opt-in fork setup skip; 343 tests across 24 suites |
| Targeted NFT metadata | 26 passed, including six new bounded-notification cases and 1,000-case fuzzing |
| Cold 50-token notification | 318,466 gas, below the unchanged 500,000 regression budget |
| Normal `forge build --sizes` | Exit zero; all 20 production module/helper runtime and initcode-object gates pass |
| Compiler binding | All 26 Solidity sources match compiler metadata; 26 sources plus three build/configuration hashes unchanged during verification |
| Full portable Python | 372 passed from a 376-test inventory; zero failures/errors/runtime skips; four unchanged Unix-only tests retained for Ubuntu |
| Focused keeper tests | 109 passed, zero failures/errors/skips, including 45 metadata cases and the pinned cast CLI parser |
| Fresh pinned Slither | 179 detections; 110 false positives, 42 accepted risks, 27 informational, zero unresolved internal review entries |
| Static review coverage | All 179 native findings covered; historical split-shape matcher fixture and seven rejected adverse mutations pass |

Full [Solidity output](solidity-tests.log), [size output](forge-build-sizes.log), [Python output](python-tests.log) and [log provenance](log-provenance.json) are retained. The first Windows size run compiled successfully but failed to access Foundry's local signature cache; the same ordinary command passed after approved cache access, with no source or limit changes. The first failure log remains externally preserved and hashed in the summary.

NFT runtime/initcode object is **18,822/42,307 bytes**. Vault runtime remains **24,407 bytes**, only **169 bytes** below EIP-170. Constructor arguments still require deployment-time initcode allowance. No standard size limit or local gas budget was increased.

The [fresh static-analysis record](static-analysis/README.md) distinguishes exact carried findings from four individually re-read NFT location changes. The unchanged checker binds all 29 source/configuration files. Prior review bytes are preserved in [history](../history/slither-review-pre-release-hardening.json). A separate internal [keeper review](keeper-review.md) reproduced two watcher correctness issues: small/wrapping batches could starve trailing NFTs, and an old observation could become an inaccurate notified baseline. The corrected cursor advances after selected work, and confirmation rereads exact receipt-block states before checkpointing. Simultaneous receipt reorgs retain pending state; invalid/expired triggers remove prior fingerprints. Independent internal regression execution verifies these fixes. No live signer/RPC operating rehearsal or external security audit is established.

## Market and release limits

The read-only [selected-market feasibility review](selected-market-review.md) records fresh matching two-provider observations at Robinhood block **89,487,849** and the required native/Pons design. It changes no pool guards. The current hookless ERC20 adapter still rejects that selected pool; creator-payment intake does not supply compatible custody. Native venue currencies and nonzero accounting assets must be modelled explicitly, with measured wrapping/settlement and hook-adjusted swaps across affected modules.

Earlier [Ubuntu CI for `5febe70`](https://github.com/ABEF/AAA/actions/runs/38793910449) passed all three jobs, including all 331 then-current Python tests and nine dependency-fork tests. This is baseline evidence for that revision, not a run of the new metadata source. Check the new published revision's full CI separately. This local offline pass did not rerun the actual-dependency fork or extended accounting stress profile. Fork tests use a separate hookless pool and mock randomness, not selected Pons custody or a real VRF service.

The [release checklist](../../docs/RELEASE_CHECKLIST.md) keeps actual selected-market integration, ZZZ/USDC routing, supported production randomness/feeds/outage policy, immutable artwork hosting, live frontend/royalty claims, actual operating rehearsals, authority inventory and independent audit open. The user has not selected production governance, guardian, keeper or mint-recipient addresses and requested leaving those gates open. Real bridge wrappers and delivery/backing validation remain required before migration is enabled; a separately reviewed migration-disabled initial launch remains possible.

The README title now uses a plain ASCII `-`. [Operations](../../docs/OPERATIONS.md#reward-timing-and-maintenance-schedule) explains actual-receipt reward timing, unrestricted funded claim windows, ten-minute polling versus conditional rebalancing, the four-hour example harvest interval and the dry-run Ubuntu service template. No guaranteed revenue, creator payment schedule, production strategy parameters or real claim integration was invented.
