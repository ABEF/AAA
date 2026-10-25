# Selected verification scope

The runner reuses the hash-pinned AST-selection driver and the separately recorded
normal37-object size gates. It preserves exact selected functions, constructors,
modifiers and helpers, omitting only unselected `test*` function/documentation
spans. Compiler settings and dependencies are unchanged. No existing Anvil,
wallet, journal, service or public RPC is touched.

The fixed selection has25 methods: four new focused behaviors and21 existing
substantive integration/rollback behaviors. It covers private native/ERC20
TAKE_PAIR settlement, recipient callback order, exact credit/prefund separation,
short-circuit V3 identity validation, both separately bound converter instances,
actual installed-v4 native conversion, contribution loss/ownership rollback,
Vault share/fee checkpoints and canonical converted-native backing.

The new native callback cases use explicitly mutable MockAccess and deterministic
core/Positions fixtures to observe call ordering. They do not assert that
production module bindings can change or qualify live venue behavior. The V3
validator cases poison later getters to detect eager reads after an identity
mismatch. Existing actual-core conversion cases retain their own local installed
Uniswap scope, not Robinhood provider or market qualification.

The code being reviewed does not change LP/royalty allocation, holder ownership,
asset custody, governance powers, source admission or execution-loss policy.
Normal production source/object/ABI/storage comparisons are separate evidence.

Results are recorded after execution; selection itself is no pass claim. A failed
fixture or runner invocation must retain its exact reason and source boundary.
Only affected failures may be repaired/re-executed, without adding repeated passes
to the distinct behavior count. This is not a full fresh regression or independent
audit, and does not approve production deployment.

## Recorded outcome

The initial25 selected behaviors all passed (447.922s). Foundry also executed
two inherited AtomicActivation methods in EntryReviewPolicyTest. The pinned
runner therefore correctly returned an incomplete-selection failure although
Forge returned0. Raw evidence is preserved. The strict reconciliation proves
those exact extra cases from compiler-AST defining declarations and inheritance;
there are no missing cases, other extras, fixture overrides or failed outcomes.
They are repeated bodies, not two additional distinct behaviors.

A preexisting unselected NativeVaultFlows assertion still expected accounting2.
After the25-case run, only that literal changed to3. Its exact preimage/byte
range is archived in `fixture-repairs/native-version-manifest.json`. The change
lies inside a previously omitted test; all15 retained functions/helpers in that
file, all other prior inputs and all44 production source hashes remain unchanged.
Fresh final131-input ABI/AST verification passed with no errors (13.39s). Only
the corrected native activation/growth/value case was then executed and passed
(126.516s), using the same source-matched37 normal object gates.

`combined-selected-summary.json` records26 distinct selected behaviors across
28 invocations:25 original bodies plus1 final corrected case, with2 inherited
repeats counted once. The25 original passes are reused on their exact unchanged
selected bodies/helpers. No broad rerun, production deployment, live-provider
approval or independent audit is implied.
