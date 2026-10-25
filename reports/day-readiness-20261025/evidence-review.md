# Evidence importer and verification boundary review

This independently reviews the current reference/evidence tooling for the
25 October 2026 campaign. It does not execute a Solidity compiler, EVM, RPC,
financial transaction or operating service. The parent records Git ancestry,
equivalent compiler/gas measurements and the broader contract review separately.

## Confirmed defects and implemented corrections

**P2, high confidence: contradictory size success could qualify.**
`import_compiler` previously trusted `creation_ok/runtime_ok` after checking
reported lengths against bytecode. It did not independently enforce normal
limits. Disposable negative probes imported runtime 24,577 bytes, creation
49,153 bytes and creation 49,121 plus a 32-byte constructor despite success
flags. The importer now derives byte lengths directly, enforces EIP-170's
24,576 and EIP-3860's 49,152 limits, and derives constructor payload sizes
recursively from ABI scalars, tuples and arrays. Contradictory reported margins,
constructor types, static sizes and dynamic flags are rejected. Dynamic actual
arguments remain explicitly unqualified; the minimum encoding is not a proof
that a final chosen URI fits.

**P2, high confidence: contradictory compiler/freeze provenance was ignored.**
The current normal producer records raw input/output hashes, compiler exit,
source closure, source counts, before/after freeze and compiler identity.
The importer previously ignored these fields while accepting `all_pass:true`.
Probes supplied wrong input/output hashes, a failed exit, failed freeze and
open closure successfully. The importer now requires coherent exact fields,
compares declared hashes with the captured raw artifacts and rejects missing
or malformed settings/status metadata. Each JSON artifact is captured once
with a bounded MAX+1-byte read; hashes and parsing refer to those same bytes.
No report flags can override independently recomputed source or byte checks.

**P2, high confidence: stored snapshot completeness was not preserved.**
Removing one actual dependency hash from the stored schema-2 snapshot passed
`build_reference`; it had no separate closed source-name inventory. Removing
the stored compiler settings also passed. Schema **3** now retains the sorted
closed compiler source names, requires their exact union with project and
dependency hashes, requires settings and normal-limit metadata, and checks the
derived dynamic-constructor qualification list against ABI. Schema 2 fails
explicitly and must be regenerated from the existing saved matching artifacts.
The raw prior report is not edited or silently relabelled.

These fixes affect evidence import, generated snapshot format and documentation
validation. They do not change contract ABI, financial rules, permissions,
wallet signing policy or running services.

## Executed evidence and controls

- [Initial probes](evidence-negative-probes-initial.json): 15 isolated cases;
  four controls behaved correctly and 11 invalid cases were wrongly accepted.
  Valid evidence was accepted; missing output, source drift and malformed
  Boolean success were rejected. The exact invalid cases and source hashes
  are preserved, with disposable input copies outside Git.
- [Focused campaign](evidence-tests.json): all 28 affected methods pass at the
  first corrected source. This includes 20 existing methods and eight new
  regression methods, not 28 new behaviors.
- [Bounded-read follow-up](evidence-failed-recheck.json): one additional new
  MAX+1 read test and two affected JSON/CLI repeats pass after final I/O
  hardening. The historical filename is retained; this follow-up has no test
  failures. Total coverage is **29 distinct methods across two source scopes**,
  not a fresh 31-test or full final-source regression.
- Constructor tests include exact size boundaries, a fixed array that cannot
  be counted as one word, minimum dynamic encoding, and explicit unresolved
  actual arguments. CLI controls verify exit 1 and preservation of existing
  generated files on contradictory input.
- Actual saved current normal artifacts remain admissible without modification:
  44 project sources, 31 dependency sources, 31 concrete targets and six
  internal-only libraries. The current reference has 608 functions and no
  missing function/input explanations. NFT dynamic arguments require at least
  96 bytes and remain release-specific qualification.

## CI, static analysis and circularity

`scripts/verify.sh` runs the reference check before the actual pinned Forge build
and execution tests, with `set -euo pipefail`. A failed reference check returns
nonzero; it cannot turn into a green compile/test result. The importer executes
no repository-provided shell command and performs no network or signing action.

The documentation check establishes coherence of a **trusted saved compiler
capture**, current source/dependency/build bytes and reviewed explanations.
It does not authenticate an arbitrary compiler binary or prove that an
adversary who can rewrite every report, hash and snapshot actually ran tests.
Independent compiler/CI capture and review remain separate evidence. Adding
more self-referential hashes cannot eliminate that trust boundary.

