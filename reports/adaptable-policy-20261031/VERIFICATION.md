# Source-scoped verification

Reviewed31October2026. [Implementation and limits](REVIEW.md). External raw inputs,
compiler output, logs, intermediate failures and receipts are retained at:

`C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/adaptable-policy-20261031`

## Normal build and callable reference

Final normal build `normal-final-0a0cac9f06`:52 production sources plus31 dependency
sources,43 EIP170/EIP3860 object gates,0 compiler errors, no source/build/compiler
drift. Solc0.8.26/Cancun/viaIR/optimizer1/Yulfalse unchanged. Real dynamic
constructor arguments and target-network gas still need deployment qualification.

| Object | Runtime bytes | Runtime margin | Creation bytes before arguments |
| --- | ---: | ---: | ---: |
| Vault |23941|635|25339|
| Budget |24339|237|25177|
| Migration |24556|20|34404|
| NFT |22192|2384|45823|
| ProtocolPolicy |14746|9830|17755|

Migration remains especially tight. Intermediate failed/drifting builds are
preserved, not labelled successes. Fixed typed read-only extraction and lean
getters restored normal limits without weakening financial/custody guards.

Source-bound reference:37 contracts,826 function rows,37 constructors,14 receivers,
zero purpose/caller/input/output gaps. Generator check passes;16 affected offline
operator-helper methods pass. Documentation coverage is not execution coverage.

## Executed evidence and precise scopes

| Campaign | Actual evidence |
| --- | --- |
| Policy / portfolio |42 distinct successful EVM methods across stages. Final12/12 match the final43-gate production source exactly, drift0; actual local-v4 journeys cover80/20main allocation,3-spacing residual gap, entrant-idle recovery preserving incumbents, and callback maintenance-policy mutation rollback. Earlier30 passing Portfolio bodies are unchanged staged reuse. |
| NFT / randomness / canonical |53 distinct methods reach success across recorded stages, including finite1000 artwork mapping, VRF drain/rotation/replay/runtime/request-callback cases, cosmetic rights and canonical threshold compatibility. Final3 affected canonical methods pass with unchanged source closure. Prior51 successes retain their scope; strengthened repeated cases are counted once. |
| Mint / native flow |Root scoped campaign records6 new mint/minima/callback cases and5 affected native-flow cases. Original9pass/2fixture failures and the exact two-case correction retry remain separately recorded. Both retries pass:11distinct methods reach success across stages; see the machine receipt. No broad rerun is inferred. |
| Buyback / payout / source gas |7 NEW methods pass, all production sources matching final0a. Six verify reviewed maximum/operating ordering/authority/lifecycle/5%reserve conservation and100k→1m isolated payout retries/current ownership/no double pay; one gas-sensitive synthetic source proves budget recovery does not waive3% agreement. |
| Backend / API / inventory |160 distinct pinned affected methods pass;10 final correction reruns overlap, not170. Four later conversion-profile/recovery methods pass, including2new cases. A separate98-method historical inventory/report batch is supplemental, without pre/post source pins; do not add it as final new coverage. |
| Dollar generator |9 affected Python methods pass. Actual fresh6 CLI refusal verifies no output/copy/compiler/source mutation and explains isolated policy configuration. No deployment occurs. |

Tests use explicit mocks/substitutes where recorded. Local real-v4 core is not
real market depth, independent feeds, VRF proof/funding, target gas or operating
qualification. Empty-selector attempts executed0 tests even when exit status was0;
they remain negative evidence. Two getter-after-expectRevert fixture issues and
the misplaced canonical check were corrected without relaxing production guards.

The initial stale root compilation was stopped before test execution; it counts
as0 tests. Source6 fixture review getters were moved before prank/revert setup;
this preserves caller identity rather than weakening expectations. Native emergency
fixtures must include the current physical-portfolio custody fingerprint.

## Preservation and limits

The baseline archives365 original files and hashes49 prior report artifacts plus
four unrelated dirty tracked files. Original report/source/failure scopes remain.
No deployment, public signing, service/site/Anvil reset or journal migration.
Main/head publication state must be checked separately; this work is local.

No current full-regression/CI, fresh static-analysis assurance, independent audit,
real provider/marketplace/host qualification or claim of exploit impossibility.
Preserve strict failures and unavailable values; never invent live observations
or silently widen financial/gas policy to obtain a pass.

## Compact evidence

- [Normal source/build gates](production-size-gates.json).
- [Policy and actual-v4 cases](policy-verification.json), [NFT stages](nft-verification.json),
  [mint/native stages](mint-native-verification.json), [payout/buyback/source gas](payout-buyback-source-gas.json).
- [Pinned backend methods](backend-verification.json), [final overlapping corrections](backend-corrections.json),
  [conversion-profile recovery](conversion-profile-verification.json), [callable/helper checks](callable-verification.json).
- [Actual fresh6 dollar CLI refusal](dollar-cli-verification.json), [source preservation](source-preservation.json).

The artifact manifest hashes these compact files. Raw compiler/test logs and
all intermediate attempts remain external at the root above; no old evidence is
rewritten. Nine dollar unit methods were recorded by the scoped tool execution;
the saved CLI receipt is separate evidence, not nine additional tests.
