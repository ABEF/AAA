# Frozen PoPL review inputs - NOT APPROVED

Source commit: `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`. Schema 2 contains committed source, tests, tooling,
public operator documentation, locked dependency inputs and the original task
ledger. Working-tree changes, local context/memory instructions, runtime state,
wallet keys, private RPC configuration, historical test reports, deployed
runtimes and installed dependencies are excluded. Consult the manifest's exact
included/excluded paths. An unpublished candidate is not exported by naming its
parent commit, and an archive never upgrades an older source profile.

Verify the archive against its SHA-256 received over a trusted separate channel.
After verification, inspect the committed README and docs before running tools
on an isolated unprivileged Unix host with Python 3.11+, Foundry 1.4.4 and
Solidity 0.8.26. Compiler/npm/forge-std downloads require separate integrity and
supply-chain review; this bundle is not self-contained. Never supply a real
wallet or reuse an installed service, chain, journal or signer for a rehearsal.

After reviewing the exact frozen scripts, source checks may use:

```sh
bash scripts/install-deps.sh
bash scripts/verify.sh
```

Choose the inventory from this commit's documented contract profile. For the
current schema6/accounting4/custody3/same-chain holder-exit V5 source, use its
explicit current example rather than config/production.example.json:

```sh
python3 scripts/validate-production-config.py --config config/production.holder-exit.example.json
```

The example MUST remain blocked; consistency is not release qualification.
An older archive without this current profile remains historical. Use its
documented explicit historical inspection mode, never relabel its addresses,
codecs, journals or evidence to satisfy the current gate. This archive executes
no tests and approves no service, deployment or transaction.

Current principal inputs and LP pools are native ETH plus one fixed deployment
ZZZ. Governance may irreversibly close all LP and allocate actual ETH+ZZZ to
current NFT owners, including pending compound. Principal return is separate
from earned rewards, reserves and future royalties. No external custody exit,
integrated bridge or post-exit canonical replacement is implemented. Compatible
same-chain canonical replacement before terminal exit remains a separate flow.

Where present in the frozen source, confirmation2 requires physical LP and the
configured independent reference to exit on the same side, with sampled900/300
settings and selected240-second service checks. This is not uninterrupted price
history or source-independence qualification. Manual emergency1 is a separate
paused governance operation; explicitly bypassed financial guards can permit
near-total principal loss. It is not a keeper fallback or ordinary user flow.
Preserve the actual versions and governed bounds in the frozen commit.

Follow docs/PRODUCTION_PREFLIGHT.md, docs/KEEPER_REHEARSALS.md,
docs/SECURITY_AUDIT_PLAN.md, docs/RELEASE_CHECKLIST.md and the applicable operator
procedures. Qualify actual dual feeds, pools/routes, VRF, authorities, hosting,
gas, recovery and artwork separately. Current direct mint is not qualified
OpenSea primary-drop integration. Public signing remains disabled and the local
browser signer remains Anvil-only. No public transaction, deployment, sealing,
service/site rollout, journal repair, Anvil reset or monitor restart is
authorized by export or verification.

Retain source/configuration/tool hashes, original failures, explicit substitutes
and scoped evidence. Independent audit/remediation and release approval remain
required. The included Todo is the committed task snapshot; inventories and
internal test counts do not establish absence of vulnerabilities.
