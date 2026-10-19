# Concurrent API operation

The confirmed read API and both unsigned preparation entry points now use bounded
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
and monitor provider and worker failures off-host. A single caller can occupy a
finite pool; this code does not implement cross-host fairness or DDoS protection.

[Scoped evidence](../reports/concurrent-services/VERIFICATION.md) covers Windows
loopback burst/admission, spawned-process isolation, timeout recovery and website
state guards. Actual Linux hosting, complete history/trace workloads, provider
failover, ingress policy and multi-device wallet/signing rehearsals remain under
[the service task](../TODO.md#task-host-services) and
[transaction integration](../TODO.md#task-transaction-ui). No public server was
upgraded, no paused monitor resumed, and no public transaction was submitted.
