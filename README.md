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

The [current activation review](reports/activation-final-six-20261118/REVIEW.md)
passes all 13 controlled cold scenarios at 20M with full 20% headroom, closing the
six previous refusals. Worst opening ZZZ/all-slow falls from 18,612,697 to
16,460,899 raw gas, or 19,753,079 with full padding. Exact NFT rights and financial
guards remain; the 12M default and reviewed 20M policy are unchanged.

This is finite evidence for 1,000 NFTs and 16 ERC20 currencies plus ETH,
not universal workload or production approval. Real markets, complete fees/providers, 64 currencies, two-LP maximum
state and other activation orders remain unqualified. Fresh F6 creation/data and
source/runtime pins are required; old private storage is never reinterpreted.
Existing chains, services, journals, websites and paused monitoring are unchanged.

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
