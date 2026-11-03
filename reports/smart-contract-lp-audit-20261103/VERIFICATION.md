# Verification and source boundary

Reviewed3November2026. Base main `e0ea4dcd4762c1c4016b7861bbacc42c2c1d72dd`.
[Review](REVIEW.md), [prompt](AUDIT_PROMPT.md), [coverage](COVERAGE.md).
No production Solidity or dependency/build setting changed in this campaign.

## Fresh checks

| Check | Result / exact meaning |
| --- | --- |
| Infeasible residual gap | New actual-core method passes: admitted but unplaceable geometry rejects, all old LP/share/reward/idle state survives, then disabled mode safely merges. |
| Minute-long price outage | New actual-core method passes: NAV fails closed, two-leg harvest/partial raw claims/residual-only closure work, shares/main survive, restored prices allow a later guarded merge. |
| Corrected final EVM selection |2/2 methods pass. The first stage had1 pass/1 fixture failure; the two successes are not additive to3. |
| Function inventory |52 project sources,795 implemented function/modifier bodies and342 declarations. AST enumeration is not795 tests or795 formal proofs. See [coverage](COVERAGE.md). |
| Compiler construct analysis | Exact83-source AST closure(52 project/31 dependencies),1023 implemented bodies/modifiers: no source internal-call cycles, unresolved internal calls, source Yul functions or named-error require constructs in the conservative graph. Applicability limitations are explicit in [assessment](compiler-assessment.json). |
| Source consistency |52 sources; zero errors. Narrow syntax/import/primitive checks, not compilation or security proof. |

EVM driver uses Forge1.4.4 with pinned solc0.8.26, isolated output/cache and explicit
large-fixture size allowance. Actual local Uniswap core/PositionManager/StateView
execute; synthetic access/admission, four correlated USD feeds, VRF/Permit2 and
test funding remain substitutes. One minute is a virtual timestamp step, not a
one-minute live service test. No existing Anvil/RPC/wallet/nonce journal was used.

The first failed outage test attached expectRevert to the intervening public
Budget-address getter rather than NAV. The corrected fixture obtains the Budget
before arming the expectation. Production guards were unchanged. Both stage
source texts are authenticated against their compiler metadata keccak and stored
alongside raw results. Compiler source binding uses LF normalization; the raw
working-file hash is recorded separately. A first final-check attempt incorrectly
compared that raw Windows hash with the compiler's LF hash and was corrected
without rerunning or changing the EVM test. A first preservation-helper attempt removed an older
identical declaration; the corrected last-occurrence reconstruction matches the
compiled source. Neither helper attempt is an EVM pass.

## Exact unchanged-source reuse

[Normal source pins/gates](../lp-lifecycle-audit-20261102/production-size-gates.json)
match all52 production files/31 dependencies and existing compiler output
SHA256 `069ae7fcc97ea97f7a114576c95c25da44937b9edf769672acb6d90771178e36`.
Thus reuse43 normal runtime/initcode gates and the source-scoped
[475-record static triage](../lp-lifecycle-audit-20261102/VERIFICATION.md#fresh-static-analysis-and-internal-dispositions).
No repeated full Solidity suite, normal compile or static invocation is claimed.
The prior static process emitted findings; it was not a clean no-findings exit.

| Normal object | Runtime bytes | EIP170 headroom |
| --- | ---: | ---: |
| Vault |23941|635|
| Migration Budget |24339|237|
| Migration |24556|20|
| LP Balancer |24216|360|

The existing [multi-day cases](../portfolio-long-horizon-20261102/VERIFICATION.md)
and [LP lifecycle methods](../lp-lifecycle-audit-20261102/VERIFICATION.md) retain
their original scopes, fixture corrections and reuse rules. New tests complement
their cases; no sum of old/new counts is a fresh entire-release result.

## Evidence, preservation and publication

Raw exclusive root:
`C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/smart-contract-lp-audit-20261103`.
It retains baseline/originals, both execution attempts, corrected metadata-bound
test sources, official compiler-list snapshots, call-graph/inventory drivers and
compiler artifacts. [Machine summary](verification.json) pins accepted artifacts
and records preservation/document-check results.

Original271 current files were archived before edits. Existing2670 report
artifacts and the four unrelated tracked dirty files are preserved; reports index
is the intentionally maintained navigation exception. Unrelated drafts are not
published. Source publication does not update services, sites, old profiles,
journals, signing, Anvil or the paused heartbeat.

No full-suite/CI/independent audit, live economic/provider qualification,
deployment or production approval is implied. Operational promises require
their separately authorized rehearsals.
