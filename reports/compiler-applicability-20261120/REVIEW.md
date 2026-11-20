# Current compiler-advisory applicability

20 November 2026. Baseline `519ff4f075022f789f46facbab56f0a944705b11`.
Trusted build: `activation-final-six-20261118`, F6/allocation2.
**No compiler/source/runtime change; production remains NOT APPROVED.**

## Result

Fresh official registry retrieval and exact current-source applicability review
found **no confirmed reachable compiler defect requiring a compiler upgrade**.
This completes the current advisory-assessment subtask within P02, not P02's
broader reproducible-release/freeze obligations, independent audit or proof of
compiler correctness. Reassess after source/dependency/settings changes or new
advisories before deployment.

The accepted build uses Solidity `0.8.26+commit.8a97fa7a`, Cancun, via-IR,
optimizer enabled/runs1, **Yul optimization explicitly disabled**. Calling this
only an “optimized via-IR build” misses the decisive setting for one advisory.
No default, guard, authority, economics, bytecode gate or deployment profile changed.

## Exact evidence and official scope

[Official retrieval](OFFICIAL_FETCH.json) preserves URLs, UTC timestamps, byte
lengths, hashes and ETags for the current official
[bug registry](https://raw.githubusercontent.com/ethereum/solidity/develop/docs/bugs.json)
and [version index](https://raw.githubusercontent.com/ethereum/solidity/develop/docs/bugs_by_version.json).
The index names eight variants for0.8.26, representing seven distinct advisory
IDs; one new advisory has separate legacy/via-IR entries. These are not eight
confirmed project vulnerabilities. The [previous six-advisory assessment](../direct-entry-v3-20261103/compiler-assessment.json)
is preserved at its original83-source/3November scope.

[AST assessment](AST_ASSESSMENT.json) authenticates the captured admitted input/
output hashes, exact settings and current filesystem bytes for all100 compiler
sources:61 project plus39 dependencies, with four build controls. It reuses
the existing compiler output; no compiler execution or normal size gate was rerun.
Metadata identifies the expected compiler version. This is not independent
authentication of the compiler executable's supply chain or deployed upstream
contracts compiled outside this closure.

## Dispositions

Full machine-readable records, original conditions/fixed versions and direct
disclosure links are in [ASSESSMENT.json](ASSESSMENT.json).

| Advisory variant | Current disposition and evidence |
| --- | --- |
| SOL-2026-8 legacy recursive storage-struct copy | Legacy pipeline is not used. The separate via-IR variant is evaluated below. |
| SOL-2026-8 via-IR recursive storage-struct copy | No relevant recursive type:75 current StructDefinitions form no recursive cycle through copied struct/array members. Mapping-only recursion is distinguished from the disclosed dynamically-array-recursive copy trigger. |
| SOL-2026-7 Yul optimizer bookkeeping | Required Yul optimizer passes are disabled by exact `optimizer.details.yul:false`. EVM optimization is a separate setting. |
| SOL-2026-6 named custom-error require | No named-argument custom-error `require` exists in the complete AST. Ordinary/standalone custom-error reverts are different constructs. |
| SOL-2026-5 memory-byte delete | Legacy evmasm-only disclosure; current build uses via-IR. |
| SOL-2026-4 mutual-recursion spill collision | No source internal-call cycle or unresolved internal call in the refreshed conservative graph, including virtual overrides and correctly static `super`/explicit-base dispatch. This is not a formal proof of compiler-generated spill correctness. |
| SOL-2026-2 unsound mutual-recursion spill | Same current-source result and limits. Do not exclude it merely because Yul optimization is disabled: the official condition can apply independently of optimization. |
| SOL-2025-1 storage-end array write | No realistic trigger established. Captured static layouts end no later than slot52; largest literal fixed array has16 elements; no layout specifier or source storage-pointer slot reassignment. Bounded membership/bucket arrays and append-only histories remain subject to ordinary keccak storage assumptions, not a mathematical guarantee for arbitrary astronomical states. |

The call graph has1,334 implemented function/modifier nodes,2,042 internal
callsites and2,088 conservative edges. Current project-only count is1,085
(1,056 functions plus29 modifiers), consistent with the workload inventory.
These are analysis counts, not executed tests or additional audit passes.

Unlike the old83-source assessment, current Oracle source contains two local
Yul `words` helpers, at [line333](../../src/ZZZOracle.sol) and line371.
Each only loops over a bounded copy and calls built-ins; neither recursively
calls itself or another source Yul function. The old “no Yul functions” claim is
not relabelled current. Generated IR was not selected in the original admitted
output; this review does not reconstruct or formally prove arbitrary generated
helper behavior by rerunning compilation.

## Analysis corrections and verification

The first conservative graph incorrectly treated static `super` and explicit
base calls as dynamic dispatch to every override, producing artificial ERC721
cycles. Its [unrefined result](AST_ASSESSMENT.unrefined.json) and
[original analysis source](analyse.unrefined.py.txt) are preserved. The final
[analysis](analyse.py) distinguishes static calls from ordinary virtual calls.
A broad source `.slot` screen was also narrowed to actual reassignment syntax;
reading `book.slot` is not assigning a storage-pointer slot.

Seven **new offline checker methods** in [test_analysis.py](test_analysis.py)
pass: positive mutual/self recursion versus DAG, positive array-recursive type,
mapping-only exclusion, static super and explicit-base calls, virtual override
inclusion, and named-error require trigger/nontrigger. These validate the audit
screens; they do not execute Solidity or prove the compiler correct. Three
revised analysis executions are one evolving review, not three independent passes.

[Verification](VERIFICATION.json) binds exact files, methods and limits. No
unchanged contract/browser/Python suites, compiler, static analyzer or size
campaign was rerun. The initial restricted HTTPS fetch was refused before any
response; the [fetch limitation](FETCH_LIMITATION.json) records the separately
reviewed read-only official-source fetch. No RPC/key/public transaction was used.

## Remaining release boundary

Independent review should still assess the final frozen code/configuration,
compiler applicability limitations, inline assembly and upstream token/core/
periphery/provider implementations. Actual chain/compiler compatibility, final
construction, sizes after any future change, complete fees, market inputs and
operating qualification remain open. No deployment, sealing, signing, hosted
service/site, old chain/journal/checkpoint or paused-heartbeat action occurred.
