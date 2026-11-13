# Pinax capability, history and capacity review

13 November 2026, baseline `11e74883787e32e816b5c01b1213189400fe01fe`.
**All 19 new bounded read requests passed. Temporary simulation, one genuine
historical event and a retained November9 state are now verified. Numerical
20M/24M work capacity and a production provider plan remain unqualified.**

No source, configuration, signer, service, website, existing Anvil, journal,
production default or paused monitoring change occurs. No old test, EVM case
or compiler runs. The separate [identity/profile report](../rpc/REVIEW.md)
owns its independently authenticated genesis and full 13-check probe results;
those are not counted again here.

## New actual checks

| Area | Actual result | Scope |
| --- | --- | --- |
| Temporary code simulation | Verified an unused task address had empty code, balance and nonce. A 10-byte code-only override returned1 through call/trace; estimate 21,221, trace 21,052 gas under 50k. A later ordinary call returned empty again. | Tiny ephemeral support; no balances/storage/nonce/block override or persistent deployment. |
| Canonical state | Same hash/number/time rechecked after the tiny witness. | Point-in-time method evidence. |
| Genuine historical event | Exact retained Transfer, transaction/index/topics/data and nonremoved flag matched at 113263446. | One filtered block/event; submission was never probed. |
| Historical state | Code/runtime pin and exact 160-byte retained round matched at 110324511, hash `0x49759bb8363ba4e95b5b090fd7bee113949b100ab1fa408a839603dc31f4e6b9`. Numbered header checked before/after. | This November9 state is available; lifetime/archive completeness remains separate. |

[Requests/responses](RPC.json), [results](RESULTS.json), [approved plan](PLAN.json).
The tiny witness uses a task-derived address and fresh canonical block 113302353,
hash `0xeeb08edcf1d7144dc305c3fe89eeb0fcfbd17721401cfb703dc134dd1d83bce0`.
Its code is a constant return, with no gas-burning loop. Estimate acceptance
alone does not prove every override/estimation interaction or a financial
operation. The eventual actual operation still needs its exact trace/accounting
and estimate reconciliation.

There were 19 attempts/19 HTTP200 results, at 2-second minimum requested spacing,
12-second transport bounds and 256KiB response bounds. Largest response 19,181 bytes.
No retry, alternate selector or denied-method fallback was used. The preceding
market campaign's429 is retained in its own scope; this small slower success
does not reveal a precise public rate ceiling or demonstrate sustained capacity.

## What primary provider documentation establishes

[Captured primary sources](PRIMARY_SOURCES.json) retain public URL/time/hash
provenance. Pinax's [Robinhood page](https://pinax.network/chain/robinhood)
advertises full historical infrastructure, but its displayed chain identifier
still says TBD. The independent chain proof belongs to the separate RPC report.

The [method catalog](https://app.pinax.network/docs/rpc) lists logs, tracing and
submission. The [Help FAQ](https://app.pinax.network/help) says logs and submission
are unsupported. The actual filtered log now establishes support on this endpoint
at this point; no submission capability is inferred or tested. Provider
clarification is still needed for the selected endpoint/tier and future policy.

The [trace page](https://app.pinax.network/docs/rpc/debug_traceCall) describes
Reth archive availability and illustrates 30s, while the genuine Robinhood
witness uses Nitro. That example is not a guaranteed server deadline.
The [call](https://app.pinax.network/docs/rpc/eth_call) and
[estimate](https://app.pinax.network/docs/rpc/eth_estimateGas) pages provide no
reviewed effective gas, request/response byte or override limit for this endpoint.
Generic method examples are not an admission contract.

[Pricing](https://pinax.network/pricing) describes Free/Pro/Enterprise resource
plans; [RPC pricing](https://pinax.network/pricing/rpc) publishes 6 USD per million
requests. Neither establishes the anonymous endpoint's numerical gas/time/byte
limits, trace weighting, rate/burst/concurrency quotas or support commitment.
No account, signup, subscription or contact message was created.

Eight initial document GETs failed in the restricted transport environment;
eight permitted GETs then returned200. These are document research stages,
separate from the19 successful RPC attempts. They do not demonstrate an outage.

## Reused workload evidence and execution boundary

[Ten existing controlled traces](REUSED_TRACE_FOOTPRINTS.json) were sized offline,
without executing them again. Maximum 2,682 frames/depth 10 fits the source's
8,192/depth 64 trace bound. Their largest compact reserialized response is
1,093,991 bytes; this is not an original-wire byte measurement or a provider
response guarantee. The 8MiB RPC transport ceiling, 25-second request budget and
30-second worker deadline remain. The 1MiB worker result limit applies to its
returned draft/result, not the internal raw trace.

The [two old graph sizes](OVERRIDE_SIZING.json) are 1,440,000 bytes for a ZZZ
activation call and 1,483,462 bytes for a two-leg replacement call, with trace
requests 95 bytes larger. They were **not sent**. Those authenticated fixtures
use source9/mint1, chain 31337 and timestamps 1,000,000/1,087,840; they are not a
fresh mint2 candidate or current Nitro state. No old runtime or result is
relabeled, and no storage-slot rebasing or block override is used.

A further simulation would first need a separately reviewed fresh fixture:
current 4663/time before construction, coherent typed feed/sale/deadline/policy
state, exact source/runtime/account/storage provenance, authenticated output
and inclusion context, reviewed provider resources and a new bounded execution
authorization. Synthetic feeds/depth would retain that explicit scope. The
missing real ZZZ reference, ETH-source and route/market qualifications remain
independent. Rebuilding a large artificial graph now would not finish those
real-operation fee requirements, so this campaign stops after the small checks.

## Required before adoption

[Provider acceptance worksheet](PROVIDER_ACCEPTANCE.json) leaves caps, plan,
fee approval and spending ceilings unset. Obtain exact call/estimate/trace gas
and time limits, body/response budgets, rate/burst/concurrency and trace weight,
history/log completeness, outage/support and change policy. Resolve the
submission documentation conflict without sending a test transaction. Qualify
matching current deployment/configuration/consumer workloads afterward.

Existing safeguards still require canonical snapshots, exact financial traces,
full 20% contribution/25% maintenance padding, fee/funding/day limits and original
pending recovery. The observed provider would also have to support the keeper's
selected submission role before live use; the current active-RPC routing does
not turn a read-only success into broadcast approval. No production code fix
is justified by these unadopted provider observations.

Run [verify.py](verify.py) for offline evidence/source checks only. It makes no
network request and executes no tests or EVM operation. Source publication
selects no provider and grants no release approval.
