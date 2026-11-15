# Isolated local deployment rehearsal

Baseline `2b7ce7630288a70c4c30af51584ce30f8e89ee23`. The first isolated run
successfully constructed and bound the fresh schema17/mint2/V10/execution1/LP3
graph **without sealing**. Production is **NOT APPROVED**.

## What executed

- **44 successful transactions:**25 creations and19 bindings, with sequential
  bootstrap nonces0–43 and zero native value. Internal creations are included in
  their parent's gas, not counted as additional transactions.
- **39 protocol instances:**17 core contracts,20 callable helpers and2 inert
  code-data children. Exact constructor inputs match the accepted normal objects;
  actual CREATE return bytes match observed immutable-patched runtime code.
  The two getter-discovered child arguments are resolved from actual addresses.
- All16 Access module bindings, separate policy/converter/mint-helper bindings,
  constructor grants/payee and112 binding/state reads reconcile. The graph
  retains its bootstrap, `isSealed=false`, canonical state0 and zero NFTs/buckets/
  residuals. No fixed-ZZZ, feeds, pools, VRF or mint-sale configuration is adopted;
  the bound converter remains disabled and mint helper unconfigured.
- Only a new PID-owned loopback Anvil with fresh genesis was used. Its45 mutations
  have exact socket/PID and genesis/runtime checks;90 ownership observations are
  retained. The owned node stopped with no pending submission. Existing8902/57306,
  journals, services, sites, public-null configs, browser signer and paused
  heartbeat were not contacted or changed.

The [independent receipt/runtime review](INDEPENDENT_RECEIPT_REVIEW.json) and
[independent binding-call review](INDEPENDENT_BINDING_CALL_REVIEW.json) verify
the exact39 CREATE inputs/outputs,19 binding payloads and actual final state.
The latter independently encodes every binding from actual module IDs and
targets; neither relies only on the producer's allowlist.

## Gas and original size limits

Total receipt gas: **141,382,621**, consisting of140,243,511 creation gas and
1,139,110 binding gas across44 blocks/transactions. The largest transaction is
NFT construction: **11,337,831 raw/estimated**, **14,172,289** with full25% padding,
below the new local node's32M ceiling. These figures are not one block's gas,
an operating-budget change, a complete Robinhood fee estimate or approval to
deploy publicly. The12M/20M/24M operating policies/defaults stay unchanged.

Current compiler objects are reused at their exact100-source closure. Cancun
and original EIP-170/EIP-3860 limits remain enabled; no code-size exemption,
production Solidity change, compiler or static-analysis rerun occurs. Oracle's
actual runtime/initcode are24,573/49,073 bytes, leaving3/79 bytes respectively.
Vault32 and Manager101 runtime-byte margins remain. The first inert carrier is
exactly24,576 bytes; that source-derived data boundary is checked explicitly.

The following measurements use a short controlled URI, synthetic roles and
constructor-only external getter/revert doubles. The exact archived SeaDrop
runtime is seeded locally, with controlled storage. Native Registry runtime
admission does not pass these doubles. Real periphery costs, final release
arguments, dependency controls, target gas/complete posting fees and fee ceilings
remain unqualified. No market, VRF, minting or operating rehearsal is implied.

| Creation | Estimated gas | Padded limit (25%) | Receipt gas |
| --- | ---: | ---: | ---: |
| access | 10,191,707 | 12,739,634 | 10,191,707 |
| protocol_policy | 3,545,498 | 4,431,873 | 3,545,498 |
| migration_budget | 5,357,684 | 6,697,105 | 5,357,684 |
| metadata_renderer | 4,257,982 | 5,322,478 | 4,257,982 |
| portfolio_policy | 4,257,603 | 5,322,004 | 4,257,603 |
| rebalance_confirmation | 3,264,752 | 4,080,940 | 3,264,752 |
| balancing_router | 9,720,392 | 12,150,490 | 9,720,392 |
| oracle | 9,903,405 | 12,379,257 | 9,903,405 |
| liquidity | 9,856,542 | 12,320,678 | 9,856,542 |
| pools | 5,823,043 | 7,278,804 | 5,823,043 |
| strategy | 5,270,790 | 6,588,488 | 5,270,790 |
| vault | 5,405,071 | 6,756,339 | 5,405,071 |
| rewards | 9,448,929 | 11,811,162 | 9,448,929 |
| fees | 2,179,891 | 2,724,864 | 2,179,891 |
| membership | 1,476,976 | 1,846,220 | 1,476,976 |
| migration | 9,210,835 | 11,513,544 | 9,210,835 |
| compounder | 535,653 | 669,567 | 535,653 |
| buyback | 1,831,805 | 2,289,757 | 1,831,805 |
| nft | 11,337,831 | 14,172,289 | 11,337,831 |
| nft_canonical | 3,496,881 | 4,371,102 | 3,496,881 |
| vault_canonical | 5,367,015 | 6,708,769 | 5,367,015 |
| fees_canonical | 2,279,634 | 2,849,543 | 2,279,634 |
| canonical | 5,347,142 | 6,683,928 | 5,347,142 |
| lp_converter | 6,289,890 | 7,862,363 | 6,289,890 |
| seadrop_mint | 4,586,560 | 5,733,200 | 4,586,560 |

