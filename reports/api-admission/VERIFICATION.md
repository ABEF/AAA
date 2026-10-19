# Client admission and proxy: scoped verification

2026-10-20. Internal development evidence. Release remains NOT APPROVED.

## Change and review

The default four isolated workers had no per-client admission rule. A caller could
occupy the finite pool repeatedly. Both CLI services now apply two active work
leases per client, separate reads (1/s, burst 12) and preparation (6/min, burst 2),
and a 4,096-entry table. Atomic acquire/release prevents oversubscription. Only
idle fully-replenishable entries can be evicted; table exhaustion fails closed.

Direct mode uses TCP peer identity; arbitrary forwarding headers cannot select a
budget. Explicit proxy mode trusts only a local 127.0.0.1 peer with one well-formed
overwritten client address and an exact configured HTTPS Origin for POST. The
Nginx profile strips other caller headers and restricts paths/methods, aggregate
concurrency/rate and body size. No automatic proxy retry or financial cache.

Manual source review checked IP normalization, origin/duplicate headers, bounded
state, lock/lease ordering, exception/disconnect cleanup, no upstream work on
rejection, CLI opt-in, exact proxy Host, route matching, unchanged worker/canonical
checks and sanitized output. No contract, wallet signer or financial logic changed.
This is not an independent audit or a no-vulnerability guarantee.

## Executed evidence

| Scope | Result |
| --- | --- |
| First affected Python run | **47 passes**, zero failures/skips, 5.043 seconds: 11 new admission cases, 16 concurrency/worker cases, 14 mint/claim HTTP cases and six activation HTTP cases. Actual local sockets and spawned worker checks are included. |
| Supplemental Python run | **3 passes**, zero failures/skips, 0.101 seconds: disconnect lease retention, both CLI proxy/default admission bindings, invalid-origin rejection before constructing a worker. Production Python code and the first 47 test bodies were unchanged; they were not rerun. |
| Nginx syntax and actual HTTP rehearsal | **22 assertions pass**, plus sanitized access-log check, with official Windows Nginx 1.30.6. Exact includes with only isolated port/path substitutions; fake projections/preparers and no RPC. Header spoofing/credential stripping, origin/method/path checks, oversized body, sanitized single upstream failure, concurrent admission and recovery verified. Own listeners/process stopped afterward. |
| Existing economic evidence | Solidity, earnings calculation, catalogue, wallet signing and keeper logic unchanged. Their suites were not rerun. |

Commands:

```sh
python -m unittest tests_python.test_client_admission tests_python.test_http_concurrency tests_python.test_frontend_transaction_http tests_python.test_frontend_activation_http -v
python -m unittest tests_python.test_client_admission.HTTPAdmissionTests.test_disconnect_keeps_lease_until_started_work_finishes tests_python.test_client_admission.AdmissionCLITests -v
python scripts/rehearse-api-ingress.py --nginx /path/to/nginx --output /external/new-rehearsal
```

The first command preceded the three supplemental test additions. **50 distinct
affected cases** are covered; this is not one newly executed 50-case run.
[Bindings](source-bindings.json) record the final production/config/test source.
[Nginx result](nginx-result.json) binds the actual rehearsal; the [initial result](nginx-attempt1.json)
is retained. Attempt 1 accepted config syntax but failed its filesystem check
because the isolated harness lacked its temporary parent directory. Only the
harness was corrected to create/bind temporary paths; production policy did not
change. Attempt 2 passed. An initial sandbox-blocked download did not execute a
binary; the official archive was subsequently downloaded through the approved
network operation, SHA-256
`c6ee35edb0a861063323f709192ae50d1eefaf2ea7d00678bd2b22d8542dc61e`
The binary hash/version are in the result.

## Limits and remaining qualification

- No public website/server update, no contract deployment/transaction and no
  paused-monitor restart occurred. This local rehearsal used HTTP, not production
  TLS/certificates or actual financial data/providers.
- IP budgets are not authenticated users: NAT clients share a budget, multiple
  addresses can have several budgets, and local proxy/host compromise bypasses
  this identity assumption. Multi-host quotas require reviewed external controls.
- Nginx limits complete-header requests; backend absolute deadlines remain but
  edge slow-header/body, kernel connection pressure and distributed attacks need
  Linux/ingress qualification. This is not DDoS protection.
- Rate budgets reset on service restart. Example aggregate edge limits are not
  real provider throughput approval. Qualify actual trace/history costs, full
  ingestion, proxy/CDN identity policy, log retention and independent alerting.
- Existing client UI code is unchanged; production integration must respect
  typed/untyped 429/503 status and bounded retries without resubmitting wallet
  transactions. No signer was added to the API.

Operator startup/stop/restart/rollback procedures are in [API ingress](../../docs/API_INGRESS.md)
and [the manual](../../docs/OPERATOR_MANUAL.md#client-admission-and-public-api-ingress).
Remaining qualification stays in the [central Todo](../../TODO.md#task-host-services).
