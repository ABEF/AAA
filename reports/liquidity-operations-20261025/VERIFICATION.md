# Liquidity operations: source-scoped verification

Baseline main `d06fcde9f641799ffdffa0d4a304c663ff0b7545`.
Read [plan](PLAN.md), [internal review](REVIEW.md),
[idle/ownership procedure](../../docs/IDLE_AND_DUST.md) and
[range/keeper procedure](../../docs/RANGE_POLICY_UPDATES.md).
Production **NOT APPROVED**; publication is recorded separately.

## Final-source behavior checked

| Scope | Evidence and result | Boundary |
| --- | --- | --- |
| Installed Uniswap v4 composition | 11 actual-v4 local contract cases pass: default2% versus explicit1%, actual shallow correction, infeasible-depth and second-swap rollback, idle-only growth/failure/cooldown, inverse25% range activation/growth, fee/royalty/share/transfer continuity and prefund exclusion. | Actual installed pool math, swaps and LP settlement with local substituted governance/admission, tokens, feeds, VRF and Permit2. No real provider/pool-depth qualification. |
| Range rules and rounding | [18 cases pass](keeper-range/range-policy-final-summary.json): nine new and nine affected existing; two fuzz properties each1,000runs. | Actual Registry/Strategy/Oracle code; physical observations/feed/authority substitutes are described in the [specialist record](keeper-range/VERIFICATION.md). |
| Keeper shared submission/recovery | [277 passes, one Unix-only skip](keeper-range/keeper-final.json), including idle/adaptive transcripts, typed limits, bridge rejection and preserved pending evidence. | Offline RPC/contract transcripts plus actual pinned cast CLI parser. No signing, service upgrade or Linux permission rehearsal. |
| Explicit API/inventory/events | [13 passes](backend/receipt.json): inverse eligibility, strict profile/ABI/policy intent, observer composition, migration-capability output and three new Strategy events. All128 prior event descriptors stay unchanged; catalog has131. | Pinned ABI/RPC fixtures, no real provider/wallet/release qualification. Historical profile0 keeps old semantics and performs no new getter reads. |
| Combined normal object gates | All37 source-object gates pass on final42-production-source snapshot. | Normal solc0.8.26/Cancun, via-IR and existing optimizer profile. Runtime/initcode limits unchanged. |

[Affected default/cap regressions](solidity/maintenance-defaults-repaired-summary.json)
pass29/29:13custody-budget adversarial,7rebalance-budget (one1,000-run property),
4governed/default/callback-cap,3explicit historical1% atomic boundaries and2dual-
price uncertainty cases. The stale fixture first failed before intended paths:
missing pricing-V2 validatePrice and a one-shot synthetic plan incompatible with
actual-state replanning. Minimal test-only seams now expose checked price/state;
old1% negative cases explicitly select100bps rather than weakening assertions.
The old constructor-shape compile diagnostic is retained separately.

Four final cold12M gates also pass: activation10,946,281; fully indexed
activation11,509,874; top-up8,314,880; indexed top-up9,225,184. The largest leaves
490,126gas under the unchanged12M gate. Their mock no-swap Strategy/venue is
explicitly different from actual-v4 execution; this is not combined live maximal
qualification. [Six additional own Entry callback cases](solidity/entry-callbacks-final-summary.json)
also pass under the explicitly retained1% historical fixture; inherited repeats
are excluded. Final distinct Solidity scope is68cases:11composition+29regression
+6callbacks+4cold+18range. Earlier eight passes retain their earlier source
snapshot and do not inflate this total. [Final bindings](solidity/final-solidity-bindings.json)
match59scoped production/test files.

## Actual placement measurement

The explicit stricter1% shallow fixture executes two swaps and measures:

| Item | Original one-pass observation | New bounded correction |
| --- | ---: | ---: |
| Original input | $100 | $100 |
| Actually deployed LP | $98.849621202259071431 | $99.378363383283897427 |
| Attributed idle | $0.533536672418156838 | $0.002217489881065215 |

