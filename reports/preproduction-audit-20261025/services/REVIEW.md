# Service and keeper internal audit - 2026-10-25

This is an internal source-scoped review, not independent audit or production approval. No live service, monitor, wallet journal, chain or deployment was changed. Website files were inspected read-only; public deployment remains null and its shared signer remains Anvil-only.

## Addressed findings

| ID | Severity | Failure chain and correction |
| --- | --- | --- |
| SV-01 | Medium | Keeper receipt accounting trusted the derived `effectiveGasPrice` and did not bind signed gas/cap/chain fields to the original fee review. An inconsistent RPC receipt could understate/overstate spent gas, corrupting future daily-budget decisions or unnecessarily stopping maintenance. The keeper now captures the bounded fee review durably before invoking the signer, validates transaction chain, exact gas limit and fee cap, and derives type-2 execution price from signed caps and the canonical inclusion block's base fee. Types 0/1 require agreement with signed `gasPrice`; unknown transaction fee types are rejected. |
| SV-02 | Medium | Actual separate L1 fees could exceed the allowance used during submission review without a failed reconciliation. The original fee semantics and L1/total maximum now remain attached to the pending intent. Missing required separate L1 evidence or a captured-bound violation preserves pending state and stops reconciliation. A later configuration cannot reinterpret an earlier pending transaction. |
| SV-03 | Low | Read-only keeper preflight checked the runtime pin but omitted the native accounting-version getter check enforced by live startup. A native profile could appear ready while live startup correctly refused it. Preflight now performs the same version check without signing or modifying state. |

These findings concern keeper budget integrity/readiness. They do not establish an ordinary NFT holder's ability to withdraw principal or control an RPC provider. Fully malicious providers can still forge internally consistent history; read failover is not Byzantine consensus or independent signature verification.

## Captured pending fee review

`pending.fee_review` has exactly these keys:

```json
{
  "schema": 1,
  "gas_limit": 125000,
  "max_fee_per_gas": 1000000000,
  "l1_fee_allowance_wei": 0,
  "maximum_cost_wei": 125000000000000,
  "receipt_fee_policy": "included"
}
```

`maximum_cost_wei` equals `gas_limit * max_fee_per_gas + l1_fee_allowance_wei + pending.value`; all numerical fields are exact integers. Supported policies are `included` and `separate_l1_fee`. Existing top-level accounting versions are unchanged. The signer still selects the EIP-1559 priority within its explicit reviewed maximum fee; the journal binds the maximum, not a separately preselected priority. `last_fee_observation` preserves raw reported and derived execution prices separately after successful canonical checkpointing.

Old intents lacking this record are loaded unchanged. The fixed sanitized `pending_fee_review_required` log tells the operator to preserve original evidence and never resend. Current limits must not be used to invent missing historical review. The operator must stop/fence the old signer, preserve its complete state/configuration and independently reconcile the actual transaction/nonce, original review and network fee semantics. There is no automatic budget repair, transaction replacement, deletion or reset. If original evidence is unavailable, reviewed recovery or signer rotation remains necessary. No existing journal was upgraded by this audit.

Receipt finality, header identity/depth, signed fields, metadata candidate and final canonical execution price all pass before any in-memory or durable spend checkpoint changes. A failed save restores the previous in-memory state. Resolving a discovered hash remains a separate identity-verified journal update; it never implies a successful receipt or advances the spend checkpoint.

## Improved harness and verification

The new independent inclusion transcript uses explicit signed fields, canonical base-fee vectors, review arithmetic and byte-identical recovery-state assertions. Before implementation, its first 12 methods produced 11 failing test methods / 13 failing subcases; the existing reorg negative control passed. For example, a type-2 receipt reported price 99, while signed maximum 10, priority 2 and base fee 3 require price 5: the old code charged 9,910 rather than 510 wei including native value. Wrong chains, absent typed chain IDs, changed gas/caps, invalid fee types/priorities, excessive L1 charges and missing historical reviews were wrongly accepted. A separate failing-first preflight case returned ready for an actual version-1 getter under a version-2 profile. These initial diagnostics were observed in the tool transcript; no standalone raw prepatch log is claimed.

The final scoped run [log](keeper-scope.log) / [receipt](keeper-scope.json) discovered 200 distinct cases: 198 passed, one Unix-only case skipped, and one stale fixture left an otherwise mocked live signer in unqualified fee mode. That fixture was corrected to declare its intended `included` fee policy; [only that case was rerun](keeper-repaired-storage-case.json). The final fixed sanitized legacy event and unchanged-state assertion were [rerun separately](keeper-legacy-event.json). Final result: **199 distinct scoped passes, one explicit Unix-only skip**, including 18 new regressions (17 fee and one preflight). Repeated cases count once.

[Final bindings](final-bindings.json) retain exact source/test/CI hashes and verify the only final production delta from the broad receipt is the fixed log call in the already-tested legacy-refusal branch. The changed branch has its own final-source rerun. This is not a fresh full final-source regression. Legacy receipt fixtures now include actual signed chain/gas-price fields and the signing-time padded gas limit; implementation guards were not relaxed to preserve fictitious fixtures.

Equivalent scoped command from repository root, with the pinned Foundry v1.4.4 directory on PATH:

```sh
python -X utf8 -m unittest -v tests_python.test_keeper_fees tests_python.test_keeper tests_python.test_metadata_keeper tests_python.test_keeper_recovery tests_python.test_keeper_ops tests_python.test_keeper_native
```

The exact observed runner is preserved alongside the receipts. Windows/Python execution covered mocked recovery/state durability and the actual pinned `cast --help` parser, which exits before signing or RPC. The Unix ownership/symlink case was skipped explicitly. The required Ubuntu keeper workflow now includes the new fee module; its future CI result and actual Linux process-crash rehearsal are separate evidence. No public signing, live provider qualification or new process/service rehearsal was performed.

## Other reviewed boundaries and remaining gates

- API handlers have bounded framing, per-IP admission, child-process isolation, hard/cooperative deadlines, sanitized logs and no transaction signer. Canonical projections/history remain same-block and fail closed on unavailable data. Their implementation does not qualify real Linux hosting, provider quotas, full workload latency or distributed DDoS resistance.
- The index database is operator-maintained evidence, not proof of log completeness. Source/provider compromise, omitted history, deep reorgs and long-term archival availability remain external qualification boundaries.
- Local file locks do not fence another host using the same keeper key. Off-host monitoring, private backups, signer revocation/rotation and lost-host recovery still require real operating qualification.
- Website production data/pricing/native-version integration, actual provider/route/feed/VRF choices and independent audit remain release gates. No new qualification is inferred from mocks or the code fixes above.
