# Manual safeguard verification

Baseline main `0b14acaf5df696c7a32243b8ea7c315a8cd191ab`.
[Stage ledger and exact pins](evidence.json), [normal gates](production-size-gates.json),
[ABI/storage comparison](compatibility.json), [static contexts](static-review.json),
[review](REVIEW.md), [operation matrix](SAFEGUARD_MATRIX.md).

## Executed checks

| Stage | Actual result / limit |
| --- | --- |
| Negative control |5new EVM methods:4fail/1pass against original production source. Reproduces emergency sample-only cooldown and raw close zero-floor blockers. |
| Corrected focused |85selected methods:84pass/1failed callback fixture. Current production pins stable throughout. |
| Callback corrected |The one failed method passes after correcting only its receipt-recipient setup to the typed LP child. It proves callback execution, rollback, then identical-manifest success without callback. |
| Distinct selected contract successes |85, including5new methods; not91 from summing overlapping stages. Exact production sources and84unaffected successful bodies remain unchanged after the fixture repair. |
| Focused Python |47methods pass,0errors/failures/skips: operator review and function reference. No backend/worker behavior changed. |
| Normal build |52production plus31closed dependencies,43runtime/initcode-plus-minimum-constructor gates pass under pinned0.8.26/Cancun/viaIR/optimizer1/Yulfalse. Dynamic constructor arguments still require concrete deployment qualification. |
| ABI/storage |179compiled objects retain exact ABI and storage semantics; only compiler AST IDs in layout fields/type identifiers are normalized. No actual deployment/runtime compatibility implied. |
| Callable reference |37contracts/818functions/37constructors/13receivers;0explanation/input/output gaps. Current normal compiler binding, exact notes and source checks. |
| Fresh static |Slither JSON reports success with471records, not zero alerts.13changed-source contexts reviewed;458exact referenced contexts/unique matching line multisets reuse prior dispositions. Nonzero detector CLI status retained. |
| Compiler AST screen |1011implemented functions/modifiers across83sources;0named-error require forms, internal cycles/unresolved internal calls, explicit source Yul functions or storage-layout declarations. This source screen is not compiler-generated-behavior proof. |

The normal runtime margins remain Migration39/Vault635/Budget237/Balancer360.
Removing optional conditions reduces the two edited routines; a shared capability
getter is not a binary identity. Fresh records replace only changed source scope;
prior reports and overlapping counts remain historical.

## Scenarios and test boundaries

New [Confirmation methods](../../test/RebalanceConfirmation.t.sol) prove samples
can authorize emergency bit16 before cooldown while ordinary ready and retained
bit1 still reject; reference re-entry and301-second expiry reject samples.
New [actual-core methods](../../test/OptionalPortfolioCore.t.sol) exercise raw
both-leg park→Parked force re-entry, real residual inventory reversal before
raw close, and active force consolidation despite unavailable USD, stopped
ordinary confirmation, disabled operations, empty ordinary routing and infeasible
optional residual geometry. They verify shares, fee/buyback separation, main/
residual ownership/burn, actual receipts, preserved claims and pause/context.

Affected existing Confirmation, NativeVaultFlows, CustodyParking and residual
methods cover boundary timing, policy restore/revisions, replay/wrong caller,
preparation/terminal locks, retained price/value guards, all32missing-price masks,
positive close/output floors, callback/reentrancy/nonce/pause rollback and later
recovery. The NativeVaultFlows venue/access fixtures are explicit models; the
OptionalPortfolio suite uses local real v4 core/periphery with synthetic assets
and feeds. They are not Robinhood operating tests or actual governor-wallet gas.
Forge's oversized fixture allowance is separate from normal production gates.

## Evidence retention, documentation and publication

Exclusive local archive `manual-safeguard-audit-20261104` retains original source/
docs, raw compiler/analyzer output, before/after hashes, failed/corrected runs
and diagnostics. One diagnostic selected0tests because its regex omitted the
ABI suffix; it is not a success. ABI/static audit-helper corrections and all
executed stages are described in the ledger. No failed output was relabelled.

Operator, emergency/parking, feature/findings/release/profile/context, callable
and sole Todo are updated together. The operation matrix distinguishes necessary
dependencies from two corrected couplings. Final document links, generated
records, protected-file preservation and exact index/HEAD Python publication
closure are recorded with publication. Existing report bytes and unrelated dirty
files remain untouched. No site/service/Anvil/journal/signer/heartbeat rollout.

## Primary guidance and limits

Uniswap's [v4 decrease-liquidity guide](https://developers.uniswap.org/docs/protocols/v4/guides/managing-liquidity/decrease-liquidity)
defines raw output minima and typed settlement actions; it does not establish
zero principal-output protection as generally safe. Here zero REVIEW floors are
an explicit paused-governance emergency choice, while current-core principal
settlement proofs remain. Installed dependency implementation, not an interface
label, determines behavior. [Solidity0.8.26 security guidance](https://docs.soliditylang.org/en/v0.8.26/security-considerations.html)
supports preserving authority, fail-safe state and cross-contract callback checks.

No full regression, fresh public CI, all-market liveness, MEV immunity, actual
target gas/host/provider/storage qualification or independent production approval.
