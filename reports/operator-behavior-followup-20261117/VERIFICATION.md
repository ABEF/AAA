# Verification — operator behavior follow-up

Baseline: `6945eeeba24304b8ddf27ac4c08fe55dc553554e`.
This record distinguishes actual EVM behavior, injected-wire worker tests,
offline planning, compiler/static gates and historical source reuse.

## Distinct method accounting

| Selection | New | Adapted/affected | Scope |
| --- | ---: | ---: | --- |
| Empty-root seal rejection/repair/authority | 3 | 0 | Actual Access/NFT/Policy/factories; explicit unused-module and VRF fixtures. |
| Canonical-preparation fixture and operator stop | 0 | 8 | Seven native fixed-ZZZ current preparation cases; one affected stop/re-enable case. Deterministic venue is not real market execution. |
| Exact-unit original-currency recovery fuzz | 0 | 1 | 1,000 nonzero inputs, independent weighted tickets, recipient deltas, exact drainage and repeat zero. |
| Keeper key/pause/compound boundary | 2 | 1 | One actual-core portfolio case, separate actual controller role case and affected positive seal case. |
| Keeper interval-crossing selection | 9 | 1 | Injected RPC, actual worker cycle including explicit accounting7 case, mocked submission. |
| Current build admission/history preservation | 1 | 2 | Exact new normal artifact/source family, constructor bytes/gates, explicit old-family rejection on changed source. |
| Empty-root prerequisite in both unsigned tools | 1 | 0 | Both outputs explain setup, emit no seal/base setter and retain false approval/live-state flags. |
| **Total** | **16** | **13** | **29 distinct methods; no unchanged full suite.** |

Rights and LP method names, final compiler-source pins, failed baselines and raw
results are retained in [RIGHTS_VERIFICATION.json](RIGHTS_VERIFICATION.json) and
[LP-evidence.json](LP-evidence.json). Worker names/source stages are in
[KEEPER_EVIDENCE.json](KEEPER_EVIDENCE.json). Its runner inventory executes zero
tests and is not counted. Offline planner method/source observations are in
[PLANNER_CHECKS.json](PLANNER_CHECKS.json).

The two adapted build checks and its new historical-family method were run
before the later warning-only output clarification. That exact source stage is
recorded separately; the new pre-seal prerequisite case checks the final warning
source. No unchanged tests were repeated solely to manufacture another total.
Those earlier three Python results were observed in the tool session; a raw
terminal log was not retained and is not invented in the evidence package.

## Compiler and object checks

[compile_normal.py](compile_normal.py) uses pinned Solidity0.8.26/Cancun,
viaIR, optimizer runs1/Yulfalse, preserving the accepted100-source closure.
It admits only the single changed production source. Test-only fixture changes
do not become production compiler inputs.

[BUILD_PINS.json](build/BUILD_PINS.json) authenticates compressed exact compiler
input/output and all48 normal object gates. Only Access creation/runtime objects
change. Concrete ABIs are equal; slot/offset/label and recursive storage type
structure are equal. Raw compiler AST IDs shifted, so an initial raw JSON layout
equality assertion failed; semantic comparison excludes those identifiers. It
does not hide a storage change or relax a compiler check.

| Object | Current size | Margin |
| --- | ---: | ---: |
| Access runtime | 10,854/24,576 | 13,722 bytes |
| Access creation + exact constructor arguments | 48,377/49,152 | 775 bytes |
| Oracle runtime | 24,573/24,576 | 3 bytes |
| Vault runtime | 24,544/24,576 | 32 bytes |

No new normal constructor transaction/gas measurement was performed. EVM
test-body gas includes fixture creation and sequential operations and must not
be treated as production transaction gas. Earlier construction receipts retain
their original objects and source scope.

The official [Solidity bug list](https://raw.githubusercontent.com/ethereum/solidity/develop/docs/bugs.json)
and [security guidance](https://docs.soliditylang.org/en/v0.8.26/security-considerations.html)
were consulted. The retained [compiler assessment](../smart-contract-lp-audit-20261103/compiler-assessment.json)
keeps its original whole-source scope. This change adds a typed static getter/
nonempty-length rejection, no assembly, optimizer/pipeline change, named-error
require or recursive source call. That scoped review does not prove absence of
compiler-generated defects or refresh every historical call-graph result.

## Actual static analysis

[STATIC_REVIEW.md](STATIC_REVIEW.md), [STATIC_RESULT.json](STATIC_RESULT.json)
and [STATIC_CLI_CHECK.json](STATIC_CLI_CHECK.json) record actual analyzer execution
with accepted normal output, no extra compiler invocation, complete570 detector
input and current strict default. Five current contexts are assessed individually;
565 exact unique fingerprints retain unchanged referenced-source evidence.
Descriptions, ordered fingerprints and source bindings reconcile with raw output.

Slither's detector-present Windows exit was4294967295, not exit0. JSON reports
analyzer success without analyzer error; the separate strict checker exits0.
Raw analyzer output/build-info/logs and comparison drivers are preserved in
the [supporting archive](SUPPORTING_EVIDENCE.json). No detector count is counted
as a passing behavior test or independent security approval.

## Preservation and remaining work

[PRESERVATION.json](PRESERVATION.json) records the sole production source change,
four protected dirty-file hashes and unchanged historical tracked report bytes.
Current generated references, Todo, document links and staged Python publication
are checked separately in the final maintenance record. The raw baseline empty-
root seal, stale-fixture failures and zero-selection attempts remain available.

No old Anvil reset, public transaction/deployment/seal, running-service change,
site rollout, signer extension, journal migration or monitoring restart occurred.
Local tests/finite source review do not qualify every token, provider, receiver,
concurrent market state, prolonged outage or operating environment. Real release
qualification and independent review remain mandatory.
