# Actual static analysis and complete strict review

Actual Slither0.11.6/crytic-compile0.4.2 ran against the accepted closed normal
compiler output for this follow-up. The analyzer reused all100 compiled sources
through a fresh build-info directory; it did not invoke another compiler.
All61 production Solidity sources and the toolchain/config source bracket were
unchanged during analysis.

The analyzer emitted **570 records**. Five contexts received individual current
source review;565 retain unique exact prior fingerprints with every
description-referenced LF source unchanged. No changed context was automatically
accepted. These are detector-review counts, not tests or vulnerabilities proved
absent. Independent audit remains false.

## Five current contexts

| Detector/context | Current assessment |
| --- | --- |
| `reentrancy-balance`: post-entry-swap Vault harvest retains incumbent share supply | False positive. Actual activation/increase hold the Vault mutex through join; old supply intentionally remains the denominator while incumbent fees settle and NAV/marginal LP are verified. This run reordered two nested call leaves; the changed exact fingerprint was reviewed rather than silently normalized. |
| `uninitialized-local`: `Access.bind.known` | False positive. The local bool has Solidity's false default, is set only by a supported-ID match and otherwise causes rejection; bootstrap/pre-seal/code/parent/one-time-slot checks remain. |
| `events-maths`: `Access.canonicalTransition` | Informational observability limit. Immutable coordinator authority, lifecycle locks, its lifecycle events, pinned state reads and NFT invalidation remain; no dedicated state-valued Access event is claimed. |
| `missing-inheritance`: NFT and `ILifecycleMetadata` | Informational. Exact structural callback ABI is implemented with existing caller restrictions; nominal inheritance would not add those restrictions. |
| `missing-inheritance`: NFT and new `IArtworkRootBinding` | Informational. Exact external view string getter exists. The new bootstrap-only seal check uses STATICCALL, rejects empty/failed roots before irreversible sealing and does not grant callback mutation or custody authority. Remote content availability is not proved. |

Full exact descriptions, referenced-source pins, rationales and source review
points are in [STATIC_REASSESSMENTS.json](STATIC_REASSESSMENTS.json).
Every reused record is traceable in
[STATIC_REUSE_PROOF.json](STATIC_REUSE_PROOF.json) and retains its prior scope.

## Strict input and executable check

[static-review.json](static-review.json) is the new full strict review, and
[static-input.json.gz](static-input.json.gz) retains all570 actual detector
descriptions and classifications. Only supporting element/AST/compilation
metadata is omitted from that projection; raw analyzer output remains in the
supporting evidence. Ordered fingerprints equal the raw analyzer input.

Both raw actual output and the complete projection pass the strict checker.
The checker default points to this new review, and its actual CLI passes with
that default. The existing default-review unit method reads the default
dynamically, so no test pointer edit or unchanged-suite rerun was necessary.
See [STATIC_RESULT.json](STATIC_RESULT.json) and
[STATIC_CLI_CHECK.json](STATIC_CLI_CHECK.json).

Slither's Windows detector-present exit was **4294967295**, preserved verbatim.
It is not called exit0. Analyzer JSON reports success with no analyzer error;
source integrity and complete strict coverage are checked independently. The
strict checker itself exits0.

The reproducible driver was copied byte-identically from the prior accepted
metadata static driver. Its isolated environment excludes credentials, uses
offline Foundry configuration and retains command/tool/build/source hashes.
No deployment, signing, service/site, existing-chain or journal operation occurs.

Accepted trust assumptions and prior detector risks remain visible. This source
analysis does not qualify actual feeds/routes/market depth, provider capacity,
complete fees, maximum-state operations, contract wallets, content availability
or independent security approval.
