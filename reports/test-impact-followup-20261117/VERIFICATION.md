# Verification and source scope

Baseline main `fdb7562bf56b11d8bade612fdaf7f9a54daf118a`.

## Source review versus finite execution

The baseline map has37 changed test roots/63 exposed files/666 declared
methods. LP, rights and tool maps overlap. These counts are navigation and
source assessment, not new passes or full branch coverage.

| Selection | Observed verification |
| --- | --- |
| Python tools |11 distinct affected methods:8 new and3 corrected management cases. The late-reorg failure and healthy control before the fix are retained. |
| Actual v4 |3 strengthened methods: intended dependency failure, real custody rollback/healthy retry and exact both-leg fee/reserve/claim conservation. |
| Rights/accounting |2 new multi-action sequences with current-owner payouts, terminal return/future royalties and last-recipient mixed-batch rollback/recovery. |
| LP fixture descendants |13 distinct methods:5 new,4 corrected existing and4 previously unexecuted affected Portfolio cases. Four failed discovery stages are retained. |

No previous passing execution is counted again because it appears in two maps.
The royalty test rename is not a new pass. Initial compiler-only failures,
failed expectations and source-stage differences remain explicit.

[SELECTED_CHECKS.json](SELECTED_CHECKS.json) deduplicates **29 distinct successful
methods** across these selections. They retain their actual source stages;
subcases, callbacks and imported method declarations are not extra passes.

## Authoritative detailed records

- [Tool impact](TOOL_IMPACT.json) and [tool review](TOOLS_REVIEW.md).
- [Physical v4 metadata/source proof](PHYSICAL_VERIFICATION.json),
  [raw methods](PHYSICAL_RAW.json) and
  [compiled test artifact](PHYSICAL_ARTIFACT.json.gz).
- [Rights source proof/results](RIGHTS_VERIFICATION.json) and
  [rights review](RIGHTS_REVIEW.md).
- [LP affected-method map](LP_AFFECTED_METHODS.json).
- [LP source review](LP_PRODUCTION_PATH_REVIEW.md) and
  [exact finite results](LP_EXECUTION_RESULT.json).

The physical selection's entire195-source compiler graph matches its metadata;
all repository files in that graph are stable before/after. Three unrelated
test-file edits during compilation are retained as global drift, not hidden or
used to rerun the successful cases. Rights/tool observations carry their own
source brackets and controlled dependency limits.

## Build, maintenance and publication

All61 production Solidity sources and the accepted100-source normal-build
closure remain byte-identical. The previous normal48size gates and strict573
static-record review retain their original source/evidence; there is no new
normal/compiler/static/full-suite claim. Actual pinned Forge version/config
validation is metadata-only and passes under the existing normal profile.

Final reference/Todo checks, local link targets, exact production/protected-file
hashes are in [COMPLETION.json](COMPLETION.json); the
[retained raw-observation manifest](RETAINED_OBSERVATIONS.json) authenticates
successes, failures and drivers. Staged/committed Python closure is checked
separately at publication. No service,
signing, public RPC, existing chain or deployment/sealing action occurred.
