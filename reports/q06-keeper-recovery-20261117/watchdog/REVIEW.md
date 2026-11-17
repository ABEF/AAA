# Watchdog progress across bounded RPC failover

**A real availability defect is fixed:** legal completed HTTP attempts could exhaust the120-second watchdog before the logical RPC call returned, despite continuing main-thread progress.

## Faithful reproduction

The NEW test module exercises actual `Rpc.call`, `_post`, `_read_http`, response-ID/chain validation, decoder, retry rotation and backoff over synthetic completed response bytes. Eight permitted endpoints each return a chain check and an action response after9seconds, below the unchanged10-second transport limit. The first seven refuse the action; the eighth succeeds. Total simulated time is151.4seconds including existing backoff. The old wrapper only notified after the whole logical call, then threw `WatchdogError` instead of returning the final success.

Baseline3new methods produce1meaningful regression failure,2positive controls and0setup errors. Plain Rpc succeeds with the identical response sequence; one genuinely overlong121-second read cannot send a late heartbeat. These are simulated clocks, not151seconds of real network or systemd execution.

## Narrow correction

`Rpc` accepts an optional callable `transport_attempt_complete`, defaultNone. `_post` invokes it only after `_read_http` returns or raises, after the HTTP-post work budget was consumed. The enabled keeper main explicitly supplies `watchdog.pulse`. No heartbeat is produced from inside a blocked open/read, a retry sleep or a new timer thread. The outer ProgressRPC final pulse remains for injected clients and existing logical-call behavior.

All endpoint chain checks, ordering, retries/backoff, timeouts, body/work limits, read-only methods and request count remain. Plain clients retain None and their prior behavior. The known watchdog exception is a RuntimeError outside RpcError failover handling: expiry aborts without trying another endpoint or publishing a late pulse. WorkLimit remains terminal before another post/callback. A completed refusal counts as process progress while its original sanitized error and degraded health semantics remain; it is not a claim that the endpoint is healthy.

systemd defines watchdog operation through periodic service notifications and its configured expiry, while notification attribution depends on NotifyAccess. [Service/watchdog reference](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html#WatchdogSec=), [notification reference](https://www.freedesktop.org/software/systemd/man/latest/sd_notify.html#WATCHDOG=1). This fix reports actual synchronous work completion rather than extending the timeout or inventing a background liveness signal.

## Verification and limits

Nine distinct NEW methods pass in `tests_python/test_keeper_watchdog_failover_progress.py`: bounded failover, unchanged plain client, overlong read, per-HTTP completion/calling-thread identity, fatal expiry/no next retry, fatal post-budget exhaustion/no premature callback, strict hook admission/defaultNone, preserved remote-error cause, and actual main-factory callback wiring. The three baseline methods are part of these nine, not additional coverage. No old test/suite is run.

Raw before/after logs, exact HTTP attempt completion times, notification times, IDs and whole-source brackets are retained in [BASELINE.json](BASELINE.json), [AFTER.json](AFTER.json) and their logs. The monitor pin also contains the separately owned intent-publication change; only main's Rpc construction belongs to this finding. The selected current source bracket is stable. All61 production Solidity sources and four protected dirty files are unchanged.

No real HTTP endpoint, key, signer, deployment, running service, existing journal/database, site or paused heartbeat is touched. The test uses inert socket channels and synthetic responses, so actual Unix notification, process-group death/restart, provider latency and host qualification belong to the separate Q06 operating evidence. No default deadline, gas budget, authority or economic rule changes.
