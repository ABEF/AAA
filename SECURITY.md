# Security and release status

ZZZ Protocol is a compiled, tested development candidate with an internal source review. It is not independently audited or approved for real-fund deployment. Current source-bound evidence is in [release hardening](reports/release-hardening/README.md) and [internal static analysis](reports/release-hardening/static-analysis/README.md). The [Implemented / Todo checklist](docs/IMPLEMENTATION_STATUS.md) separates source features from remaining integration and release work. Earlier artwork/alignment/readiness reports preserve their historical scope.

Permanent custody makes implementation and configuration mistakes particularly difficult to recover from. Publishing this repository does not close any release gate.

- [Security model and intended invariants](docs/SECURITY.md)
- [Historical source-level self-review](docs/AUDIT.md)
- [Current static-analysis findings and individual dispositions](reports/production/slither-review.json)
- [Mandatory release checklist](docs/RELEASE_CHECKLIST.md)
- [Component implementation status](docs/COMPONENT_STATUS.md)
- [Historical verification evidence](reports/README.md)
- [Publication verification](reports/PUBLICATION_CHECKS.json)

Do not place private keys, RPC credentials, signer passwords, or keystores in this repository. The deployment template is local-only and does not enable deposits.

No dedicated security reporting channel has been established. Avoid posting exploit details or sensitive data in public issues; arrange a private channel with the repository owner before disclosing them.
