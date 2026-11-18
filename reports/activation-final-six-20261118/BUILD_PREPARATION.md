# Prepared verification wrappers

These scripts are prepared for review. They have not compiled or run the new
combined source. They do not authorize rollout, signing, deployment or sealing.

The baseline is the actual trusted `activation-gas-20261118/build/final01`
normal input/output, not an engineering source override. The new owned root is
`activation-final-six-20261118` beneath the visualization workspace. Public
normal evidence is written to this report's `build/final` only after admission.

## Freeze and one normal compilation

The existing schema1 `SOURCE_FREEZE.json` in the new owned root must include
the exact61project source hashes, protected four-file hashes, unchanged fixture
hash and original `foundry.toml` hash. Add this explicit object:

```json
"normal_build": {
  "build_id": "activation-final-six-20261118",
  "baseline_input_sha256": "EXACT_BASELINE_INPUT_HASH",
  "baseline_output_sha256": "EXACT_BASELINE_OUTPUT_HASH",
  "approved_changed_source_sha256": {
    "src/libraries/ExactLPAllocation.sol": "EXACT_ADOPTED_RAW_FILE_HASH"
  }
}
```

Only actually adopted changes belong in that map. Optional approved families
are `src/ZZZRoyaltyRewards.sol`, `src/libraries/ExactRoyaltyAllocation.sol`,
`src/ZZZContributionPricing.sol` and the independently verified canonical codec in
`src/ZZZOracle.sol` and an independently checked identity codec in
`src/ZZZV4SpotPriceFeed.sol`. A different family needs an explicit wrapper
review. Unknown layouts are never normalized into acceptance.

After the root agent freezes source, `build_final.py final01` performs one
closed100-source normal compile and48size gates. It emits strict ABI equality,
canonical function/tuple/event/error/constructor types and mutability checks,
private semantic-layout differences, exact input/output/source/compiler hashes
and authenticated royalty payload/two-part hashes. A successful size result
still has `pass:false` pending explicit admission.

## Review outputs without compiling again

For changed private layouts or ABI parameter/output names, review the emitted
`PRIVATE_LAYOUT_DIFFS.json` and `ABI_STORAGE_COMPARISON.json`. Put exact accepted
pairs into a separate `LAYOUT_ACCEPTANCE.json` in the owned root:

```json
{
  "schema": 1,
  "build_id": "activation-final-six-20261118",
  "reviewed": true,
  "source_freeze_sha256": "EXACT_FREEZE_HASH",
  "compiler_input_sha256": "EXACT_COMPILED_INPUT_HASH",
  "compiler_output_sha256": "EXACT_COMPILED_OUTPUT_HASH",
  "accepted_semantic_storage_deltas": {
    "SOURCE_PATH:CONTRACT_NAME": {
      "baseline_semantic_sha256": "EXACT_BASELINE_SEMANTIC_LAYOUT_HASH",
      "final_semantic_sha256": "EXACT_REVIEWED_FINAL_LAYOUT_HASH"
    }
  },
  "accepted_abi_name_changes": {}
}
```

The ABI-name map must exactly reproduce any reported name/internalType changes,
keyed by contract identity. Public signature, tuple type, output type, event
indexedness or mutability changes cannot be approved by this file. Empty maps
are appropriate only when those differences are absent.

`build_final.py final01 --admit` recomputes comparisons from the captured input
and output, checks current source/freeze/compiler/build hashes and exact review
acceptance, then runs strict offline artifact admission. It does not invoke
Solidity again. Historical baseline evidence is preserved. Private LP carries
must retain the exact two-slot `packed`/`wide` footprint; a fresh sentinel is
not permission to reinterpret an old physical deployment.

## One affected workload,13controlled cases

The existing `RoyaltyRoundsCapacity20261118` fixture and exporter remain
byte-identical at
`f648f3f21f2d3fbf80795211ec2afce7efca1a06d1bc43fc707188c389643e57`.
The four wrappers adapt campaign paths and explicit new-build acceptance, while
retaining the prior controlled1,000-NFT population,13exports, actual20M calls,
full20%padding, unchanged fault read caps and financial checks.

The compile wrapper uses one new owned Forge cache. The execution wrapper
reuses that cache and requires a source-bound exclusive configuration window
before temporarily adding the owned export permission; it restores the original
configuration and preserves any unexpected concurrent configuration change.
The verifier accepts only fresh normal bindings from this campaign, checks
actual normal and fixture source identities and starts only new owned loopback
nodes. Existing chains, journals and services are untouched. All owned nodes
must be stopped. Thirty-two-million diagnostic execution never admits a failed
twenty-million profile.

`NORMAL_BINDING.json` retains the previous exact artifact path/hash fields and
adds `build_id:"activation-final-six-20261118"`. Its freeze hash must match the
new source freeze. `RUN_WINDOW.json` retains the explicit freeze hash, stage and
exclusive configuration-window flag. Old campaign bindings and interrupted
attempts must not be relabelled.

This re-executes one affected existing method, not thirteen tests. It is not
maximum64-currency/LP2 qualification, real market/provider/fee qualification,
operation acceptance or independent release approval.
