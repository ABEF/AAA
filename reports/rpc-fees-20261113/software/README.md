# Existing software and new RPC evidence

Baseline `0330a98a0be91c979fcba291258eb6019e528b1f`. This partition reuses existing
production readers; it adds no qualifier CLI, signer, service configuration,
deployment, default or fee-policy approval. No old test suite or EVM case runs.

## What the existing tools already provide

`python -m keeper.probe --profile activation_api_v1` is the existing preparation
compatibility tool. Its exact runtime/genesis pins, canonical state reads,
unknown-block control, discarded `approve(0)` simulation and actual Approval-log
witness should be reused. A getter trace with no logs is insufficient. The tool
also checks bounded ordinary receipts and pre/post reference headers; it cannot
approve full fees, a PoPL deployment, provider honesty, uptime or complete history.
See the [existing procedure](../../../docs/RPC_PREPARATION_QUALIFICATION.md).

The probe bounds its witness to 500,000 gas, 256 frames and depth16. Actual Entry
preparation separately validates the exact Entry/Vault/Manager/PositionManager
flow, marginal deployed LP, captured price scope, share issuance and final
callbacks, with an8,192-frame/depth64 trace bound. Passing the small witness
does not execute the undeployed PoPL graph or qualify its20M workload.

The same distinction applies to the24M keeper profile: accepting a large gas
field on a cheap precompile does not show how much work a provider will execute.
Production request time, transport response size, worker, fee, ownership,
canonical-state and financial guards remain independent requirements.

## New actual observations replayed offline

[Baseline replay](BASELINE_TRACE_REPLAY.json) reconciles the new Pinax evidence through the
unchanged production `_approval_trace` and strict `Rpc._post` parser, using the
original recorded response bytes and exact request IDs. No socket, additional
RPC, signed transaction or persistent allowance exists in this replay.

The actual Approval witness uses33,237 gas and matches the independently retained
2,202-byte WETH runtime. Its numbered canonical header is checked before and
after the witness. Both20M/24M cheap call/estimate fields are accepted. Explicit
unknown-hash calls, estimates and traces reject. The trace's literal
`block 0x00…00 not found` wording remains **unclassified** by the production
error parser; call/estimate `header not found` is recognized as unavailable.
The replay preserves that difference and does not broaden the parser.

The [current integrity record](RESULTS.json) reuses that completed witness after
the separately scoped keeper fee work. It verifies the unchanged complete
probe/RPC/ABI sources, exact AST and source of the four imported monitor helpers,
and the original response hashes inside the final network index. It does not
execute the unchanged trace/parser again or relabel the baseline receipt.

This is a real tracing-capability improvement over the earlier providers. It is
not a full `activation_api_v1` CLI pass: an independently reviewed genesis and
the remaining complete profile checks have not been supplied. The [network
record](../network/REVIEW.md) owns actual request counts, provider outcomes,
transport failures, anchors and provenance.

An initial offline verifier metadata-path error stopped before any production
RPC-parser replay completed. The corrected report-local verifier then succeeded;
no network call or old test was repeated. The
[failure record](PRECHECK_FAILURE.json) remains explicit.

## Concrete fee incompatibility found

The [baseline receipt](BASELINE_RECEIPT.json) applies the unchanged generic
Ethereum fee helper to a newly observed ordinary Robinhood transaction with
a nonzero signed priority fee. The helper derives70,100,000 wei/gas; its canonical
receipt reports20,100,000. For56,722 gas, those imply3,976,212,200,000 versus
1,140,112,200,000 wei. These values and their original helper source hash remain
immutable baseline evidence; this result must not be presented as corrected
fee accounting or a production approval.

The [fee investigation](../fees/REVIEW.md) assesses Nitro's current collect-tips
policy, exact NodeInterface components, receipt semantics and any separately
implemented source correction. Component-only estimates are not complete
execution estimates. Do not add L1 posting costs twice or require equality
between differently padded estimator paths. A zero observed L1 component is
a dated observation, not a permanent waiver.

Current activation/claim policies require explicit complete-estimate approval
before their gas×price calculation can be used. Keeper recovery retains the
original pending fee review, signed caps, canonical inclusion state and spending
limits; an unknown/new fee model requires review rather than journal relabeling.
The baseline mismatch is a concrete reason those approvals remain false until
the appropriate source/configuration/consumer change is reviewed and verified.

The separate keeper correction adds explicit future-only
`submission_fee_profile:2`: Robinhood4663, reviewed inclusive fees and zero
separate L1 allowance. New submissions use type2 with priority fee zero, bind the
same fee envelope through simulation and signing, and save an exact schema2
model before submission. Recovery requires that saved type/zero-tip model and
canonical price. The generic Ethereum helper and old schema1 pending reviews
remain unchanged; no old positive-tip transaction is relabeled as zero-tip.
This does not configure a running keeper or approve complete fee semantics.

The new14-method keeper verification belongs to the fee partition. This
partition only adds its one module-inventory line to the existing runner:
[AST proof](KEEPER_INVENTORY.json), [full selection](KEEPER_FULL_INVENTORY.json).
It selects965 methods, including those14, and executes **zero**;965 is not a pass
count. No unchanged test body runs here.

## Remaining acceptance and operator handoff

[ACCEPTANCE.json](ACCEPTANCE.json) distinguishes existing software checks,
new small-operation observations and actual release requirements.
[HANDOFF.json](HANDOFF.json) lists the exact inputs for the existing CLI without
inventing a genesis pin, endpoint approval or fee budget. Its empty endpoint
list/null approvals deliberately make it incomplete.

Still review independent identity and full CLI results; actual PoPL deployment,
runtime and market configuration; complete fee semantics and operator ceilings;
representative operation size/state/response/time limits; archive and outage
recovery; and matching hosted consumers. Keep20% contribution and25% maintenance
padding, canonical-hash calls, exact traces and all financial safeguards.
No public signing, live configuration, service, website, existing Anvil/journal
or paused monitoring changes follow from these observations.

Reproduce only the offline integrity/witness reconciliation:

```text
python reports/rpc-fees-20261113/software/verify-current.py --network-index reports/rpc-fees-20261113/network/RPC.json --external-root RETAINED_NETWORK_RESPONSE_DIRECTORY --output NEW_OUTPUT.json
```

Without `--external-root`, current verification checks published identity/hash
equivalence and does not claim access to original response bytes. The original
`verify.py` is retained unchanged for the exact baseline helper replay; its
all-source pins intentionally reject a later changed keeper checkout. Its optional
parsed-only mode is semantic replay, without original byte-level validation.
Current verification invokes no trace helper, test suite or network call.
