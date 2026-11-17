# Repaired test infrastructure: baseline dependency exposure

This map locates dependent declarations. It does not prove execution,
assertion strength or branch coverage. Behavior reviews and finite
observations are recorded separately.

| Consumer | Changed test roots in dependency closure | Declared methods |
| --- | --- | ---: |
| `test/AdaptableTerms.t.sol` | `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 6 |
| `test/AtomicActivationIntegration.t.sol` | `test/AtomicActivationIntegration.t.sol`, `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 8 |
| `test/BucketCapacity.t.sol` | `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 2 |
| `test/BuybackExecution.t.sol` | `test/BuybackExecution.t.sol`, `test/RewardsAndFees.t.sol` | 25 |
| `test/CanonicalHandoff.t.sol` | `test/CanonicalHandoff.t.sol`, `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol`, `test/helpers/CanonicalNativeVenue.sol` | 39 |
| `test/CanonicalPreparation.t.sol` | `test/CanonicalPreparation.t.sol`, `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol`, `test/helpers/CanonicalNativeVenue.sol` | 7 |
| `test/CollectionScale.t.sol` | `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 3 |
| `test/CombinedCapacityGas.t.sol` | `test/CombinedCapacityGas.t.sol`, `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 5 |
| `test/CompoundInterval.t.sol` | `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 6 |
| `test/ContributionBudgetIsolation.t.sol` | `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 6 |
| `test/ContributionEntryPriceSecurity.t.sol` | `test/AtomicActivationIntegration.t.sol`, `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 6 |
| `test/ContributionMarkPacking.t.sol` | `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 2 |
| `test/ContributionPool.t.sol` | `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 7 |
| `test/ContributionPriceSecurity.t.sol` | `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 10 |
| `test/ContributionThreePercent.t.sol` | `test/ContributionThreePercent.t.sol`, `test/MigrationBudgetAdversarial.t.sol`, `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 9 |
| `test/CurrentNativePoolFork.t.sol` | `test/CurrentNativePoolFork.t.sol` | 11 |
| `test/CustodyParking.t.sol` | `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 11 |
| `test/DynamicAccounting.t.sol` | `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 4 |
| `test/EntryExecutionBudget.t.sol` | `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 5 |
| `test/EntryReviewPolicy.t.sol` | `test/AtomicActivationIntegration.t.sol`, `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 6 |
| `test/ExactLPVaultWire.t.sol` | `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 1 |
| `test/GlobalMembershipDust.t.sol` | `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 8 |
| `test/GovernedExecutionLoss.t.sol` | `test/GovernedExecutionLoss.t.sol`, `test/MigrationBudgetAdversarial.t.sol`, `test/RebalanceBudget.t.sol`, `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 9 |
| `test/HarvestAudit20261106.t.sol` | `test/OptionalPortfolioCore.t.sol`, `test/RewardsAndFees.t.sol` | 3 |
| `test/HolderCollectiveExit.t.sol` | `test/HolderCollectiveExit.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 26 |
| `test/IntegratedEconomicConservation.t.sol` | `test/IntegratedEconomicConservation.t.sol` | 18 |
| `test/KeeperCompletion.t.sol` | `test/KeeperCompletion.t.sol`, `test/MigrationBudgetAdversarial.t.sol`, `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 9 |
| `test/LPOnlyEntryBoundary.t.sol` | `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 2 |
| `test/MaintenanceCadence.t.sol` | `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 11 |
| `test/MetadataLifecycleNotifications.t.sol` | `test/HolderCollectiveExit.t.sol`, `test/MetadataLifecycleNotifications.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 10 |
| `test/MigrationBudgetAdversarial.t.sol` | `test/MigrationBudgetAdversarial.t.sol`, `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 13 |
| `test/MigrationExecutionBudget.t.sol` | `test/MigrationExecutionBudget.t.sol`, `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 6 |
| `test/NFTOwnershipRights.t.sol` | `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 7 |
| `test/NFTRightsInvariants.t.sol` | `test/NFTRightsInvariants.t.sol`, `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 4 |
| `test/NativeCanonicalIntegration.t.sol` | `test/NativeCanonicalIntegration.t.sol`, `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol`, `test/helpers/CanonicalNativeVenue.sol` | 2 |
| `test/NativeFeeRewards.t.sol` | `test/NativeFeeRewards.t.sol` | 22 |
| `test/NativeVaultFlows.t.sol` | `test/NativeVaultFlows.t.sol` | 23 |
| `test/OperatorControls.t.sol` | `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 12 |
| `test/OperatorSealArtwork20261117.t.sol` | `test/OperatorSealArtwork20261117.t.sol` | 3 |
| `test/OptionalPortfolioCore.t.sol` | `test/OptionalPortfolioCore.t.sol` | 82 |
| `test/PoolSwitching.t.sol` | `test/PoolSwitching.t.sol`, `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 6 |
| `test/PooledEntry.t.sol` | `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 4 |
| `test/PooledRewards.t.sol` | `test/PooledRewards.t.sol`, `test/RewardsAndFees.t.sol` | 8 |
| `test/PooledSecurity.t.sol` | `test/PooledSecurity.t.sol`, `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 13 |
| `test/PortfolioAccounting.t.sol` | `test/PortfolioAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 17 |
| `test/ProductionGas.t.sol` | `test/ProductionGas.t.sol`, `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 4 |
| `test/ProductionInvariants.t.sol` | `test/ProductionInvariants.t.sol`, `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 3 |
| `test/RebalanceBudget.t.sol` | `test/MigrationBudgetAdversarial.t.sol`, `test/RebalanceBudget.t.sol`, `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 7 |
| `test/ReservationCapacity.t.sol` | `test/ReservationCapacity.t.sol`, `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 12 |
| `test/RewardsAndFees.t.sol` | `test/RewardsAndFees.t.sol` | 22 |
| `test/RewardsCheckpointCaching.t.sol` | `test/RewardsAndFees.t.sol` | 6 |
| `test/RoyaltyAudit20261105.t.sol` | `test/RoyaltyRecovery.t.sol` | 33 |
| `test/RoyaltyLaunchWindow.t.sol` | `test/RoyaltyRecovery.t.sol` | 18 |
| `test/RoyaltyNoCustodian.t.sol` | `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 4 |
| `test/RoyaltyRecovery.t.sol` | `test/RoyaltyRecovery.t.sol` | 11 |
| `test/SeaDropArtworkBoundary20261117.t.sol` | `test/SeaDropArtworkBoundary20261117.t.sol` | 1 |
| `test/SeaDropFullHandoff.t.sol` | `test/SeaDropFullHandoff.t.sol`, `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol`, `test/helpers/CanonicalNativeVenue.sol` | 2 |
| `test/SealCriticalInputs20261117.t.sol` | `test/SealCriticalInputs20261117.t.sol` | 5 |
| `test/UniswapV4Fork.t.sol` | `test/UniswapV4Fork.t.sol` | 6 |
| `test/VaultAccounting.t.sol` | `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 35 |
| `test/helpers/AccountingExecutionFixture.sol` | `test/helpers/AccountingExecutionFixture.sol` | 0 |
| `test/helpers/CanonicalNativeVenue.sol` | `test/helpers/AccountingExecutionFixture.sol`, `test/helpers/CanonicalNativeVenue.sol` | 0 |
| `test/helpers/CanonicalPreparationFixtures.sol` | `test/VaultAccounting.t.sol`, `test/helpers/AccountingExecutionFixture.sol` | 0 |
