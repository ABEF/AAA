# Frozen review package for auditors and rehearsal operators

`scripts/prepare-release-review.py` exports an explicit committed candidate for
independent review and reproduction. It is offline and read-only: it does not
start services, access a wallet, install dependencies, run tests, or approve a
release. It preserves the existing Anvil, browser journals and paused monitoring.

## Create and independently verify

Choose the **exact 40-character lowercase commit**, not a moving branch name.
Use an existing output directory outside this repository:

```sh
python3 scripts/prepare-release-review.py create --commit EXACT_COMMIT --output /review/popl-EXACT_COMMIT.zip
python3 scripts/prepare-release-review.py verify --bundle /review/popl-EXACT_COMMIT.zip --expected-sha256 TRUSTED_SHA256
```

The creator prints the archive hash and exact source commit/tree. Give the
auditor that hash through an independently authenticated channel. A hash detects
changes; it is not an identity signature or approval. Keep the original output
and hash immutable. An existing output is never replaced. Repeating an export of
the same commit with the same exporter produces identical ZIP bytes; the export
does not include timestamps, installed binaries or working-tree changes.

The verifier reads the archive without extracting or executing it. It requires
the expected SHA-256 and checks every file's SHA-256, Git blob identity, mode,
size and canonical path. It rejects extra/missing/duplicate members, case clashes,
symlinks, compression, unsafe portable paths, modified dependency records,
forged approval flags, appended data and oversized input. Maximums are 2,048
members, 8 MiB per member and 64 MiB expanded. The source tree ID records the
original Git tree; the archive deliberately excludes other tracked files and
is not a replacement for authenticating the commit against the trusted remote.

## Contents and limitations

`source/` contains allowlisted committed contract, test, backend, keeper,
indexer, tooling and workflow files, operator Markdown, the central Todo and
dependency/compiler inputs. `manifest.json` binds each file. `HANDOFF.md` gives
the exact existing verification/rehearsal entry points and external release gaps.
The original Todo is a frozen task snapshot; this creates no second task ledger.
The manifest separately inventories each excluded committed path and its reason;
it includes no excluded file contents. Untracked paths are not inventoried.
The exact artwork catalogue/generator inputs, static analyzer configuration and
fixed Keccak test vectors are included. The fixed vector JSON under `reports/`
is a required test fixture, not a copied historical qualification report.
The two exact callable-reference JSON inputs and generated Markdown are also
included. If their generator is present, omitting any of those frozen inputs
blocks export; unrelated/private documentation JSON remains outside the allowlist.

Local/untracked drafts, historical reports, `.git`, environment files, memories,
private/live configuration, runtime state and dependency directories are excluded.
Test fixtures may contain **public disposable test identities**. A filename
allowlist and private-key-marker check cannot prove all committed prose is free
of accidentally embedded secrets: review the proposed contents before sharing.
The tool never scans or exports untracked files to find additional inputs.

Dependencies are **not bundled**. The manifest includes the exact Foundry
profile, npm direct versions and integrity pins, forge-std commit and any Git
submodule commit records. Follow the committed `scripts/install-deps.sh`, whose
`npm ci --ignore-scripts` and exact forge-std checks remain mandatory. Independently
qualify tool binaries and fetched transitive packages. This is not an offline
self-contained build or supply-chain attestation. A future repository dependency
layout needs corresponding exporter review, not silent omission.

## Rehearsal and independent audit

On an isolated unprivileged Ubuntu host, inspect `HANDOFF.md` and the scripts
before running them. `scripts/verify.sh` reproduces the frozen candidate's normal
checks; failures and obsolete fixtures remain findings, never automatic passes.
`scripts/rehearse-keeper.py` uses its own disposable loopback Anvil and encrypted
signer. That test-only venue exercises recovery mechanics; it does not qualify
the current native production deployment or real markets and services.

For real operating evidence use the [native inventory procedure](PRODUCTION_PREFLIGHT.md)
and [staging/service scenarios](KEEPER_REHEARSALS.md). Record exact tools, source,
network, configuration, dependency pins, original logs, failures, substitutes,
single-signer fencing, alert delivery and off-host restore. A blocked example
inventory is an expected result; do not fill unknown addresses or mark a service
qualified to force a passing gate.

The current OpenSea release profile must explicitly set `mint_integration_version: 1`.
A gate report must state `production_qualification_supported: true` as well as
passing every applicable check. Legacy consistency-only reports do not qualify
production; neither result substitutes for actual independent review or approval.
The existing `vault_direct_v1` mint surface does not establish OpenSea primary
mint compatibility. Do not relabel it as a supported marketplace integration.

The independent reviewer receives this package, the exact deployment/configuration
inventory when available, original source-scoped evidence and the [audit workstreams](SECURITY_AUDIT_PLAN.md).
Record findings and remediation against the frozen commit. Changed source needs
affected review and a new export; historical tests retain their real scope.
Approval still requires a named independent reviewer and the separate
[release record](RELEASE_CHECKLIST.md). The export cannot appoint authorities,
qualify feeds/routes/VRF/OpenSea, authorize public signing or replace an external audit.
