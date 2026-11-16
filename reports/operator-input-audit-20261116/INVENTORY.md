# Operator inventory and input coverage

This is a source/reference reconciliation and documentation inventory, not approval or a claim that every ABI row was dynamically tested.

Current ABI: 1016 entries = 963 functions + 40 constructors + 13 receivers across 40 concrete contracts.

Actual operator/nominated targets: 92 = 72 governance/configuration + 11 bootstrap + 7 keeper + 2 nominated acceptances. Other roles: 689 reads, 159 module endpoints, 19 permissionless, 12 holder, 5 callbacks, 40 constructors.

Every operator input now has prose: 333 records including tuple containers, 317 leaves, 137 nested records. Units/bounds and current hash domains were checked against their defining source; executing all combinations is not implied.

The machine-readable [inventory](inventory.json) has every exact overload/selector, caller/lifecycle, all recursively expanded input/output fields, unresolved examples, and explicit assessment limits.

## Confirmed corrections

- Three LP converter controls incorrectly called their boolean/basis-point value a native mint payment. They now state the actual type, unit and bounds.
- Nested tuple component notes were always discarded by the reference producer. Optional strict nested notes preserve all operator field explanations in ABI order, with legacy string-note compatibility.
- Operator expanded examples were keyed only by Solidity struct name. Distinct parking/close/consolidation/replacement semantics now keep separate anchors and field meanings instead of borrowing the first operation’s template.

## Operator targets

