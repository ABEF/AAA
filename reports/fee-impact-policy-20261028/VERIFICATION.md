# Fee-adjusted execution verification

Base commit`bf94b03158558296c0103a8ea06143f29c42d35f`; fresh undeployed candidate.
**Production NOT APPROVED.** [Review](REVIEW.md) owns behavior and limitations.
Current source/dependency/compiler pins are recorded in
[normal build evidence](production-size-gates.json), [source pins](source-pins.json)
and [external raw artifact hashes](artifact-manifest.json).

## Executed scope

| Evidence | Actual result and boundary |
| --- | --- |
| [Solidity initial selection](solidity-initial-methods.json) |55distinct methods:54pass,1failure because the new test expected `InvalidState` where Strategy correctly rejects invalid observed fees with `InvalidConfiguration`. Original test/raw output/pins are preserved. |
| [Corrected fee-rejection method](solidity-corrected-method.json) | Only the two expected-error selectors in that one new test changed. Its single method then passed; production source unchanged. Thus55distinct methods pass across the two scopes, not56tests or a fresh whole-suite run.22new fee-quality methods and33affected route/accounting methods are included once. |
| [Backend](backend-verification.json) |53distinct methods pass,14new/39existing, no errors/failures/skips or Python drift. Earlier51-method helper-owner receipt is preserved externally and is not additive. Synthetic inert RPC/trace tests disable network and subprocess signing. |
| [Normal production build](production-size-gates.json) | Closed76source/45project inventory, solc0.8.26/Cancun/viaIR/original optimizer profile;38normal runtime/initcode gates pass with exact source/dependency/build/compiler pins. No source drift, limit relaxation or public deployment. Manager48938creation+160static args=49098 leaves54initcode bytes. Exact actual release arguments/URI and target gas remain unqualified. |
| [Source consistency](source-checks.json) |45source files, no consistency errors. Delimiter/import/pragma checks do not constitute compilation, exploit testing or security audit. |

Actual installed-v4 local fixtures cover directional/asymmetric fee composition,
raw-unit ceil/dust/6decimal/zero/highfee boundaries, stricter existing gross floor,
source-bound rather than spot quotes, cap0/default/max/role/lifecycle controls,
changed-and-restored policy around pull/refund, exact atomic rollback/prefunds,
direct-swap weak/strong caller minima, no-swap plans, selected quote minimum and
the previously affected route/accounting behaviors. Real external market attack
profitability was not tested or established.

## Preserved failures and efficient reuse

1. [Initial helper-only build](attempt1-build.json) fails Manager initcode:
   creation49550+160arguments=49710 exceeds49152. Runtime24383fits. No gate was
   widened. Moving policy/public quote to Strategy resolves the creation size.
2. [Intermediate build](attempt2-build.json) reports Yul stack-too-deep after a
   separate local cap was introduced in route planning. Capturing that cap in the
   existing Prices struct removes the extra stack local; no monetary limit changed.
3. The initial Solidity expected-error mismatch above remains a failed run. Only
   that corrected method reran; the other54pass results reuse exact unchanged
   production/fixture dependencies and unchanged method bodies.

[Commands](commands.json) and exact raw input/output hashes retain these scopes.
No unrelated suite, old four dirty files or historical report was overwritten.
No website/service/journal/Anvil/signing/network funds changed. The user explicitly
keeps40%trigger/passive-second-position discussion outside implementation.

## Final consistency and remaining release work

Generated Todo and source-bound644function/32contract reference are checked with
the final source pins. [Final checks](final-checks.json) record link/anchor,
source preservation, scope and publication-file validation. Those checks are
documentation/source consistency, not economic or independent audit approval.

Qualified real feeds/routes/VRF/authorities/OpenSea, current website/API/keeper
acceptance, actual gas/depth/ordering, operating rehearsals and independent audit
with remediation remain open. This feature constrains accepted output; it does
not prove organic prices, execution optimality or absence of profitable attacks.
