# Frozen reviewer and operating-rehearsal inputs

## What improved

Added an executable, offline exporter/verifier instead of another release
checklist. `scripts/prepare-release-review.py` reads an explicit 40-character
commit through Git object reads with replacement objects disabled. It never
copies dirty working-tree contents or untracked local state. The deterministic
ZIP carries the original central Todo, operator guides, source/tests, compiler
and dependency-installation inputs, exact commit/tree, per-file Git/SHA-256
identities and an excluded-path inventory. It supplies an auditor or isolated
Ubuntu rehearsal operator with one frozen source package.

The verifier requires an independently obtained expected archive hash. It checks
canonical paths/modes/order/bytes, member and expanded-size bounds, dependency
pins, complete listed members and explicit NOT APPROVED/no-test status. It
rejects duplicate keys/members, case aliases, path traversal/Windows ambiguity,
symlinks, compression, extra/missing/changed files and trailing payload. Output
publication is atomic/exclusive and cannot replace an earlier review package.

Required artwork catalogue/generator inputs, the static analyzer configuration
and fixed Keccak vectors are explicitly included; the vector JSON is a test
fixture, not a historical approval report. Missing consumer fixtures block export.
Dependencies, installed binaries and historical evidence are not bundled or
qualified. The exact locked installer and any Git submodule pins are included;
missing pins/metadata or credential-bearing dependency URLs fail export. Public
disposable test identities may exist in tests. This tool is not a secret audit,
a commit-authentication service or a substitute for reviewing contents before
sharing them.

## Verification performed

- **19 distinct affected Python methods pass across the recorded scopes.** They exercise malformed/adversarial
  archives, exact identities, omitted pins, unlisted files, hash mismatches,
  excluded paths, fixed deterministic bytes and atomic no-overwrite publication.
- An initial 14-method run had 13 passes and one test-builder error caused by
  mutating the original ZipInfo before reading it. Only that fixture was repaired;
  its case passed. Dependency/exclusion checks were subsequently added and the
  affected 17-method suite rerun after the archive schema changed. Final fixture
  admission added one new guard case; only its three affected cases were rerun,
  all passing. Repeated cases are not counted again; no final full repository
  regression is claimed.
- The final callable-reference consumer adds two exact JSON inputs and generated
  Markdown to the review package. Its required-input guard and allowlist were
  checked with only two affected cases (one new), both passing. The earlier
  baseline ZIP is unchanged and does not contain the later reference generator.
- Actual Git export of the **earlier baseline**
  `ac98b5bab417dc813a2533f4e1e5c6dfcc95dda0`: 386 source files and 1,381 excluded
  committed paths. Separate CLI verification, repeat-export determinism, wrong
  hash rejection and immutable existing output passed. A known unrelated dirty
  document was compared: the archive contains the committed blob, not the draft.
- Baseline archive SHA-256:
  `30d1ecfb70a121d6c9630270489757cb2ff42d083e441c30b89fa3bb203a81d3`.
  The ZIP is external to Git. It is **not** the final release package and does not
  contain this pass's later changes. Regenerate against the final publication
  commit when choosing a candidate for external review.

[Machine-readable scope and hashes](verification.json) bind the final tool,
wrapper, tests and [operator guide](../../../docs/FROZEN_REVIEW_BUNDLE.md).
No unchanged Solidity/backend/historical suites were rerun for this exporter.

## Remaining gates

Actual native target-chain and Ubuntu service rehearsals still require reviewed
deployments/configuration, supported independent feeds/routes/VRF, approved public
authority wallets, marketplace integration and real operating providers. The
current marketplace profile requires `mint_integration_version: 1` and
`production_qualification_supported: true`; legacy consistency-only reports do
not qualify production. Direct Vault mint compatibility cannot stand in for
OpenSea primary mint support. Even a consistent current profile is not approval.

The existing keeper rehearsal is an isolated ABI/transaction-recovery fixture,
not real Uniswap/native operations. The package gives exact existing commands
and limits; it does not run a multi-day soak, verify off-host alarms, replace a
server, recover lost production keys, hire an auditor or perform an independent
audit. Those need actual dated evidence and named independent sign-off.

No public transaction/signing, wallet/private key access, deployment, service
action, website build, Anvil/NFT/LP/balance/journal change or monitoring restart
occurred. Public DEPLOYMENT remains null, signer Anvil-only; production remains
**NOT APPROVED**.
