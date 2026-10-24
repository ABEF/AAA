# Native ETH accounting V2 - scoped verification

2026-10-24. Undeployed development candidate; production NOT APPROVED.
Publication is recorded separately. Existing Anvil 8902, NFTs, LP, balances,
journals, website source/build/server and paused monitoring are untouched.

## Implemented boundary

Native ETH is actual currency zero across admission, Oracle, Entry, Vault,
LiquidityManager, fee reserves, individual/equal-collective indices, claims,
buybacks, parked raw exit and funded return. WETH remains a separate asset used
only by an explicitly wrapped operation, such as an existing v3 converter.
Direct native LP fees do not require conversion. ZZZ conversion keeps its 1%
loss cap, gas separate, and still needs a cheaper independently qualified route.

Exact ingress values are checked once per funding boundary. Native operation
deltas exclude existing prefunds and reject forced ETH during typed manager
pulls and Vault collect/close callbacks. Fee and principal domains remain separate.
Readonly guards are extracted into the immutable Budget to preserve normal
contract-size limits; no state-changing delegatecall or new executor exists.

Canonical V2 uses `keccak256("ZZZ_CANONICAL_SAME_CHAIN_NATIVE_V2")`, explicit
native backing, all 33 reward currencies, and funding-before-zero-value-acknowledgment
for delivery and abort. Native receiver slot0 is not duplicated in slot2.
Old V1 schema import is rejected, not silently interpreted as native indices.

The read/preparation API and keeper have explicit version2 configurations and
runtime/version checks. Legacy profiles and predecessor identities stay separate.
No shared browser signer or public transaction capability was changed.

## Evidence scope

Focused EVM suites exercise actual production accounting/custody/Entry/manager
contracts with deliberately named fake market, price, token and VRF dependencies.
They do not qualify a Robinhood market, live randomness, real feeds, pricing,
target-chain gas, hosted service or actual browser extension.

| Changed boundary | Observed checks and exact scope | Evidence |
| --- | --- | --- |
| Native venue/admission | 9 new foundation cases pass, including exact ingress, settlement and forced-ETH exclusion. | [Final venue run](venue/native-foundation-final.log), [bindings and backend scope](venue/verification-final.json) |
| Vault, Entry, maintenance and exit | 61 passes: 10 new native flows, 35 existing Vault accounting, 13 existing security and 3 execution-budget cases. One existing fuzz fixture failed because its old lower bound allowed less than the existing $5 top-up minimum; only that repaired case was rerun, passing 1,000 fuzz runs. No production minimum was relaxed. | [Original run and source snapshot](vault/verification.json), [repaired-case run](vault/repaired-fixture.json) |
| Fees, rewards, membership and inbox | 15 distinct new native cases pass across scoped runs, plus 104 affected existing cases before the final companion-gas optimization. The new-case first runs are explicitly transcribed observations. Existing raw Forge JSON is compressed losslessly. The four directly affected canonical cases were rerun after the final prefund fix and pass; these reruns are not extra distinct cases. | [Accounting scope](accounting/accounting-scope.json), [existing run](accounting/affected-existing.json.gz), [final prefund rerun](accounting/prefund-grief-fix-rerun.json) |
| Custody and canonical helpers | 13 native custody cases passed against the frozen core/Budget candidate. After the source-companion prefund correction, only the changed abort case and a new successor-becomes-source case were rerun, both passing: 14 distinct cases overall, not 15. | [Earlier scope](custody/frozen-source-verification.json), [two final affected cases](custody/tests-prefund-abort.json), [final helper bindings](custody/prefund-abort-verification.json) |
| Whole-collection handoff | Earlier affected run: 37 passes and four failures. Three failures were stale native-index fixtures; the fourth exposed a real cold-capture gas regression. The repaired cases and two new real native handoffs subsequently pass. After the final source-prefund fix, four directly affected cases pass: ordinary maximum domain, prefunded maximum domain and both native handoffs. | [Original diagnostics](canonical/canonical-affected.log), [first repaired cases](canonical/canonical-final-targeted.log), [final four-case run](canonical/canonical-prefund-final.log) |
| Read/preparation backend | 102 affected existing Python cases pass. Eleven distinct new cases pass across scoped runs, including native zero-asset identity, exact child call values, explicit version/lineage boundaries and native LP/royalty earnings without duplicate income. A Windows SQLite fixture cleanup error was repaired and only the affected case rerun. | [Affected log](venue/backend-affected.log), [new-case scope and bindings](venue/verification-final.json) |
| Keeper | 51 cases pass: 12 new native profile/journal cases and 39 affected existing pool cases. No persisted user journal is rewritten. | [Keeper scope](custody/keeper-native-verification.json) |
| Compiler and size | All 102 Solidity source/test/script inputs typecheck. All 34 current production object gates pass normal limits; 78 compiler dependency bindings match current files, with the documented forge-std CRLF normalization. Incremental compilation reuses unchanged objects. | [Typecheck](build/typecheck.json), [successful build](build/production-build-final-approved.log), [size gates](size-gates.json), [compiler bindings](production-source-bindings.json) |

