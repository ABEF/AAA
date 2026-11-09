# Consumer compatibility review — 2026-11-09

Read-only inspection of the six contract commits after `2138dd6` through `d811856`, plus the unchanged source9 website at `a41dbf8`. The initial inspection performed no tests, network probes, signing, deployment or source changes. Two resulting preflight fixes were then explicitly authorized and verified as described below.

Two narrow consistency findings were found in the pinned source and are now corrected locally:

| ID | Priority | Location | Finding | Minimal correction |
| --- | --- | --- | --- | --- |
| CONSUMER-01 | P2 | `zzz_ops/production_v15.py:160` | `current_phase` is range-checked but not reconciled with the pinned block timestamp and inclusive stage windows. | Recompute the deterministic phase, including0 during gaps and before/after sale. Do not require the sale to be open. |
| CONSUMER-02 | P3 | `zzz_ops/production_v15.py:167` | `False` aliases0 in signer/token-gate counter comparisons. | Require exact integer type and zero for each counter. |

These concern offline observation consistency. Actual contracts still enforce their phase and authority rules; the ordinary observer produces integer counts. Neither finding establishes a live exploit.

Source9 remains V9/schema16 and unsigned: it cannot silently accept V10, never constructs the signing transaction controller, and preserves the shared signer and both null public configurations. New API mint2/V10 is explicitly selected, verifies immutable mint bindings, blocks direct mint preparation, and keeps mutable sale state separate from existing claims. LP/royalty monetary units, original mint recipients, current-owner rights, versioned history/checkpoints, exact approvals and reviewed gas boundaries were traced without finding a concrete wrong-output or public-signing defect.

`REVIEW.json` contains the detailed boundary inventory, exact reviewed revisions and38 source hashes. This inspection is not independent approval or operating qualification. Root may implement the two fixes separately; this report records the original findings without rerunning unchanged evidence.

The only implementation edits are `zzz_ops/production_v15.py` and `tests_python/test_production_v15.py`. The synthetic fixture now explicitly observes timestamp300, the inclusive start of its public stage. Five new methods first ran against the unchanged validator:16 mismatching/invalid subcases failed as expected, while valid boundaries and interstage gaps already passed. After the two fixes, all13 methods in the affected inventory class passed once. Raw red/green logs and before/after source hashes are retained under `regression-01/`; unchanged observer-wire, browser and Solidity suites were not rerun. No RPC, deployment, financial-limit, contract, signer, website, service or journal change occurred.
