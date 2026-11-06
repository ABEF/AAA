# Verification scope and retained evidence

Baseline e1a85a2; production NOT APPROVED. [Review](REVIEW.md).

## Actual local core

[Accounting record](accounting/FINAL_TEST_REVIEW.json):10 distinct selected EVM
successes,3new and7affected controls. New3 passed on first EVM attempt in216.719s;
controls7 ran once afterward in7.344s using the same exclusively copied cache.
No new3 rerun or broad unchanged suite. Initial runner shell-preparation failure
is retained separately; it did not run an EVM. ABI/type closure188 passes.

New cases cover prepared automatic OFF calldata followed by real price change,
activation and growth; exact current shares/funded nonzero80/10/5/5 and released
compound retention; a reachable raw-recovery/externally withdrawn-depth fixture
where legacy picks an inactive self quote and active solver selects a healthy
alternate; and no feasible active route restoring all principal/fees/review state.
Three prior read-to-execute races plus pending-width, forced inactive, outside
entry/growth and callback/floor controls protect shared behavior. Existing76
test method bodies and old callback modes remain unchanged; new mode4 withdraws
only the TEST provider's own liquidity through actual core operations.

Source/test/config/toolchain are frozen through both runs; production/dependency
pins match the84-source accepted normal closure. Actual core/periphery is local
with recorded mock Access/admission, correlated feeds, token/VRF/Permit2. The
test-only minL1/1M code allowance is not a production review or size waiver.
Normal Royalty creation family remains separate from Forge's existing family.

## Keeper and reference checks

[Services record](services/SERVICES_EVIDENCE.json):67 unique final methods,
21new/46explicit affected,0failures/errors/skips. Original-source probes reproduce
3bad acceptances before the fix. Two further late-policy expiry/day-budget
negatives fail against the earlier65stage and pass after final reorder. Preserve
all stages; never sum65+67 or count probes/subtests as additional final methods.
Initial setup suberrors required explicit compound thresholds, not a weakened
production guard. One old expected2-versus3policy-read assertion was corrected.

Current93 reference/operator/static-default methods pass at their recorded
source scope. Fresh callable reference has37contracts/839functions/37constructors/
12receivers,0gaps and888explicit operator rows. An initial generator check rejected
a raw-byte example digest; only canonical reference hashing was corrected.
No signature/input/output/authority/value or public signer change followed.

## Normal compile, static and unchanged data

[Contract record](contract/CONTRACT_VERIFICATION.json): exact pinned
Solidity0.8.26/Cancun/viaIR/runs1/yul=false,84closed sources;44normal compiler
objects and2actual carrier runtime/initcode gates pass. Manager runtime22411,
margin2165; initcode plus192static arguments46265,margin2887. Vault24469/margin107,
Budget24018/margin558 and Balancer24216/margin360 remain unchanged. No raised
production size limit; release-specific target deployment gas is unqualified.

Actual Slither0.11.6/crytic0.4.2 ran on the new normal output without recompiling.
Source freeze and JSONsuccess are proved; Windows findings exit4294967295 is
retained, not called exit0.497strict records:44individually reassessed
(20false-positive/24informational),453unique exact referenced-source reuses.
[Strict record](static-review.json), [coverage](static-coverage.json), actual
execution and full compressed detector data retain provenance. Default/CI
pointer and new full record change together; prior495record remains immutable.
Internal review is not independent approval or proof of exploit absence.

Manager ABI/storage match except compiler AST identifiers; only its runtime
template changes. Full normal25522-byte Royalty creation matches the prior exact
payload including metadata and passes frozen F2part/whole validation. Schema15
and all historical codecs/profiles remain explicit; no artifact is relabelled.

## Preservation and publication

The [preservation record](preservation.json), document/Todo/reference checks and
exact staged/committed Python closure separate local source from publication.
All original report bytes except the maintained map, four unrelated dirty files
and other drafts remain preserved. No running server/site/service, wallet key,
public signing, Anvil state, pending journal or heartbeat change is authorized
or implied. Real operating/provider/target-gas/independent qualification remains.
