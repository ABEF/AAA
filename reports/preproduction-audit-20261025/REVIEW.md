# Pre-production internal audit - 2026-10-25

**Production NOT APPROVED.** This review found and corrected concrete keeper and
operator-documentation defects and improved composition/invariant coverage. It
does not establish that all vulnerabilities have been found. No reproducible new
unprivileged principal theft, double claim or canonical replay exploit was found
in the inspected current paths. Immediate governance and external custody remain
deliberately trusted; real dependencies and independent audit remain open.

**Two activation gaps remain open:** thin-market deployed-LP feasibility (A-07)
and signed review-cap binding (A-08). Both are explicit release requirements;
the keeper fixes and passing checks do not close them.

Read the [plan and coverage boundaries](PLAN.md), [verification](VERIFICATION.md)
and [service findings/evidence](services/REVIEW.md). Baseline contract revision:
`214d9a104643df0643a21ceec6970329f3525d3f`. Publication is recorded separately.

## Findings and corrections

| ID | Severity | Concrete failure | Correction and evidence |
| --- | --- | --- | --- |
| A-01 | Medium | Keeper budget accounting trusted RPC `effectiveGasPrice`, although a type-2 receipt can report a price inconsistent with signed fee caps and the canonical base fee. Wrong spend affects later maintenance budgets. | Persist fee-review schema 1 before signing; bind chain/gas/cap; derive dynamic execution cost from signed limits and inclusion block. Preserve reported price separately. Independent failing-first transcript and affected recovery checks: [services](services/REVIEW.md). |
| A-02 | Medium | Confirmation did not preserve and enforce the original L1 allowance/fee semantics. Changed configuration or a larger reported L1 charge could corrupt reconciled budget assumptions. | Capture L1/total review with the intent; reject missing required data, incompatible semantics and excessive cost without consuming pending state. This cannot retroactively prevent an external L1 charge already paid: a violation stops further work for operator reconciliation. |
| A-03 | Low | Read-only keeper preflight could report readiness for a pinned native-V2 profile while the deployed Vault reports version 1; live startup would correctly reject it. | Preflight now calls the same accounting-version check. A failing-first case and final focused rerun verify refusal. |
| A-04 | Medium | Current operator guides contradicted each other: pause described as stopping all outgoing principal, limits described as immutable 3%, native custody described as WETH, and retired bridge APIs prescribed as executable. These could cause unsafe or impossible incident actions. | Corrected operative sections, exact stop/cancel/restart boundaries, schema/helper inventory and loss-floor calculations. Pause explicitly permits separately approved paused custody exits. Default percentages are separated from captured policy and original approved absolute minima. |
| A-05 | Medium, verification integrity | The existing NFT-rights invariant handler generated $2/$4 growth actions below the production $5 minimum while `fail_on_revert=true`. It could fail on an invalid input instead of exercising accounting. | Bound equal-sided $1 fixture inputs to at least 3+3, count completed top-ups and assert strict share growth. A focused non-skipping minimum-bound regression and bounded invariant verify the repaired domain. No production minimum was weakened. |
| A-06 | Coverage gap | Separate venue and ledger fixtures did not demonstrate the complete installed-v4 principal/revenue lifetime in one harness. | Added five composition scenarios with installed Core/StateView/PositionManager and real protocol Entry/Vault/Strategy/ledgers. Actual swaps must produce positive fees, royalty claims must pay, rebalance must replace LP, and ghost cash/liability conservation must hold. Local substitutes are explicitly listed; this is not selected-chain qualification. |