`scripts/source_checks.py` labels its output consistency-only, with
`solidity_compiled:false` and `security_audit_pass:false`. Its delimiter/keyword
checks are not a substitute for parsing or security analysis.

The static-analysis workflow pins Slither and deletes the old analyzer output
before each invocation. `check-slither-review.py` requires the exact current
source/build inventory and hashes, exact reviewed findings and explicit
non-independent scope. The current saved review has **43** bound names versus
**47** currently required: 11 additions, seven retirements and 28 changed
retained contents. That old review cannot qualify current source. No fresh
Slither run or green published CI was claimed or performed in this subtask.

The dated deep-cleanup build driver is a campaign artifact with fixed output
paths. Do not rerun it into an existing evidence directory: it was not designed
as an append-only general operator service. A future reusable producer should
require a fresh attempt directory and preserve failed-attempt state. This
limitation does not affect the preserved successful capture or the production
CI's separate fresh compiler/analyzer execution.

## Remaining limits

Actual dynamic initcode arguments, maximal real gas, feeds/routes/VRF,
authorities, marketplace compatibility, target-chain operation and independent
audit remain separate release gates. Existing source profiles, journals,
Anvil state, signing restrictions and services are untouched. Production
remains **NOT APPROVED**.

## Final independent self-review

The final `function_reference.py` source is frozen at SHA-256
`f11052dacf9eb14654fd13478173a3e20bcf7213eed91d29d5b4e76a4db2e4d3`.
The follow-up reviewed the new diff, current importer call sites and recorded
results without another suite run. Recursive fixed/dynamic array and tuple
encoding, exact versus minimum constructor arguments, strict gate/count flags,
closed names, same-capture raw hashes and bounded reads were checked for
coherence. No additional successful bypass was identified in those new paths.
Schema-3 regeneration remains the parent's documented final workflow step;
this reviewer does not silently upgrade a stored schema-2 snapshot.

Two pre-existing, low-risk malformed-artifact strictness candidates were
reported to the parent: outer schema-1 equality accepts Boolean `true`, and
the legacy fixed/ufixed scalar pattern does not bound its bit/precision fields.
Valid output from the pinned compiler does not use either malformed shape.
They are not new financial or contract defects; no source change or extra
tests were made for them during this final static review. Their disposition
belongs in the parent review rather than being silently normalized away.

Compiler identity remains a binding to a trusted capture, not independent
authentication of an arbitrary report producer. Successful static documentation
validation cannot replace execution, current source-scoped static analysis,
real-service qualification or independent audit.

## Authorized strict-format addendum

After the preceding static review, the parent authorized both small format
corrections. The final source now requires an exact integer `1` for outer ABI
snapshots, explanation notes and merged-note schema fields; Boolean `true` and
floating-point `1.0` no longer qualify. Fixed/ufixed ABI widths must be 8 through
256 in multiples of eight, with decimal precision 1 through 80 and canonical
numeric spelling. Aliases and valid boundary forms remain supported, following
the [pinned Solidity 0.8.26 ABI specification](https://docs.soliditylang.org/en/v0.8.26/abi-spec.html#types).

[Original-failure evidence](format-tests-initial.json) runs the two new focused
methods against the preceding `f11052d` implementation: 16 invalid subcases
were accepted, with no test/environment errors. [Corrected evidence](format-tests-final.json)
runs those two methods plus one affected existing canonical-type control:
all three pass. No broad suite, Solidity compilation or EVM run was repeated.
The normal current reference `--check` also passes unchanged: 31 contracts,
608 functions, zero missing function/input explanations. Regeneration was not
required because the stricter parser leaves all valid current artifact values
and generated documentation unchanged.

Final source hashes:

- `zzz_ops/function_reference.py`:
  `ae2489961d0a104a0810799d82559bfae5d02a960e4514e4892897b707759dfd`.
- `tests_python/test_function_reference.py`:
  `9cea757d716f039a4bceb3b162709267def17ac2c9f800a582f6b328675a0d76`.

The earlier 29 distinct passing methods remain their original two-source
evidence; the two additional methods bring the total to **31 distinct methods
across three corrected source scopes**. The last source has three targeted
passes, not a fresh complete 31-method final-source run. These format changes
do not change production contracts or financial behavior.
