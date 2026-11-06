# Verification and evidence scope

Baseline main `9025735fca5a6011bce3772f981881d66d3ea082`; 6 November 2026.
Production NOT APPROVED. [Review](REVIEW.md), [matrix](OPERATING_MATRIX.md)
and [machine-readable evidence](evidence.json) separate source from qualification.

## Contract behavior

**20 distinct selected EVM successes:** 12 new methods and8 existing regression
controls. The [17-method actual-v4 stage](accounting/evm-initial/status.json)
is followed by [three real fixed-token binding controls](accounting/evm-binding/status.json)
using the same exclusively owned cache sequentially. The first17 were not rerun.
See [final test scope](accounting/FINAL_TEST_REVIEW.json).

New cases verify guarded immediate same-main reinvestment, desiredON→OFF,
pre-disabled OFF, independent width pending, mixed/fully converted residuals,
earlier raw-close idle, a nonzero compound reserve that is NOT released, explicit
forced swaps/checks0 faults/inactive geometry, stale hashes/replays/unauthorized
calls, impossible floors and callback control/nonce/policy rollback. Positive
sampled-bit16 tests reach the authenticated Budget caller in both new and old
full-emergency paths. AlreadyOFF/no-residual work invalidates a genuinely mature
sample without resetting lastRebalance. Re-enable/reopen/consolidate cycles stay
bounded and keep shares/fee liabilities.

The existing controls cover entry/growth, six-day harvest/compound/claims,
raw residual close during outages, full emergency, park/reentry, collective
holder return/royalties and real bootstrap/exit-token matching before seal.
All61 prior OptionalCore method bodies remain unchanged. Only180 test lines
were appended. Exact before/after production/test/config/toolchain hashes are
retained; every53 production and31 dependency pin matches accepted normalf907.

Final test SHA256:
`5a535616e32d280bb6dcc88c19647680fe71be8df6778f68c91e123d114f9a75`.
The isolated test EVM uses actual local v4 core/periphery with mock Access,
feeds/admission/token/VRF/Permit2 where recorded. Fixture code-size limit is
1,000,000; normal production gates below remain separate. These are not target
gas, wallet, provider or uptime rehearsals. Retained early ABI checks include
the internal Policy completion changing from three arguments to zero; this was
a test-call correction, not a passing execution or relaxed guard.

## Normal compilation and source families

Fresh closed [normal gates](normal/production-size-gates.json): pinned
Solidity0.8.26/Cancun/viaIR/runs1/yul=false,84 sources, **44 normal compiler-object
gates plus two actual carrier runtime/initcode gates all pass**. Exact compressed
compiler input/output and their raw digests are retained. No EIP-170/EIP-3860
waiver; exact release-specific dynamic NFT constructor values/gas remain open.

| Contract | Runtime bytes | Runtime headroom |
| --- | ---: | ---: |
| Migration |23,830 |746 |
| Vault |24,469 |107 |
| Budget |24,018 |558 |
| ContributionPricing |23,756 |820 |
| PortfolioPolicy |19,315 |5,261 |
| CustodyValidation |18,196 |6,380 |

The retained normal attempts include the initial undeclared-interface typo and
subsequent size failures. They are not passes. The harness was hardened to record
compiler errors before accessing missing contract objects and to return failure
for failed size gates. Safe factoring/caching recovered space; financial or
custody checks were not dropped to fit.

Royalty normal creation bytes remain byte-identical to the frozen schema14
format2 payload, hash `0x4a520b4af1c8ded6fe2539ec7f3ec4f6d9a1c7fbdd710a53ccffd3412bfce831`.
Do not relabel the actual Forge test family's `0xee61b402...` bytes as that normal
artifact. Historical14 factory artifacts/modules keep their original source
scope; fresh15 independently checks the current full graph and new capabilities.

## Static, callable and backend evidence

Fresh actual Slither0.11.6/crytic-compile0.4.2 used the final normal compiler
output without recompilation. Its source freeze succeeded and analyzer JSON says
success; the Windows findings-process exit4294967295 is recorded, not misreported
as exit0. **495 strict records**:133 individually reassessed current contexts,
362 unique exact description-referenced-source reuses. The current133 comprise
76 false positives,28 accepted bounded gas/dependency/timing risks and29
informational suggestions. [Review](static-review.json), [coverage](static-coverage.json)
and [actual execution record](static/EXECUTION.json). This is internal review,
not independent audit or proof of exploit absence.

The source-bound callable reference has37 classes/839 functions/37 constructors/
12 receive hooks, zero input/output gaps, and **888 explicit operator rows**.
**93 distinct reference/operator/static-default methods passed**. No analyzer or
contract rerun was used for those data/generator checks. The backend profile,
event and manifest records retain their own exact final counts and source
stages in [services evidence](services/SERVICES_EVIDENCE.json); overlapping earlier
profile stages are not summed. The original107-method LF stage is preserved;
after restoring only the event schema's original CRLF format,25 overlapping event
methods passed at its new raw hash. All other15 owned files remained unchanged.
Reinvested principal never becomes earned income.

## Preservation and publication

Original historical report bytes, the four protected dirty files, unrelated
drafts and existing website/signing/Anvil/journal boundaries are preserved in the
[preservation record](preservation.json). Documentation/function/operator/Todo
checks and exact staged Python import closure are recorded separately.
Matching actual runtime/service rollouts, maximum-state gas and independent
approval remain open. Source publication changes no environment.
