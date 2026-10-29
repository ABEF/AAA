# API client admission and proxy operation

The read/unsigned-preparation services enforce bounded per-client work admission.
This is implemented locally; public API hosting, real provider quotas and Linux
operating qualification remain under [host services](../TODO.md#task-host-services).
No transaction signer, wallet session or RPC credential is exposed by this feature.
The manifests must identify the exact deployment/profile explicitly. The fresh
backend supports accounting4/custody3/V5; the served poplint reader remains
accounting3, and historical Anvil profiles are separate. Admission does not qualify contracts,
prices or routes, and preparation never broadcasts a transaction.

## Capacity and identity

| Control | Default, per API process |
| --- | --- |
| Concurrent work per client IP | 2, configurable with `--per-client-active 1..4`. Keep below `--workers` to leave capacity for another client. |
| Read admission | One token/second, maximum burst of 12; all accepted read routes share it. |
| Unsigned preparation admission | Six tokens/minute, maximum burst of 2; independent of reads. |
| Client table | Maximum 4,096 entries. No queue or per-client timer. Only idle entries whose budgets can fully replenish are evicted. A full table returns 503. |
| Existing server bounds | Four worker slots/eight HTTP connections by default; request, child-process and ingress deadlines remain. |

Concurrent requests share one locked budget. Invalid transaction inputs discovered
by the preparer and failed upstream reads still consume admission; retrying must
not provide free expensive work. A disconnected client retains its lease until
the already-started bounded work and HTTP cleanup finish. No resubmission occurs.

Without `--proxy-origin`, identity is the TCP peer address. `X-Forwarded-For` and
`Forwarded` never select a budget. A supplied `X-PoPL-Client-IP` is rejected to
catch accidental proxy misconfiguration. Existing loopback clients continue to
work, sharing the loopback IP's budget; the separate disposable launcher is not
changed. The embedding `ReadServer` constructor requires an explicit admission
object; both production command-line entry points always install one.

With `--proxy-origin https://EXACT-HOST`, the service requires one valid
`X-PoPL-Client-IP` from a proxy connecting over **127.0.0.1**. The public proxy must
overwrite that header from the actual TCP client; no forwarded identity chain is
trusted. Duplicate/malformed/zone-scoped addresses fail closed. Equivalent IPv6
spellings and IPv4-mapped IPv6 share a key. This trusts the local machine/proxy:
untrusted local processes must not have access to these listeners.

Proxy-mode POST requests require the exact configured HTTPS Origin. An Origin on
GET must also match; absent Origin on a public read is allowed. Cross-site Fetch
Metadata is rejected. Origin checks prevent accidental cross-site browser use;
they are **not authentication** (non-browser callers can set Origin themselves).
No CORS wildcard, cookies or authorization header is needed for these endpoints.

IP capacity is not a unique-user identity: shared NAT clients share a budget,
IPv6/multi-address clients can have several budgets, and this is not DDoS protection.
Do not introduce wallet-address-based quotas: anyone can submit arbitrary wallets.

## Configure and start

Authority: infrastructure operator, no contract governance call. Use reviewed
deployment/history/pricing and optional transaction manifests; never add a key.
Substitute the actual reviewed same-origin website host and filesystem paths:

Startup reads every supplied configuration file as a strict UTF-8 JSON object
before constructing workers or listeners. Nested/escaped duplicate keys,
nonfinite/overflowing floating-point values and nonobject roots are rejected through the existing
fixed error messages. No file is rewritten and a rejected startup performs no
RPC work. Repair the reviewed private file; do not normalize ambiguous input or
change a deployment/profile merely to make startup succeed. This does not change
the separate bounded HTTP-body parser or its limits.

```sh
python3 -m frontend_api.server --config /etc/popl/read.json --transaction-config /etc/popl/transactions.json --port 8787 --workers 4 --max-connections 8 --per-client-active 2 --proxy-origin https://popl.example.test
python3 -m frontend_api.activation_server --config /etc/popl/read.json --activation-config /etc/popl/activation.json --port 8788 --workers 4 --max-connections 8 --per-client-active 2 --proxy-origin https://popl.example.test
```

Omit `--transaction-config` when mint/claim preparation is not qualified; POST
remains disabled. Remove its proxy location as well. The activation listener is
also opt-in. Omit `--proxy-origin` only for direct local operation, not as a
workaround for failed public identity/origin checks. Restart to change policy.

Candidate Nginx includes are under [config/nginx](../config/nginx):

1. Copy the three reviewed files to `/etc/nginx/popl/`, owned by the administrator
   and not writable by API users. Include `popl-api-http.conf` once in `http {}`.
2. Include `popl-api-locations.conf` inside exactly one existing, reviewed TLS
   website `server {}`. Preserve website routing. It exposes only the enumerated
   `/v1` GET paths and the two exact preparation POST paths to fixed loopback ports.
   Do not add a catch-all proxy, dynamic upstream or automatic retry.
3. Verify certificate renewal, exact host/default-host rejection, same-origin
   frontend configuration, firewall and localhost-only services. Keep header
   timeout at 5 seconds, header buffers bounded, keepalive/worker-connection limits
   finite, and both backend ports unreachable remotely. The snippets do not
   install certificates, alter a running website or authorize public hosting.
4. This profile assumes **direct TLS termination**. Do not enable inherited
   `real_ip_header`/`set_real_ip_from`, CDN/proxy-chain forwarding or PROXY protocol
   without separately reviewing the new identity boundary. Otherwise clients can
   be collapsed into one budget or an unsafe edge policy can permit spoofing.
5. Run `nginx -t` against the complete selected configuration before a controlled
   reload. Confirm startup JSON includes the intended worker/connection/client
   counts and `proxy_identity: true`. Verify protocol chain/configuration, exact
   unsigned drafts, expiry and no-store headers through the proxy.

The edge permits two concurrent requests per IP, six total, and eight requests
per second with an eight-request immediate burst; it does not queue excess work.
These shared Nginx limits cover both listeners. They are example ceilings, **not a
qualified RPC throughput budget**: each admitted request can make many RPC calls.
Backend limits remain per process; several hosts/restarts do not share persistent
quotas. Coordinate provider budgets, distributed ingress and actual peak load
before hosting. Nginx connection limits count complete headers; header/body
timeouts are inactivity limits, not the backend's absolute ingress deadline.
Keep edge connections bounded and qualify slow-client/network attacks separately.

## Responses, logs and recovery

- 429 `client_busy` / `client_rate_limited`: no worker/RPC work started for that
  request. Respect `Retry-After`; use finite jittered retries for reads. Never
  automatically replay wallet submissions. Preparation retries require a fresh
  snapshot/draft and explicit wallet confirmation.
- 503 `admission_capacity_unavailable`: the finite client table is full. Existing
  clients may continue; newly seen IPs wait until idle entries replenish. Do not
  turn this into a zero balance or bypass the limiter. Existing `service_busy`,
  unavailable projection and preparation failures retain their meanings.
- 400 proxy identity / 403 origin failures: inspect exact proxy overwrite, Host,
  service origin and browser Origin. No financial result or draft was returned.
- Application logs contain fixed `api_admission_rejected` reason/status fields,
  no IP/wallet/body. The example edge access log has status/timing/limit outcomes,
  no raw paths, queries, addresses or credentials. Apply log rotation, disk limits
  and independent alerts. Review inherited/default-server/error logs too; arbitrary
  Nginx debug/error logging can expose raw requests. Edge-generated 4xx/5xx may be
  Nginx error bodies: clients must check status before decoding a success schema.

On sustained rejection, distinguish one busy NAT, distributed load, client retry
storms, worker quarantine and upstream slowness. Inspect sanitized counters and
provider usage. Stop public ingress first for an incident; drain bounded requests,
then stop the exact reviewed service/process group. Never change contract slippage
or return cached financial results to resolve an HTTP capacity problem.

Restart the same reviewed configuration and verify cleanup and fresh protocol
responses before reopening ingress. Client budgets reset on restart; contracts,
index history and already-broadcast transactions do not. A rollback must preserve
the identity/header policy on both sides; disable affected public locations before
running older code. Do not remove proxy mode while retaining public forwarding.

## Scoped rehearsal

The reproducible tool starts only new loopback listeners and its own Nginx process,
with fake projection/preparation data, no RPC/signature/deployment:

```sh
python3 scripts/rehearse-api-ingress.py --nginx /path/to/nginx --output /external/new-api-ingress-rehearsal
```

The new output directory must be outside the repository. The tool adapts only
ports and filesystem locations, validates the real includes, tests the actual HTTP
boundary, preserves hashes/results, and shuts down its own services. See
[scoped evidence](../reports/api-admission/VERIFICATION.md). This HTTP/Windows run
does not qualify production TLS, Linux hosting, RPC load or external alerts.

Directive semantics were checked against the official Nginx
[rate-limit](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html),
[connection-limit](https://nginx.org/en/docs/http/ngx_http_limit_conn_module.html)
and [proxy](https://nginx.org/en/docs/http/ngx_http_proxy_module.html) references.
