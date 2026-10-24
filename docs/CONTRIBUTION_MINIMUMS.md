**Current policy, 2026-10-24:** [Typed v4 conversions](TYPED_V4_ROUTES.md) and
[governed execution-loss limits](EXECUTION_LOSS_POLICY.md) are implemented in the
undeployed candidate. Defaults are 2% contribution, 1% conversion and 3% maintenance;
immediate governance may set each category up to a hard 10%. Existing stricter
venue/caller minima remain. Pending normal custody approvals retain their original
absolute floor. Earlier fixed-cap or v3-only descriptions below retain their
historical/default scope. Actual routes, services and independent audit remain open.

# Activation and LP top-up minimums

The production candidate requires **$100 original input value to activate** and
**$5 original input value to increase an already activated NFT's LP**. Values use
reviewed Oracle prices and token decimals; five tokens do not necessarily equal
five dollars. Native V2 values actual ETH at address zero using its two-source USD policy; legacy wrapper profiles retain their historical meaning.

[Activation Entry](../src/ZZZActivationEntry.sol) checks the original input floor.
The Vault also checks it through its fixed [Budget](../src/ZZZMigrationBudget.sol)
and [VaultCanonical validation](../src/ZZZVaultCanonical.sol).
Direct Vault calls cannot bypass the $5 rule. The effective minimum is the larger
of the action floor and the pool's configured `minDepositUSD`. The current
one-contribution-pool policy, owner/lifecycle checks and cumulative maximum remain.

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
   Governance calls `configure` or `configureNative` as appropriate through the
   AccessController's exact-operation procedure. These calls still perform full
   token, price and venue validation. Preserve unrelated parameters and selection.
3. Simulate the exact call, execute, confirm the getter/event and re-prepare quotes.
   Independently check original source value, actual new LP, unchanged incumbent
   shares and separate gas. Exercise below/exact boundaries using qualified routes.
4. To stop contributions during an incident, use dependency-free
   `disablePool(poolId,true,false)`. Full validation is required to reopen. Raising
   the minimum is a reversible configuration change; lowering it cannot remove
   the immutable $100/$5 floors. Changing sealed implementations requires the
   supported reviewed replacement process, not a parameter update.

See [the operator manual](OPERATOR_MANUAL.md#contribution-minimums) and
[preparation](ACTIVATION_PREPARATION.md). Production route/feed qualification is
still tracked in the [central Todo](../TODO.md#task-activation-assets).

## Wallet allowance and contribution are separate

New ERC-20 allowance targets the pinned Entry and the exact requested source
amount in verified token decimals. The production preparer returns only an
approval draft when allowance is insufficient, resetting an existing nonzero
insufficient allowance to zero first. After confirmation it prepares again.
It never requests an unlimited or arbitrary larger approval. Sufficient existing
allowance is reused; it is not automatically revoked or reduced. Cancelling or
failing the later contribution can leave an approval in place. Native ETH requires
no ERC-20 approval and must equal the requested transaction value.

Entry pulls exactly `amountIn`; its downstream router/Vault allowances are bounded
to the relevant amount and cleared after use. Ownership, lifecycle, expiry and
execution checks still apply to the separately confirmed contribution. The
local TEST-1 wallet follows explicit exact-approval/Entry confirmations; it is
not production extension-wallet integration or proof that every token behaves
like the mock. The port-4179 static site does not sign wallet transactions.

## Local integration and preservation

The current launcher source configures its disposable pool minimum to $5, while
activation retains the contract's $100 floor. Its whole-token TEST-1 input accepts
5-99,999 for increases and 100-99,999 for activation. The normal static preview
accepts USD examples in USDC, ZZZ, ETH or USDG; this does not qualify public routes.

New preview writes enforce $5. Existing v7 histories retain smaller historical
top-ups when replayed; user holdings are not reset. The isolated $1 activation
rehearsal continues to change only its copied activation floor, not production.

Existing running Anvil deployments are not patched by editing source. This change
did not restart port 8892, change its pool configuration or discard its state.
Rebuild with source-matched artifacts and start a separate disposable session to
exercise the new deployed rule. Preserve wanted receipts before intentionally
replacing a session; see [local setup](LOCAL_TEST_STACK.md).
