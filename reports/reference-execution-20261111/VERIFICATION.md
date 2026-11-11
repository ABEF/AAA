# Verification — reference execution

Source candidate over contract main6654500 and website maine3108bc. This is
internal source-scoped evidence, not deployment, production or independent
approval. [Design](../../docs/REFERENCE_SWAP_EXECUTION.md) and [review](REVIEW.md)
explain the exact execution-price1/LP3 boundary; older profiles remain explicit.

## Production build and size

The [closed normal input](build/compiler-input.json.gz) and
[actual output](build/compiler-output.json.gz) use unchanged0.8.26/Cancun,
via-IR, optimizer1/Yul-disabled settings. They compile61project/100total
sources. All [48runtime/initcode gates](build/production-size-gates.json) pass.
[Source/settings hashes](build/source-manifest.json) bind this a846 snapshot.
Earlier size failures remain outside this final acceptance; no limit was raised.

| Contract | Runtime bytes | Runtime headroom | Creation plus static arguments |
| --- | ---: | ---: | ---: |
| Vault |24544|32|26066|
| Oracle |24488|88|48395|
| Manager |24386|190|48286|
| Budget |24124|452|24953|
| Balancer |22442|2134|45237|
| Existing Math child |21776|2800|21830|
| Pricing |20106|4470|20943|

Exact constructor arguments and deployment graph still require release review.
No new deployed helper, generic executor or custody recipient was introduced.
Read-only factoring preserves typed caller/mask authority in its original owner.

## Actual-core and Entry verification

The [reference-context record](reference-context/VERIFICATION.json) contains
**29distinct successful verification methods**:24unchanged scoped passes,
two exact-error rechecks and three explicitly named policy2 diagnostics.
It is not one final all-green whole suite. The optional export utility skips by
default. Original three strict12M failures and two incorrect test error-class
expectations remain in the [attempt records](attempts/focused-a5d209f94a/VERIFICATION.json).
They are not additional successful methods.

A later [export-completeness follow-up](reference-context/export-completeness/FOLLOWUP.json)
changes only optional setup/export capture. [Body preservation](reference-context/export-completeness/BODY-PRESERVATION.json)
proves all29verification methods and other helpers byte-identical, all61production
sources unchanged, and no default setup I/O/state write when the export env is
absent. Its targeted compile/default skip and [actual result](reference-context/export-completeness/RESULT.json)
retain their own source hashes; the optional skip adds no successful method.

The fixture uses actual installed local v4 core/StateView/PositionManager and
production Entry/Vault/Pricing/Rewards/Fees/Manager/Oracle. Authority, admission,
Permit2, ETH publications and VRF are explicit test seams; depth is controlled
synthetic funding. Independent cores deliberately share PoolIDs. Coverage includes
both swap directions, stored-tick/liquidity crossings, exact output/full-state
negatives, source-kind revisions, source/round changes, disagreement, nested
scopes, sequential recapture, callbacks reading captured data, final mutation
rejection and exact policy-hash parity.

Each of three opt-in Entry workflows first submits the exact reviewed call
with12M gas, proves rejection and unchanged economic/LP/approval/context state,
then re-cools and executes the same payload under an explicit local32M diagnostic
with full20% headroom. Numerical assertions retain marginal LP, net NAV, shares,
incumbent rights, ownership, unchanged main geometry/clock and rollback.
No default, source policy or financial ceiling was raised.

| Controlled diagnostic | Raw call gas | With full20% headroom |
| --- | ---: | ---: |
| ETH activation |15317541|18381050|
| ETH growth |14103737|16924485|
| ZZZ activation |15644361|18773234|
| ZZZ growth |14404957|17285949|
| Second ZZZ entrant |15038024|18045629|

These are fixture call costs, not Robinhood fees or universal ceilings. Earlier
strict-host activation values differed by115gas in the wrapper; their original
records remain exact. Initial32M and intermediate16.5M prototypes are not final
acceptance. [Gas attribution](attempts/gas-attribution/eth-full-composition.json)
guided optimization; inclusive categories overlap and cannot be summed.

The separate [compatibility run](compatibility/VERIFICATION.json) passes77selected
methods:23original spot-reader,25routing and29actual-v4 portfolio/lifecycle.
One fuzz method runs1000cases; that is not1000additional methods. Its
[scope](compatibility/SCOPE.md) lists the58/61production-source execution closure,
substituted dependencies, single/hybrid transitions, contributions, both-leg
harvest/claims, consolidation, force0 and terminal return. Original stale-call
failure remains. Old ERC20/ERC20 fake-reference hosts are not relabeled as current
native evidence. No full published CI/frozen-release regression is claimed.

