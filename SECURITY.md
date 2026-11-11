# Security and release status

PoPL is an **undeployed development candidate; production NOT APPROVED**.
Publishing source or passing scoped checks does not approve real funds.

- [Current security model](docs/SECURITY.md) and [seven-workstream audit plan](docs/SECURITY_AUDIT_PLAN.md).
- [Current review and remaining decisions](reports/whole-project-review-20261111/REVIEW.md)
  and [source-scoped historical evidence](reports/README.md).
- [Strict static-review selection](scripts/check-slither-review.py): its default
  must match the current source. Historical finding counts are not a fresh audit.
- [Sole security Todo](TODO.md#security--audit), [release approval](docs/RELEASE_CHECKLIST.md),
  [operator response](docs/OPERATOR_MANUAL.md) and [historical evidence index](reports/README.md).

Holders cannot withdraw LP principal during ordinary operation. Direct governance
can configure bounded policy, move/park both LP legs, or irreversibly return
principal to NFT holders. There is no external custody-address exit or bridge.
Paused governance emergency maintenance can bypass selected financial guards,
so governance remains trusted with potential trading losses. Sealed core code
cannot be patched in place; compatible pre-exit same-chain replacement is a
separate authenticated process. Permanent chain loss has no implemented recovery.

Actual dependencies, independent prices/routes, randomness, authorities,
marketplace/services/operations and independent audit/remediation remain open.
Never commit keys, credentialed RPC URLs, passwords or keystores. No dedicated
private security-reporting channel is configured; arrange a private channel with
the repository owner before sending exploit details or sensitive information.