| Contract-qualified exact signature | Role | Family | Input leaves |
| --- | --- | --- | --- |
| `ZZZAccessController.acceptGovernance()` | N | authority-bootstrap-pause-canonical-notice | 0 |
| `ZZZAccessController.bind(bytes32,address)` | B | authority-bootstrap-pause-canonical-notice | 2 |
| `ZZZAccessController.bindProtocolPolicy(address)` | B | authority-bootstrap-pause-canonical-notice | 1 |
| `ZZZAccessController.cancelPreparation(bytes32)` | G | authority-bootstrap-pause-canonical-notice | 1 |
| `ZZZAccessController.proposeGovernance(address)` | G | authority-bootstrap-pause-canonical-notice | 1 |
| `ZZZAccessController.seal()` | B | authority-bootstrap-pause-canonical-notice | 0 |
| `ZZZAccessController.setGuardian(address,bool)` | G | authority-bootstrap-pause-canonical-notice | 2 |
| `ZZZAccessController.setKeeper(address,bool)` | G | authority-bootstrap-pause-canonical-notice | 2 |
| `ZZZAccessController.setPaused(bool)` | G | authority-bootstrap-pause-canonical-notice | 1 |
| `ZZZAccessController.startPreparation((uint256,address,bytes32,bytes32))` | G | authority-bootstrap-pause-canonical-notice | 4 |
| `ZZZActivationAssets.configureZZZ(address,bytes32,bytes32)` | B | source-token-admission | 3 |
| `ZZZActivationAssets.setAsset(address,bool,bytes32,bytes32)` | G | source-token-admission | 4 |
| `ZZZBuyback.execute(address,uint256,bytes32,uint256)` | K | buyback-reserve-conversion | 4 |
| `ZZZBuyback.setMaximumTradeUSD(uint256,bytes32)` | G | buyback-reserve-conversion | 2 |
| `ZZZBuyback.setOperatingTradeUSD(uint256)` | G | buyback-reserve-conversion | 1 |
| `ZZZCanonicalHandoff.abort()` | G | canonical-freeze-import-commit-abort-recovery | 0 |
| `ZZZCanonicalHandoff.commit()` | G | canonical-freeze-import-commit-abort-recovery | 0 |
| `ZZZCanonicalHandoff.finishAbort()` | G | canonical-freeze-import-commit-abort-recovery | 0 |
| `ZZZCanonicalHandoff.freeze()` | G | canonical-freeze-import-commit-abort-recovery | 0 |
| `ZZZCanonicalHandoff.prepareImport(address)` | B | canonical-freeze-import-commit-abort-recovery | 1 |
| `ZZZCanonicalHandoff.recoverCancelledRoyalties(address,bytes32)` | G | canonical-freeze-import-commit-abort-recovery | 2 |
| `ZZZCompounder.compound(uint256,uint128,uint256)` | K | compound-existing-geometry | 3 |
| `ZZZLPBalancer.configureExecutionPools(bytes32[],bytes32)` | G | execution-venue-solver-policy | 2 |
| `ZZZLPBalancer.configureSolver(uint8,uint32,bytes32)` | G | execution-venue-solver-policy | 3 |
| `ZZZLPRewardConverter.addRoute((address,address,address,address,uint24,bytes32,bytes32,bytes32,bytes32,bytes32))` | G | earned-LP-currency-conversion | 10 |
| `ZZZLPRewardConverter.addV4Route((address,address,(address,address,uint24,int24,address),address,address,bytes32,bytes32,bytes32,bytes32,bytes32))` | G | earned-LP-currency-conversion | 14 |
| `ZZZLPRewardConverter.configureWrapper((bytes32,address,address,address,bytes32,bytes32,bytes32))` | G | earned-LP-currency-conversion | 7 |
| `ZZZLPRewardConverter.setConversionLossBps(uint16)` | G | earned-LP-currency-conversion | 1 |
| `ZZZLPRewardConverter.setEnabled(bool)` | G | earned-LP-currency-conversion | 1 |
| `ZZZLPRewardConverter.setRouteEnabled(bytes32,bool)` | G | earned-LP-currency-conversion | 2 |
| `ZZZMigration.allocatePrincipal(uint256)` | G | principal-custody-recovery-terminal-exit | 1 |
| `ZZZMigration.beginCollectiveExit(bytes32)` | G | principal-custody-recovery-terminal-exit | 1 |
| `ZZZMigration.closeBucket(uint256,uint256,uint256,uint256)` | G | principal-custody-recovery-terminal-exit | 4 |
| `ZZZMigration.closeResidual((uint256,bytes32,uint256,uint256,uint256,uint64,uint64,address,address,uint128,uint128,uint256,bytes32,bytes32))` | G | principal-custody-recovery-terminal-exit | 14 |
| `ZZZMigration.configureZZZ(address,bytes32,bytes32)` | B | principal-custody-recovery-terminal-exit | 3 |
| `ZZZMigration.consolidateResidual((uint256,bytes32,uint8,int24,int24,bytes32,bool,uint128,uint128,uint128,uint256,bytes32),bool)` | G | principal-custody-recovery-terminal-exit | 13 |
| `ZZZMigration.distributePrincipal(uint256[])` | G | principal-custody-recovery-terminal-exit | 1 |
| `ZZZMigration.emergencyRebalance((uint256,bytes32,uint8,int24,int24,bytes32,bool,uint128,uint128,uint128,uint256,bytes32))` | G | principal-custody-recovery-terminal-exit | 12 |
| `ZZZMigration.invalidateParking(uint256)` | G | principal-custody-recovery-terminal-exit | 1 |
| `ZZZMigration.moveFunds(uint256,bytes32,uint128,uint256)` | G | principal-custody-recovery-terminal-exit | 4 |
| `ZZZMigration.park((uint256,bytes32,uint256,uint256,uint256,uint64,uint64,address,address,uint128,uint128,uint256,bytes32,bytes32))` | G | principal-custody-recovery-terminal-exit | 14 |
| `ZZZMigration.resume(uint256,bytes32,uint128,uint256)` | G | principal-custody-recovery-terminal-exit | 4 |
| `ZZZMigrationBudget.setCompoundInterval(bytes32,uint32)` | G | loss-and-compound-cadence-policy | 2 |
| `ZZZMigrationBudget.setLossLimits(uint16,uint16)` | G | loss-and-compound-cadence-policy | 2 |
| `ZZZNFT.addRoyaltyAsset(address)` | G | mint-royalty-metadata-administration | 1 |
| `ZZZNFT.increaseRoyaltyAssetCapacity(uint8,bytes32)` | G | mint-royalty-metadata-administration | 2 |
| `ZZZNFT.setBaseURI(string)` | B | mint-royalty-metadata-administration | 1 |
| `ZZZNFT.setMintEnd(uint64)` | G | mint-royalty-metadata-administration | 1 |
| `ZZZNFT.setMintPaused(bool)` | G | mint-royalty-metadata-administration | 1 |
| `ZZZNFT.setSeaDropMint(address)` | B | mint-royalty-metadata-administration | 1 |
| `ZZZNFT.updateAllowList(address,(bytes32,string[],string))` | G | mint-royalty-metadata-administration | 4 |
| `ZZZNFT.updateAllowedFeeRecipient(address,address,bool)` | G | mint-royalty-metadata-administration | 3 |
| `ZZZNFT.updateCreatorPayoutAddress(address,address)` | G | mint-royalty-metadata-administration | 2 |
| `ZZZNFT.updateDropURI(address,string)` | G | mint-royalty-metadata-administration | 2 |
| `ZZZNFT.updatePayer(address,address,bool)` | G | mint-royalty-metadata-administration | 3 |
| `ZZZNFT.updatePublicDrop(address,(uint80,uint48,uint48,uint16,uint16,bool))` | G | mint-royalty-metadata-administration | 7 |
| `ZZZOracle.setDualFeed(address,(address,bytes32,bytes32,uint32,uint8),(address,bytes32,bytes32,uint32,uint8),uint16,bytes32)` | G | independent-pricing-source-policy | 13 |
| `ZZZOracle.setExecutionSource(address,bool,bytes32,bytes32)` | G | independent-pricing-source-policy | 4 |
| `ZZZOracle.setSequencerFeed(address,bytes32,bytes32)` | G | independent-pricing-source-policy | 3 |
| `ZZZPoolRegistry.configureNative(((address,address,uint24,int24,address),bool,bool,uint16,uint16,uint16,uint16,uint32,uint256,uint256))` | G | pool-key-contribution-and-maintenance-policy | 14 |
| `ZZZPoolRegistry.disablePool(bytes32,bool,bool)` | G | pool-key-contribution-and-maintenance-policy | 3 |
| `ZZZPortfolioPolicy.configureMainAllocation(bytes32,uint16,bytes32)` | G | main-residual-mode-geometry-policy | 3 |
| `ZZZPortfolioPolicy.configureResidualGap(bytes32,uint24,bytes32)` | G | main-residual-mode-geometry-policy | 3 |
| `ZZZPortfolioPolicy.configureResidualSide(bytes32,uint16,bytes32)` | G | main-residual-mode-geometry-policy | 3 |
| `ZZZPortfolioPolicy.setMode(bytes32,bool,bytes32)` | G | main-residual-mode-geometry-policy | 3 |
| `ZZZPortfolioPolicy.setTriggerBps(uint16,bytes32)` | G | main-residual-mode-geometry-policy | 2 |
| `ZZZProtocolPolicy.acceptMintRecipient()` | N | future-operating-sale-gas-VRF-policy | 0 |
| `ZZZProtocolPolicy.configureRandomness(address,bytes32,bytes32,uint256,uint16,uint32,bool,bytes32)` | B | future-operating-sale-gas-VRF-policy | 8 |
| `ZZZProtocolPolicy.proposeMintRecipient(address,bytes32)` | G | future-operating-sale-gas-VRF-policy | 2 |
| `ZZZProtocolPolicy.rotateRandomness(address,bytes32,bytes32,uint256,uint16,uint32,bool,bytes32)` | G | future-operating-sale-gas-VRF-policy | 8 |
| `ZZZProtocolPolicy.setEntryPolicy(uint128,uint128,uint16,bytes32)` | G | future-operating-sale-gas-VRF-policy | 4 |
| `ZZZProtocolPolicy.setEvolutionThresholds(uint128,uint128,bytes32)` | G | future-operating-sale-gas-VRF-policy | 3 |
| `ZZZProtocolPolicy.setGasPolicy(uint32,uint32,uint32,bytes32)` | G | future-operating-sale-gas-VRF-policy | 4 |
| `ZZZProtocolPolicy.setMaintenancePolicy(uint16,bytes32)` | G | future-operating-sale-gas-VRF-policy | 2 |
| `ZZZProtocolPolicy.setMintPrice(uint128,bytes32)` | G | future-operating-sale-gas-VRF-policy | 2 |
| `ZZZProtocolPolicy.setRandomnessRequestSettings(uint16,uint32,bytes32)` | G | future-operating-sale-gas-VRF-policy | 3 |
| `ZZZRebalanceConfirmation.configure(uint32,uint32,bytes32)` | G | sampled-confirmation | 3 |
| `ZZZRebalanceConfirmation.observe(uint256)` | K | sampled-confirmation | 1 |
| `ZZZRebalanceConfirmation.resetObservation(uint256)` | K | sampled-confirmation | 1 |
| `ZZZRebalanceConfirmation.setRequireReferenceExit(bool,bytes32)` | G | sampled-confirmation | 2 |
| `ZZZRewards.addAsset(address)` | B | fixed-LP-assets-binding-and-conversion | 1 |
| `ZZZRewards.bindConverter(address)` | B | fixed-LP-assets-binding-and-conversion | 1 |
| `ZZZRewards.convertBatch(address,uint256[],bytes32,uint256,uint256)` | K | fixed-LP-assets-binding-and-conversion | 5 |
| `ZZZRoyaltyRewards.allocateAllUnallocated(address,bytes32)` | G | original-currency-recovery-allocation | 2 |
| `ZZZRoyaltyRewards.allocateUnallocated(address,uint256,bytes32)` | G | original-currency-recovery-allocation | 3 |
| `ZZZSeaDropMint.configure((uint16,uint16,uint16,uint16,uint8,uint48,uint48,uint48,uint48,uint48,uint48,bool,bytes32,address,bytes32),uint128,bytes32)` | G | primary-sale-coordination | 17 |
| `ZZZStrategy.applyKeeperRange(bytes32)` | K | range-orientation-and-execution-quality | 1 |
| `ZZZStrategy.setAdditionalLossBps(uint16,bytes32)` | G | range-orientation-and-execution-quality | 2 |
| `ZZZStrategy.setKeeperRangePolicy(bytes32,bool,uint16,uint16,uint32,bytes32)` | G | range-orientation-and-execution-quality | 6 |
| `ZZZStrategy.setRangeOrientation(bytes32,uint8)` | G | range-orientation-and-execution-quality | 2 |
| `ZZZVault.rebalance(uint256,uint128,uint256)` | K | rebalance-and-permanent-bucket-reservation | 3 |
| `ZZZVault.reservePool(bytes32,uint256)` | G | rebalance-and-permanent-bucket-reservation | 2 |

## Evidence limits and retained rights

No production Solidity, ABI, storage, economics, guards or environment changes. LP fees and royalties remain distinct. FeeController.flushDust is module-restricted; Vault.collectFees remains public. Same-main consolidateResidual already atomically sets residual mode OFF; residual-only close does not. External swaps move current price, not existing LP bounds. Each emergency bit retains its stated guard; a raw mask never bypasses authority/accounting/terminal locks.

Source-aware behavioral and economic conclusions are recorded in the main audit and contract-family report; this generated ledger must not be cited as 1,016 independently executed security cases.
