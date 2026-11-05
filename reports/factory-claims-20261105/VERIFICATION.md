# Verification: factory storage and claim planning

Campaign5–6November2026. Production NOT APPROVED. Source baseline main `4f7436a`; no deployment, external
transaction, service/site change, signer extension or local-chain reset.

The machine-readable `evidence.json` and linked artifacts record final results.
External retained compiler/analyzer/test attempts are under
`C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/factory-claims-20261105-a71c`.
Failed/intermediate attempts are preserved, not counted as successful verification.

## Normal compiler and actual data runtimes

Pinned Solidity0.8.26/Cancun, unchanged viaIR optimizer runs1/yul=false. Closed
input84sources:53 production and31 dependencies. All44 compiler-object gates
pass. In addition, the actual constructor-returned children are checked:

| Child | Payload bytes | Actual runtime | Exact maximum-used initcode |
| --- | ---: | ---: | ---: |
| Part0 |24,573 |24,576 |25,095 |
| Part1 |949 |952 |1,479 |

The generic CodeData deployedBytecode placeholder is not an actual child runtime.
Access runtime/initcode and actual96-byte constructor arguments fit normal limits;
NFT's dynamic URI/arguments remain release-specific qualification. Reference
compiler artifacts use exact source bytes throughout.

Royalty creation remains25,522 bytes, byte-identical to the baseline:
`0x4a520b4af1c8ded6fe2539ec7f3ec4f6d9a1c7fbdd710a53ccffd3412bfce831`.
Part runtime hashes:
`0x4c299ec7864f0c7e6bece16d767ed0624ce7687e0198c94fcfa598615f8ae32e` and
`0x5b6332402959637249f7d1610282b50e17831b01cf546bf2b4ad83358e23edd0`.
Factory runtime grows1,182→1,893 bytes for authentication/reassembly; this is not
a claim that every bytecode object shrank. Normal runtime/initcode limits were
not relaxed. Isolated EVM test contracts use only their disclosed fixture limits.

## Focused behavior, gas and profile checks

Final campaign records below are source-scoped. Controlled constructor gas is
inner CREATE execution with identical inputs/compiler settings, excluding full
EOA intrinsic/calldata fees and actual Robinhood network charges. Separate warm/
cold labels must not be combined or described as actual deployment receipts.

Four exact-normal artifact contexts pass under the normal24,576-byte EVM code
limit, without a fixture override. They load pinned normal Access/NFT/Policy
creation artifacts, append identical typed arguments and verify the actual
Factory/part hashes. Access/NFT addresses reset identically for each context.

| Exact normal inner CREATE | Previous gas | New gas | Reduction |
| --- | ---: | ---: | ---: |
| Access controller construction |21,743,406 |9,424,695 |56.65% |
| NFT, same-transaction warm graph |13,957,742 |13,827,621 |0.93% |
| NFT, explicitly account/storage-cooled graph |15,555,742 |13,827,621 |11.11% |

Each context verifies the same instantiated royalty runtime:
`0xec2561a95ac3ea81b40666e17386ffe144c6e45e036f686154254aeecc979e26`.
These are constructor executions, not per-user mint/claim savings, complete EOA
receipts or Robinhood fee estimates. The four gas contexts are separate from
the13 source-behavior EVM cases, not four additional economic features.

Claim planning is verified against bounded injected RPC fixtures, including
adaptive gas/fee sizing, original currencies, zero/blocked/unresolved selections,
failed first currency with healthy later claims, changed ownership/fees, malformed
results, stale/reorg snapshots, work limits and strict HTTP/worker dispatch.
These do not qualify actual provider latency, maximum-state gas or a live wallet.

Final Python scopes are separate:31 planner/boundary methods(25 new plus6
existing),344 distinct affected profile methods(including17 factory cases) and
93 callable/operator/static-review methods. The profile campaign preserves its
two stale current-CLI assertion failures, corrected narrow follow-up and exact
overlap accounting; these numbers are not sums of repeated stages. The planner
retains its initial test-only provenance-key failure. No full suite is claimed.

The13 selected source-behavior EVM cases use the main Forge build's own artifact
family, not the normal deployment pins. Its royalty creation digest is
`0xee61b40298c3a075124538647c141c5d4a92a761fabc17b61960f883d42eb3ee`.
The initial controlled warm old/new gas cohort uses
`0xa0cddcb14b869a99faac0f269c54fdef0e9d65b2592d4e213dbf40c490307c18`.
Normal closed compilation pins the separate `0x4a520b...` family above. All
payloads are25,522 bytes, but exact hashes are NOT interchangeable. Full metadata/
source/settings comparisons retain their own evidence; no relabelling occurs.
All three creation bodies are byte-identical after removing only their terminal
53-byte CBOR metadata. The controlled build normalizes seven CRLF sources; its
raw compiler settings match. The main Forge family additionally includes four
unused auto-detected remappings in metadata. Their full hashes remain distinct;
schema14 stays pinned to the normal family and the actual normal-artifact tests.

## Static, callable and preservation evidence

Fresh actual Slither0.11.6/crytic-compile0.4.2 reads the final compiler output
without recompilation.489 strict records:20 individually reassessed current
contexts and469 unique exact referenced-source reuses from the previous record.
Internal review is not independent approval or proof of exploit absence. Analyzer
success/source stability and its nonzero findings-process exit are recorded.

Callable reference:37 concrete contract classes,820 functions,37 constructors,
12 receive hooks,869 explicit operator rows, zero input/output explanation gaps.
The data constructor has no callable runtime methods.93 focused reference,
operator and strict-review methods pass. Historical counts are not added.

Final preservation/publication records verify protected dirty files, original
reports, website/signer and unrelated drafts. Existing Anvil/services/journals
were not reset, relabelled, inspected as new deployments or rolled out.
