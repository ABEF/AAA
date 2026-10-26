# Callable and source coverage

[Final prompt](PROMPT.md), [review](REVIEW.md) and [verification](VERIFICATION.md)
explain the scope. The tables link each concrete contract to its full function
scenario matrix, including inherited/generated getters, constructor and receiver.
Each callable row has at least three relevant static cases, source location,
property and evidence status. This is not a per-row execution pass or a proof of
every possible input/order/state.

| Contract | Functions | Constructor | Receive | Detailed matrix |
| --- | ---: | ---: | ---: | --- |
| [ZZZAccessController](../../src/ZZZAccessController.sol) | 33 | 1 | 0 | [Cases](custody-review.json) |
| [ZZZActivationAssets](../../src/ZZZActivationAssets.sol) | 14 | 1 | 0 | [Cases](principal-review.json) |
| [ZZZActivationAssetsFactory](../../src/ZZZActivationAssetsFactory.sol) | 3 | 1 | 0 | [Cases](principal-review.json) |
| [ZZZActivationEntry](../../src/ZZZActivationEntry.sol) | 17 | 1 | 1 | [Cases](principal-review.json) |
| [ZZZBuyback](../../src/ZZZBuyback.sol) | 6 | 1 | 1 | [Cases](custody-review.json) |
| [ZZZCanonicalHandoff](../../src/ZZZCanonicalHandoff.sol) | 38 | 1 | 0 | [Cases](custody-review.json) |
| [ZZZClaimRouter](../../src/ZZZClaimRouter.sol) | 5 | 1 | 0 | [Cases](rights-review.json) |
| [ZZZCompounder](../../src/ZZZCompounder.sol) | 2 | 1 | 0 | [Cases](principal-review.json) |
| [ZZZContributionPricing](../../src/ZZZContributionPricing.sol) | 12 | 1 | 0 | [Cases](principal-review.json) |
| [ZZZCustodyValidation](../../src/ZZZCustodyValidation.sol) | 5 | 1 | 0 | [Cases](custody-review.json) |
| [ZZZFeeController](../../src/ZZZFeeController.sol) | 17 | 1 | 1 | [Cases](custody-review.json) |
| [ZZZFeesCanonical](../../src/ZZZFeesCanonical.sol) | 14 | 1 | 1 | [Cases](custody-review.json) |
| [ZZZLPRewardConverter](../../src/ZZZLPRewardConverter.sol) | 20 | 1 | 1 | [Cases](rights-review.json) |
| [ZZZLiquidityManager](../../src/ZZZLiquidityManager.sol) | 14 | 1 | 1 | [Cases](principal-review.json) |
| [ZZZMembership](../../src/ZZZMembership.sol) | 13 | 1 | 0 | [Cases](rights-review.json) |
| [ZZZMigration](../../src/ZZZMigration.sol) | 25 | 1 | 1 | [Cases](custody-review.json) |
| [ZZZMigrationBudget](../../src/ZZZMigrationBudget.sol) | 37 | 1 | 0 | [Cases](custody-review.json) |
| [ZZZNFT](../../src/ZZZNFT.sol) | 64 | 1 | 0 | [Cases](rights-review.json) |
| [ZZZNFTCanonical](../../src/ZZZNFTCanonical.sol) | 10 | 1 | 0 | [Cases](rights-review.json) |
| [ZZZNFTMetadata](../../src/ZZZNFTMetadata.sol) | 3 | 1 | 0 | [Cases](rights-review.json) |
| [ZZZOracle](../../src/ZZZOracle.sol) | 24 | 1 | 0 | [Cases](principal-review.json) |
| [ZZZPoolRegistry](../../src/ZZZPoolRegistry.sol) | 14 | 1 | 0 | [Cases](principal-review.json) |
| [ZZZPythPriceFeed](../../src/ZZZPythPriceFeed.sol) | 11 | 1 | 0 | [Cases](principal-review.json) |
| [ZZZRewards](../../src/ZZZRewards.sol) | 41 | 1 | 1 | [Cases](rights-review.json) |
| [ZZZRoyaltyConverter](../../src/ZZZRoyaltyConverter.sol) | 20 | 1 | 1 | [Cases](rights-review.json) |
| [ZZZRoyaltyFactory](../../src/ZZZRoyaltyFactory.sol) | 2 | 1 | 0 | [Cases](rights-review.json) |
| [ZZZRoyaltyRewards](../../src/ZZZRoyaltyRewards.sol) | 57 | 1 | 1 | [Cases](rights-review.json) |
| [ZZZStrategy](../../src/ZZZStrategy.sol) | 15 | 1 | 0 | [Cases](principal-review.json) |
| [ZZZV4RouteExecutor](../../src/ZZZV4RouteExecutor.sol) | 11 | 1 | 1 | [Cases](principal-review.json) |
| [ZZZVault](../../src/ZZZVault.sol) | 37 | 1 | 1 | [Cases](principal-review.json) |
| [ZZZVaultCanonical](../../src/ZZZVaultCanonical.sol) | 24 | 1 | 1 | [Cases](custody-review.json) |

[Machine coverage](coverage.json) checks31contracts/652rows,608 functions plus
31 constructors/13 receivers, with1,987 scenario instances. Every catalog row appears
exactly once. All44 project source units and relevant transitive helpers are
identified/pinned; an interface/abstract/library is not another deployed contract.
The remaining NFT canonical interface was directly checked for record/header,
trait/randomness/ordinal signatures and the concrete privileged write callers.

[Principal](PRINCIPAL.md), [rights](RIGHTS.md), [custody](custody-review.md) and
[backend](BACKEND.md) reports explain the interactions. [Financial/backend pins](backend-rights-review.json)
and [127operator-function rows](ops-review.json) complement the contract matrix.
Nested helper inventories and inherited getters reuse their appropriate case
families; their number does not create additional executed checks.

All production contract source/dependency/build pins remain unchanged. Prior
Slither triage, normal object gates, actual-v4 and randomized reward evidence
retain their exact scopes. Fresh evidence is the244affected Python methods (241 passes/3 explicit skips),
including42 new methods once; no new Solidity/static/full-release execution is implied.

Unqualified provider/token/marketplace/service/gas/recovery inputs remain release
gates. Complete function inventory is useful audit preparation, not independent
audit approval or a promise that no vulnerability exists.
