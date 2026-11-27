# Concurrent API operation

The confirmed read API and both unsigned preparation entry points use bounded
parallel admission. Each request owns a separate spawned process and Projection,
RPC client, SQLite reader and request budget. There is no shared wallet session,
nonce manager, signer or cached financial result. Each result retains its existing
confirmed-block, final canonicality, deployment and expiry checks.

## Start and size the services

An infrastructure operator, not a contract authority, configures these processes.
Use reviewed deployment, history, pricing and optional preparation manifests; no
private key belongs in these services. Keep manifests containing RPC credentials
outside Git and restrict their filesystem permissions.

```sh
python -m frontend_api.server --config /path/to/frontend-read.json --port 8787 --workers 4 --max-connections 8
python -m frontend_api.activation_server --config /path/to/frontend-read.json --activation-config /path/to/activation.json --port 8788 --workers 4 --max-connections 8
```

The first command remains GET-only unless the existing `--transaction-config`
option is supplied for unsigned mint/claim preparation. Activation uses a separate
listener. Both bind only to 127.0.0.1; no public endpoint is created by this work.

| Limit | Default and behavior |
| --- | --- |
| Concurrent expensive requests | `--workers 4`, accepted integer range 1-8, per service process. No waiting work queue; a full pool returns HTTP 503 `service_busy` and `Retry-After: 1`. |
| Per-client admission | Both CLI services limit each IP to two active requests, reads at 1/s (burst 12) and preparation at 6/min (burst 2). Optional reviewed proxy identity and exact-origin policy; see [ingress operation](API_INGRESS.md). |
| Active HTTP connections | `--max-connections 8`, accepted integer range 1-32. Admission occurs before a handler thread is created. Excess connections receive the same bounded busy response. The TCP listen backlog is 16. |
| Request headers | At most 8 KiB per line and 32 KiB total including the request line; oversized input returns 431. Duplicate Host/length and ambiguous framing are rejected before RPC work. |
| Request ingress | Five seconds from handler start, including all headers and the complete POST body; periodic trickle input does not reset this deadline. POST body limit remains 16 KiB. |
| Operation work | Existing 25-second cooperative budget, 1,024 logical RPC calls / 2,048 physical POSTs; earlier snapshot/quote expiry still wins. |
| Child supervision | Thirty seconds including process startup, then up to one second each for terminate/kill and reap. Incomplete, oversized or expired results are rejected. |
| Whole connection | Forty-five-second socket shutdown deadline and five-second socket inactivity timeout. A disconnected caller is not retried; an already started child remains bounded by its supervisor. |

Limits apply **per process**, not across machines. The two default listeners can
together run eight expensive requests and sixteen HTTP handlers, with up to two
timer threads per accepted handler. Per-request RPC limits multiply with admitted
concurrency. Raising limits can exhaust provider quotas, CPU, RAM or database I/O;
it is not a throughput improvement without measurements. Start smaller when the
provider's capacity is unknown. Never increase signing concurrency in the separate
disposable local launcher to match these read/preparation settings.

## Optional bounded wallet read aggregation

Only a reviewed accounting7 read configuration with earnings history and integer
`wallet_read_batch: 1` enables wallet_view_profile2 and the aggregate earnings
route. Omitted/integer0 keeps profile1. The new route uses the same admission,
worker supervisor,25-second work budget,1,024 logical RPC/2,048 POST, response
and snapshot-expiry limits. It does not add a signing path, public listener or
operator write capability.

The helper is fixed checked-in constructor bytecode passed to `eth_call` with no
destination, zero sender/value and canonical blockHash. It cannot persist code
or change state; only an explicit set of STATICCALL getters is available. Each
outer call remains charged through the existing BudgetedRPC. At most16 requested
NFTs split into at-most3-NFT constructor calls with at most4 royalty currencies;
plain/LP/royalty getter gas caps are50,000/500,000/1M and the whole simulation
cap is24M. Initcode/returned-code bounds are49,152/24,576 bytes. No arbitrary
target/selector/calldata program or state override is accepted. This read gas
bound does not change transaction profiles, network fee ceilings or any monetary
safeguard. Provider support and expensive valid getters require qualification.

Authenticated raw replies seed only the same request's canonical cache; the
ordinary Projection decoders, deployment/identity and accounting checks still
run. Getter failures are remembered without retry/fallthrough. Contradictory
replies or malformed batch output fail integrity checks; inability to retain a
batch within64KiB-entry/8MiB-total bounds fails closed. Repeated identical proof
groups reuse their retained replies; no financial result or failed state crosses
request boundaries. Head/chain/header/final/checkpoint proofs remain live.

The explicit opt-in also scopes individual NFT and earnings reads to this same
bounded cache. After the exact canonical code reply for each target is retained,
identical actual runtime bytes may share their computed Keccak digest. Every
expected-pin comparison still runs. Digest metadata consumes the existing cache
allowance and clears at scope exit; an entry that cannot fit is hashed without
retention. This changes neither concurrency nor any financial/resource limit.

