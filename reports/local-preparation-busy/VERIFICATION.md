# Local preparation and refresh contention - 2026-10-20

Scope: website `local-client.js` only; no Solidity or running backend changes.
The disposable 8896 service holds one mutation/read lock. Portfolio replay can
occupy it for tens of seconds. The old client rejected activation preparation
on the first busy response; its balance refresh retry count also expired before
the overall request deadline, leaving cards unavailable despite intact state.

The client now retries only the exact pre-handler busy 409 for GET `/state`
and unsigned POST `/prepare`: at most 30 attempts under one 90-second timeout.
Backoff remains 0.5/1/2/3 seconds, capped at 3 seconds. No POST `/action`,
network failure, ambiguous/lost response or accounting error is retried.
Preparation retries cancel when the account/client state changes. Rejected busy
attempts create no draft; client expiry is conservatively measured from the
last preparation attempt, including its processing time. Waiting does not renew
an existing draft. Explicit approval/Entry confirmations remain separate.

## Evidence

- 43 affected Node client checks pass, including five added contention/cancellation/
  expiry cases; JavaScript syntax check passes.
- A live unsigned activation review during another real portfolio read recovered
  from seven busy responses in 17.15 seconds and produced an activation draft.
  Revision stayed 12; zero action submissions; no test NFT was reset or changed.
  The running server serves the new client directly from the website checkout.
- Source hashes and sanitized live results: [verification.json](verification.json).
- The first live attempt exhausted the old 13-attempt window. The revised bounded
  wait resolved it. A Windows editing-script encoding error affected one existing
  test literal, was corrected, and the complete affected file then passed.
- The live probe precedes extending the same wait to GET reads; the final 43-case
  run covers that extension, while preparation behavior is unchanged.

No unchanged contract suites were rerun. This fixes local lock-contention recovery,
not the backend's serialized throughput or production browser-wallet integration.
USD earnings can independently remain unavailable when the local ETH price is
absent; no dollar peg or zero value is invented. The public server and paused
monitor are unchanged. Reload the local page; no backend restart is required.
