# Public RPC preparation observation - 25 October 2026

The user authorized bounded, read-only Robinhood mainnet capability checks. The
attempt to establish independent pins for `activation_api_v1` stopped before that
profile ran. **No approval trace was observed and no provider is approved.**

The [official connection guide](https://docs.robinhood.com/chain/connecting/)
lists chain 4663, links the Blockscout explorer and lists the public Pinax RPC.
It also warns that its public endpoints are rate limited and unsuitable as a
production-service plan. Listing a provider does not qualify its capabilities.

## What was attempted

Two bounded GETs requested the public explorer's genesis block and the already
deployed ZZZ contract metadata/runtime. The initial restricted-network attempt
returned `URLError` for both reads. An explicit network-authorized retry returned
HTTP 403 for both. Redirects were refused, each request had an eight-second
timeout and responses were limited to 2 MiB. The web reader also could not open
the two public API URLs; its failure supplies no chain identity or runtime pin.

| Observation | Evidence |
| --- | --- |
| Initial independent-source attempt | [Sanitized results](blockscout-public-pins.json) |
| Explicit network retry | [HTTP 403 results](blockscout-public-pins-network-retry.json) |
| Stop decision and exact source/evidence hashes | [Observation receipt](OBSERVATION.json) |

No expected genesis or runtime hash was invented or copied solely from the RPC
under test to obtain a pass. Consequently the preparation profile, its discarded
`approve(0)` simulation and its `callTracer`/`withLog` witness were not attempted.
No signing, transaction submission, allowance change, state override, deployment,
key access, service operation or monitor change occurred.

## What remains

Obtain independently corroborated chain-genesis and ZZZ runtime identities,
retain their dated public evidence, then run the existing
[`activation_api_v1` procedure](../../../docs/RPC_PREPARATION_QUALIFICATION.md).
A token runtime pin identifies bytecode; it does not establish token safety,
implementation/proxy administration, pricing or route qualification. Even a
successful capability profile would not establish uptime, complete archive
history, fee budgets, finality or an actual PoPL financial operation.

The parent's separate `keeper_v1` observation recorded 11 Pinax checks passing
and failure to read the other public endpoint. Its exact external artifact hash
is referenced in the receipt. Those observations are not rerun here and are not
promoted into preparation-profile or production approval.

## Parent basic-profile capture

The [saved two-endpoint report](public-two-provider-observation.json) preserves
the exact canonical reference number/hash/time and all11 successful Pinax checks.
The documented public endpoint returned HTTP403 from this environment. Initial
[restricted](public-rpc-observation.json) and [authorized network](public-rpc-observation-network.json)
attempts remain diagnostic records, not proof of provider outage. The
[read-only driver](observe-public.py) records the bounded scope. This does not
establish independently reviewed genesis/runtime or preparation-profile support.
