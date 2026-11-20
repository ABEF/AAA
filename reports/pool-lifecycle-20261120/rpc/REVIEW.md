# Bounded alternate-RPC screen

20 November 2026; source baseline `4b6497be76191a8a3a5295267b4706f811d5a899`.
No public transaction, credentials, registration, provider purchase, service
change or production configuration change occurred.

## Actual observations

The restricted transport first made three attempts that returned `URLError`.
Those records and exact script stage remain; they are not provider HTTP refusals.
The separately authorized network screen then made **four HTTP requests** in
about1.16seconds: one public catalogue GET and three read-only JSON-RPC calls.
No retry was made. [Result](RESULT.json), [raw responses](capture-network/RESULT.json)
and [byte manifest](MANIFEST.json) retain the evidence.

| Candidate | New bounded observation | Disposition |
| --- | --- | --- |
| Official public endpoint | `eth_chainId` returned HTTP403. | Stop; no repeated request or historical-read assumption. |
| BlockVectra public endpoint | Chain4663 read succeeds; exact block119107223 header returns -32011, `state_window`, `retryable:false`. | Stop; code/storage screens not attempted after the required anchor failed. |
| Pinax public endpoint | No new probe in this subtask. | Reuse prior rate-limit evidence and existing exact-URL cache restrictions. |

The fetched BlockVectra catalogue declares a900-block state/public-history
window,3requests/second, burst20 and one in-flight request. That is not fixed-
historical archive access. At the chain's advertised100ms block cadence,900blocks
is about90seconds as an estimate, not a measured service retention SLA. Merely
choosing a fresh block could let it age out during a several-minute fork run.
The catalogue's keyed `state_window_blocks` is also900; obtaining a key alone
must not be presumed to remove this boundary.

## Primary documentation and operational consequence

Robinhood's [connection guide](https://docs.robinhood.com/chain/connecting/)
recommends provider-backed archive access for historical work and labels public
endpoints rate-limited and unsuitable for production. Its Alchemy URL requires
an account-specific key. Other named providers need their own endpoints/terms;
no such account or tier was created or selected here.

BlockVectra's [mainnet guide](https://docs.blockvectra.com/en/guides/robinhood-chain/)
documents its public URL and3RPS limit; the actual
[catalogue](https://api.blockvectra.com/v1/chains) and refusal above determine
this screen's history conclusion, rather than generic support claims.

Pinax's [network page](https://pinax.network/chain/robinhood) describes full-archive
RPC, but the anonymous endpoint's prior429 responses still require cache/rate
handling. [QuickNode](https://www.quicknode.com/chains/robinhood) advertises Robinhood
archive/debug access through account endpoints. [Blockdaemon](https://docs.blockdaemon.com/docs/how-to-connect-to-robinhood)
requires a configured node/endpoint and auth token. These are actionable provider
leads, not measured endpoints or production approvals.

The current `scripts/source9_rehearsal_fork.py` cache helper intentionally
allowlists only the exact keyless Pinax URL. Do not substitute an alternative
silently. Any report-only transport change must preserve read-only methods,
exact chain/anchor identity, immutable captured requests, byte/work/time bounds
and stop-on-refusal behavior. Reusing verified pinned cache entries can reduce
duplicate upstream reads; it cannot fabricate missing state or prove capacity.

No anonymous alternate archive endpoint qualified in this finite screen. This
does not prove no suitable provider exists. Full operation, tracing, complete
fees, selected tier/limits, failover and operating acceptance remain open.
