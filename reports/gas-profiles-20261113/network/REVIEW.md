# Public-provider compatibility for 20M / 24M profiles

Observed 13 November 2026 against source baseline `fbe47c3`. This campaign made
bounded read-only requests, not public transactions. It adopted no provider,
configuration, gas default, service, site, signer or journal.

**The required complete preparation provider remains unqualified.** Daybreak
accepts the requested 20M/24M gas fields for canonical-hash calls and estimates,
but does not expose the requested tracer. BlockVectra's public tier rejects
fresh canonical-hash state requests and disallows tracing. OrdoFi's initial
chain handshake failed in transport. These are concrete compatibility gaps;
neither numbered-block fallback nor a skipped trace is permitted.

## Current chain parameters

At BlockVectra anchor **113212776**, hash
`0x3d0c507677cf75fc617f4455edfdef12656ebc5d46093e277e19f62fecfc7678`,
**08:21:35 UTC**, chain ID was 4663. The same numbered header was rechecked
after the reads. ArbGasInfo returned **32,000,000 transaction and block execution
parameters**. Header `gasLimit` remains the synthetic `2^50`; it is not capacity.

Pinned base fee was **20,014,000 wei/gas (0.020014 gwei)**; the separate later
`eth_gasPrice` read was **20,034,000 wei/gas (0.020034 gwei)**. All six gas-price
components are retained in [RESULTS.json](RESULTS.json). Their zero L1/calldata
component is a snapshot, not permanent zero posting cost. No complete PoPL
operation or total-fee quote was simulated on a public provider.

## Exact compatibility observations

All work used the permissionless `getMaxTxGasLimit()` precompile view or other
explicit gas-info getters. Passing a large `gas` field to a cheap view does
**not** prove the provider will execute that much work: an internal clamp could
remain invisible. No gas-burning or stress probe was performed.

| Public endpoint | Required canonical-hash call / estimate | 20M / 24M field result | `callTracer` with logs |
| --- | --- | --- | --- |
| [BlockVectra](https://docs.blockvectra.com/en/guides/robinhood-chain/) | Fresh `requireCanonical` hash requests return `-32011 state_window` | Numbered-block diagnostics alone succeed; both estimates are 23,182 gas | `-32601 method_not_public` |
| [OrdoFi](https://rpc.ordofi.network/) | Chain handshake ends in `URLError`; no valid chain data | Not attempted after transport failure | Not attempted |
| [Daybreak, registry-listed](https://raw.githubusercontent.com/ethereum-lists/chains/master/_data/chains/eip155-4663.json) | Calls and estimates succeed at a rechecked `requireCanonical` hash | Both fields accepted; both cheap estimates are 23,182 gas | `-32601 Method not found` |

BlockVectra's hash failures occurred within seconds of the fresh anchor and
despite its numbered header remaining available. The response alone cannot tell
whether selector support or gateway policy caused it; it must not be described
as demonstrated age expiry. We preserved the four planned call/estimate/profile
combinations and their failures. A separate numbered diagnostic isolated field
admission; it was never a fallback for financial preparation.

The fresh [public catalog](https://api.blockvectra.com/v1/chains) advertises
3 requests/second, burst 20, batch 10, one in-flight public request and only 900
recent blocks. Its anonymous method list omits `debug_traceCall`. The one explicit
cheap negative trace probe confirms that boundary. General provider documentation
advertising network tracing does not establish anonymous-tier access.

Daybreak anchor **113214617**, hash
`0xf0e5783f4a6e87f2a40a697980f3eeaf720aebfaa90b853ea6ee4e63f62e1145`,
**08:24:48 UTC**, was also rechecked. Its own `eth_getBlockByHash` matched. It
returned the exact earlier BlockVectra anchor, and its selected Uniswap core
code was 24,009 bytes with Keccak
`0xbd3881180b547f5fe817545743cfb4343e96b1bc6640dcd70c106b0066e95626`,
matching the literal Registry pin. An unknown canonical hash correctly failed
with `header not found`. This corroborates recent data and interface behavior,
not operator independence, finalized state or lifetime archive coverage.

[OrdoFi's documentation](https://app.ordofi.network/docs) advertises an anonymous
endpoint and tracing. We did not turn those claims into acceptance: the first
RPC request failed before a response. Its cause and a provider-wide outage are
not inferred from the recorded `URLError`. No alias, account, key or paid plan
was tried. Previously denied official/PublicNode/dRPC/BlockReq endpoints were
not retried or accessed with modified client signatures.

## Scope, evidence and remaining qualification

There were **33 new RPC attempts: 24 valid results, eight explicit RPC errors
and one transport failure**. No HTTP access denial occurred in this campaign.
The catalog GET and primary-source research are separate from that RPC count.
Requests were sequential, spaced at least 0.45 seconds, bounded to 12 seconds
and 262,144 response bytes. Only the explicit read/estimate/trace allowlist was
used. Every failed result remains in [OBSERVATIONS.json](OBSERVATIONS.json);
full response bytes stay externally hashed.

The offline [verifier](verify.py) reconciles published summaries, raw response
hashes, exact methods/targets/caps, counts, anchors and code identity. It sends
no network request, executes no EVM test and compiles nothing. An initial offline
decoder import-path error was corrected without repeating a network call.

Still required: a provider that supports the complete canonical-hash trace with
logs and full-operation estimate at the reviewed caps; actual effective execution
ceilings, response/time/workload limits, sufficient history and sustained recovery;
representative PoPL operations and complete fees. Select operator ETH spending
ceilings and attest the fee policy only from separately reviewed evidence. These
reads do not invent a spending budget or establish a fee-review hash.

Keep the financial guards, canonical-hash requirement, exact trace validation,
20% contribution headroom, 25% keeper/manual padding, source/runtime bindings,
fee/balance/day limits and pending-first recovery. The source's 20M/24M profiles
must retain this explicit provider qualification boundary before adoption.
