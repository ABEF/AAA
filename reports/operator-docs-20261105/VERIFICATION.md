# Documentation verification

Baseline main28f7573. Source-bound checks only; **not a new contract security
audit, public CI result or production approval**. Exact identities and preserved
inputs are in [evidence.json](evidence.json).

| Check | Result and scope |
| --- | --- |
| Function reference | Current source-bound37contracts/820functions/37constructors/13receivers; no ABI/input/output/notes drift. |
| Operator tables |870callable examples, every overload, exact tuple/array shape, separate payable value, one-to-five-word explanations, reviewed caller classes and source-reference hash. Uppercase replacements remain unresolved. |
| Focused Python |49selected methods pass, no failures/errors/skips and no Python source drift. Covers18new operator-reference methods and31existing function-reference methods. The earlier47-method stage overlaps; counts are not added. |
| Negative cases | Missing/extra/stale examples; incorrect public/keeper/holder/bootstrap classifications; omitted payable value; opaque/truncated tuple; malformed bytes/addresses; floats, booleans-as-integers and integer overflow; fixed-array length and unknown ABI types; stale generated output. |
| Example semantics | Distinct independent source placeholders with300bps agreement; separate NFT/bucket/physical LP IDs; governance-only terminal batches and owner fallback; exact seven-field Entry tuple/policy; uint256 JSON precision and genuine boolean literals. These are documentation assertions, not transaction simulations. |
| Navigation and sole Todo | Generated-reference and Todo consistency checks; changed/new Markdown and incoming local links checked from both repositories. Remote URLs are outside the local link-check scope. |
| Contract evidence reuse | All52production and31dependency hashes match the existing normal compiler evidence. No Solidity behavior changes; existing43normal size gates/static/EVM reports retain their original revision and limits. No unchanged contract suite rerun. |
| Preservation | All earlier report bytes except maintained reports/README navigation remain exact. Four protected dirty files remain byte-identical. Originals of109maintained inputs were archived before edits; unrelated drafts are excluded. |

The example catalogue is explicitly reviewed data, not automatically inferred
authority or a substitute for a current snapshot. Function/notes/ABI changes
invalidate its full reference commitment until reviewed. The checker has no RPC,
simulation, signing, deployment or service-control path. It cannot certify current
prices, approvals, route depth, authority or operation feasibility.

Raw selection/results/logs and original-document archive remain in the external
`operator-docs-20261105` directory referenced by evidence.json. No keys, credentials,
wallet journal, website overlay or running service was used or changed.
