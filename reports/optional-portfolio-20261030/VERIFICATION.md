# Optional portfolio source-scoped verification

Reviewed31October2026. This is local implementation evidence, not production
approval, a published CI result, a fresh whole-suite run or an independent audit.
The [machine ledger](verification-ledger.json), [source pins](source-pins.json)
and linked receipts retain exact stage boundaries. Do not add overlapping runs.

## Executed checks

| Group | Actual scope |
| --- | --- |
| Final real local v4 |14/14 OptionalPortfolioCoreTest methods pass after the half-width default and final callback guard. Real local PoolManager/PositionManager/StateView; explicit controller/feed/VRF/Permit2/admission and failure substitutes. Tests cover both-leg custody/NAV/floors, second-mint/burn rollback, main-only entrants, incumbent rewards/transfers, collection/claims, disable/merge, parking, same-pair movement and terminal holder return/future royalties. |
| Final active-main guard |8/8 typed sentinel methods pass, including completed positive mint, exact downward boundary, narrow inverse-price case and late same-sqrt tick flip with full native/state rollback. These are guard tests, not actual-market execution. [Receipt](active-main-verification.json). |
| Half-side geometry |26Policy methods pass at the half-default source stage, including explicit10000full-side alternative. That run also includes the earlier6guard methods; they overlap final8. [Receipt](half-policy-verification.json). |
| Policy/math/cadence/confirmation |91distinct earlier-stage methods:34confirmation,10threshold,11cadence,26Policy,10math including a1000-run fuzz. Two initial fixture getter/prank ordering errors corrected and exact methods rerun; empty selection run excluded. Later26Policy rerun is not additional coverage. |
| Accounting/canonical/custody |15focused methods pass at the recorded sourcePool-fix stage.35earlier ledger-harness methods pass including two1000-run fuzz cases. Test-only transport harness preserves old two-ERC20 fixture semantics; it is not production native-ingress qualification. A broader custody compile timed out and is excluded. |
| API |181distinct affected methods across recorded stages. One historical fixture error fixed and rerun. Final12fresh portfolio methods also pass after the half-default fixture update; they are a subset, not12additional methods. |
| Keeper/inventory |298distinct methods across recorded scopes:38fresh keeper,25fresh inventory,161historical keeper and74historical inventory/CLI. They are not one fresh final whole-suite run. [Stage/source receipt](keeper-inventory-verification.json). |
| Normal compiler |81closed inputs,42normal gates,zero errors, unchanged before/after source/build/compiler hashes. Normal0.8.26/Cancun/viaIR/optimizer1/Yul-disabled settings retained. [Exact sizes](normal-size-gates.json). |
| Callable documentation |36contracts/765functions/36constructors/14receivers; zero explanation/input/output gaps; strict generated-source check passes at final compiler pins. [Receipt](callable-reference-verification.json). |

Real local core tests deliberately use correlated synthetic USD sources and local
funding. They prove exercised paths and rollback, not oracle independence, token
authenticity, organic volume, target-chain costs or maximum1000-holder gas.
No public RPC, disposable public wallet or existing Anvil service was used.

## Size and compatibility

| Contract | Runtime bytes | Creation bytes before ABI arguments |
| --- | ---: | ---: |
| Vault |24562|26007|
| Strategy |23950|25434|
| Manager |21117|43825|
| Typed position child |19463|20481|
| Balancer |23410|32756|
| Budget |23128|23938|
| PortfolioPolicy |15926|16445|

Static constructor argument lengths are included in their normal initcode gates;
exact target deployment/dynamic arguments and gas remain unqualified. Vault has
14runtime bytes of headroom. Modular extraction substantially restores Manager
initcode margin without relaxing EIP-170/3860. No historical runtime is relabelled.

## Failures and limits retained

- Initial actual-core setup exceeded the production one-day feed-age maximum;
  the fixture was corrected, not the guard. Accidental Foundry testFail naming
  rejected selection before execution. One final royalty-claim fixture consumed
  prank in its getter; caching the getter corrected only that fixture.
- Earlier Forge build produced valid compiler objects then failed its Windows
  local-signature cache-directory step; it is not a successful full verifier.
  Final closed pinned-solc compilation independently succeeds without that step.
- Initial partial API/fixture failures, empty selections, prior full-side/default
  stages and broader custody timeout remain external. No failed run is overwritten
  or counted as a pass. Exact paths/hashes are in the machine ledger.
- The one warm local trace measuring roughly10.13Mgas for a hybrid rebalance is
  a prior pre-final-callback fixture observation, not target gas/capacity approval.
  Test function gas includes multiple operations and must not be presented as a
  single production transaction estimate.
- Meaningful new tests do not establish exhaustive correctness or manipulation
  immunity. Real qualification/current static-analysis triage and independent
  audit/remediation remain in the [sole Todo](../../TODO.md).

Four unrelated dirty tracked files match their original hashes. Old report
narratives are unchanged; only the navigation index and this new evidence pack
are updated. No service/site/Anvil/journal/signer/public signing/heartbeat change.
Git work remains local/uncommitted; this report does not publish or deploy it.
