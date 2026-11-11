# Individual review: evidence, frontend and metadata

Baseline `6cfa4f1d478c3d15470519801f9703f9f8a8d656`. This part of the
remaining271review individually addresses **87assigned original records**. It
does not duplicate the39previously reassessed records or claim the other184
were reviewed here. Production remains **NOT APPROVED**.

Every assigned original record was read, including its recorded source/failure
subclaims and remaining acceptance requirements. [FINDINGS.json](FINDINGS.json)
contains exactly87individual assessments, split implementation/boundary claims,
actions, original JSON pointers/hashes and concrete current code/report/guide
locations. It references106distinct evidence files; this counts references,
not106whole-file line-by-line audits or executed contracts. Historic scope-only
and publication rows remain historical evidence rather than invented new bugs.

Contract repository evidence explicitly declared at the baseline comes from
that exact Git blob. Website evidence uses main
`e1d698868d32572bc5f04b3f683d2919234f5f19`. The new generator correction is
explicitly a later working candidate with a separate raw hash. None of its bytes
are represented as already present at the baseline. Original reports are not
edited or assigned newer test results. Private chats, credentials and unrelated
untracked drafts are not review inputs.

## Implemented improvement

**EF-01: offline artwork catalogue admission remained ambiguous.** The source
generator used default JSON parsing and Python numeric equality. A read-only
before probe accepted duplicate keys, nonfinite values, boolean palette masks,
boolean/float packed-code equivalents and a zero-color mask. Zero masks could
emit a palette without a valid primary color. This was an offline artifact
validation defect; no deployed financial exploit or new authority is claimed.

The generator now rejects duplicate keys, NaN/Infinity and exponent overflow,
requires exact integer nonempty byte masks and exact integer packed-code lists.
Finite irrelevant metadata remains allowed. Hash/supply/range/code agreement
checks remain. No artwork, catalogue or Solidity library was regenerated.

[Generator evidence](GENERATOR_ADMISSION.json) preserves original acceptance
and distinguishes verification stages. Five distinct focused methods ran:
four new methods and one affected valid-input control. Later stages overlap;
seven invocations are not seven distinct methods. Ordinary and Python `-O`
inputs are checked. A stronger finite-metadata control verifies that only the
raw catalogue-fingerprint comment changes; the generated library body remains
exact. Final valid generation equals the existing library SHA-256
`3be3048d60b601b35aa17affd822be78da4f40e70a6c9368cdff0cfa81d26606`.
The prior five unchanged test methods and broad library/contract suites were
not repeated. No compiler/runtime/ABI/economic change follows from the parser fix.

## Material reconciliation results

- Historical wallet fixes remain local/profile-scoped. Current source10 is
  unsigned; no shared signer/public configuration is broadened. Actual extension,
  wallet/provider and hosted rollout acceptance remain separate work.
- Dormant intrinsic royalty traits remain1/2/3, distinct from zero preactivation
  economic entitlement. Existing metadata/cursor/receipt proofs do not guarantee
  permanent hosting, marketplace cache updates or live VRF.
- Current supply-stop reporting and mint2 source integration supersede old
  “OpenSea unimplemented” statements, while actual onboarding/fee/payer/stage/
  eligibility/VRF acceptance remains open.
- Current40contract/956function/1009call-row and48normal-object/567static-context
  evidence must not be replaced by historical33/696or52source/43gate/471records.
  Bytecode and constructor margins are exact-source measurements, not current
  market/target-gas approval.
- Evidence output reservation, strict configuration admission, deduplicated test
  inventories, normal settings and frozen schema3exports remain implemented.
  Historical schema1/2instructions and old failures remain immutable. No
  evidence-only row is promoted into fresh execution or independent approval.
- Root was notified of remaining maintained `AUDIT_FINDINGS` old-profile,
  old-“current” size/static and reuse wording. Those owning-guide corrections
  are separate from unchanged original report records.

## Verification and limits

`verify.py` checks87unique remaining-row IDs, exact original matrix/pointer
provenance, task references, source revision/raw-byte hashes and matching lines.
It uses explicit exceptions, so Python `-O` does not disable integrity gates.
These checks are provenance checks, not additional financial or security tests.

No old Solidity/keeper/browser test campaign was rerun. No website/source asset
rollout, signer change, public transaction, deployment, service restart,
Anvil/journal mutation or paused-heartbeat restart occurred. Actual independent
sources/market depth, target workload/gas, authority/provider selection,
OpenSea/VRF, immutable hosting, operating recovery and independent audit remain
in their existing owning tasks.
