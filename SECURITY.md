# Security and release status

ZZZ Protocol v0.2 is an uncompiled implementation candidate with a source-level self-review. It is not independently audited or approved for real-fund deployment.

Permanent custody makes implementation and configuration mistakes particularly difficult to recover from. Publishing this repository does not close any release gate.

- [Security model and intended invariants](docs/SECURITY.md)
- [Source-level self-review, findings, and open risks](docs/AUDIT.md)
- [Mandatory release checklist](docs/RELEASE_CHECKLIST.md)
- [Component implementation status](docs/COMPONENT_STATUS.md)
- [Historical verification evidence](reports/README.md)
- [Publication verification](reports/PUBLICATION_CHECKS.json)

Do not place private keys, RPC credentials, signer passwords, or keystores in this repository. The deployment template is local-only and does not enable deposits.

No dedicated security reporting channel has been established. Avoid posting exploit details or sensitive data in public issues; arrange a private channel with the repository owner before disclosing them.