## Backend, keeper and browser consumers

[323distinct final Python methods](backend/python-consumers.json) pass with zero
failures/errors/skips and identical before/after source brackets. They cover
profile/legacy compatibility, traces, reads, keeper health/journal, operation
review and unsigned management. [Source manifest](backend/source-manifest.json)
binds the21changed Python/test paths, including the later actual-trace module.
Earlier300mixed-source checks are not current
passes. The23new-profile/48health/one-manual sub-runs overlap323; do not add them.

The actual website checkout passes [140focused browser methods](website/VERIFICATION.json):
48source10 and92unmodified source9 cases. These use synthetic RPC/DTO fixtures,
not wallet/hosting acceptance. Source10 authenticates execution1/LP3 and the same
33-role graph; claims/holdings gain no live mutable Oracle-context dependency.
Shared signer and public null configurations remain unchanged. Exact applied
source hashes and log are retained.

The [four actual owner-origin RPC cases](backend/rpc-cases.json) pass production
backend accounting measurement on new owned Anvil nodes. They restore an
authenticated setup baseline plus actual later per-slot delta, preserving zero
writes; the [independent merge probe](backend/export-merge-format.json) verifies
changed, unchanged and nonzero-to-zero slots.35nonharness code identities are
checked. Foundry omits its running harness; no Entry descendant calls it.
No caller normalization or guessed code/storage/balance is used. An initial
untouched-state omission is a corrected fixture failure, not a production fix.

| Actual local RPC case | Trace gas used | Estimate plus20% reviewed envelope |
| --- | ---: | ---: |
| ETH activation |14780416|18521988|
| ZZZ activation |14995485|18929126|
| ETH growth |13594955|17180808|
| ZZZ growth |13829824|17570676|

Trace accounting and Foundry gross-call measurements are different metrics;
neither substitutes for target-chain estimation. Each32M diagnostic respects
the local64M block and explicit fee budget. Each exact call ALSO succeeds at
its actual [reviewed17.18M–18.93M envelope](backend/reviewed-envelope-calls.json).
Every default12M call rejects. [Four additional offline replay methods](backend/actual-trace-replay.json)
pass against the four immutable compressed fixtures; these replay the same
workflows and are not four additional EVM campaigns. All owned nodes stopped;
there were zero signed/broadcast transactions. The setup uses1000USD activation
and100input-token growth, not the browser's exact100USD selection or a fully
admitted production inventory/API. Authorities, feeds, VRF and depth remain
explicit test seams; actual market/provider/wallet/operating acceptance stays open.

## Static analysis and documentation

Actual offline Slither used existing a846output without another compile. The
[strict record](static-review.json) has567findings:162individually reassessed
current contexts and405unique exact referenced-source reuses. Root reviewed
22high/reentrancy/equality contexts; a collaborator reviewed140others. The
[raw data/decisions/source brackets](static/README.md) retain accepted risks,
transitive limits and analyzer diagnostics. Strict/default checks and44checker
regressions pass. This is not exploit-absence or independent approval.

Function/operator references cover40contracts,956functions,40constructors and
13receive hooks:1009explicit example rows, zero purpose/input/output gaps and
1–5word summaries. Both generators pass against normal source. Their
[receipt](documentation/function-reference-verification.json) records that the
manual's prose intentionally changed outside generated tables. Current guides,
memory, sole Todo and source template distinguish LP3/execution1 from historical
LP2; the old schema17 template remains byte-exact. [Source consistency](documentation/source-consistency.json)
checks61files without claiming compilation/security coverage from that scan.

## Remaining qualification and preservation

Default12M does not admit these cold Entries. Qualify existing optional policy2,
actual transaction/block/RPC limits, full headroom and complete fees before
operating adoption. The [bounded public-RPC attempt](GAS_QUALIFICATION.md) returned
403 before valid chain data; no target gas/cost result is claimed. Actual source
honesty/independence, useful depth, VRF/OpenSea, authorities, hosting/recovery
and independent audit remain open.

The reference may be an external swap venue, not the same-core principal
destination. Large own impact or source/control changes can correctly reject
an exact quote. No always-executable, automatic highest-TVL or MEV immunity
guarantee is made. Service-only compound policy remains a separate exposure.

Source publication changes no deployed contract, public signing, site/service,
existing Anvil8902, journal or user-paused heartbeat. Four unrelated tracked
dirty files remain byte-identical/unstaged. Old failures/reports/codecs/checkpoints
and actual environment identities remain distinct.
