# Residual cleanup verification

Current evidence is source-scoped. It is not a fresh full regression, real-market
qualification, published CI result, independent audit or deployment approval.

| Check | Result and scope |
| --- | --- |
| Normal production compile | 41 current source files and 36 normal runtime/initcode object gates pass. Compiler inputs are frozen before compilation; no size/optimizer/EVM waiver. |
| Whole-source typecheck | All 122 current production/test/script inputs compile with ABI/AST output and zero errors. This does not execute test assertions. |
| ABI comparison | 104 project-object ABIs unchanged. Only the Registry's five obsolete selectors/two events and its minimal interface's four obsolete declarations are removed; unused finality interface disappears. No new selector or authority. |
| Runtime comparison | Seven metadata-stripped runtime bodies are identical: NFT, Vault, VaultCanonical, MigrationBudget, Membership, Rewards and RoyaltyRewards. This is not an upgrade/storage compatibility claim. |
| Size | Registry runtime9,987 (-2,040), creation41,366. Vault runtime23,889 (687 margin). Access minimal role-array initcode49,123 (29 margin); actual arguments remain unqualified. |
| Keeper example | Three focused constructor/mock-RPC cases pass once, with exact config/source bindings. No RPC, chain, signer or running service is used. |
| API profile | Three existing current/historical profile-isolation cases pass on the final API source. The only API change is current LP-scope explanatory wording, not a schema or accounting change. |
| Callable reference | 31 concrete contracts/644 functions,31 constructors/14receive hooks; zero missing purpose/caller/value notes or top-level input notes.137outputs rely on function purpose instead of a dedicated output annotation. |

All **10 selected cleanup-affected Solidity cases pass** on the recorded final
source: Registry native-funds rejection, three pool-control cases, two reviewed
Entry cases, two actual canonical native funding/abort cases and two metadata/URI
cases. The AST harness preserves every selected assertion and helper body
byte-for-byte, whitespace-omitting unrelated methods. The complete selection,
omitted methods, source hashes and raw results are in [the manifest](solidity/selected-transformation.json)
and [summary](solidity/selected-summary.json). Only selected execution is claimed;
the unchanged compiler profile and normal production object gates are separate.

Retired tests are preserved byte-for-byte and never counted as current coverage.
Unchanged broad Solidity, provider, website and keeper-recovery suites are reused
only at their original source scope; they are not rerun or relabelled as fresh.

The first ABI-comparison utility expected only the concrete Registry ABI to change
and omitted its intentionally pruned minimal interface. That utility expectation
was corrected to include exactly those four interface declarations; no extra
production change was needed. Original compiler and test diagnostics remain in the
external evidence workspace.

Read Git and the separate publication receipt for commit/push status. Production
is NOT APPROVED. No public transaction/deployment/seal, website/server/service
change, local-chain reset or journal rewrite follows from these checks.
