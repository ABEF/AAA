# Test maintenance and evidence reuse

The upgrade changes accounting/ABI semantics. Current fixtures must use native
ETH/fixed ZZZ, post-write typed hooks, whole-unit LP books and V9. Retain earlier
profiles as explicit history; do not silently reinterpret an old deployment or
change financial guards to make a fixture pass.

| Work | Disposition |
| --- | --- |
| Exact host |16distinct methods, including1,000ordinals/37wallets/900active/four buckets, tiny units, current-owner claims/conversion, deficits and cold32/8router calls. Two initial setup/rounding expectations corrected; per-function reuse proofs preserve earlier unchanged successes. |
| Real Vault producer | One executed producer,77actual logs and four26-field snapshots, independently consumed by four backend methods. Synthetic authority/venue/VRF/feeds and synthetic consumer timestamps remain explicit. |
| Native Vault controls |35distinct methods:33unchanged successful methods and two corrected tests only rerun. Exact unsealed NotReady followed by positive sealed mint avoids a vacuous setup failure; rejecting an old selector without mint leaves1ETH, not0.95. |
| Actual-v4 local accounting | Two selected methods verify entrant swap fees belong to incumbents before new shares, both-leg entry checkpoints and complete second-leg failure rollback. Local core is real; target providers/dependencies/economics are not qualified. |
| Canonical |34distinct final-stage methods with actual raw pending/phase/direct import, future growth/credits/claims, funding, abort, cutoffs and malformed-record rejection. Repeated/empty/failed attempts remain excluded. |
| Native fixture ports | Dependent sources now typecheck the fixed native pair. Oracle normalization and small-unit token fixtures are test-only. The45-class broad runtime attempt ran out of memory before results; unexecuted ported cases are not reported as passes. |
| Removed architecture | Two old full-Vault WETH/ZZZ fork methods and three third-LP-currency cases are explicitly retired with exact64f9source pointers/original bodies. Typed primitive fork tests and historical original-currency royalty coverage remain. Phantom compound-release mocks are not accepted as evidence of a genuine current fee path. |
| Final typing |315actual src/test/script/dependency sources pass ABI type closure, raw before/after hashes unchanged. This establishes signatures/types only. |

See [accounting index](accounting/INDEX.json), its exact original/current source
snapshots, retirement records and host/native/canonical imported-fixture reuse
proofs. Native95 and canonical105 closures were frozen at execution. Later only
two unselected test bodies changed in VaultAccounting; imported declarations,
helpers and all other94/104imports remain raw-exact. Preserve that distinction
instead of needlessly rerunning unrelated successful methods or pretending raw
file identity.

Compiler memory failure and initial failed/empty/mismatched fixture attempts are
retained. Normal production build/static gates are separate from enlarged test
harness envelopes. Neither a32-entry count nor an8-row page proves target gas.
No compiler/production/service limit was widened; old services, websites, chain
state, journals and signer boundaries remain unchanged.
