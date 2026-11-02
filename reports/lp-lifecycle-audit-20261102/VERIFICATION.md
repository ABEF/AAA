# LP lifecycle verification and evidence boundary

Reviewed 2 November 2026. [Findings and implemented changes](REVIEW.md).
Evidence is internal, source-scoped and not a full release qualification.

## Executed checks

| Campaign | Actual result | Scope |
| --- | --- | --- |
| Routing negative control |2 expected failures against original production sources | Actual-core ordinary single/hybrid quotes end at ticks-403/-401 for lower-400; verifies the reported failure existed. |
| Initial routing repair |2 passes | Same targeted regressions; included in the later24, not additive. |
| Final routing regression |24/24 pass | Both modes, active candidate selection, exact lower tick, downward-crossing ambiguity, unauthorized planner, existing routing and contribution policy. |
| Composed portfolio lifecycle |39 passes,2 fixture-expectation failures out of41 | Both new mode/reward lifecycle tests pass. First failing fixture requested60.01% but expected60.005% to qualify. Second expected mint to be reached, although the repaired planner now rejects earlier. |
| Corrected fixture methods |2/2 pass | First uses the actual default60% floor. Second witnesses the earlier planner rejection and retains exact Slippage/full old-LP rollback checks. No production limits loosened. |
| Geometry-provenance backend |5/5 pass | Main/residual identity/coherence, malformed geometry and price-outage availability; explicitly false source-independence metadata. |

There are **65 distinct successful EVM methods across these stages**, not67 and
not a one-shot fresh final full suite. Compiler metadata authenticates the
reconstructed first-stage test source after LF normalization; only the two
listed fixture expectation bodies differ from the corrected final lifecycle
file. The other39 successful bodies are reused. Final routing and corrected
lifecycle test files match their compiler metadata. [Method/stage ledger](tests.json)
records individual results, source scope and raw-output hashes.

Tests use real local Uniswap v4 core/PositionManager/StateView and isolated test
funding. Access, registry/feed/VRF/Permit2 fixtures and explicit callback-failure
injections are substitutes, not approved production services. The test harness
permits large fixture contracts; normal production limits below are separate
and were never relaxed. No RPC, signer, Anvil state or public transaction used.

## Exact production build

[Normal gates](production-size-gates.json):52 production sources plus31 explicit
dependencies;43 runtime/initcode gates pass at
`normal-final-a8e7dc7cc5`. Solc0.8.26/Cancun/viaIR/optimizer1/Yulfalse unchanged.
Compiler executable SHA256:
`537fd8d8d4a0433a971bf456fc06f7b021cdcee27b252f74da49e0d8559aeb67`.
Closed-input source pins, exact compiler input/output hashes and settings are
recorded; source contents stayed unchanged during the accepted build.

| Object | Final runtime bytes | EIP170 headroom |
| --- | ---: | ---: |
| LP Balancer |24216|360|
| Liquidity Manager |21943|2633|
| Vault |23941|635|
| Migration Budget |24339|237|
| Migration |24556|20|

[Build attempts](build-attempts.json) retains the rejected24953-byte Balancer
attempt. It did not pass. The final stored-tick comparison avoids the large
inverse-tick routine and preserves the exact downward-crossing condition.
These are object sizes, not deployment binding, live strategy gas or economic
qualification. Two production files changed; the other50 retain original hashes.

## Fresh static analysis and internal dispositions

[Execution receipt](static-execution.json) binds Slither0.11.6/crytic0.4.2 to the
accepted final compiler artifacts. Compiler was not invoked again. Analysis
succeeded with475 detector records:75High/92Medium/211Low/76Informational/
21Optimization. Its Windows finding exit is4294967295, not a clean no-findings
exit. Raw detector output/log hashes and tool versions are retained.

[Strict review](static-review.json) and [coverage](static-coverage.json) account
for all475 records:407 reused only where exact detector fingerprint/context and
all referenced sources are unchanged;68 current contexts reviewed. The checker
rules are unchanged. Its default review path now points to this exact-source
record. Dispositions are internal technical judgments, not proof of absence of
exploits or an independent audit. Previous471-record/source reports remain historical.

## Records, preservation and publication

[Preservation](source-preservation.json) binds the base main,52 raw source hashes,
the four unrelated tracked dirty-file hashes and2568 original report hashes.
All protected files and historical reports remain byte-identical. Original
current guides and test fixtures were archived externally before changes.

Raw compiler, EVM and95MB static artifacts are retained outside Git at
`C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/lp-lifecycle-audit-20261102`.
Compact evidence is published here. Generated Todo/callable references, current
links, staged/committed Python publication and exact remote publication are
checked separately in [final checks](FINAL_CHECKS.json). No deployed update is
implied. Production approval, a full-suite green published CI, real routes/feeds/
VRF/marketplace/host acceptance and independent audit remain open.
