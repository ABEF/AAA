# Operator-selected 32M contribution profile

19 November 2026. Baseline main: `f1ef361cccfd5d88136463c9cdd107491aca67ef`.
Production remains undeployed and NOT APPROVED.

The operator selected a **32,000,000 gas activation/growth ceiling**. The existing
schema2 preparation already accepts this value, so no Solidity, accounting,
financial safeguard or production Python implementation changes are needed.
The [new candidate](../../config/activation-gas-32m.candidate.json) provides the
exact backend decimal string and matching website integer. It is an incomplete,
non-live overlay, with all fee/provider/release approvals false or unresolved.

## Meaning and unchanged boundaries

- Full 20% estimate padding remains mandatory. The largest admissible estimate
  at this ceiling is 26,666,666 gas; 26,666,667 is refused.
- Each review proposes its exact padded estimate, rather than automatically
  requesting the entire 32M ceiling. A 16,460,899 estimate still proposes
  19,753,079. A larger ceiling does not change that operation's measured work.
- Legacy activation/claim defaults remain 12M. Keeper/manual maintenance remains
  the separate 24M profile with full 25% padding. Source-call, royalty-read/sync,
  solver and payout subcall budgets remain unchanged.
- Network-fee, gas-price and wallet-funding limits remain separate. The candidate
  supplies no fee ceiling, credential, live address, approval or signing ability.
- There is no on-chain gas setter or new seal prerequisite. Future adoption uses
  the existing reviewed configuration/identity/restart procedure; recover saved
  operations under their original records first. No service is changed here.

## Network capacity is a separate prerequisite

The [13 November reads](../gas-profiles-20261113/network/REVIEW.md) observed
32M transaction and block **execution** parameters. The Nitro header's `2^50`
gas limit is synthetic and is not execution capacity. The current API's header
clamp is only a header check; it does not authenticate ArbGasInfo's transaction
execution parameter or a provider's capacity.

A single bounded refresh on 19 November failed locally with `URLError` on its
first identity request. No state was obtained, no higher cap was demonstrated,
and no automatic endpoint adoption or stress request followed. The candidate
therefore explicitly leaves current execution/provider limits unverified.
Before any rollout, freshly verify the actual transaction/block limits,
provider call/estimate/trace bounds and complete Nitro fee semantics. Smaller
limits remain binding. A 32M ceiling does not authorize 32M of raw work plus
another 20%; the margin must fit inside the ceiling, with data-posting accounting
qualified separately.

## Verification and evidence scope

Seven NEW injected-RPC methods in
[test_reviewed_gas_profile_32.py](../../tests_python/test_reviewed_gas_profile_32.py)
pass. They verify the new configuration and exact padding boundary, lower-header
constraint, unchanged defaults and historical identities, distinct fee/price/
funding refusals, incomplete-fee rejection and exact smaller proposed allowance.
The [verification record](VERIFICATION.json) retains the single-run result,
exact source hashes, failed network refresh and preservation observations.
The test module imports an older fixture without inheriting or rerunning its
test methods. It is registered in the maintained runner for future selection.

The [existing F6 EVM results](../activation-final-six-20261118/REVIEW.md) remain
20M evidence at their original source/configuration. No old result is relabelled
32M, and no unchanged suite, compiler, static analysis, EVM campaign or existing
node is rerun. Current 32M full-state/real-market/provider/complete-fee acceptance
is still open, including expanded currencies and both physical LP positions.

The Todo, feature/findings reference, operator/configuration guides, roadmap,
release record and repository memory distinguish the selected 32M candidate
from historical 20M evidence. Existing sites, Anvil state, journals, public null
configurations, signer and paused heartbeat remain unchanged.
