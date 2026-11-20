# ZZZ Collection - Proof of Permanent Liquidity (PoPL)

PoPL connects transferable ERC-721 NFTs to vault-managed ETH/ZZZ liquidity.
Activation attaches an independently accounted LP share and unlocks funded LP
fees plus rarity-weighted NFT-sale royalties. Holders cannot redeem principal
during normal operation. Governance can permanently end LP activity and return
actual ETH + ZZZ to current NFT owners; transfers, old rewards and royalties remain.

**Source candidate; undeployed for production. Production NOT APPROVED.**
Current accounting7/direct Entry3/custody5/mint2 uses canonicalV10. The trusted
normal build is `activation-final-six-20261118` (factory payload6 / royalty allocation2). Source publication does not update
contracts, services, journals or websites; public signing remains disabled.
The [readiness advance](reports/readiness-advance-20261120/REVIEW.md) updates the23-package
status and adds offline mint-transaction intent review. It does not approve
OpenSea's standard signed stages, a randomness provider or a production pool.
The [full normal backend claim review](reports/full-claim-admission-20261120/REVIEW.md)
adds real contract-graph validation and fixes a request-budget failure by returning
a freshly validated safe prefix. Current live environments and financial limits stay unchanged.

[Expanded market qualification](reports/market-route-qualification-20261120/REVIEW.md)
checks additional native and WETH/v3 routes; no complete production route or
independent source pair is approved. Final production-pool selection is deferred;
the recorded integration configuration and safeguards stay unchanged. The
[conversion scope correction](reports/market-route-qualification-20261120/ERRATA.md)
separates existing v3 earned-conversion code from current graph/worker support.

The [maximum-state LP settlement and claim review](reports/lp-claims-maximum-20261120/REVIEW.md)
adds exact same-NFT conversions, cold partial claims and a bounded claim-planner
CPU improvement. Actual routes, production HTTP/provider admission, maximum-state
API workloads and operating approval remain open.

The [latest findings consolidation](reports/seven-report-consolidation-20261119/REVIEW.md)
reconciles seven subsequent reports and retains all original finding IDs.
The [whole-project workload review](reports/whole-workload-review-20261119/REVIEW.md)
adds the full function/scenario map, corrected exact-unit market tests and bounded
large-wallet ownership pages; it does not claim every scenario is qualified.

The [current activation review](reports/activation-final-six-20261118/REVIEW.md)
passes all 13 controlled cold scenarios at 20M with full 20% headroom, closing the
six previous refusals. Worst opening ZZZ/all-slow falls from 18,612,697 to
16,460,899 raw gas, or 19,753,079 with full padding. Exact NFT rights and financial
guards remain; the 12M default is unchanged. The selected activation/growth
profile is now **32M with full20% padding**; keeper/manual maintenance stays24M.
The [32M candidate and review](reports/contribution-gas32-20261119/REVIEW.md)
require actual provider/execution/fee qualification before live adoption;
these earlier20M results are not relabelled32M.

This is finite evidence for 1,000 NFTs and 16 ERC20 currencies plus ETH,
not universal workload or production approval. Real markets, complete fees/providers, full64-currency/two-LP
qualification and other activation orders remain open; new finite results follow. Fresh F6 creation/data and
source/runtime pins are required; old private storage is never reinterpreted.
Existing chains, services, journals, websites and paused monitoring are unchanged.

The [expanded controlled rehearsal](reports/maximum-workload-20261119/REVIEW.md)
now covers64 ERC20 royalties plus ETH and both LPs:11/12 contributions fit32M
with full20%; one slow-ZZZ opening state remains above budget. All five executable
maintenance cases fit24M/full25%, with three intended guard rejections verified.
Exact payouts/backing reconcile; synthetic external depth and remaining real
provider/market/full-state limits stay explicit. Defaults and safeguards stay.

The worker defaults to dry run. Raw checks can occur during cooldown; paid
confirmation enrollment starts near eligibility to avoid hours of unnecessary
writes. Compounding waits for an in-range main below the adjustment threshold and no pending geometry change;
hourly harvesting remains independent. See [operations](docs/OPERATIONS.md),
[coordination](docs/KEEPER_COORDINATION.md) and [recovery](docs/KEEPER_RECOVERY.md).
Host restart, RPC inclusion, gas and writer/checker rollout remain qualification gates.

