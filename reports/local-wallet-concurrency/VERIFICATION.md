# Local wallet concurrency verification - 2026-10-20

## Cause and correction

Chrome and Codex keep independent cached portfolios but use one local service
operation revision. A valid freshly simulated draft at a newer revision was
rejected against the older browser cache as `Invalid transaction confirmation`.
The local website client now reads and validates confirmed state when the draft
is newer. If another operation lands during that read, it prepares again, at most
three times. It never updates only the revision or broadcasts during preparation.

Account/session/version, exact wallet inventory, uncertainty, monotonic/wall-clock
expiry and nondecreasing safe-integer revisions remain checked. Reconciliation
time consumes the original draft lifetime. An operation after review can still
invalidate that review: the backend revision guard remains unchanged. An explicit
pre-submission rejection refreshes balances and requires a new manual review.
Ambiguous responses retain the exact saved operation ID for recovery; a definite
rejection during recovery clears only that rejected intent. There is no automatic
transaction retry or new operation ID to bypass uncertainty.

## Evidence

- 59 focused Node cases passed (local-client and contribution-flow), including
  eight new concurrency/recovery cases. Two independent in-memory browser clients
  complete successive operations despite stale cached revisions; additional cases
  cover repeated contention, account switching, expiry, malformed/backwards state,
  uncertain outcomes and changed inventory. These are simulated HTTP responses.
- The first check caught a template delimiter syntax error before test execution;
  it was fixed, then syntax and all 59 cases passed. No failed test is omitted.
- [Running-service observation](local-observation.json) exercises two independent
  clients concurrently against 8898 using a real earlier confirmed snapshot of
  the same deployment. Only unsigned mint preparations are requested: no action,
  transaction, new NFT, allowance, reward or LP mutation by this verification.
- Production Solidity/backend code is unchanged; unchanged contract suites were
  not rerun. Local services and both Anvil chains were preserved without restart.

Website fix published on main as `7c858c1`. [Source hashes](source-sha256.json)
bind the final 59-case run; the running 8898 mount serves both exact client files.

## Scope and residual limits

This repairs the website's disposable loopback adapter. Production browser-wallet
signing and public-host concurrency qualification remain open. The local backend
still serializes operations and conservatively invalidates reviewed drafts after
any intervening operation. During sustained changes a new review can be needed;
this is not a throughput or latency certification. Public website/server and the
paused monitor are unchanged. Release remains NOT APPROVED.
