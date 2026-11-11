# Verification scope

Baseline `db509fb`; no deployment or production approval.

- **Reused traces:** four immutable actual-owner Entry RPC fixtures authenticate
  all 61 original Solidity sources. Offline attribution distinguishes inclusive
  cost, signed residuals, estimates and the earlier prototype. No repeated RPC
  simulation or old-runtime relabeling. [Baseline](verification/ARTIFACT_REUSE.json),
  [metrics](trace/FINAL_METRICS.json).
- **Fresh build:** one final accepted closed normal build, 100 sources / 61
  project files, unchanged 0.8.26/Cancun/via-IR/optimizer1/Yul-disabled settings.
  All 48 compiler-object gates pass. The two unchanged actual returned-data
  carrier checks retain their original creation evidence; no extra CREATE ran.
  All current raw source files exactly equal compiler-input
  contents; metadata is not assumed invariant under EOL conversion. Only Oracle
  objects change; all 191 project ABI entities/semantic layouts match.
  [Build manifest](build/ARTIFACTS.json), [source pins](build/source-manifest.json).
  Failed alternatives are retained separately, not successful release builds.
- **Fresh execution:** 23 successful method statuses in one frozen run, with
  exact before/after source brackets. 200 supplied / 197 compiled test sources.
  Eighteen existing methods exercise changed code; five new methods measure
  complete maintenance and adverse source behavior. All 30 prior test bodies and
  original Entry setup remain unchanged. [Scope](verification/TEST_SCOPE.json),
  [receipt](verification/EXECUTION.json), [gas](verification/GAS.json).
  The runner's postprocessing error and unpersisted Forge exit status remain
  explicit; successful raw method output was recovered without rerunning tests.
- **Public network:** 31 bounded read attempts: 23 valid responses, three explicit
  RPC errors, four HTTP denials and one local network failure. Two fresh anchors
  rechecked; selected-core code pin corroborated. Numerical execution parameters
  and fee observations are dated. No key, account, public transaction or provider
  configuration. [Network scope](network/REVIEW.md), [integrity](network/ARTIFACTS.json).
- **Fresh static analysis:** actual offline Slither reuses the accepted normal
  compiler output. All 567 records are covered: 13 current Oracle contexts
  individually reassessed, 554 unique exact referenced-source reuses. The new
  full record and actual default coverage check pass. Checker logic is unchanged;
  its 44 unchanged regressions were not repeated. Analyzer `success:true` and
  detector-present Windows exit4294967295 are retained separately.
  [Scope](static/README.md), [current review](static-review.json).

Final documentation/preservation checks are recorded in the [completion receipt](COMPLETION.json).
Static analysis is internal coverage, not an
independent security audit. No unchanged full test suite is claimed.

Synthetic market depth, controlled publications/VRF/authority/registry/Permit2,
one-NFT maintenance state and the $1,000 Entry fixture are explicit limitations.
Foundry call gas is neither a full target-chain estimate nor a public receipt.
The unchanged 12M default still rejects Entries; measured/padded diagnostics
do not authorize larger limits. Actual operating and release gates remain open.
