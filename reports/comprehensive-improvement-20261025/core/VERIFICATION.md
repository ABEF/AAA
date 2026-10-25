# Core metadata/buyback verification and combined normal sizes

Read the [core findings](../CORE_REVIEW.md) and [source/artifact receipt](receipt.json). This is targeted offline evidence for the undeployed candidate, not a full unchanged regression, real-provider/venue qualification or independent audit.

## Useful checks and deliberate reuse

- **10 distinct metadata cases pass:** eight existing/updated valuation, evolution, pending/revealed JSON, palette, fixed-trait and transfer cases from `metadata-final`, plus the two new dormant-rarity/activation-flag cases from `metadata-repaired`. The original new cases were first run against the old renderer: all three selected cases failed for the expected dormant-zero/unrevealed-zero mismatch. The first fixed-renderer run exposed two test-fixture mistakes: a one-shot `vm.prank` was consumed by the NFT receiver getter instead of the subsequent claim. The immutable receiver is now cached before pranking. Only those two corrected cases were rerun. Eight passed test bodies and all nine shared harness/helper functions match the final file exactly; the receipt records their hashes. The final production renderer/NFT dependencies match those runs; the later Buyback change is outside their executed subject.
- **41 distinct Buyback cases pass:** 22 composed execution cases and 19 operating-limit cases, including six new boundary/failure controls. Two existing affected fuzz properties each ran 1,000 inputs. The new cases use the real dual-source Oracle with separately controlled mock feeds: admitted 3% spread, upper-bound exact ceiling, one raw unit above, upward USD rounding, native input, missing dual-bounds interface and a failed secondary source. These synthetic feeds do not prove production provider independence. Existing composed cases retain real FeeController/Rewards/Buyback/Oracle/Registry/Strategy/Manager logic with mock authority, assets, VRF, share custody and AMM settlement. No real pool price formation, live VRF or target-chain service is claimed.
- **37 normal source-object gates pass across all 42 final production Solidity sources**, using Solidity 0.8.26/Cancun, via-IR, optimizer runs1 and Yul optimization disabled. No runtime/initcode limit is relaxed. All final source hashes match the build receipt; all Buyback run source/test inputs match current files.

The initial Buyback harness had a forbidden Foundry `testFail*` name and was rejected before the selected cases ran. That diagnostic is retained as `buyback-red`. After renaming, `buyback-red-repaired` demonstrates the missing budget protection on the old Buyback code. One secondary-source expected-error assertion also needed the exact encoded address rather than a selector-only expectation. Final results supersede these explicitly retained diagnostics; none is hidden or counted as a pass.

Unchanged mint quota/full-inventory randomness, whole-collection migration, custody and strategy suites were not broadly repeated for the read-only renderer and local Buyback budget change. Their earlier evidence keeps its original source/scope. Other changes in this campaign have separate targeted evidence.

## Normal size gates

| Object | Runtime bytes | Creation bytes including fixed arguments | Normal margin/qualification |
| --- | ---: | ---: | --- |
| Vault | 24,519 | 47,372 | **57 runtime bytes** remain; future edits must recheck normal limits. |
| PoolRegistry | 12,027 | 48,334 | 818 creation bytes remain; includes its embedded current Entry. |
| ActivationEntry | 17,511 | 30,116 | Fixed 96-byte constructor arguments included. |
| ContributionPricing | 15,200 | 15,918 | Fixed 64-byte constructor arguments included. |
| Buyback | 7,838 | 8,628 | Fixed 96-byte constructor arguments included. |
| NFT renderer | 12,831 | 13,187 | Fixed 32-byte constructor arguments included. |
| NFT | 23,929 | 44,097 before dynamic arguments | A 67-byte illustrative URI gives 192 encoded argument bytes and total44,289. Actual release URI remains unset and must be encoded/checked. |
| Access controller | 14,508 | 40,832 before dynamic arguments | One proposer/one executor illustration gives 288 argument bytes and total41,120. Actual role arrays remain unselected and need exact release encoding. |

Full object output and settings are in [production-final-size-gates.json](production-final-size-gates.json). Dynamic examples are size illustrations, not approval of real addresses or an artwork content root. Raw standard-json input/output hashes and the reproducible compiler driver are retained in the receipt/external local evidence; no deployment was performed.

Preserved: public signing disabled, shared signer Anvil-only, public deployment null, monitoring paused, existing local Anvil/NFT/LP/balances/journals/services untouched. Production remains **NOT APPROVED**.
