# Verification scope and reproduction

Baseline `da24f65e6e10e5e0185cb0a0b229944f803b58b2`. New implementation changes
exactly six existing production source files. Defaults, compiler profile, financial
caps, token identity, rights, authority and existing environments are preserved.

| Record | What it establishes |
| --- | --- |
| [Plan](PLAN.md) | Targeted fix, invariant/mask matrix, permitted work and primary references. |
| [Build attempts](build/ATTEMPTS.json) | Four actual changed-source normal compiles. Failed1–3 retain their exact inputs/hashes; final4 passes all48 original runtime/initcode gates. No unchanged-suite run. |
| [Normal source manifest](build/source-manifest.json) | Exact raw100-source compiler closure,61production sources and original settings. |
| [Bytecode equivalence](build/EQUIVALENCE.json) | Oracle/Vault/Strategy runtime template executable bodies equal the prior accepted output after metadata stripping. Constructor immutables/deployed pins remain separate; Oracle creation changes through its Pricing child. |
| [Methods](UNIT_METHODS.json) |25 unique new passes+3 adapted passes across34 invocations. Six earlier new-fixture failures retained; no unchanged test method rerun. |
| [Callback proof](CALLBACK_TRACE_REVIEW.json) | Nine actual callback frames return success and log completion before later production rejection. Source/artifact/frame indices and rollback scope are explicit. |
| [Actual gas/transactions](GAS_AND_TRANSACTIONS.json) | Three current manual CLI reviews/receipts, exact calldata/original floors/mask, integer25% padding and receipt gas. The complete park→recovery journey adds one park receipt. |
| [Static review](static-review.json) |565 complete dispositions,113 individually current+452 exact referenced-source reuses. Internal/non-independent scope; accepted complexity/time/operating risks remain. |
| [Function reference review](FUNCTION_REFERENCE_REVIEW.json) | Existing ABIs and1009 examples preserved; three fixed-helper methods added. New reference/source snapshot hashes require new reviews. |

The new methods execute against real current Access/sealing, mint2/V10 and actual
v4 core/periphery. The local Registry admission seam, token/feeds, VRF/Permit2,
synthetic depth and bounded cohorts are explicit fixture dependencies. Local gas
and successful exact quotes are not real-market or complete target-fee acceptance.

Current source was compiled and run only for affected/new tests. The old
ManualRecoveryQualification methods that asserted self-rejection were deliberately
adapted; historical bytes/evidence remain archived. Other old methods, including
the unchanged D0 method, and Python/browser suites were not rerun. Inspection
found no further maintained test that intentionally expected this defect.

The nine callback negatives exclude helper failure selectors. They first establish
same-request success without mutation and a genuine independent mutation, then
prove the actual callback completes and production rejects. The post-own-swap
disagreement case also changes an independent market; it is not claimed to isolate
own-swap-only disagreement. That unchanged Oracle validation remains covered by
the exact-source/runtime-body reuse and current proof boundaries.

Use the [manual source procedure](../../docs/MANUAL_LP_PREPARATION.md#local-manual-recovery-rehearsal)
for the fresh owned-node wrapper. The old `rehearse-manual-recovery.py` and its
rejection expectations are explicitly historical; current acceptance uses
`scripts/rehearse-manual-reference.py` with source-pinned exports and artifacts.
No existing RPC target or private key is accepted. Original prepared/submitted
review expiry is never extended; a separately selected fresh intent precedes
preparation and preserves its own provenance.

The current function reference was frozen before actual CLI capture; saved reviews
retain those original bytes. Exact code/runtime proof is distinct from the
offline Catalog's legacy family label. Public signer/configuration, services,
sites, existing Anvil and journals are unchanged. Historical RPC unavailable is
recorded explicitly; no old live state-root equality is inferred.

Completion checks cover ledger/reference consistency, new links/anchors, exact
owned publication blobs/import closure and protected-file hashes. They are
mechanical checks, not additional EVM tests, public qualification or CI pass claims.

## Inspect original evidence without replaying transactions

The [core archive](public-evidence.zip) contains all four complete actual
transaction captures/call trees plus explicitly derived producer cases and wire
slices. The [unit archive](unit-evidence.zip) contains all28 complete original
accepted Forge JSON results, both compiled fixture artifacts, three source stages,
branch-equivalence records and the full non-code read-wire transcript. ZIP-LZMA
retains exact original bytes; it is read without extraction. Manifests identify
derivatives and originals separately.

From the repository root, choose new output filenames:

```text
python reports/manual-reference-swap-fix-20261115/verify_reference_evidence.py --repository . --output NEW_REFERENCE_RESULT.json
python reports/manual-reference-swap-fix-20261115/verify_unit_evidence.py --output NEW_UNIT_RESULT.json
```

These standalone checkers require assertions enabled, validate bounded archive
paths/sizes/hashes and use recorded responses only. They cannot start a node,
submit a transaction or run a test method. Root verification of the published
copies reconciles4receipts,28full unit files,9callbacks and4wire groups.

The actual manual wire records contain three successful full24M-cap calls and
one exact padded-gas call per manual operation; the park management record has
three full-cap and three padded calls. Both manual snapshot stages report the
same estimate/padding; this is not a claim that each stage made a padded call.
See [independent receipt review](ACTUAL_RECEIPT_REVIEW.json).

The [core manifest](EVIDENCE_MANIFEST.json), [unit manifest](UNIT_MANIFEST.json),
[core bundle hash](BUNDLE.json), [unit bundle hash](UNIT_BUNDLE.json),
[original capture manifest](RAW_CAPTURE_MANIFEST.json),
[original test results](FINAL_TESTS.json) and recorded offline verification
outputs retain exact source/attempt provenance. Larger raw compiler/RPC duplicates
remain at the external evidence directory recorded in [preservation](PRESERVATION.json);
they are not silently relabelled as public extracts.
