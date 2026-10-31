# Activation and LP top-up minimums

Fresh accounting6 supports [governance-triggered collective holder return](HOLDER_COLLECTIVE_EXIT.md).
After LP closes, each NFT retains unpaid proportional ETH+ZZZ principal, old
rewards and future royalty eligibility. Direct payouts are separate from income;
no holder principal withdrawal exists during normal operation. LP cannot reopen
after exit starts. Historical deployments keep their original rules.


The production candidate defaults to **$100 original input value to activate**
and **$5 to grow LP**. ProtocolPolicy governs future minima (USD18), each at least
$1 and growth no greater than activation. Existing activations/shares do not change. Values use
reviewed Oracle prices and token decimals; five tokens do not necessarily equal
five dollars. Current accounting6 values actual ETH at address zero using its
two-source USD policy. Native ETH and fixed ZZZ are the only original inputs;
legacy deployments retain their actual profiles.

[Activation Entry](../src/ZZZActivationEntry.sol) checks the original input floor.
The Vault also checks it through its fixed [Budget](../src/ZZZMigrationBudget.sol)
and [VaultCanonical validation](../src/ZZZVaultCanonical.sol).
Direct Vault calls cannot bypass the current governed growth minimum. The effective minimum is the larger
of the action floor and the pool's configured `minDepositUSD`. The current
one-contribution-pool policy, owner/lifecycle checks and cumulative maximum remain.
Fresh6 entrants increase only the existing main ticks; incumbent residual/idle/
compound stay in checkpointed NAV and cannot satisfy the new contribution floor.

At the current 2% default, the captured execution budget requires at least
**98% of conservative original value as marginal new LP**, with gas separate.
A $5 top-up therefore needs at least $4.90 of LP and $100 activation at least $98.
Read the governed cap for the exact deployment; old fixtures may retain 1%. Existing LP, idle or rewards cannot
subsidize it. A route that cannot meet the limit reverts; the smaller minimum does
not promise that every route or market condition will support a $5 transaction.

## Operator procedure

1. Read the selected pool's complete `accounting(poolId)` configuration and current
   authority/canonical state. The deployed binary must include these floors.
2. To allow $5 top-ups, set `minDepositUSD` to `5e18` in the full reviewed config.
   Governance calls `configureNative` for the supported native ETH/fixedZZZ pool directly from the
   selected governance wallet; Access has no generic/scheduled executor. These calls still perform full
   token, price and venue validation. Preserve unrelated parameters and selection.
3. Simulate the exact call, execute, confirm the getter/event and re-prepare quotes.
   Independently check original source value, actual new LP, unchanged incumbent
   shares and separate gas. Exercise below/exact boundaries using qualified routes.
4. To stop contributions during an incident, use dependency-free
   `disablePool(poolId,true,false)`. Full validation is required to reopen. Raising
   the minimum is a reversible configuration change; lowering the pool minimum cannot remove
   the current helper minima. Governance separately uses ProtocolPolicy.setEntryPolicy
   for future action floors; fresh reviews capture its exact fingerprint. Changing sealed implementations requires the
   supported reviewed replacement process, not a parameter update.

See [the operator manual](OPERATOR_MANUAL.md#contribution-minimums) and
[preparation](ACTIVATION_PREPARATION.md). Production route/feed qualification is
still tracked in the [central Todo](../TODO.md#task-activation-assets).

## Wallet allowance and contribution are separate

New ERC-20 allowance targets the pinned Entry and the exact requested source
amount in verified token decimals. The production preparer returns only an
approval draft when allowance is insufficient, replacing it with exactly the
requested amount even when the previous allowance is smaller and nonzero.
Tokens requiring a separate zero-reset fail simulation and are unsupported by
this at-most-two-send flow. After approval confirmation, prepare again.
It never requests an unlimited or arbitrary larger approval. Sufficient existing
allowance is reused; it is not automatically revoked or reduced. Cancelling or
failing the later contribution can leave an approval in place. Native ETH requires
no ERC-20 approval and must equal the requested transaction value.

Entry pulls exactly `amountIn`; its downstream router/Vault allowances are bounded
to the relevant amount and cleared after use. Ownership, lifecycle, expiry and
execution checks still apply to the separately confirmed contribution. The
local disposable wallets exercise explicit exact-approval/Entry confirmations;
they are not public-wallet qualification or proof that every actual token behaves
like a mock. Public website deployment remains null and signing Anvil-only.

## Local integration and preservation

Existing deployments retain the minimums compiled into their actual bytecode.
Source edits do not patch their storage, reset NFTs or change saved journals.
Historical mock currencies and older USDC/USDG examples do not describe the
current ETH/ZZZ production input policy. A separately copied $1 rehearsal is
local-only and cannot qualify the production $100 activation floor.

Preserve historical preview events and wanted receipts rather than rejecting or
rewriting them to fit a new display rule. Use a separate source-matched disposable
session for a newly reviewed profile; see [local setup](LOCAL_TEST_STACK.md).
Actual routes, dual-price observations, wallet/API services and target-chain gas
remain release work. A minimum is not a capital guarantee: current LP value can
fall after execution, and holders cannot redeem principal during normal operation.
Fresh accounting6/custody4/portfolio2/canonicalV6 permanently stops activation and growth
once governance begins collective LP retirement, even after ordinary unpause.
Only governance starts/closes that exit; later permissionless allocation and
direct delivery cannot redirect the fixed current-owner entitlements. Normal
holders need no transaction to receive principal; failed receivers have retry or
exceptional owner-only fallback. The optional keeper `principal_distribution`
job implements bounded allocation/delivery after governance closure; it is
disabled by default and no installed service has been changed.