The accounting invariant in the 104-case run used 32 runs and 4,096 handler calls.
This is not the historical 65,536-call campaign. The repaired Vault fuzz case and
the native fee conservation fuzz case each used 1,000 runs. No full fresh global
regression, target-chain fork, static-analysis campaign or load test is claimed.

### Gas and deployability

The initial native maximum-domain capture measured 12,884,426 gas and failed the
unchanged 12M per-call guard. The final ordinary maximum-domain capture measures
**11,477,451 gas**; the companion-prefunded case measures **11,474,953 gas**.
That case covers 33 LP currencies, four buckets/inboxes and 17 royalty currencies,
funds the replacement, aborts, and verifies all 132 companion prefunds remain.
The final [adversarial-only extension](canonical/canonical-prefund-inboxes-final.log)
also prefunds all three protected balances in each of four source inboxes. Its
cold freeze is **11,713,754 gas**, leaving 286,246 under the same 12M budget;
eight-row import peaks at 4,836,260. All 132 companion and 12 inbox prefunds
survive full funding and abort. Only that extended case was rerun; production
source is identical to the preceding four-case run.
The final four-case run also measures maximum-domain commit at 3,707,482 gas,
one-domain settlement at 5,649,015 and eight-row import at 4,597,453. Entire test
function gas includes constructing fixtures and many bounded calls; it is not
the gas of one public transaction. These are local measurements, not Robinhood
block-limit or RPC/service qualification.

Vault runtime is **24,504 bytes**, leaving 72 bytes under EIP-170. Raw initcode is
48,015 bytes; including its three fixed constructor arguments gives 48,111 bytes
under EIP-3860. Fees is 24,133 bytes, Migration 24,047, VaultCanonical 17,499 and
FeesCanonical 13,914. Unchanged RoyaltyFactory has 69 bytes of runtime margin.
Future code changes require size review. Dynamic AccessController arrays and NFT
URI constructor arguments require the actual release inventory; the raw artifact
gate does not approve arbitrarily large deployment arguments.

Build output initially ended with a Foundry signature-cache filesystem permission
error after successful compilation/size output. The same offline build completed
with approved local cache access; both logs are retained. No compiler, optimizer,
code-size limit, gas guard or supported asset count was relaxed.

Earlier failed attempts and later targeted repairs retain their source scope.
The production-source binding manifest proves current compiled objects, not that
every earlier test was rerun after every later change. Historical test and fork
reports are not relabeled as native qualification.

[Final source snapshot](source-sha256.json) identifies this candidate's Solidity,
backend, keeper and focused test inputs. [Evidence hashes](evidence-sha256.json)
bind the published logs and reports; publication receipts are recorded separately.

## Required remaining work

- Explicit atomic ETH/WETH conversion boundary. `moveFunds` currently requires
  identical actual currencies; different-pair external custody is separate.
- Reviewed V1-to-V2 codec if ever needed; no such public deployment exists here.
- Typed v4 input/reward conversion and noncritical post-seal control extensions.
- Native V2 website profile and full deployment/inventory configuration review.
- Actual selected-pool fork, qualified input/conversion routes, independent feeds,
  supported VRF, metadata publication and target-chain/service rehearsals.
- Production authority addresses, independent audit, remediation and release approval.

The public website remains a simulation with null deployment; signing stays
Anvil-only. No public deployment, sealing, transaction or service action occurred.
