# Scoped compiler advisory applicability

Reviewed 2026-10-29 against the existing `build-attempt-011` input/output. All
78 input source/dependency texts still match this checkout. Settings are
solc 0.8.26, Cancun, viaIR, optimizer enabled/runs 1, with `details.yul=false`.
The local command and exact hashes are in
[compiler-applicability-screen.json](compiler-applicability-screen.json).
This step read the existing AST; it did not compile or run tests.

The current official [0.8.26 bug list](https://raw.githubusercontent.com/ethereum/solidity/develop/docs/bugs_by_version.json)
still lists six advisories. Applying the official
[bug predicates](https://raw.githubusercontent.com/ethereum/solidity/develop/docs/bugs.json):

| Advisory | Current scope and qualification |
| --- | --- |
| `YulOptimizerKnowledgeBaseStaleBookkeeping` | Requires Yul optimization; disabled in this exact input. |
| `MisorderedNamedParametersInRequireWithCustomErrors` | Requires a custom error passed to `require`. Fresh source-pattern scan finds only four calls, all with one argument: core `BitMath` lines 13/32 and `FullMath` lines 30/113. |
| `MemoryByteArrayElementDeleteClearsWholeWord` | Applies to the legacy pipeline; this build uses viaIR. |
| `SpillSlotCollisionAcrossMutualRecursion` and `UnsoundSpillInMutualRecursion` | Both involve IR mutual recursion with relocated stack variables. Optimizer-off alone does not exclude them. Manual source-body review found no demonstrated trigger; full generated/virtual call-graph qualification remains open. |
| `LostStorageArrayWriteOnSlotOverflow` | Requires storage arrays crossing the storage-address boundary. Ordinary bounded/hashed storage here gives no demonstrated reachable trigger; this is not a proof against every storage collision. |

The older repository `COMPILER_DEPENDENCIES.md` records its own 77-source AST
screen. Its 1,124-node and declared-call-SCC results are historical evidence;
they were not relabelled as a fresh generated-code proof for this 78-source
closure. This targeted update confirms current settings and `require` sites
only. No compiler upgrade, size/gas gate relaxation or global dependency
security attestation follows. Exact bytecode evidence and real deployed
dependency qualification remain separate release requirements.
