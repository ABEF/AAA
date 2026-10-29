# Verification — historical reconciliation checkpoint

## Fresh isolated execution

The website evidence-admission tests ran8methods: seven passed and one actual
dangling-symlink setup was skipped because this Windows host cannot create it.
[Result and pre/post pins](website-tests.json), [log](website-tests.log).

The separate stack evidence-admission tests ran5methods, all passed with no
failure/error/skip or source drift: [result/pins](stack-tests.json),
[log](stack-tests.log). A final rerun captured missing source bindings, not five
additional unique checks. Total disjoint scope: **13 methods,12passes/one skip**.
No server, Anvil, wallet, public RPC or financial transaction was contacted.

Baseline negative controls are retained in [website](website-before-negative.log)
and [stack](stack-before-negative.log) logs. Earlier fixture errors are errors,
not assertion failures or passing evidence. The website's independent before/
after witness records one HTTP call and clobbered prior evidence before the fix,
versus zero HTTP calls and preserved bytes afterward. Stack old-source controls
show admission occurring too late and no durable initial marker.

## Reused unchanged contract evidence

[Compiler comparison](compiler-reuse.json) compares78 production/dependency
texts and four build inputs with build011 in
[the original verification](../independent-rebalance-20261029/VERIFICATION.md).
Zero mismatches;39normal object gates are **reused**, not newly run. Manager
initcode is48955+160=49115bytes (37margin); Vault runtime24517 (59margin) and
initcode48951+96=49047 (105margin). Dynamic production constructor arguments,
actual target gas and final release remain unqualified. No Solidity or ABI change.

## Documentation and preservation

The initial staged whitespace check rejected CRLF in new report text. Only those
publication copies were normalized to LF; original raw files remain externally.
[Line-ending transfer hashes](publication-line-endings.json) record both forms.
Executed scripts/tests and all pre-existing report bytes remain unchanged by
this formatting repair. No check was disabled.

The final [preservation/check record](preservation-and-checks.json) records
Todo generation/check, source-bound callable consistency, whitespace/link checks,
historical report hashes and pre-existing dirty-file preservation. Generated
reference consistency covers33concrete contracts/696functions with no reported
purpose/input/output annotation gaps; it is not renewed body-level execution.

The complete historical per-finding reconciliation remains unfinished; see
[scope](REVIEW.md) and [inventory](READING_INVENTORY.json). No services, sites,
signer policy, old deployments/journals or paused heartbeat were changed. Public
signing stays disabled. No independent audit or production approval is claimed.
