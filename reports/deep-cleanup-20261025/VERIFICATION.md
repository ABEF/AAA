# Deep cleanup verification - 2026-10-25

This is source-scoped internal evidence for the [adapted workflow](ADAPTED_PROMPT.md)
and [changes](REVIEW.md), against baseline `964e6b6` / implementation `ea2a70c`.
It is not a full regression, current Slither approval, real-provider or operating
qualification, formal proof, independent audit or authorization to deploy.

## Baseline and compatibility

[Baseline](BASELINE.json) records the preserved dirty tree, compiler/build pins,
installed versions and 44 matching project-source hashes. The earlier four
refactors were not repeated. Historical dependency bytes were not fully embedded
in that old compiler input; they cannot retrospectively be declared identical.

The new normal build explicitly supplies **75 source units: 44 project and 31
dependencies**, with hashes before/after compilation. It uses actual
0.8.26/Cancun/viaIR/optimizer runs1/Yul disabled and all seven existing Foundry
remappings. The older bespoke driver had five; the two added aliases are unused
by production imports. All 234 resolved production imports and 75 logical source
paths match. No compiler or dependency upgrade was performed.

The normal build passes **37 EIP-170/EIP-3860 object gates** in 59.5 seconds:
31 concrete callable targets and 6 internal-library compiler objects. No size
limit was increased or waived. [Size/input evidence](solidity/production-size-gates.json).
Exact final NFT URI constructor encoding remains unqualified separately.

[Saved-output comparison](compiler-comparison.md) checks 108 project objects.
Recursive storage slots/offsets/member types and names match. Public function
encodings, constructor arguments, tuple/output labels and mutability remain.
Explicit ABI differences are only:

- Access adds `GuardianChanged`; constructor initial keeper/guardian events are
  new observable behavior, not changed authority.
- Three concrete and one abstract ABI list lose an identical duplicate error.
- The internal-only library loses its sole locally declared error descriptor;
  inlined checks still revert the same Module error selector `0xc52a9bd3`.

The first strict comparison correctly flags the abstract/library metadata rows;
its exact failed report/script are preserved as `initial-*`. Only the saved-data
comparison is repeated after admitting these exact exceptions. No other sole
error removal or function change is normalized. All 108 checks then pass.

Only Access size changes: runtime 9,207→9,252 (+45), creation 42,081→42,256 (+175).
With 96 fixed constructor bytes, total 42,352 leaves 6,800 below 49,152. Vault remains
22,852 with 1,724 runtime margin; RoyaltyFactory's 69-byte margin remains tight.
RoyaltyRewards executable creation/runtime are unchanged after compiler metadata
removal; all 12 helper calls preserve expression/order. Vault/Migration/Handoff
executables also match after only known complete metadata regions are masked.
No execution-gas saving or maximal target-chain gas qualification is claimed.

## Typecheck and targeted EVM execution

The final ABI/AST pass binds **265 explicit inputs: 131 project/test/script and 134
dependency files**, with no implicit-source fallback, and passes in 11.06 seconds.
An initial 0.91-second typecheck failed because four new role-log tests omitted
the explicit `Vm` import. Its actual error/input and test preimage are retained.
Only that import was repaired and only the failed AST stage repeated. All 75
successful production inputs, build files and compiler binary remained exact;
the normal production compile was reused, not rerun or counted again.

**32 selected Solidity methods pass** in one isolated Forge run:

| Scope | Distinct methods |
| --- | ---: |
| Actual installed Core/PosM native mint/increase/harvest/close/swaps/rollback |20|
| Constructor and authorized/unauthorized guardian/keeper role logs |4|
| V3 endpoint/error/short-circuit validation |2|
| Real Vault activation during optional royalty-currency failure |1|
| Exact token/native royalty custody return/current-owner rights |2|
| Earned-only conversion and complete loss-limit rollback |2|
| Converted-native whole-collection handoff |1|

[Selection and limitations](solidity/SELECTED_VERIFICATION.md),
[case/source receipt](solidity/selected-verification.json) and the hash-pinned
runner preserve exact selected bodies/helpers. The run takes 352.453 seconds
including compilation, with no failures, skipped tests, retries, missing methods
or unexpected/inherited extras. All 265 AST inputs and 75 normal-build inputs
remain byte-identical through execution.

Native tests instantiate installed PoolManager/PositionManager/StateView.
FactualPermit is an explicit allowance/expiry seam because actual Permit2 pins
0.8.17; authority/admission/USD pricing are local seams. The ownership test uses
real PoPL ledgers with its existing mock venue/currencies/VRF. These are not live
Robinhood market/fork or complete dependency/provider qualification. The 24→20
native test mapping and old ownership expectation preimages are retained; tests
were aligned with approved behavior, not used to redefine economic rules.

## Python/evidence and upstream checks

**41 distinct affected Python methods pass**: 20 function-reference and 21 event-
schema methods. The new snapshot schema2 captures explicit source/dependency/
build inventories and exact artifact hashes. Unknown or missing entries,
dropped existing build pins, source-root escapes, malformed hashes, duplicate
JSON keys and truthy nonboolean size flags cannot silently qualify documentation.
These are integrity/drift guards, not authentication of a malicious compiler or
reviewer. Controlled path resolution is not a physical host-symlink rehearsal.

Two initial negative controls demonstrate ignored dependency/build drift. Four
additional independent-review controls expose dropped pins, string gate flags,
extra content hashes and an escaping source root. Their failing logs/preimages
are retained. A 16-method pre-review pass is not added to the final 20. The final
event suite preserves all 135 previous descriptors exactly and adds only the new
guardian topic: 136 total, including 33 unchanged historical descriptors.
[Reference results](reference-tests.json), [event results](event-tests.json).

[Current upstream/compiler applicability](UPSTREAM.md) and the final 265-input
graph cover 31 concrete roots, zero unresolved internal calls/cycles/named-error
`require` triggers, and 51 distinct inline-assembly scopes. Actual failed compiler
output is rejected by the graph as a negative control; an earlier empty attempt
is explicitly excluded. This does not prove compiler correctness or callback
safety. Frozen-release compiler/dependency and generated-code review remain open.

The normal source consistency, sole Todo, callable-reference and owned-document
link checks are recorded with publication. The full `scripts/verify.sh`, fresh
Slither, broad fuzz/invariants, target-chain maximal gas and operating campaigns
were not rerun and are not claimed passed. No green published workflow is inferred.

## Operating and publication boundary

Source remains undeployed. Existing local Anvil/NFT/LP/balances/journals and old
profiles stay unchanged. No public RPC/transaction, deployment/seal, website
source/build/server/service, signer or paused-monitor action. Public DEPLOYMENT
stays null and signing Anvil-only. The sole Todo retains external qualification,
authority/OpenSea/provider decisions and independent audit/remediation.

README, architecture/component/feature/roadmap, operator/callable guidance,
release record and memories are updated. Unrelated drafts remain separate;
native-claim documentation is corrected with exact owned substitutions only.
Local saves, source publication and deployment are distinct. Inspect the
separate publication receipt. Production NOT APPROVED.
