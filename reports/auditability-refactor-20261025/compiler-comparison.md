# Saved compiler comparison

This compares saved normal compiler outputs; no compiler or tests were rerun.

- Common project objects: **101**. Wire ABI checks pass: **True**; recursive storage checks pass: **True**.
- Current source hashes match the candidate compilation: **True**.
- All **37** recomputed normal runtime/initcode object gates pass: **True**.

Only converter struct-owner metadata and identical duplicate ABI error entries are normalized. Names, tuple members, events, indexing, errors and mutability otherwise remain exact.

## Explicit ABI metadata exceptions

- `ZZZActivationEntry`: baseline struct-owner paths=0; candidate identical error duplicates=1. Normalized ABI equal: True.
- `ZZZLPRewardConverter`: baseline struct-owner paths=3; candidate identical error duplicates=1. Normalized ABI equal: True.
- `ZZZRoyaltyConverter`: baseline struct-owner paths=3; candidate identical error duplicates=1. Normalized ABI equal: True.

## Size changes

| Object | Runtime delta | Creation delta | Current runtime / margin |
| --- | ---: | ---: | ---: |
| ZZZActivationEntry | -29 | -29 | 17956 / 6620 |
| ZZZCanonicalHandoff | +139 | +139 | 21034 / 3542 |
| ZZZLPRewardConverter | -122 | -150 | 16830 / 7746 |
| ZZZLiquidityManager | -344 | -365 | 20769 / 3807 |
| ZZZPoolRegistry | +0 | -29 | 10269 / 14307 |
| ZZZRoyaltyConverter | -122 | -139 | 16830 / 7746 |
| ZZZV3VenueValidation | new | new | 62 / 24514 |

## Executable comparison

- `ZZZVault` metadata-stripped creation/runtime equal: **False / True**.
- `ZZZMigration` metadata-stripped creation/runtime equal: **False / True**.
- `ZZZCanonicalHandoff` metadata-stripped creation/runtime equal: **False / False**.

Terminal stripping leaves embedded child metadata in creation objects. The
separate [known-metadata comparison](embedded-metadata-comparison.json) identifies
two complete compiler metadata regions in each Vault/Migration creation object.
Masking only those recorded metadata bytes makes their creation objects equal.
Handoff still differs after metadata masking; its +139 bytes are not reported as
a metadata-only change.

Vault and Migration naming changes are distinguished from Handoff named-constant code generation. Any unequal executable output is reported honestly; ABI/storage equality is not a formal behavioral-equivalence proof.

The separate [readability comparison](readability-body-comparison.json) records
53 Vault, 26 Migration and 25 Handoff bodies. Tokens match after only explicit
private/local identifier aliases, the exact 20 private numeric constants and
reviewed formatting wrappers. These are static comparisons, not executed tests
or formal equivalence proofs.

NFT creation has dynamic URI arguments; exact final ABI-encoded arguments still need qualification. The internal v3 library adds one compiler object, not a new externally linked execution dependency or a production deployment.

See `compiler-comparison.json` for every object, normalization exception, hash and gate. Actual execution tests and their source scope are recorded separately. Production remains NOT APPROVED.