The original observation belongs to the earlier audit's exact source. The new
result retains an explicit100bps policy, so the improvement is not manufactured
by raising the default to200bps. Infeasible thinner depth still reverts. The
second-swap injected failure restores the first swap, principal, ownership,
eligibility and reward state; failed compounding separately verifies cooldown/
context rollback. These split cases are not a fabricated two-pass compound fixture.

The separately observed **6,126,388 harness execution gas** excludes setup, mint,
intrinsic/calldata and maximum-capacity cold effects. It is not a production
gas-limit recommendation or network-cost estimate. Do not combine it with the
substituted maximum-state gate to claim proven actual-market worst-case gas.

## Normal size limits

| Object | Runtime bytes | Creation plus constructor arguments |
| --- | ---: | ---: |
| Vault | 24,519 | 47,276 +96 |
| Budget | 20,687 | 21,720 +32 |
| Registry | 12,027 | 49,089 +32 =49,121 |
| Strategy | 20,960 | 21,556 +32 |

Vault has57runtime bytes and Registry31initcode bytes of normal margin. Use the
final combined receipt for constructor widths/settings; no size gate is relaxed.
Oversized candidates and test-harness/recorder diagnostics are retained, with
their exact source scope rather than presented as passing final tests.

## Rehearsal generator metadata and source-anchor repair

A related generator check found hardcoded100bps metadata and obsolete Budget
floor anchors after production validation moved to VaultCanonical. The tool now
patches only actual floor owners Entry/Canonical, adds their31337constructor
checks and copies Budget unchanged; its manifest derives actual200/1000bps
literals before output. Invalid/missing/duplicate/unsupported declarations fail
closed. The inherited historical test fixture still explicitly configures100bps.
Its constructor guard target and $5 growth case are corrected.

[Seven focused Python checks and actual generation](generator/receipt.json) pass;
[50generated Solidity inputs typecheck](generator/typecheck.json). This is **not**
a fresh runtime $1 rehearsal, signing or deployment. Existing generated builds,
Anvil and journals are untouched. The manifest's constructor default is not an
immutable operating setting. [Generated metadata](generator/generated-manifest.json).

## Review and remaining work

[Source-bound keeper peer review](backend/keeper-read-review.json) complements
Vault/Budget and Strategy/Registry inspection. Latest-read races can safely defer
or revert work; selection and physical rebalance are separate transactions;
thresholds/gas budgets do not establish economic optimality. Optional settings
may need deliberate restoration/disabling while recovering a saved transaction,
never journal deletion or blind resubmission.

Real input/conversion routes, independent two-source policies, authorities, VRF,
OpenSea, native website/services, Linux/target-chain rehearsals, maximum actual
venue gas and independent audit remain open. Signed review-time contribution-cap
binding is still absent from current Entry.Request and required before public
activation/growth signing. Current source-chain custody does not implement remote
NFT/reward relocation; integrated bridging is deferred optional scope.

No fresh full regression, current fork, unchanged-source suite rerun, production
service qualification or independent audit is claimed. Existing8902/Anvil/NFT/LP/
balances/journals/dist overlay, website source/build/server and paused monitoring
are preserved. Signer remains Anvil-only and public DEPLOYMENT remains null.

## Exact publication scope

[Final scope](FINAL_SCOPE.json) reconciles112distinct working-snapshot inputs
across the receipts and111exact evidence inputs selected for publication. The
keeper recorder's broad inventory also hashed the pre-existing unrelated
`zzz_ops/activation_route.py` research-reader draft. That reader is neither
imported nor tested by this campaign; its published baseline is deliberately
unchanged. Both hashes and this exclusion are explicit. Do not interpret that
extra diagnostic hash as functional qualification or silently publish the draft
to make inventories match. All42production-source and all selected functional
inputs match the actual index/commit; older unrelated drafts remain local.
