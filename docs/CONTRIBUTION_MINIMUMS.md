# Activation and LP top-up minimums

The production candidate requires **$100 original input value to activate** and
**$5 original input value to increase an already activated NFT's LP**. Values use
reviewed Oracle prices and token decimals; five tokens do not necessarily equal
five dollars. Native ETH uses the admitted wrapper's valuation.

Both [Activation Entry](../src/ZZZActivationEntry.sol) and the Vault's fixed
[contribution budget helper](../src/ZZZMigrationBudget.sol) enforce the floors.
Direct Vault calls cannot bypass the $5 rule. The effective minimum is the larger
of the action floor and the pool's configured `minDepositUSD`. The current
one-contribution-pool policy, owner/lifecycle checks and cumulative maximum remain.

The existing execution budget still requires at least **99% of original value
as marginal new LP**, with gas separate. Thus a $5 top-up must add at least $4.95
of LP; a $100 activation must add at least $99. Existing LP, idle or rewards cannot
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
