# Security and release status

PoPL is an **undeployed development candidate; production NOT APPROVED**.
Publishing source or passing scoped checks does not approve real funds.

- [Current security model](docs/SECURITY.md) and [seven-workstream audit plan](docs/SECURITY_AUDIT_PLAN.md).
- [Latest backend fee-integrity review](reports/backend-remediation-20261026/REVIEW.md)
  and [source-scoped full audit](reports/full-audit-20261025/REVIEW.md).
- [Current internal static dispositions](reports/production/slither-review.json):
  actual399findings/47bindings, internal coverage PASS; not independent audit.
- [Sole security Todo](TODO.md#security--audit), [release approval](docs/RELEASE_CHECKLIST.md),
  [operator response](docs/OPERATOR_MANUAL.md) and [historical evidence index](reports/README.md).

Holders cannot redeem LP principal. Direct governance can immediately change
supported policy and approve trusted external custody; no timelock notice or
forced custodian return is promised. Sealed implementations cannot be patched
in place. External custody does not migrate NFT ownership/reward accounting,
and permanent chain loss has no implemented canonical recovery.

Actual dependencies, independent prices/routes, randomness, authorities,
marketplace/services/operations and independent audit/remediation remain open.
Never commit keys, credentialed RPC URLs, passwords or keystores. No dedicated
private security-reporting channel is configured; arrange a private channel with
the repository owner before sending exploit details or sensitive information.
