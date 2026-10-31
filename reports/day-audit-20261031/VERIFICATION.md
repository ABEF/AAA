# Scoped verification and source identity

Reviewed 2026-10-31, Europe/Paris. See [findings and boundaries](REVIEW.md).
Compact receipts are listed in [the artifact manifest](artifact-manifest.json).
Raw compiler/analyzer outputs, logs, archived originals and negative controls are
retained outside Git under:

`C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/consolidation-audit-20261031`

## Executed checks

| Evidence | Actual result and limit |
| --- | --- |
| [Backend receipts](backend-verification.json) |156 distinct affected Python methods pass:11 new regression methods,102 portfolio/keeper/summary methods and43 activation/routing methods. Archived original code reproduces3 causal failures: owner/claim projection outage twice and missing executor verification once. These are local fixtures, not provider or service acceptance. |
| [EVM receipts](evm-verification.json) |19 distinct affected methods pass across2 stages. First stage:18 pass,1 new fixture fails because5ETH growth is below that fixture's100USD admitted pool minimum. Correct only the test contribution to100, then rerun that exact method successfully. No production guard or minimum is relaxed. Twelve typed active-tick cases and seven real-core cases cover both ordinary modes and explicit exceptions; this is not a fresh full suite. |
| [Final normal gates](production-size-gates.json) |81 closed source inputs,42 EIP170/EIP3860 production object gates, zero compiler errors. Unchanged solc0.8.26/Cancun/viaIR optimizer1, Yul disabled. Source/build/compiler identities are captured before/after. Real constructor bindings, target gas and future edits are separate. |
| [Cleanup comparison](cleanup-bytecode-comparison.json) |After the EVM stages, remove only the unused private Balancer wrapper and recompile. All42 ABIs and creation/runtime instructions match after replacing actual per-object CBOR metadata, including embedded child metadata. This justifies avoiding redundant EVM reruns for that removal; it does not make raw bytecode/codehashes identical. |
| Callable reference |Final compiler source closure generates36 concrete contracts,778 functions,36 constructors and14 receivers; zero purpose/input/output explanation gaps. Includes the executor-only ordinary-replacement getter. Generator check passes. Documentation coverage is not execution coverage. |
| Documentation |66 changed/new documents and1874 relevant links, including125 inbound links, pass with no failures. Todo generation and778-callable reference checks pass. The consolidated manual has one5-line historical-link pointer. |
| Final source/preservation |Final source pins match50 production files,31 dependencies,4 build inputs and the3 changed backend files. All23 prior portfolio/management report files and four unrelated dirty tracked files remain byte-identical; task IDs/statuses/order and Git HEAD/main are unchanged. See the compact preservation receipt in the manifest. |

Final normal build: `normal-final-8511732986`.
Compiler input SHA256: `13e9b1586356317d80d520c8af979d3214650793104dd21eaf6ca2d9eed1192c`.
Compiler output SHA256: `5e94e8046b7219dbef7cf60681b64720d3f99a8f0249fabf80851573130ab145`.

| Object | Runtime bytes | Runtime margin | Creation bytes, without constructor arguments |
| --- | ---: | ---: | ---: |
| Vault |23671|905|25039|
| Budget |24290|286|25135|
| Manager |21711|2865|45352|
| PositionExecutor |20312|4264|21379|
| Balancer |23226|1350|32558|

Constructor arguments still count toward the real initcode limit. The Manager's
192 static argument bytes fit this build; exact release deployment still needs
its own reviewed inventory. No old37/59-byte headroom claim is carried forward.

## Fresh static analysis and manual disposition

[Analyzer receipt](static-analysis-receipt.json) and [full triage](static-triage.json)
bind the final source/compiler output. Slither0.11.6, crytic-compile0.4.2 and
Python3.12.14 run102 detectors over174 parsed contracts. JSON reports success;
Windows exit4294967295 represents Slither's finding exit−1, not a clean pass or
an analyzer crash. No new install, compiler-setting change or service action.

463 tool findings:74High,90Medium,207Low,71Informational,21Optimization. All have
source-context dispositions:164 High/Medium plus one Low in the first contextual
review, then142 loop,66 callback/time/call and90 maintainability findings.
Body/file hashes and finding IDs match; no unread items are silently suppressed.
Original partial triages remain unchanged. No new material exploit was established
by the detector review; this is not an independent assurance statement.

The environment matched48 locked package versions and executable runtime file
hashes. Five shared documentation RECORD paths were overwritten by another locked
package; the mismatch and classification are preserved. This is not pristine
wheel attestation. Raw91.9MB analyzer output stays external with SHA256 in the
manifest; the repository contains compact source-bound dispositions.

## What was not verified

No public transaction, deployment, sealing, source publication, operating-service
change, website rollout, old-Anvil/journal migration or signing extension.
No full current regression, successful published CI, independent audit, real
provider/VRF/OpenSea acceptance, target-chain gas/strategy profitability or
uninterrupted operating evidence. Prior reports keep their original source
stages, failures, skips and limits; this report does not relabel them current.
