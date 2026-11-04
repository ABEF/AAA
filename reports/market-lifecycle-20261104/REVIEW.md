# Market, LP lifecycle, accounting and recovery campaign

November4,2026; baseline main `44f5fa7db5d8472e4cd8f3e1af13a4b9dc27fa09`.
Production **NOT APPROVED**. [Scenario coverage](COVERAGE.md),
[verification and retained failures](VERIFICATION.md).

## What this campaign improves

The actual local Uniswap v4 fixture now has a multi-holder receipt model, rather
than relying only on successful transactions or aggregate balances. It replays
each actual `PoolRewardsCredited` event against the shares and equal collective
membership captured BEFORE that operation. Separate individual/collective
fractions and prior claims are maintained outside the production reward ledger.
Every modeled NFT's exact raw claim is reconciled after entries, harvests,
compounding, replacements and claims. No production index/fraction/accrual getter
supplies the model.

New composed journeys exercise ETH and fixed-ZZZ direct Entry3; main-only growth;
repeated one/two/one modes; rising/falling/reversing prices; new members before
and after replacement; a mixed residual while disable is pending; wholly outside
inventory; ordinary samples during cooldown; price disagreement and recovery;
transfers; separate rarity royalties and terminal current-owner payouts.
Multiple NFTs per wallet and a dormant NFT are included.

Independent assertions reconcile actual raw main+residual inventory, Vault-owned
LP IDs, live-leg bounds, attributed idle/compound, per-NFT current value, fair
share issuance at post-swap incumbent NAV, exact source approvals, unchanged
residual L/centre/clock on entry, funded liabilities and actual wallet payouts.
The 60/40 bounds are replacement constraints, never permanent wallet weights.

The actual current-profile API and worker code also gain composed transcript
tests. A long-lived Projection follows single/dual/pending-disable/residual-close
snapshots without retaining old backing. Price failure preserves custody and raw
claims. Missing or inconsistent residual custody fails closed. Worker decisions
wait at the adjustment threshold, outside range or pending geometry, survive a
restart, preserve price-independent harvest review, and recover pending work
before attempting broken new-work reads. These are inert RPC tests, not a daemon
or a live deployment.

## Findings and corrections

1. **Operator profile mismatch corrected.** One current deployment-boundary
   sentence still named Migration custody4 while the executable candidate and
   authority guide require custody5. It now requires5 and explicitly preserves
   historical4. No old deployment or journal is relabelled.
2. **Economic rounding is now explicit.** USD marking sums each asset's actual
   principal components before rounding. Individual and collective raw reward
   fractions remain separate; combining them can invent a spendable raw unit.
   The new model originally made both mistakes; failed runs are retained and
   the model was corrected. Production rounding/guards were not relaxed.
3. **Current-profile composed coverage strengthened.** The model follows cohorts
   and fractional claims across transitions that earlier two-NFT aggregate
   checks did not independently reconstruct. Existing shared harvest helper now
   returns its captured logs so the model can consume the SAME actual receipt.
4. **No production contract defect was established by these selected scenarios.**
   Contract implementations, authority, economics, profiles and normal build
   settings remain unchanged. New assurance is scoped to the executed methods;
   it does not certify every function or market.

## How the request was challenged

An infinite market cannot be tested100%. The campaign enumerates reachable
geometry/lifecycle classes and labels fresh execution, inspected behavior,
historical scoped evidence and external gaps. It does not call report reading a
new security audit. Main/residual are two positions in one pool, not two pools;
the nested residual cannot normally be active while main geometry is inactive.
Mode ON permits rather than forces a residual; contributions increase main but
purchase shares of the aggregate bucket. Current owner, earned rewards, raw
claims, converted balances and returned principal are separate concepts.

A second review of the plan required pre-operation participant snapshots,
independent receipt/fraction accounting, actual marginal deployed LP, failed-call
rollback checks and recovery, both ordinary timing and explicit operator-change
exceptions. It rejected profitable-strategy, uninterrupted-uptime, real-oracle,
MEV-immunity and100-user claims from controlled local swaps or virtual time.
It retained prior authority/callback/maximum-holder evidence at its stated source
scope instead of rerunning every unchanged suite.

## Operator consequences and limits

There are no new calls, parameters, permissions, restarts or automatic fallback.
Use custody5 for the fresh candidate; keep keeper principal_distribution disabled.
Main contributions never apply a pending merge or reset the hard clock. A desired
mode change is not successful LP replacement. Raw funded claims remain distinct
from unavailable USD marks. Individual and collective fractions are not a sweepable
balance; returned principal and claims are not newly generated fees.

Actual feeds/routes/VRF/authorities/OpenSea, target-chain gas and economics,
matching source8 services/site, Unix storage/restore and long-lived history,
receiver/dependency liveness and independent audit remain open. Synthetic feeds
in the EVM campaign deliberately follow core price; they do not qualify source
independence or attacker profitability. No existing Anvil, NFT/LP/balance, wallet,
pending journal, site, service, signer or paused heartbeat changed.
