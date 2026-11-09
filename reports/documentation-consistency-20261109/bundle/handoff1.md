# Frozen PoPL review inputs - NOT APPROVED

Source commit: `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`. The archive contains committed source, tests, tooling,
operator documentation, locked dependency inputs and the original task ledger.
No working-tree draft, local runtime state, wallet key, private RPC configuration,
historical test report, deployed runtime or dependency installation is included.
The exact committed artwork catalogue and fixed Keccak vectors are included as
generation/test inputs; the vectors are not historical production-approval evidence.
This export runs no test and makes no production-readiness claim.

Verify the archive against its SHA-256 received over a trusted separate channel.
After verification, inspect the source and install dependencies on an isolated
unprivileged Ubuntu host with Python 3.11+, Foundry 1.4.4 and Solidity 0.8.26.
The bundle is not self-contained: compiler/npm/forge-std downloads need independent
integrity and supply-chain review. Do not supply a real wallet to local rehearsals.

From the extracted `source` directory, after reviewing each command:

```sh
bash scripts/install-deps.sh
bash scripts/verify.sh
python3 scripts/rehearse-keeper.py --offline --output /review/keeper-rehearsal.json
python3 scripts/validate-production-config.py --config config/production.example.json
```

The example validation MUST remain blocked. Local/fixture tests do not qualify
real pools, independent USD feeds, routes, VRF, RPCs, authorities or OpenSea.
Current OpenSea qualification requires explicit mint_integration_version 1 and
production_qualification_supported true in addition to all gate checks and actual
independent review. Legacy consistency-only profiles cannot qualify production.
The vault_direct_v1 mint surface does not establish OpenSea primary compatibility.
`rehearse-keeper.py` starts its own disposable loopback chain and temporary
encrypted signer; it never uses the existing operator's chain or wallet.

Then follow docs/PRODUCTION_PREFLIGHT.md, docs/KEEPER_REHEARSALS.md,
docs/SECURITY_AUDIT_PLAN.md and docs/RELEASE_CHECKLIST.md for exact-configuration
market, target-chain and real-host evidence. No public transaction, deployment,
service action, sealing, or authority appointment is authorized by this export.
Use reviewed separate deployments for any later authorized rehearsal. Preserve
source/configuration/tool hashes, complete logs, explicit substitutes and failures.
Historical evidence is not rebased onto this commit by copying it into a folder.

The independent auditor must review custody/governance trust, shared LP/rewards,
royalty cohorts, price bounds, native reserves, external dependencies, recovery,
same-chain handoff and cross-component operation. Record findings, remediation
and independent sign-off separately. Integrated bridges and post-halt ownership
recovery are deferred; source-chain external custody is not a guaranteed return.

Remaining inputs: actual independently approved dual feeds and cheaper conversion
routes, supported randomness, public authority wallets, exact OpenSea product and
settlement compatibility, qualified RPC/API/keeper hosting, native wallet and
operating/restore rehearsals, published artwork, independent audit and release
approval. The included Todo is the snapshot's source of tasks, not a new checklist.
