# Native production inventory: scoped verification

Recorded 2026-10-24. Undeployed development candidate; production NOT APPROVED.
Publication is recorded separately. No actual RPC/provider, contract transaction,
wallet key, public deployment or operating service was used.

## Results and evidence

| Changed scope | Distinct passing cases | Evidence |
| --- | --- | --- |
| Native schema-5 gate | 41 new Python cases: core/helper bindings, native identity, live policy observations, source/route domains, v3/v4 separation, fee scope, prices/VRF/services, canonical/custody gates, malformed inputs and qualification scopes | [Initial final40](schema-focused-final.log), [last fee-scope addition and two affected reruns](schema-fee-scope-final.log) |
| Read-only observer | 19 new mock Python cases: canonical anchor/depth/reorg, strict actual ABI, separate approved pins, route/native/ledger/role/sequencer reads, finite read-only work, sanitized failures, atomic output and gate composition | [Run accounting and hashes](observer-tests.json), [affected12](observer-final-focused.log), [composition/JSON2](observer-composition-json.log), [I/O guards5](observer-io-guards.log), [fee-scope composition rerun](observer-composition-fee-final.log), [two final bounded-call reruns](observer-bounded-gas-final.log) |
| CLI and legacy compatibility | 13 focused Python cases, including eight new CLI checks and five affected existing template/legacy checks | [Initial result](cli-tests-initial.log), [scope](cli-tests-initial.json), [final affected reruns](final-integration.log) |

**73 distinct passing cases** across these scopes. Repeated positive/composition
cases are counted once. The last five-case integration run reruns four current-
template/dispatch cases and the existing composition case against final gate
source; it adds no distinct cases. No new full regression is claimed.

The complete composition uses the actual new validator and expected getter map.
Known mock bytecode pins are explicitly substituted inside that test, since
production-runtime preimages cannot be invented. A consistent mock inventory
never authorizes deployment. Missing or changed current caps become unavailable
or blocked; observations cannot upgrade review evidence.

## Compatibility and unchanged contract evidence

[Compatibility receipt](compatibility.json) confirms the old validation body is
AST-identical after the explicit schema-5 dispatch and all **131** prior typed-v4
source/test hashes still match. Schema 4 retains its previous semantics and its
blanket governed/native refusal. The previous blocked example is preserved as
[the historical template](../../config/production.legacy-v4.example.json).

No Solidity build, size command, unchanged contract suite, fork campaign or load
campaign was rerun. Earlier [typed-v4 verification](../typed-v4-routes/VERIFICATION.md)
retains its source scope and normal production limits. This tooling does not
alter custody, caps, routes, accounting, signing or deployed bytecode.

## Real blockers remain explicit

The current [schema-5 example](../../config/production.example.json) stays blocked:
unknown PoPL addresses/runtime observations, authority wallets, independent
pricing, conversion/input routes, randomness/services, immutable artwork
publication and independent release evidence remain unset. The [machine report](example-blockers.json)
and [CLI result](final-integration.json) distinguish actual missing requirements
from the legacy blanket rejection. No unqualified value becomes zero or ready.

Current profile scope is one active native-V2 canonical deployment without
external creator inboxes. Nonzero inbox counts, cross-chain canonical activation,
legacy V1 import and atomic ETH/WETH principal conversion remain explicitly
unsupported. Declared mappings require complete history review; passing supplied
records cannot authenticate their truth or external proxy/governance safety.

Observations must match one fresh canonical anchor. Retained rehearsals keep their
actual historical block and exact current configuration scope. Route protocol-fee
changes invalidate the associated qualification; normal price changes do not
require falsely relabeling historical tests. Every actual operation still needs
fresh simulation/validation; the observer never simulates or authorizes a send.

No website source/build/server, 8902/Anvil/NFT/LP/balances/journals/dist overlay,
shared signer, service or paused monitoring changed. Public DEPLOYMENT is null
and signing remains Anvil-only. Older unrelated drafts are preserved.

See [internal review](REVIEW.md), [runbook](../../docs/PRODUCTION_PREFLIGHT.md),
[feature reference](../../docs/IMPLEMENTATION_STATUS.md) and [single Todo](../../TODO.md).
