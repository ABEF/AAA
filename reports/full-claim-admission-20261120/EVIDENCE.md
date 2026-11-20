# Evidence locations and offline reproduction

No command below starts a node, signs, deploys or sends a transaction. Extract
only into a new empty directory. Original absolute capture paths inside records
are provenance; they are not permission to overwrite that location.

- [Qualified stages](evidence/qualified-stages.tar.xz) and its [file manifest](evidence/MANIFEST.json)
  preserve original normal construction/configuration, requests, state export,
  receipts and exact-state continuation bytes. Every member was independently
  streamed back and matched its original SHA256. Only regular relative files
  are present, without links. The archive is26,121,920bytes.
- [Full ordered setup wire](native-wire/attempt02.json.xz) and its
  [transcode proof](native-wire/attempt02-TRANSCODE.json) losslessly preserve
  all94,335 original observations, including repeated runtime checks. The exact
  expanded1,568,472,867bytes match the independently verified original gzip.
  The352,968,569-byte original gzip stays external, unchanged.
- The duplicate original `attempt02/CAMPAIGN_RESULT.json` is omitted from the
  tar because its byte-identical `qualification/qualification.json` is present.
  Omitted originals and hashes are explicit in the manifest.
- [Initial normal verification](verification/NORMAL_ADMISSION.json),
  [eight rejection controls](verification/NORMAL_CORRUPTION_CONTROLS.json),
  [late-case verification](LATE_TAX_VERIFICATION_FINAL.json),
  [ordered clock supplement](CLOCK_WIRE_SUPPLEMENT.json) and
  [focused test receipt](FOCUSED_TESTS.json) retain distinct scopes. Do not add
  their overlapping checks into a new EVM test count.
- [Failed-attempt index](failed-attempts/INDEX.json) preserves original paths,
  hashes and selected small records. Complete failed captures remain external;
  they are not passes or inputs silently substituted into successful records.

From the repository root, after extracting the standard tar.xz to `NEW`:

```text
python reports/full-claim-admission-20261120/tools/verify_admission.py NEW/attempt02 --wire reports/full-claim-admission-20261120/native-wire/attempt02.json.xz --output NEW/normal-check.json
python reports/full-claim-admission-20261120/tools/verify_late_tax.py NEW/late-tax32-03 NEW/late-tax32-04 --output NEW/late-check.json
python reports/full-claim-admission-20261120/tools/verify_clock_wire.py NEW/late-tax32-03 NEW/late-tax32-04 --output NEW/clock-check.json
```

Use a matching supported Python environment and exact committed source/artifacts.
Each output path must be unused. The first reader streams the large original
wire; it does not load1.5GB into the API or raise a production resource limit.
It explicitly loads the trusted archived6d5 planner for the original normal
stage, then restores the current module. The late reader separately binds old
6d5 refusal and current7a3 positive records. No old deployment or journal is
relabeled as a new profile.

The current graph/source/currency/clock/provider seams and remaining release
requirements are explained in [the review](REVIEW.md). Offline reproduction is
not another actual transaction or production approval.
