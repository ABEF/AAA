# Verification and source reuse

Baseline0330a98. Evidence partitions retain original source and response hashes;
no historical runtime, test result or pending review is relabeled.

| New work | Verification | Limit |
| --- | --- | --- |
| Network |56new attempts, actual canonical Approval0/log and missing-hash controls | Cheap gas fields are not full-work capacity; no full provider approval |
| Fee components |10L1-only payloads, one full harmless approval component call, two actual ordinary receipts | Not a complete undeployed PoPL fee quote |
| Software replay | Baseline actual trace/envelopes replayed through unchanged helpers; current checks compare exact retained bytes/control helper source | No trace/parser rerun after the fee source fix |
| Keeper source |14new focused methods pass; exact source/data bracket | Inert signer; original tests not executed |
| Installed Cast | One unsigned type2/chain4663/priority0 construction with fixed fields, clean environment, closed loopback URL | No signing, keys, service or public transaction |
| Runner | One explicit module-inventory line;965selected, zero executed | Inventory is not a pass count |

The only production-code change is `keeper/monitor.py`'s explicit future fee
profile; the generic `zzz_ops/ethereum_fees.py`, all61Solidity sources and
100normal compiler inputs remain byte-identical. Reuse prior contract/gas/
normal/static evidence for that exact scope only. Oracle24,573bytes/3bytes
headroom and Vault24,544/32 remain. No compiler, size or financial gate changed.

The actual public zero-tip transaction is unmodified in receipt tests. Only its
test keeper intent/journal is constructed; it is not a PoPL submission. A real
positive-tip receipt retains the baseline overstatement evidence. Schema1
pending recovery is separately checked under future profile2, without migration.
Malformed new settings, provider funding refusal, bad receipt price/type/tip,
original spending caps and signer-timeout/no-resend preserve their boundaries.

[Fee source/checks](fees/REVIEW.md), [network](network/REVIEW.md),
[software source/data integrity](software/README.md),
[completion receipt](COMPLETION.json). Offline evidence verifiers make no new
RPC request, execute no old suite and compile nothing. Publication and
preservation checks retain the four unrelated dirty files unchanged and unstaged.

No default, live configuration/service/site, public signer, existing Anvil,
journal or paused-heartbeat adoption occurs. Actual signing/provider/full-operation
fees, maximum state, fees/caps, real markets and independent approval remain open.
