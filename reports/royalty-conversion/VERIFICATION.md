# Royalty conversion and outage isolation verification

2026-10-19. **Development candidate; release NOT APPROVED.** No public transaction,
contract deployment, website/server change or monitoring restart occurred.

| Check | Result and evidence | Scope |
| --- | --- | --- |
| Affected Solidity suites | [135 passed](solidity.json), no failures/skips; [individual results](test-results.json) | 22 conversion/outage cases, 22 existing royalty cases, 22 claim-router cases, 34 complete canonical handoff cases, 27 metadata cases and eight gas cases. Includes 1,000-run conservation fuzzing. |
| Normal production compilation | [31 runtime/initcode-object gates; 40 source bindings](build.json) | Solc 0.8.26/Cancun, normal via-IR/optimizer settings. Constructor arguments still require deployment allowance. |
| Keeper Python checks | [195 distinct passes; two Windows platform skips](python.json) | Combined scoped coverage: 184 unchanged existing passes plus 11 corrected new-worker cases. Not one newly executed all-green 197-case run. |
| Static analysis/internal review | [392 dispositions, complete coverage and five rejected review mutations](static-review.json) | 378 expressions matched to the preceding review; 14 new entries reviewed. 167 false positives, 75 accepted risks, 150 informational. [Execution binding](static-execution.json); [security review](REVIEW.md). |

The final Solidity source remained unchanged during execution. Compiler metadata
binds every production source. The royalty receiver is 20,696 runtime bytes, its
factory 22,243, and the new converter 12,553. Existing Vault headroom remains only
19 bytes; this work adds no Vault bytecode. The eight gas fixtures retain their
existing budgets and assertions; they are not real-router, production-fee or
every-token-failing gas qualification.

The static analyzer completed successfully. Its Windows process status
4294967295 is the finding-present exit status, not a clean zero-finding result.
Every detector entry has a disposition in the current
[review ledger](../production/slither-review.json). This is an internal review,
not an independent audit or a guarantee against vulnerabilities.

## Attempts and reuse

[Earlier attempts](attempts.json) remain separate. The initial fuzz test failed
because its mock wrapper had insufficient ETH; only fixture funding was corrected.
The Python fixture clock was also corrected without weakening freshness checks.
The final callback-view guard changed Solidity, so the seven affected suites were
run again on the final source. Unrelated bridge, pool and frontend suites were
not rerun. Historical complete-suite/fork results keep their original scope.

An initial build hit the Windows signature-cache permission boundary. A retry
succeeded. The first final static-input check rejected incomplete incremental
compiler records before analysis; a full production compilation supplied the
complete final compiler input. Neither failure was silently treated as success.

## Remaining qualification

Conversion is opt-in and requires binding the fixed helper before sealing, with
reviewed wrapper/router/token policies and real feeds. The generic seal procedure
does not require this optional helper: production inventory review must verify its
binding when automatic ETH settlement is intended. Actual route liquidity,
marketplace receipts, service deployment, keeper economics, full release checks
and independent audit/remediation remain open in the [central Todo](../../TODO.md).
The frontend still needs per-currency deferred eligibility and conversion history.
LP allocation and royalty rarity weights are unchanged.
