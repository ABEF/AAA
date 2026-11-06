# Verification scope

6 November 2026. Baseline main `b76dfcc5d1a2513ce6b277e43a6254eb63a74640`.
Production **NOT APPROVED**. See [changes and limits](REVIEW.md).

## Solidity allocation engine

The final [test record](accounting/FINAL_TEST_REVIEW.json) covers **17 distinct
successful methods**: 15 exact-source unchanged successes plus two final
default-budget differential methods. Two fuzz properties each ran 1,000 inputs.
Earlier baseline, combined and diagnostic runs overlap; they are not added.
The [reuse proof](accounting/DEFAULT_SPLIT_REUSE_PROOF.json) binds unchanged test
methods/helpers, source closure and the split action/assertion sequences.

Coverage includes both final currency units, independent eager/rational math,
fixed-weight batching and claim order, real growth/no-op/empty transitions,
old-weight rights for both books, outstanding limits with repeated lifetimes,
overflow/invalid rollback, 1,000 ordinals without padded recipients, full-width
carry/rebase and the integer-boundary phase approximation limitation. Complete
storage differential checks include every node after every selected action.

Final source SHA256:

| File | SHA256 |
| --- | --- |
| `src/libraries/ExactLPAllocation.sol` | `346aec80ab734d2e4d751a48ada676b0ab1b3a14607fe13a75d336b6a30a8a72` |
| `test/ExactLPAllocation.t.sol` | `b88100bfe45912a99811822e13eb800dd41b6176e4b8e85a34275dd5e5ea155e` |
| `test/helpers/ExactLPAllocationBaseline.sol` | `e165eadc22cb7902f66fbcf80c25df21c5c55efb42788df9468f74bda7482c8a` |

The frozen baseline helper is test-only. Initial test parsing rejected the
reserved identifier `after`; corrected test compilation is separate. The former
combined scanner exceeded default 1,073,741,824 gas, then passed a diagnostic
10-billion test budget. Final scanners were split at an existing fresh-pair
boundary and pass **without a gas override** at 689,488,274 and 401,664,650.
No foundry configuration or production/operating gas cap changed. Large scanner
costs are full-state test assertions, not estimates of an operator transaction.
Historical failures and diagnostic source snapshots are retained.

## Normal compilation and static review

[Contract verification](contract/CONTRACT_VERIFICATION.json) and
[comparison](contract/NORMAL_COMPARISON.json) bind the final source closure:
**85 Solidity sources, 45 normal objects and two actual Factory carrier gates**.
All 84 prior source hashes and 44 prior ABI/runtime/creation objects are identical.
Only the new internal library shell is added: runtime 62 bytes / creation 93.
It is not the integrated host. Vault remains runtime 24,469 / headroom 107;
Manager 22,411 / headroom 2,165; Rewards 21,311 / headroom 3,265.

Actual Slither 0.11.6 / crytic 0.4.2 output succeeds. Its raw Windows findings
exit code is retained alongside analyzer JSON success; it is not confused with
a failed analyzer. The strict [review](static-review.json) covers **497 records:
three individually reassessed false positives and 494 unique exact-source
reuses**. Three descriptions reorder unchanged nested call/write leaves; each
was reviewed explicitly. Checker normalization was not broadened. The initial
strict-match rejection remains preserved. The new library has no detector flag;
the separate implementation review covers all eleven internal/private functions.
Static silence does not prove correctness, funding safety or independent approval.

Compiler and raw analyzer streams are deterministically compressed where large;
copy manifests bind original bytes and decompressed checksums. Original baseline
normal/static stages remain historical. No unchanged full project EVM suite was
rerun and no published CI result is inferred.

## Backend diagnostic

[Backend evidence](backend/BACKEND_EVIDENCE.json) records **40 distinct focused
Python methods**: ten new retry cases, 29 operation-review methods and one
current6 outage/harvest method. All pass, without skips. The original three-action
retry mismatch is reproduced; the first decimal-string TypeError is retained
with its correction. Runs overlap and are not summed.

Cases cover future/equal/expired/missing deadlines, missing journal, decimal
strings, pending/lifecycle/authority precedence and current6 price-outage harvest.
No added RPC or journal write is used to produce the new diagnostic.

## Source publication and preservation

Maintained feature/Todo, economics, architecture, operator, roadmap, release and
repository context distinguish the implemented engine from unfinished ledger
integration. The current ABI reference is regenerated from the final normal
compiler output. All 888 explicit operator call rows are preserved; there is no
new explorer target or operator switch for this internal library.

Final Todo, callable/operator reference, strict static coverage and source
consistency checks pass. The three affected reference/checker test modules pass
93 methods; this is documentation/default-binding verification, separate from
the 40 backend methods. The first Todo check caught a stale generated sentence;
its failed log remains beside the regenerated passing check.

[Physical copy manifest](COPY_MANIFEST_PHYSICAL.json),
[accounting copy manifest](accounting/COPY_MANIFEST_ACCOUNTING.json) and
[backend copy manifest](backend/COPY_MANIFEST_BACKEND.json) bind evidence bytes.
Final publication closure and preservation records accompany this report.
Four protected dirty files, original reports,
unrelated artwork/drafts, website, Anvil, journals and signing boundaries are
preserved. Source/docs publication makes no deployment or production approval.
