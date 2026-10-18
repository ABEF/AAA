# PoPL integration campaign

This is the refined execution brief, not a second task-status list. Progress and
acceptance criteria remain in the [central Todo](../TODO.md#task-activation-assets).

## Corrections to the requested campaign

Wallet authorization, an available key and disposable funds do not establish a
verified deployment, adequate balances or qualified services. The current PoPL
candidate is undeployed. Production minting costs 0.05 ETH; the observed test
wallet balance of approximately 0.005 ETH cannot fund that mint plus gas.

The existing [$1 rehearsal](ONE_DOLLAR_REHEARSAL.md) is an isolated local build
with mocked dependencies and constructor guards for chain 31337. It is not a
public Robinhood deployment. Production stays at $100 with at least 99% marginal
LP deployed and network gas separate. A $1 conversion quote is not $1 activation.

The execution environment does not permit the assistant to sign or broadcast
transactions moving real digital assets. This is an execution restriction, not
a missing-key error. The assistant must not read `POPL_TEST_PRIVATE_KEY` or invoke
a signing/broadcast script. Any future public execution needs an operator-controlled
signer and independently reviewed deployment/configuration. No such script was
executed or supplied by this checkpoint.

## Refined prompt

> Advance a bounded PoPL integration campaign using three distinct evidence layers:
> public read-only observations, local Robinhood-fork execution, and separately
> identified operator-executed public transactions. Never label one layer as another.
>
> Read the current Todo, feature reference, deployment inventory and source-bound
> evidence. Reuse unchanged tests after checking their dependencies; run new tests
> only for changed behavior or an unresolved integration requirement.
>
> First verify chain 4663, a confirmed canonical block, asset provenance, proxy
> implementations and authority, contract/runtime bindings, pool/router identity,
> oracle denomination/freshness and provider capabilities. Fail closed on stale,
> inconsistent or unsupported responses. Do not infer stablecoin pegs or ZZZ prices.
>
> Exercise the complete source-to-LP path, activation and later contributions,
> shared-position accounting, guarded rebalance, funded LP fees and royalties,
> ownership transfer and current marked LP value. Compare raw balances, shares,
> liabilities and event-derived changes before and after each operation. Verify
> unclaimed fees follow ownership and rebalances preserve earlier entitlements.
> Report mocked prices, authorities, funds and randomness explicitly.
>
> Preserve production economics. The $1 variant stays isolated. Evaluate the 1%
> limit across the entire conversion and marginal LP deployment, not each swap
> separately. Keep network gas separate. Ordinary rebalances retain the 3% aggregate
> cap and existing execution guards. Revenue tests require actual funded receipts;
> trading in the zero-conventional-fee Pons pool cannot manufacture PoPL rewards.
>
> Before any operator-controlled public campaign, require an exact reviewed test
> deployment, current owner/roles, available balances, explicit per-transaction and
> total spending limits, gas reserve and stop conditions. Resolve the unchanged
> 0.05 ETH mint cost. Simulate the exact operation and refresh all time-sensitive
> checks immediately before signing. Do not relax production guards to make a test pass.
>
> Respect execution restrictions. When public broadcasting cannot be performed,
> state that restriction and continue authorized read-only/fork work without
> accessing a key. Do not report public transaction hashes or receipts for simulations.
>
> Record exact source/configuration hashes, chain/block identity, operation inputs,
> raw balance changes, assertions, failures and remaining scope. For operator-run
> public actions, record transaction hashes, confirmed receipts, gas and reorg
> handling. Keep secrets out of commands, logs, reports and Git. Fix discovered
> production defects in production with focused regression evidence; update the
> central Todo, feature reference and repository handoff accurately.

## Current execution record

The [read-only route observation](../reports/activation-route-observation/VERIFICATION.md)
reads actual USDG/WETH dependencies and four conversion quotes. The earlier
[$1 local evidence](../reports/one-dollar-rehearsal/VERIFICATION.md) and
[selected native/Pons fork evidence](../reports/range-policy/VERIFICATION.md)
retain their original scopes. They are not newly rerun or combined into a claim
of complete real-transaction testing.

No public PoPL deployment, wallet signature, transaction or receipt exists from
this campaign. Complete source-to-Pons LP execution with qualified USD pricing,
live services and wallet integration remains open. Use the owning Todo tasks;
this document does not grant release approval or close them.