## Verification and release status

The [fresh F6 local construction](reports/f6-construction-20261120/REVIEW.md)
verifies39instances/bindings and default/unsealed authority state, with no compiler
or production-code change. Real deployment inputs, dependencies, fees and approval
remain separate; both rehearsal nodes are stopped.

The [current Gate A results](reports/readiness-gate-a-20261120/REVIEW.md) complete
compiler-advisory applicability review and refresh actual market/platform blockers.
Production remains unapproved; no source/compiler or live configuration changed.

The [production qualification plan](docs/ROADMAP.md) orders23 acceptance packages
from real-market feasibility through source, services, deployment, sealing and
public opening. It preserves the sole Todo and separates predeployment checks
from evidence that requires actual deployed addresses. No release approval is implied.

### Find the relevant evidence

| Need | Reference |
| --- | --- |
| Current capabilities, source pins and limits | [Feature/evidence reference](docs/IMPLEMENTATION_STATUS.md), [authority verification](reports/authority-audit-20261103/VERIFICATION.md), [whole-project supplement](reports/comprehensive-audit-20261104/REVIEW.md) |
| Historical findings applied to the current code | [Consolidated findings](docs/AUDIT_FINDINGS.md), [report map](reports/README.md) |
| Exact management action, inputs, stop/restart and recovery | [Operator manual](docs/OPERATOR_MANUAL.md), [callable reference](docs/CONTRACT_FUNCTIONS.md) |
| What remains and final approval | [Sole Todo](TODO.md), [roadmap](docs/ROADMAP.md), [release record](docs/RELEASE_CHECKLIST.md) |

Local checks, scoped source review and documentation reconciliation do not imply
published CI, target-chain operation, independent audit or production approval.

The [launch workload review](reports/launch-workload-20261117/REVIEW.md) distinguishes actual local gas estimates from body measurements.16-currency capacity does not guarantee that every activation or32-entry claim fits its budget; qualify the selected workload and use fresh bounded claim batches.

### Production approval

Actual independent feeds/routes/VRF, authorities, OpenSea, current-profile website
and services, target gas/strategy economics, operating recovery and independent
audit/remediation remain open. The [sole Todo](TODO.md) owns tasks and the
[release record](docs/RELEASE_CHECKLIST.md) owns final sign-off. No public deployment
or service rollout is authorized by source implementation/publication.

## Try the local browser test

Use the [historical local-stack guide](docs/LOCAL_TEST_STACK.md) for the preserved
versioned setup. Do not reset it to resemble newer source or infer a port is live.

## Development

### Setup and verification

Use the [supported environment](docs/DEVELOPMENT.md):

```bash
bash scripts/install-deps.sh
bash scripts/verify.sh
python3 scripts/sync-project-todo.py --check
```

Solidity remains pinned to 0.8.26/Cancun with the normal via-IR profile. Run useful
affected checks; preserve exact source pins before reusing earlier evidence.
Do not relax runtime/initcode gates or test filters to obtain a pass.

### Small-value experiments

The [$1 isolated rehearsal](docs/ONE_DOLLAR_REHEARSAL.md) uses separately authorized
test-deployment policy configuration; it does not patch fresh source or alter
production defaults, loss settings or rights. Local substitutes qualify no provider.

### Keep project records consistent

Update [task ledger](docs/project-todo.json), generated Todo, features/evidence,
operator/callable procedures and context together using the
[maintenance procedure](docs/TODO_WORKFLOW.md). Publication and deployment are separate.

Fresh royalty4 retains the [one-hour sale-close activation window](docs/ROYALTY_LAUNCH_WINDOW.md)
and adds [exact-unit allocation](docs/EXACT_ROYALTY_ALLOCATION.md): GCD-normalized rarity
weights, deterministic rotating indivisible units, and no allocated rounding
remainder after all eligible claims. Initial holding, prefunds, zero participants,
unsupported currencies and pathological-token failures remain distinct. Current canonicalV10
rejects older peers; original V9 evidence retains its own source scope. Actual OpenSea, gas/workloads and independent approval remain open.