No cap increase, new governance permission, generic executor, redemption path,
automatic raw-exit fallback, public signer or deployment is introduced. Old pending
keeper intents are preserved; their missing historical reviews cannot be guessed
from current settings. See [recovery upgrade steps](../../docs/KEEPER_RECOVERY.md#fee-review-upgrades-and-legacy-pending-intents).

## A-07: thin-market activation feasibility remains open

**Medium availability/qualification gap; no fund theft observed.** With selected
static fee10020/spacing200 and observed protocol1000 applied to installed local
v4, a native-input activation at the fixture's $100 value retained approximately
$99.383158 but deployed only $98.849621; about $0.533537 remained idle. The new
swap changed spot, so the planner's pre-swap balance ratio left too much idle for
the strict $99 deployed floor. The guard correctly reverted. These are local
mock-dollar/depth observations, not current Robinhood prices or liquidity.

The harness now preserves a specific thin-market `Slippage`/full-rollback case.
A separately identified deeper fixture exercises successful lifetime operations;
it cannot qualify live feasibility. The callback-round test also now requires
the actual feed callback and exact `InvalidState`, so an unrelated thin-market
revert cannot satisfy it. Earlier generic revert scope is retained separately.

Production quote qualification must simulate the full operation at current
liquidity/ticks/fees and refuse infeasible reviews. Determine whether a bounded
post-swap ratio reconciliation can improve deployed amount within the same budget;
do not assume every market is solvable or add an unreviewed extra swap. No planner
rewrite, cap relaxation or incumbent subsidy is hidden in this audit. The owning
activation/strategy tasks remain open, including price impact, MEV, separate gas,
exact final LP and stale-quote behavior. A previously confirmed approval and paid
gas do not roll back with a later failed Entry transaction.

## A-08: the signed contribution review does not bind its loss cap

**Medium review-integrity gap; release blocker for public activation signing.**
Entry Request contains amount/route/minimum output/minimum liquidity/deadline,
not the maximum loss policy displayed by preparation. ContributionPricing captures
current Budget policy at execution. Backend preparation checks the cap at its
pinned block and derives a raw liquidity minimum using caller slippage; it does
not turn that reviewed percentage into an on-chain USD/cap commitment.

An immediate governance increase from1% to10% before Entry begins can therefore
apply the higher policy. Existing raw minima may prevent some worse results,
but do not establish the earlier1% guarantee, especially if ticks/range/prices
change. Mid-operation callback changes remain separately guarded. This is a
source-traced stale-review risk, not a reproduced unprivileged theft or a claim
that governance lacks the broader custody trust already accepted.

Required fix: a versioned reviewed contribution path binding a caller maximum
loss BPS, checked against the actual captured execution policy before transfers,
plus coherent exact calldata/trace/API/inventory/wallet updates. Preserve stricter
caller/venue minima, final price/policy checks and atomic rollback. No silent
legacy/direct-path fallback may claim that guarantee. Existing Anvil identities
and pending journals must remain historical profiles. The [owning task](../../TODO.md#task-reviewed-contribution-policy)
is explicitly open; this audit did not ship an unreviewed ABI rewrite. Public
signing remains disabled. No unnecessary blanket test was run to establish the
absence of a field visible in source.

## Review coverage and adversaries

| Area | Failure paths inspected | Result and practical limit |
| --- | --- | --- |
| Entry and shared LP | Direct/native/conversion context, exact approvals/refunds, incumbent versus marginal NAV, prefunds/donations, price-round callbacks, actual PoolKey/owner/ticks/liquidity, out-of-range joining, dust and historical compound | No new exploit confirmed. Composed tests strengthen evidence; production route execution, independent prices and MEV remain unqualified. |
| LP and royalty ledgers | 80/10/5/5 classification, equal activated collective membership, rarity-only royalties, pending/cohort isolation, fractions, transfers, owner claims, converted ETH, late funding | Rights remain NFT-bound; dormant NFTs have no eligibility. Receipt/processing-time economics are not swap-time historical entitlement. Actual token liveness and market payment behavior require qualification. |
| Maintenance and custody | Trigger/cooldown/range, close/swap/deploy floors, original price/cap capture, same-pair moves, paused parking, normal/raw custody exit, return/completion, recipient rejection | No new unauthorized path confirmed. A per-operation cap does not bound cumulative erosion. External custody may be lost or diverted by the approved recipient. |
| Canonical lifecycle | Preparation/freeze, ordered settlement/import, separate backing, partial funding, abort/retry, repeated successors, ancestor late receipts, terminal uniqueness | Existing focused tests cover these source-bound edges and were not needlessly repeated. Future-chain canonical transport/finality and post-halt recovery are not implemented. Contract-owner/escrow cutover still needs rehearsal. |
| Oracle/dependencies | Two-source bounds, runtime/round/age/sequencer checks, proxy/common-mode risks, fail-closed behavior, exact transfers and callbacks | Two addresses cannot prove independent truth. A compromised quorum or two correlated/wrong sources defeats the economic assumption. Blacklists, paused tokens or failed venues can still prevent movement. |
| Keeper/backend | Pending persistence, fee/nonce identity, reorg/finality, budget day, recovery and save failures, profile preflight, bounded API work, canonical reads and history completeness | Keeper defects above corrected. Failover is not a Byzantine quorum; raw log completeness and trusted RPC history remain operating assumptions. Host-level locks do not fence a second host with the same key. |
| Website/marketplace | Public null deployment, Anvil-only coordinator, confirmed LP before artwork, exact approvals and original saved-hash recovery, intended OpenSea primary mint | Website inspected read-only; existing public simulation unchanged. Actual native-V2 wallet/API profile, extensions and OpenSea integration remain unqualified. |
| Release/tooling | Pinned compiler/dependencies/CI, normal size gates, evidence scope, old drafts, production inventory and actionable docs | Production Solidity behavior is unchanged by these fixes. Earlier source-bound gas/size evidence is reused, not presented as a fresh full run. Exact-release independent static/fork/CI review remains required. |

This includes adversarial holders and callbacks, transaction ordering/front-running,
malformed or inconsistent RPC data, compromised keepers within role bounds, failed
tokens/venues, and governance/recipient misuse as an explicit trust case. No claim
is made to prove the safety of unprovided future contracts, providers or bridges.

The thin-market arithmetic diagnostic also indicates a feasible additional ratio correction in that particular no-tick-cross state. It is not an executed correction or a general solution; see the [economic scope](ECONOMICS.md).

## Architecture and operating improvements

- [Architecture](../../docs/ARCHITECTURE.md) now separates principal, LP liabilities,
  royalties, governance, services and canonical lifecycle. An accounting or native
  version cannot be changed by relabeling an old deployment/journal.
- [Operations](../../docs/OPERATIONS.md) gives current schema-5/native/V2 procedures,
  removes executable retired bridge setup and distinguishes current functionality
  from real service qualification. Historical reports retain their source scope.
- [Custody guide](../../docs/GOVERNED_CUSTODY_HANDOFF.md) computes rounded-up floors
  from captured `L` and preserves both pre-parking minima and the original approved
  plan. Parking and later approval are not automatically one cached loss budget.
- [Operator manual](../../docs/OPERATOR_MANUAL.md#stop-controls) distinguishes mint,
  pool, keeper, global and preparation stops. Pause is not a custody freeze; before
  stopping dependencies, review outstanding plans and already submitted hashes.
- [Recovery](../../docs/KEEPER_RECOVERY.md) covers the fee-journal upgrade, original
  evidence, no blind resends, off-host state preservation and reviewed signer rotation.
- [Roadmap](../../docs/ROADMAP.md) sequences unresolved functionality, actual
  dependencies, native integration/operating rehearsals and independent release
  review. It does not create another task list; [Todo](../../TODO.md) owns status.

## Release blockers and accepted residual risks

1. **Real service assumptions:** independent USD sources per asset (including proxy/
   common-mode/depeg review), executable activation and cheaper ZZZ conversion routes,
   supported funded proof-verifying VRF, correct authorities and permanent artwork.
2. **Operational qualification:** actual selected-market fork/native lifecycle,
   chain fee/RPC/trace/finality behavior, Linux recovery/backup/rotation/monitoring,
   maximum-state gas, strategy backtesting and service capacity. The user-deferred
   10/25/100-user load campaign remains deferred, not passed.
3. **Versioned integration:** native/pricing-V2 API/website/wallet configuration,
   complete indexed history, unavailable-state handling and OpenSea primary mint/
   royalty/escrow compatibility. Public signing stays disabled.
4. **Future capability before sealing:** resolve the required whole-collection
   future-chain finality/transport/lineage boundary. Atomic different-pair/ETH-WETH
   conversion is unsupported; explicit external custody is a different trust path.
   No configuration can add missing bytecode after seal.
5. **Independent approval:** current-source audit/static/fork review, remediation,
   exact runtime/configuration and operator sign-off. Vault's prior measured runtime
   is 24,551 bytes (25-byte EIP-170 margin); keep ordinary limits and remeasure after
   any bytecode change. Do not hide growth by weakening gates.

Immediate governance can approve dishonest feeds, supported custody recipients or
reviewed replacement code. No delay was added against the user's decision. Holders
cannot withdraw principal; that fact does not make operator custody trustless.
Market losses, range downtime, repeated bounded losses and external failures remain
possible. Native raw exit avoids a wrapper but still requires working pool/token
settlement. Backups cannot repair a stopped blockchain or make a failed token spendable.

Technical review uses installed source and primary standards. Relevant principles:
[Solidity external-call/reentrancy and gas guidance](https://docs.soliditylang.org/en/v0.8.26/security-considerations.html),
[ERC-721 transfer/receiver semantics](https://eips.ethereum.org/EIPS/eip-721) and
[EIP-1559 signed fee calculation](https://eips.ethereum.org/EIPS/eip-1559). These
references guide the review; they do not certify this implementation.
