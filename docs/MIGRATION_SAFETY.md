# Local LP maintenance and collection preparation safety

This guide covers fresh accounting6/custody4/portfolio2/canonicalV6. The removed bridge and
external custody executors are historical. Use [current movement/exit choices](GOVERNED_CUSTODY_HANDOFF.md),
[loss policy](EXECUTION_LOSS_POLICY.md) and [same-chain handoff](CANONICAL_HANDOFF.md).

## Aggregate maintenance budget

Guarded same-pair moves, resume and ordinary rebalancing capture starting LP plus
attributed idle at fixed initial prices, add actual released compound, then
compare final LP plus idle using that same vector. Default 3% means 97% retained,
not 97% deployed. The 5% idle ceiling, nonzero LP, per-step and stronger caller
floors remain. Optional hybrid replacement must leave the actual new main active,
at least 60% main and at most 40% residual of retained value including idle at captured
starting prices. Both physical legs are harvested/closed and backing/fingerprints
include both; no hidden auxiliary can remain. Governance may set future maintenance up to 10%; callbacks cannot
weaken a captured operation. Gas is separate.

Other buckets, donations, claims, royalties and buyback reserves cannot subsidize
principal. Failure reverts the atomic action; per-operation caps do not bound
cumulative turnover, impermanent loss or future market loss. Contributions instead
require marginal deployed LP under their captured default 2% cap/caller maximum,
conservative price bounds and$100/$5 original-value minima.

Same-pair movement cannot turn ETH into WETH or exchange ZZZ for a new token.
Governed parking closes into attributed Vault idle with reviewed close-only raw
minima. Terminal collective return closes all buckets without swaps and returns
actual ETH/ZZZ to current NFT owners under its own total-principal raw minima;
neither path promises 3% USD retention or sends funds to an operator custodian.
Broken venues/tokens can still block closure or payment.

The separate globally paused governance emergency manifest may deliberately
disable selected economic/timing checks. It never redirects custody or rewrites
shares/rewards; financial bypass can lose nearly all principal. It is not an
ordinary maintenance fallback. [Emergency procedure](EMERGENCY_REBALANCE.md).

## Preparation and canonical replacement

Governance announces an exact `PreparationNotice` through the direct controller;
there is no scheduled executor. Preparation stops new work/configuration while
permitted existing claims, transfers, original reveal, harvest and reviewed
parking retain their own guards. Cancel only the exact notice. The manual and
function reference own callable inputs and permissions.

Preparation alone neither retires the source nor activates a successor. Before
terminal holder exit starts, compatible same-chain handoff freezes ownership and
accounting, exports/imports complete bounded domains, verifies exact classified
backing and atomically retires/activates one deployment. Funded abort restores
source rights. Existing draws must finish and all funded LP must be parked,
with both physical legs closed and activeSecondaryCount zero before export;
there is no external custody return/completion ingress. An unfulfilled original
draw or unreadable backing may block handoff without blocking unrelated rights.

The keeper rejects malformed preparation/lifecycle reads before new work and
preserves pending receipt recovery. Runtime/profile changes require reviewed
configuration and journal reconciliation, never a relabel or reset.

After `lpExitStarted`, canonical replacement and new principal work stay blocked
permanently. This importer does not transport terminal principal-payout ledgers.
Bridges, remote ledgers/finality and post-halt recovery are outside the release;
they are not launch prerequisites or capabilities supplied by a config change.
Actual providers, target gas/recovery and independent audit remain unqualified.
