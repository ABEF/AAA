# Verification scope

**221 distinct affected methods pass:** 129 backend, 67 keeper and 25 tooling.
These are deduplicated scoped results, including 66 new methods, not a fresh
whole-suite or published CI run. No selected methods skipped. Linux/systemd,
target-chain operations and independent release qualification remain open.
[Exact results and source pins](verification-summary.json).

## Executed checks

- Backend: final indexer 47, mint 14 and reservation 68 receipts.
- Keeper: the final 67-method campaign covers the prior 65 distinct methods plus
  two new same-height checkpoint identity controls. Earlier 62/23-method receipts
  remain preserved at their original pins; their overlap is not added.
- Tooling: 10 runner, 10 profile and five inert Bash-wrapper methods. Fake compiler
  commands in wrapper tests do not count as real builds or Solidity execution.
- The two existing [scaffold/composition controls](scaffold-check.json) were
  rechecked after adding the flat null example field. They overlap the backend
  scope and add no unique methods.
- The [full Python inventory](python-inventory-summary.json) imports selected
  modules but runs no test bodies. Its selected count is not a pass count.

Before-fix controls reproduce lost confirmation depth, changed ancestry at a
reused cursor, regressing timestamps, sold-out status contradictions, missing
reservation evidence, nested availability errors and keeper checkpoint/JSON
faults. Independent review also reproduced changed hash/time after entry checkpoint
validation at the same height, then verified rejection before any paid-state save.
Methods and subcases are counted separately. The runner's initial new-API
tests errored before implementation; they are not all old-behavior witnesses.
The actual controlled discovery counterexample selected four cases before the
repair versus two locally defined cases afterwards, without running test bodies.

Four existing physical fixture methods failed in five assertions against both
the before and after implementation: their manually changed physical/reference
side metadata contradicted their intended positive scenario. Only those fixture
values were corrected; financial gates were retained. The failed 66-method run,
intermediate 123/125 scopes and original receipts remain external at their pins.
A Windows temporary-file fixture error and prototype version-substring problem
were also retained and corrected. Version controls reject 1.4.40, 11.4.4 and
unreviewed suffixes. Intermediate successful runs are not added to coverage.

## Local tool inspection and exact reuse

Actual local Forge metadata reads accept the normal profile and reject an
actual `FOUNDRY_FUZZ_RUNS=1` child with a safe setting-specific diagnostic. These
inspect `--version` and `config` only; they do not compile, execute tests, contact
an RPC or authenticate a potentially compromised compiler/host.

All 78 closed production/dependency sources and compiler inputs match the prior
build 011. Its 39 normal runtime/initcode gates are reused at exact hashes.
No Solidity, static-analysis or fork suite was rerun. Manager initcode headroom
remains 37 bytes; constructor/cold target gas and compiler qualification stay open.

The four original dirty files and 2,289 previously tracked report files preserve
their bytes. The report index is intentionally updated. Protected signing and
local-service code is unchanged. Before sources, failures, selected receipts and
independent challenges remain in the external `operational-reliability-20261029`
directory; each owning report retains its scope. No service/site/Anvil rollout,
public signing, deployment, sealing or production approval occurred.