The consumer assembles independent16-ID ownership/summary and four-currency
whole-wallet earnings axes, then checks matching complete inventory, currencies,
history/configuration/epoch identity and final freshness. This reduces data-page
count without raising workers, quotas or request ages. It does not establish
concurrent production capacity or replace the separately deferred load campaign.
See [the response contract](FRONTEND_API.md#opt-in-whole-wallet-earnings-profile2).

## Fixed-block card reads

The additive NFT detail/earnings `/at/{block}/{hash}` routes use the same workers,
GET admission,25s/1024logical/2048POST/1MiB and original snapshot-expiry budgets.
Capability `fixed_block_nft_view_profile:1` requires exact7 plus both reviewed
history profiles. It is an output selector, not a server configuration flag.
The exact number/hash is revalidated with live final proofs; newer blocks do not
reset120 seconds. Complete raw history need only cover that captured block, so
Indexer lag/ahead relative to the newer head does not justify mixing snapshots.
Adopt the reviewed exact Nginx allowlist with matching server/worker/consumer and
a NEW independently reviewed checkpoint. No concurrency, retry, signing, ingress
or financial limit changes. [Inputs and failures](FRONTEND_API.md#fixed-block-nft-detail-and-earnings).

## Failures, observations and recovery

1. Check startup JSON for chain ID, port, worker count and connection cap. Verify
   `/v1/protocol` against the reviewed deployment and confirm it returns no-store
   headers. Opt-in preparation still returns unsigned calldata only.
2. A busy response means admission failed; it does not mean a transaction was sent
   or a balance is zero. Read clients may use a small finite jittered backoff,
   respecting Retry-After. Do not automatically replay a wallet submission or
   replace an unresolved transaction with a fresh intent. An expired draft needs
   fresh preparation and explicit wallet confirmation.
3. Worker logs contain fixed `api_request` outcome and elapsed time fields.
   `api_worker_quarantined` means cleanup could not be established for that slot;
   it is permanently removed from this process's pool. Healthy slots continue.
   `api_http_failure` is sanitized and contains no request body, wallet address,
   endpoint credential or exception text. Monitor these events and HTTP 503/431
   rates using bounded reverse-proxy logs. All quarantined slots require operator
   recovery; there is no hidden unlimited respawn loop.
4. For quarantine or persistent overload, drain ingress, inspect supervisor/OS
   state, provider limits and temporary-directory permissions, then stop the
   configured service and all of its children. On a managed host use a reviewed
   process-group/cgroup supervisor; in local foreground use Ctrl+C and verify exit.
   Do not delete a live child's temporary directory. Retain sanitized incident
   evidence before cleanup and restart the same reviewed configuration. No API
   request authorizes cleanup of server files or contract changes.
5. Verify fresh protocol responses, child cleanup and corrected capacity after
   restart. There is no API wallet balance/session state to restore; canonical
   contracts and the verified index/history remain the source of data. Do not
   substitute a cached response, guessed balance or incomplete earnings history.

Reducing `--workers` to 1 is the supported bounded-capacity fallback, preserving
the ingress/cleanup safeguards. Reverting to the older serial server removes
these protections and can let a slow user block others. Neither restart nor
rollback recovers or changes a user's signed blockchain transaction.

## Hosting and verification boundary

Keep a separately reviewed HTTPS reverse proxy in front of these loopback
listeners. It must set the exact loopback Host/port, strip untrusted forwarding
headers, enforce origin policy and rate/connection/queue/time/response limits,
and monitor provider and worker failures off-host. The implemented
[client admission and proxy profile](API_INGRESS.md) prevents one IP from leasing
all four default workers. Shared NATs share a budget; this is not cross-host
fairness, unique-user identification or DDoS protection. Actual deployment remains
subject to hosting qualification.

[Scoped evidence](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/concurrent-services/VERIFICATION.md) covers Windows
loopback burst/admission, spawned-process isolation, timeout recovery and website
state guards. Actual Linux hosting, complete history/trace workloads, provider
failover, ingress policy and multi-device wallet/signing rehearsals remain under
[the service task](../TODO.md#task-host-services) and
[transaction integration](../TODO.md#task-transaction-ui). No public server was
upgraded, no paused monitor resumed, and no public transaction was submitted.

## Capacity qualification and historical acceptance

The user reported six historical local two-wallet flows passed; see the
[manual acceptance record](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/local-wallet-concurrency/MANUAL_ACCEPTANCE.md).
This report does not change operator functions, roles, configuration, limits or
stop/restart procedures. The dedicated 10/25/100-user load campaign is deferred;
do not run it automatically or raise worker limits as part of this decision.
Bounded API admission and saved transaction recovery remain requirements for
reviewed integration. Existing local signer/locks and manual fixture acceptance
are not current-accounting-3 or production browser-signing qualification. The
shared signer remains Anvil-only; the current public deployment is disabled.
Production capacity is unverified, and accepting real
funds still requires the outstanding dependency and release qualification.
