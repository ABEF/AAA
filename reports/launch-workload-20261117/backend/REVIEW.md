# Pre-seal launch-workload checklist

The current unsigned planner now includes two additional **unverified** read checklists:

- `royalty_workload`, targeting the assigned `royalty_rewards`: actual `assetCapacity`, hard ceilings, `assetCount` and every `assets(index)`. Its parameterized read requires a canonical decimal uint256 index starting at0 and strictly below the observed count. It explicitly separates the initial16ERC20 capacity plus ETH from the actual admitted list and64ERC20 engineering ceiling.
- `gas_policy`, targeting the assigned `protocol_policy`: the full tuple, payout/source/royalty-sync getter values and fingerprint. Per-currency gas limits are not whole-operation guarantees. Qualification must measure aggregate healthy/pending/fault work, exact calls/estimates, full20% activation-policy2 or25% maintenance padding, selected service/block bounds and complete fees.

No read is performed by preparation. These instructions observe/admit nothing, infer no live asset count, and enable no setting. The24conditional setup calls and false readiness/authority/adoption flags remain; no gas policy, currency admission, capacity increase or seal call is added. New producer/manifest hashes describe the updated source; old artifacts retain their original hashes/scope.

## Focused evidence

Four NEW methods in `tests_python/test_preseal_launch_workload.py` pass with actual production preparation/current trusted compiler ABIs and synthetic public inputs:

| Method suffix | Actual assertion |
| --- | --- |
| `actual_plan_keeps_capacity_distinct_from_admitted_royalty_workload` | Exact royalty target/read set, initial/lifetime capacity meaning, three workload classes and unverified state. |
| `parameterized_currency_read_requires_observed_zero_based_uint256_index` | Explicit uint256 indexing and observed bound; unknown target remains null without invented count/value. |
| `new_required_reads_exist_on_exact_trusted_target_abis` | Every NEW required read is an actual view/pure callable on its correct current contract; assets takes uint256. |
| `gas_review_remains_unverified_and_cannot_change_setup_calls_or_flags` | Exact gas target/read set, aggregate warning, allfalse readiness, no execution/seal/configuration calls and input preservation. |

The selected module executes4methods in9.484seconds with no failures/errors. Network connection is forbidden during the selection. Recorded source brackets are stable; all61 production Solidity sources and four protected dirty files remain unchanged. Existing test files are not modified or rerun. No compiler/static/EVM/RPC/signing/deployment/old-chain/service/site/journal work is performed. This backend check is not the separately owned launch-scale gas measurement or production acceptance.

[Raw results and source pins](PRESEAL_WORKLOAD.json), [raw log](PRESEAL_WORKLOAD.log), [summary](VERIFICATION.json).
