# Public tracing and fee evidence

13 November2026; source baseline `0330a98a0be91c979fcba291258eb6019e528b1f`.
**A real canonical-hash trace with an emitted log now works through Pinax.**
This closes the previously demonstrated missing-tracer interface gap for one
bounded observation. It does not approve a production provider, establish full
20M/24M execution capacity or qualify an undeployed PoPL operation's total fees.

## Actual trace, not an empty-log getter

The [official connection guide](https://docs.robinhood.com/chain/connecting/)
lists `https://robinhood.rpc.pinax.network`. Earlier9November Pinax state reads
had succeeded; this campaign does not retry a previously denied method there.
Mainnet chain4663 was verified before reading application state.

At block113260778, hash
`0x2b948af7b0f9a46e2009c112527abe67eb18573d792a14d916272cc3a9c5cf1e`,
09:46:19UTC, canonical-hash WETH code matched the independently retained
9November pin:2,202bytes, Keccak
`0x5706be52f64875fee65a2cec0d80e47a23d8793cbe85d214b48445e2d05f5353`.
Its address agrees with the [official token inventory](https://docs.robinhood.com/chain/contracts/).
That runtime pin is a witness identity, not a new PoPL asset admission.

The unchanged `keeper.probe._approval_trace` then simulated
`approve(probeAddress,0)` with zero ETH from its fixed public probe address,
using500,000gas. `eth_call` and `debug_traceCall` used the same
`{blockHash,requireCanonical:true}` selector. The actual call tree verified the
caller, target, calldata, zero value, success output and precisely the expected
`Approval(0)` log. Trace gas was33,237. The discarded simulation changes no real
allowance, balance or persistent chain state; no wallet is needed.

The same anchor accepted20M/24M fields for cheap ArbGasInfo calls and estimates.
Both calls returned32M maximum transaction execution; both estimates were23,003.
These cheap views do not consume or prove20M/24M provider execution capacity.
The synthetic header `2^50` is not the network execution allowance.

An all-zero unknown canonical hash was explicitly rejected by calls, estimates
and traces. Calls/estimates returned `-32000/header not found`; tracing returned
`-32000/block <requested zero hash> not found`. The last wording is demonstrably
about the requested missing hash but remains `unclassified` in the current
generic RPC classifier. The report preserves that distinction; it does not turn
an arbitrary error into a successful negative control. Both hash-addressed and
number-addressed headers were rechecked.

## Fee evidence at one separate fresh anchor

The fee campaign used block113263446, hash
`0x2c662ff9ff253f4ea68a1dbd6affdc9547b4c0c8a3bb33f44832c63d3f79bfd5`,
09:50:48UTC. The WETH runtime was rechecked there before the component witness.
The [fee analysis](../fees/REVIEW.md) interprets:

- Ten exact previously captured PoPL payloads passed only to NodeInterface's
  **L1 component estimator**. Their undeployed destinations were not executed,
  and no local PoPL code/state was injected into a public request. Controlled
  ETH fixture values remain100ETH/5ETH, not real-market$100/$5 contributions.
- One full `gasEstimateComponents` call for the actual zero-allowance WETH
  witness; same-anchor ArbGasInfo prices, ArbOS version and `getCollectTips()`.
- An anchored four-block fee history, separately observed unpinned gas/priority
  suggestions, and actual ordinary nonzero-tip and zero-tip transactions with
  their receipts and exact canonical inclusion header. The separately authorized
  zero-tip lookup used four new reads and preserved the original sample unchanged.
  Client version and block execution limits
  were also retained. The genesis header is an unapproved observation only.

The fee anchor was rechecked after both component and receipt phases. This is
concrete target-chain evidence, not approval of a complete PoPL estimate, an
operator spending ceiling, or all future Nitro/provider fee semantics.

## Failures and exact scope

[Triport's specific public reference](https://triport.io/docs/robinhood/public)
advertises keyless debug access, while its older landing page lists different
light-only limits and a different URL. The exact current documented public URL's
first network-permitted chain handshake returned HTTP403, body
`error code:1010`. It was stopped immediately. No alternate path, client
signature, account or credential was tried; no valid chain data came from it.

Two initial restricted-network handshakes failed as `URLError`, as did that
environment's documentation fetches. They remain separately recorded. The
explicitly authorized network-permitted campaign followed; the restricted
failures are not evidence of a provider outage. Documentation GETs and browser
research are separate from RPC counts. Three primary HTML sources were retained;
failed direct documentation fetches remain explicit alongside browser research.

There were56 logical RPC attempts:50 valid replies, three explicit missing-hash
RPC errors, one HTTP denial and two initial restricted-network transport failures.
The permitted phases made54 requests. Requests were sequential with configured
one-second monotonic spacing within each phase, bounded to12seconds and256KiB
ordinary/1MiB trace replies, with no redirects or retries. Recorded UTC intervals
reach0.986650seconds; monotonic intervals were not separately retained, so this
is not proof of exact one-second wall-clock spacing. A new phase's handshake can follow the
preceding response without an extra one-second delay; there were no concurrent
requests. One in-flight transport can outlast the75-second per-phase
new-call deadline; this is not a hard process watchdog. The total stayed within
the reviewed60-call maximum. Previously denied official/PublicNode/dRPC/BlockReq,
Daybreak tracing, BlockVectra hash/tracing and earlier OrdoFi transport were reused
as historical limits, not retried as new probes.

## What remains open

This was not the entire `activation_api_v1` CLI profile: no independently reviewed
genesis hash was available, and the additional storage/tag/receipt checks were
not all repeated. Never copy the candidate's observed genesis into a trusted pin
to manufacture a pass. The actual emitted-log witness remains a valid, narrower
positive result.

Still qualify full20M/24M work and response/time bounds, actual current PoPL
deployment/feeds/routes/state, complete operation estimates, operator fee caps,
independent provider identity, archive coverage, sustained concurrency, outages
and recovery. A public endpoint may fabricate self-consistent replies; these
reads are not consensus/finality or honesty proof. No provider was installed,
no fee field attested true and no public transaction, service/site/signer,
existing Anvil/journal or paused-heartbeat state changed.

[Exact RPC records](RPC.json), [summary](RESULTS.json), [bounds](METHODS.json)
and [source pins](SOURCES.json) retain the distinctions. The offline verifier
checks artifact hashes, methods, actual log witness, missing-hash controls,
anchors and source pins; optional external verification also checks original
response bytes. It sends no request and executes no EVM or unchanged test suite.
An initial offline check incorrectly tried to prove monotonic spacing from UTC
timestamps; its assertion was corrected to reconcile the recorded UTC minimum
and keep the unrecorded monotonic timing boundary explicit. No RPC was repeated.
