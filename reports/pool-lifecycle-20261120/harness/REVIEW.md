# Prepared-driver controls executed offline

Eight NEW focused controls pass against the exact previously prepared report
driver. [Execution](EXECUTION.json) binds its source hash, new test bytes,
command, timing and raw stdout/stderr. No unchanged suite is rerun.

- Capture the actual serialized request and its hash before later nested
  transaction dictionaries change.
- Stop a partially started owned process and retain cleanup evidence.
- Escalate from bounded terminate/wait to kill for a stubborn owned fake process.
- Reject an unrelated revert selector before submitting the negative case.
- Refuse to count gas exhaustion as the intended liquidity guard failure.
- Accept the intended simulated guard only with a failed, non-exhausted receipt.
- Reject local writes when the loopback listener is not the owned process.
- Reject an unrecognized transaction method before transport.

These use fake transport and fake process objects only. They validate report
recording, cleanup and test-result classification, not live process supervision,
EVM behavior, actual liquidity guards or production security. The source-pinned
run driver has its own later source stage; unchanged methods may reuse these
controls only after explicit comparison, and changed methods retain their own
verification obligations. No past malformed capture is repaired or relabeled.

[The earlier static comparison](METHOD_REUSE_FINAL.json) binds the500d attempt3
stage. [The successful04 comparison](METHOD_REUSE_04.json) binds0ba103: capture
and startup bodies are unchanged, but cleanup adds an owned-state snapshot.
Its actual successful cleanup is captured in the run verification; the eight
offline controls are not relabeled as a full new-driver test suite. Changed
send/receipt checks and helpers retain their own scope. Earlier comparisons
remain their original source stages.

Two additional NEW [deadline-helper controls](DEADLINE_EXECUTION.json) execute
its exact AST with a fake node: fresh empty-block/header calculation produces
300seconds, and pending work blocks clock changes before any call. The pinned
Solidity source permits inclusive now..now+600; the earlier+3600 fixture input
was invalid. These controls are not EVM, process or provider acceptance and do
not rerun the eight previous controls.

Two NEW [Cast parser cases](BOOLEAN_EXECUTION.json) exercise the exact0ba103 ABI
helper for Python True and False and match independently assembled selector/
argument words. This fixes a report-wrapper Boolean spelling error, not an
on-chain issue; no RPC or EVM runs in those two parser cases. No original test
source/hash or prior failure is relabeled after correction.
