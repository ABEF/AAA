# Activation and maintenance gas feasibility

Baseline `db509fbf4e357e5aec1d614ce66923fea0594d7e`; 11 November 2026.
Source improvements and bounded public reads, **not production approval or a
deployment**. Defaults, financial safeguards, public signing, services, websites,
existing Anvil state, journals and the paused heartbeat are unchanged.

## Outcome

The Oracle now reads the configured source-call gas ceiling once per complete
STATIC capture/validation chain. It passes that local value through its private
source reads instead of repeatedly calling Access and ProtocolPolicy. Each later
validation reads it afresh. Ordinary observations/admission retain fresh reads;
no value is cached across mutable calls or transactions. All full source/market,
callback, authority and financial proofs remain. A single comparison also obtains
the same minimum/maximum source values; the exact agreement inequality is unchanged.

Cold activation is about **4.4% cheaper**, and growth about **4.7–4.8% cheaper**,
in the like-for-like controlled fixture. They still reject the unchanged 12M
default. Complete maintenance measurements now replace speculation based on
router-only costs. A working anonymous Robinhood RPC establishes dated 32M
transaction/block execution parameters; it does not qualify the full provider,
market, gas-estimation or fee path.

## Measured Entry improvement

These are cold external-call `gasleft()` deltas, excluding transaction intrinsic
and network data-fee estimation. The original fixture uses $1,000 activation and
100 input-token growth, controlled depth, feeds and VRF. It is not the website's
exact $100 market qualification. [Exact measurements](verification/GAS.json).

| Operation | Original raw gas | Current raw gas | Saving | Current ×1.20, rounded up |
| --- | ---: | ---: | ---: | ---: |
| ETH activation |15,317,541|14,636,780|680,761 / 4.44%|17,564,136|
| ZZZ activation |15,644,361|14,963,971|680,390 / 4.35%|17,956,766|
| ETH growth |14,103,737|13,422,920|680,817 / 4.83%|16,107,504|
| ZZZ growth |14,404,957|13,724,583|680,374 / 4.72%|16,469,500|
| Second ZZZ entrant |15,038,024|14,357,635|680,389 / 4.52%|17,229,162|

All exact default-12M probes still reject with atomic rollback. The displayed
20% numbers are arithmetic on measured call costs, **not fresh RPC estimates or
admitted transaction envelopes**. The backend must still obtain its own complete
estimate, headroom, fee and canonical-state proofs. Existing optional policy2
remains unadopted; no automatic larger-budget retry is added.

The four original actual-owner RPC fixtures were reused for attribution only,
with their original source/runtime identities. Their trace gas, estimates and
refund accounting are different metrics from the table. They were neither
re-executed nor relabeled as this optimized runtime.

## Complete maintenance, including two LP legs

These new measurements use a separate one-activated-NFT cohort with real
Compounder/Vault/Budget/Pricing/Manager and installed local Uniswap core,
StateView and PositionManager. They are full outer operations, not only balance
quotes. Controlled registry, authority, Permit2, prices and depth remain seams.
They establish no maintenance before/after saving or full-collection worst case.

| Full operation | Raw call gas | Keeper ×1.25, rounded up |
| --- | ---: | ---: |
| Harvest main |661,011|826,264|
| Compound into existing main |10,680,943|13,351,179|
| Ordinary single-main rebalance |13,447,522|16,809,403|
| Open optional main + residual |16,324,139|20,405,174|
| Harvest both legs |1,016,015|1,270,019|
| Next replacement closing both legs |16,631,798|20,789,748|

Harvesting stays independent and applies actual 80/10/5/5 once. Compounding
preserves shares/main geometry; ordinary replacement preserves the hard 12-hour
cooldown, 600-second sampled confirmation and 300-second maximum gap. Hybrid
replacement verifies old legs are closed and the new physical portfolio remains
accounted. Source failures retain principal, earned backing and atomic rollback.

Raw compound execution fits a diagnostic 12M call, but its full 20% unsigned
margin (12,817,132) and 25% keeper margin do not. Neither that raw success nor
the historical 2.5M blocked keeper example is a qualified operating budget.
Real estimates, calldata, route count, token behavior, cohorts, royalty capacity
and historical buckets can change cost. Keep each service's existing budget,
padding and daily/network-fee limits until separately reviewed configuration.

## Live chain and fees

The [read-only network report](network/REVIEW.md) records chain 4663 at block
111632516, rechecked by hash, plus a later matching selected-core code hash.
ArbGasInfo reports **32,000,000 transaction and block execution parameters**;
the header's `2^50` gas limit is synthetic and cannot be used as capacity.

Pinned base fee was **0.020132 gwei**. Its zero L1 price estimate is a snapshot,
not a permanent promise. Standard total estimation includes the posting component;
do not add it twice. No complete target-chain PoPL fee quote or public receipt
was obtained. See the [operator gas procedure](../../docs/ROBINHOOD_GAS.md) and
[raw decoded observations](network/LIMITS.json) for sources and interpretation.

The working BlockVectra public tier advertises 3 requests/second and only 900
recent blocks. An actual archived-anchor read fails. Numerical call/estimate
gas ceilings and sustained workload remain unqualified. It is a useful discovery,
not a replacement production/archive/trace provider configuration. Access
denials from other providers are preserved, not treated as chain outages.

The controlled costs are below the observed execution parameters, but that
does not establish provider admission, actual fee/data semantics, inclusion
throughput or real-market success. Concurrent website activity cannot be mapped
directly to simultaneous chain inclusion.

## Code size and security tradeoff

The unchanged normal compiler profile passes all 48 runtime/initcode gates.
Oracle is **24,573 bytes, only 3 bytes below the project limit**, versus 24,488
before this gas optimization: an 85-byte increase buys lower recurring execution
cost. Creation plus its 64-byte arguments is 48,530 bytes. Vault remains
24,544 bytes / 32-byte runtime margin. No gate or compiler setting was loosened.

All 191 compiled project ABI entities and semantic storage layouts are unchanged;
only Oracle creation/runtime bytes differ. The full 49-word transient decoder,
writer, clearing, quote loader, controls, caller checks and round decoder remain
unchanged. Broader manual-decoder/compact-object experiments failed size limits
and were rejected. [Source/equivalence proof](build/EQUIVALENCE.json),
[candidate review](trace/CANDIDATE_REVIEW.md), [exact build](build/ARTIFACTS.json).

This small margin is an explicit pre-deployment maintenance risk, not additional
space for future functions. Exact runtime/configuration admission remains required;
same ABI/version never upgrades an existing deployment, fixture or journal.

## Verification and remaining work

[23 focused EVM methods](verification/EXECUTION.json) succeed: 18 existing methods
through changed Oracle code and five new full-maintenance methods. No unchanged
broad contract/browser/backend suite was repeated. A wrapper failed after Forge
finished while reading an artifact directory; the original successful method
results and frozen source hashes were recovered without rerunning execution.
Its missing process-exit receipt is explicitly retained, not invented.

The [verification record](VERIFICATION.md) separates fresh normal/static/EVM
checks, exact-source reuse, preparation-only work and retained failed attempts.
Original reports and the four unrelated dirty files remain untouched.

Still open: a complete exact-$100/$5 real-route campaign, maximum actual
cohort/asset/history gas, a qualified archive/trace provider and complete fees,
matching reviewed budgets/consumers, independent sources and useful external
depth, VRF/OpenSea/authorities, operating recovery and independent audit.
The central [Todo](../../TODO.md) retains those gates; this campaign approves
neither policy2 adoption nor production operation.
