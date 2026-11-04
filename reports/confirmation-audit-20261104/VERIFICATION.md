# Focused confirmation verification

November4,2026. Baseline main `cf39b1402915c438b8278cf9c8b51c321922b98f`.
[Findings](REVIEW.md), [coverage](COVERAGE.md), [stage ledger](evidence.json),
[preservation](preservation.json).

## Fresh execution

| Stage | Actual outcome |
| --- | --- |
| negative-control |11new wake-up methods,9failures/2passes/0errors. Reproduces ignored maturity/jitter, time spent after head, multi-bucket deadline, restart and actual daemon sleep behavior against original monitor. |
| corrected |94selected methods pass after deadline/monotonic-wait correction. Includes12new wake-up regressions and existing priority, incidents, portfolio3 and policy6 classes. |
| reset-negative |Two new router-metadata/clear-priority regressions fail before the clear-priority correction. |
| final |100selected methods pass,0failures/errors/skips; exact source unchanged during execution. All14new regressions, affected existing priority/incident/portfolio/policy and main watchdog cases execute at corrected source. |

The result is **100distinct successful selected Python methods**, including14new
methods, not207from adding overlapping stages. The runner enumerates canonical
method IDs, rejects empty/duplicate selection, records runtime source pins before
and after, and saves raw logs and results under exclusive stage directories.
Python3.11+ code runs on the available Windows bundled runtime with `-B -X utf8`.
Tests use synthetic RPCs, temporary journals, fake monotonic time and mocked
sleep/signing boundaries. No endpoint, credentials, running service, Anvil or
public transaction is used. Simulated seconds are not measured operating latency.

[New wake-up tests](../../tests_python/test_keeper_confirmation_wakeup.py)
exercise the actual daemon loop,120-second maturity,60-second jitter,90seconds
of work, two-second watchdog work, multiple deadlines, overdue retry, missing/
expired/backward local anchor, invalid RPC head, saved jitter/restart and pending/
global-error behavior. [Priority tests](../../tests_python/test_keeper_confirmation_priority.py)
add queued-clear independence from routing metadata and blocked-clear no-renewal.
Their serial submit seam is mocked: this establishes queue behavior, not public
signing qualification. Existing submission/receipt/revocation tests retain their
explicit scopes in the selected record.

The affected main-loop fixtures now advance fake monotonic time when sleeping;
without that, a mocked sleep cannot exercise a deadline-driven wait. The older
watchdog FakeKeeper also now implements the already-existing poll_delay method.
No production permission was changed to accommodate a fixture.

## Unchanged on-chain evidence

All52production Solidity files,31dependency sources and4build inputs match the
current authority [43normal gates](../authority-audit-20261103/production-size-gates.json)
byte-for-byte. The10-minute ordinary sampled journey in the prior
[actual-core campaign](../market-lifecycle-20261104/VERIFICATION.md) retains its
source/test scope. On-chain condition/readiness/reset/try-catch, Strategy timing,
Vault/Budget validation and raw observation/control snapshots were inspected.
No unchanged Solidity suite, compiler or analyzer was rerun for these worker
corrections. Historical900-second/confirmation1/2 reports are not relabelled as
fresh confirmation3 proof. Runtime margins remain Migration39/Vault635/Budget237/
Balancer360; no bytecode or deployed instance changed.

## Preserved boundaries and publication

Original monitor and maintained documents are archived externally, with failed
and corrected stages retained under `confirmation-audit-20261104/` in the local
evidence root. The four unrelated dirty files retain their original raw hashes
and remain excluded. Existing pending/nonce/spend journals, NFTs/LP/balances,
sites/services, signer restrictions, public DEPLOYMENT and paused heartbeat remain
unchanged. Publishing source requires a separately authorized reviewed matching
service rollout to affect operation; no journal migration or on-chain setter is
part of these fixes.

Generated Todo/function-reference, document links, exact staged and committed
Python import closure and preservation checks are recorded separately. Public
signing, current-profile operating acceptance, target-chain latency/gas and
independent audit remain unapproved.

## Primary guidance

[Python's monotonic clock documentation](https://docs.python.org/3.11/library/time.html#time.monotonic)
supports measuring local elapsed waits without relying on wall-clock changes;
the on-chain clock remains authoritative for eligibility. The
[Solidity0.8.26 security guidance](https://docs.soliditylang.org/en/v0.8.26/security-considerations.html)
and [Uniswap v4 state-reading guide](https://developers.uniswap.org/docs/protocols/v4/guides/read-pool-state)
were reviewed against the installed implementation for callback/state-read
boundaries. No reference provides a continuous-price, MEV or production guarantee.