See [all44 gas records](GAS_SUMMARY.json) for hashes, estimates, padded limits
and receipt gas. Children must not be added again to these parent costs.

## Findings corrected without repeating deployments

1. **Construction verification:** the accepted output lacks immutable-reference
   maps. Before running the node, verification was corrected to authenticate
   actual CREATE inputs/returned code and top-level constructor simulations,
   not compare deployed code to unpatched compiler templates.
2. **Output ownership:** pre-run review prevented cleanup from writing into an
   existing output folder and preserved lexically existing/dangling paths.
3. **Mutable request logging:** independent review found the original BA runner
   stored request dictionaries by reference. Later changes to gas/nonce/gasPrice
   altered archived preflight descriptions. The original run remains unchanged:
   sends, receipts, traces, getter responses and actual gas reconcile, but the
   raw log cannot attest the exact earlier full-cap/estimate/padded-request fields.
   Current recording freezes the exact serialized request and copies the response.
   A new regression failed on the original source and passes after the fix.
4. **Evidence admission:** the new offline checker initially accepted build pins
   from the evidence itself. It now requires the exact trusted build inventory/
   hashes before filesystem reads, rejecting forged hash/traversal entries. A
   separate new regression failed on the old checker and passes after correction.

Eight new focused methods pass at explicitly recorded source stages: six launcher
checks, one recording regression and one checker-admission regression. They are
not presented as one fresh final-source suite. Original failures, snapshots and
AST/source deltas are retained. The [initial independent capture failure note](INDEPENDENT_INITIAL_CAPTURE_FAILURE.json)
is a contemporaneous tool-output transcription, not a raw process log; its
limitations are stated. No unchanged tests or deployment workload were rerun.
The logger-only source change leaves all constructor/binding workload bodies
unchanged. [Current and execution source hashes](SOURCE_SHA256.json) keep that
distinction explicit; no original evidence is relabelled.

## Reproduce the evidence review without a node

The complete [evidence archive](evidence.zip) retains44 transaction records,
25 full CREATE traces, full compressed original RPC records, all instance/code
proofs, binding observations, process/genesis/cleanup and exact source/test stages.
[Archive identity](EVIDENCE.json) and [report artifact hashes](ARTIFACTS.json)
bind the published bytes. Filenames such as FINAL_SOURCE/CURRENT_SOURCE inside
the archive are historical checkpoints, as explained by its EVIDENCE_SCOPE;
the source inventory outside it identifies the current published tools.

From the reviewed checkout:

```powershell
python scripts/check-local-deployment-evidence.py --evidence reports/local-deployment-rehearsal-20261115/evidence.zip --output path/to/new-offline-result.json
```

The [published-ZIP reconciliation](PUBLIC_ZIP_RECONCILIATION.json) passes without
starting a node or repeating tests. It explicitly returns
`legacy_mutable_transaction_request_capture:true` and
`preflight_request_fields_verified_from_original_wire:false`; it does not repair
the original log or claim exact transport evidence. This is an offline data
integrity/composition check, not cryptographic proof of public-chain state or
independent production approval.

## Operator and release boundary

The [operator guide](../../docs/OPERATOR_MANUAL.md#isolated-local-construction-rehearsal)
and [owning procedure](../../docs/DEPLOYMENT_PREPARATION.md#isolated-local-construction-rehearsal)
explain exact CLI inputs, new-directory/PID ownership, stop/restart, unsealed
postconditions and evidence scope. Todo, feature reference, roadmap, inventory,
release record and repository memory distinguish this local milestone from
actual release construction/admission. All61 Solidity sources and the four
unrelated dirty files remain unchanged; the offline planner is byte-identical.

Actual authority/metadata inputs, real constructor/dependency/runtime bindings,
two-source markets/routes, funded VRF and OpenSea, target deployment/operation
fees, hosting/recovery and independent audit remain open under the
[sole Todo](../../TODO.md#task-deployment-initcode). No public deployment,
sealing, service rollout, chain reset or production signing was authorized.
