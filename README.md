# ZZZ Collection - Proof of Permanent Liquidity (PoPL)

PoPL connects transferable ERC-721 NFTs to vault-managed ETH/ZZZ liquidity.
Activation attaches an independently accounted LP share and unlocks funded LP
fees plus rarity-weighted NFT-sale royalties. Holders cannot redeem principal
during normal operation. Governance can permanently end LP activity and return
actual ETH + ZZZ to current NFT owners; transfers, old rewards and royalties remain.

**Source candidate; undeployed for production. Production NOT APPROVED.**
Current accounting7/direct Entry3/custody5/mint2 uses canonicalV10. The trusted
normal build is `activation-gas-20261118` (factory payload5 / royalty allocation2). Source publication does not update
contracts, services, journals or websites; public signing remains disabled.

The [activation gas review](reports/activation-gas-20261118/REVIEW.md) preserves exact LP/royalty rights, public inputs and Factory5 bytes while reducing tested activation estimates by693k-713k gas. At1,000NFTs, all13 cold local scenarios pass accounting/execution checks;7 fit20M with full20% headroom and6 remain refused. Worst padded gas is22.34M, so maximum-state qualification remains open. Fresh runtime pins are required; private carry slots cannot be copied from older builds. Component costs can increase in zero-fee states; always review the complete exact call. Limits and live environments are unchanged.

The worker defaults to dry run. Raw checks can occur during cooldown; paid
confirmation enrollment starts near eligibility to avoid hours of unnecessary
writes. Compounding waits for an in-range main below the adjustment threshold and no pending geometry change;
hourly harvesting remains independent. See [operations](docs/OPERATIONS.md),
[coordination](docs/KEEPER_COORDINATION.md) and [recovery](docs/KEEPER_RECOVERY.md).
Host restart, RPC inclusion, gas and writer/checker rollout remain qualification gates.

## Verification and release status

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
