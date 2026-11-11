# Verification scope — project review

This records the local source candidate on main over contract base
`0acb123c9dd71cc9424667c4531d4e9fd40a7df4` and website base
`2c6f0c822b909a8d44c457c2fd24d3f546745ba8`. It is not release approval.
The [review](REVIEW.md) separates corrections, retained compatibility and decisions.

## Contract evidence

- The [normal compiler input](evidence/contracts/normal-final-ea7e55d22b/compiler-input.json.gz)
  closes60project/99total sources under pinned0.8.26/Cancun and the existing
  via-IR optimizer. The [actual compiler output](evidence/contracts/normal-final-ea7e55d22b/compiler-output.json.gz),
  [producer](evidence/contracts/normal-final-ea7e55d22b/START.json) and
  [48normal size gates](evidence/contracts/normal-final-ea7e55d22b/production-size-gates.json)
  pass without higher limits. Vault remains24544bytes:32bytes of runtime headroom.
- [Before/after comparison](evidence/contracts/normal-comparison-final.json)
  verifies all48concrete ABIs and175shared semantic storage layouts unchanged.
  A removed private unused interface changes its own ABI, so **all interfaces**
  are not falsely reported identical. Four deployed runtime bodies shrink by
 3413bytes combined. Compiler objects are not a proof of behavioral equivalence.
- [52distinct accepted EVM methods](evidence/contracts/VERIFICATION-SUMMARY.json)
  comprise [30final affected synthetic fixture tests](evidence/contracts/focused-final-c71604bf5a/VERIFICATION.json)
  plus22earlier passing Native/Membership/metadata methods with exact unchanged
  current import closures. Nine overlapping earlier contribution successes are
  not counted twice. Current and original project/test snapshots are retained
  alongside each stage; third-party hashes are in its START record.
- [Initial seven failures and traces](evidence/contracts/focused-6cdccb71d2/original-seven-failure-traces.txt.gz),
  [zero-match first selector failure](evidence/contracts/focused-6cdccb71d2/VERIFICATION.json)
  and the [canonicalV8 fixture failure](evidence/contracts/focused-fb8c0ee384/VERIFICATION.json)
  remain visible. Only explicitly corrected fixtures and later accepted source
  stages count. Native mock admission is test-only, not production qualification.
- [Source coverage](evidence/contracts/COVERAGE.json) and
  [findings](evidence/contracts/FINDINGS.md) record review scope and unresolved
  strategy/market risks. No new actual-core two-leg/multi-day campaign was run.

## Backend and keeper evidence

- [Final117backend methods](evidence/backend/final-backend-117.json),
  [log](evidence/backend/final-backend-117.log):21codec,13indexer startup,
 81affected consumer and2checkpoint-source-drift checks, deduplicated,0skips.
  They bind final `zzz_ops/abi.py` SHA256
  `154d92685b6e473bd064880ec15a16a9b8aafa0b9104df671538cf1375a7250d`.
  [Negative/final subclass checks](evidence/backend/abi-subclass-negative.json)
  preserve the extra rejection found during review. These use injected/local
  fixtures, not live providers or databases.
- [Keeper final summary](evidence/keeper/final-summary.json) maps370distinct
  affected passing methods and2host skips across exact source-scoped stages.
  The skips require Cast or Unix ownership behavior unavailable on this host.
  It binds monitor SHA256
  `54f0abd903462e30caeb2649e14d07679600db7bb6a378ca86ff85f1dc03ecbc`.
  These stages used the preceding codec (`33c5e1…`), before the final narrowing
  rejecting custom string subclasses; ordinary supported typed inputs are
  unchanged, and that final narrowing is separately covered by all117backend
  methods above. No final927-method keeper rerun is claimed.
- [Final submission consumers](evidence/keeper/final-submit-consumers.json),
  [incident fixture correction](evidence/keeper/confirmation-fixture-final.json)
  and [restored-selector checks](evidence/keeper/inventory-final.json) retain
  exact selected/executed IDs and source pins. Five late-budget and three
  simulation-output regressions overlap root runs and are counted once.
  [Initial broad nonpass](evidence/keeper/keeper-existing-first.json),
  [strict-output negative](evidence/keeper/simulation-negative-corrected-fixture.json)
  and the source-drift-marked inventory stage are retained, not promoted to
  current passes. Historical pending/receipt fixtures retain their old calldata.

## Website, static and documentation evidence

- [Website verification](evidence/frontend/VERIFICATION.json) and
  [scope](evidence/frontend/REVIEW.md):86affected demo/domain/concurrency/display
  methods plus2module-graph checks pass. Six new demo cases are included in86;
  two packaging cases are separate. Eight syntax checks are not extra tests.
  Both packaging regressions reproduce before/after; the demo pre-fix5fail/1pass
  run was tool-observed without a retained original producer log and is explicitly
  not presented as equivalent saved negative evidence.
- Legacy seed/mixed replay hashes, shared signer and both null public configs
  are preserved. Existing Anvil profiles, dist overlays, journals and served
  sites were not changed. No full unchanged website/wallet suite was repeated.
- Actual offline [Slither execution](static/EXECUTION.json), raw
  [output](static/slither.json.gz) and [log](static/slither.log) use the final
  normal compiler output, without recompilation/disabled detectors. The
  [strict review](static-review.json) covers541records:45individually reassessed
  contexts and496unique exact fingerprint plus all description-referenced
  unchanged-source reuse. [Coverage](static/review-coverage.json) and
  [artifact hashes](static/artifact-sha256.json) retain provenance. The expected
  findings/Windows nonzero analyzer exit is not called an analyzer-clean run;
  acceptance is the successful strict current-source review check.
- [98focused documentation/tool methods](evidence/documentation-tests.json)
  pass with0skips/source drift. [Generated/source gates](evidence/document-gates.json)
  pass:40contracts,913functions,40constructors,13receive hooks,966explicit
  operator examples,0coverage gaps; sole Todo consistency and60-source checks.
  They do not simulate operator templates or authorize transactions.

## Preservation and limits

The [task-start inventory](evidence/inventory.json) records750current text files;
the [start record](evidence/START.json) pins original dirty/protected sources and
archived originals. Inventory coverage is not execution or exhaustive line review.
The [packaging manifest](evidence/manifest.json) binds decoded and stored evidence
hashes. Gzip files retain exact original JSON/text bytes; tar snapshots exclude
caches and installed dependencies. Absolute local paths inside original records
are producer provenance, not deployable configuration or live service locations.

Earlier9November spot-adapter evidence retains its original source scope and
bytes. The four unrelated dirty files remain untouched/unpublished. No private
key, password, credentialed endpoint or keystore belongs in this evidence.
Current references must adopt new runtime/source pins through reviewed builds;
old deployments/checkpoints/journals are never relabeled. Checkpoint rebuilding
applies when the optional checkpoint reader is enabled with the new backend.

No public transaction, sealing, deployed runtime update, site/service restart,
wallet signer extension, Anvil reset or paused-heartbeat restart was performed.
No fresh live market/provider/OpenSea/VRF, sustained uptime, target gas, archive
recovery, broad user-load or independent audit acceptance is implied. Exact
publication/HEAD checks are separate from these test results.
