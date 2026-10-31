# Verification and limits

Baseline main `e4113b79526adec829c8b888b2ca7795fdf0008b`, October31 Europe/Paris.
[Findings](REVIEW.md), [executed prompt](PROMPT.md), [artifact manifest](artifact-manifest.json).

## Fresh affected evidence

| Check | Result and scope |
| --- | --- |
| Portfolio accounting |17/17 affected Solidity methods pass, including two new policy-restore and configured80%-main/residual/idle regressions. The fixture now exposes real source6 policy interfaces. No production source drift. Typed accounting fixtures are not live-market v4 qualification. |
| Backend/lineage/publication tests |67 distinct affected Python methods pass across scoped stages. The initial65 plus two later new checker methods are distinct; repeated correction checks are not added again. Original fixture failure and causal negative reproductions are retained. No final skips. |
| Git publication closure |Original HEAD fails at18 missing-import sites. The reviewed staged set contains278 Python files and passes with zero missing static imports. Local untracked files cannot satisfy this check. This does not prove dynamic imports or third-party installations. |
| Isolated staged runtime export |73 Python files compile;12 requested runtime modules import, loading41 project modules exclusively from indexed bytes with required tracked resources. Resource guards record zero socket/process/database/write attempts; no application constructors or RPC. This is importability, not service operation. |
| Current static analysis |Slither0.11.6 runs against exact final0a compiler artifacts without invoking compilation. JSON reports success and471 flags:74High/90Medium/211Low/75Informational/21Optimization. Finding exit4294967295 is retained, not called a clean analyzer pass. |
| Static disposition |383 complete normalized detector contexts and enclosing bodies match earlier scoped reviews;88 changed contexts, including23 High/Medium, receive explicit current review. The unchanged strict source/finding coverage checker passes with the new record. Its default pointer is updated and separately checked through the actual CLI; matching/coverage rules are unchanged. |

The initial Python-only isolated export omitted the tracked event-schema resource
and failed. That fixture attempt is preserved; the corrected full-resource export
does not hide a repository dependency failure. The accounting/source fixtures and
test bodies remain distinct from actual providers, hosts and chain deployments.
All82 exported runtime/resource files still match final staged bytes exactly;
the separately verified static-checker default is outside that runtime export.

The67 Python executions precede the sole later change to the static checker's
default review path. Their relevant backend/checker bodies remain unchanged;
the later pointer is verified by an actual default-argument CLI run, without
needlessly repeating those unrelated tests or claiming a new full-suite snapshot.

## Reused build and dependency evidence

Production Solidity remains unchanged. The final0a input/output,52 production
source files,31 dependency files, normal build settings and compiler identities
are rechecked against current raw bytes. The43 normal EIP170/EIP3860 gates are
reused; no new compilation or whole-suite run is invented. Solc0.8.26/Cancun/
viaIR/optimizer1/Yulfalse and normal limits remain unchanged.

Vault runtime margin635bytes, Budget237, Migration20 remain exact-source facts.
Real dynamic constructor arguments and target gas still require qualification.
Callable reference remains37contracts/826function rows/37constructors/14receivers.

The static environment verifies48 locked versions and2,823 hashed installed
RECORD entries. Five pre-existing shared documentation paths match another locked
package's metadata; zero runtime-file mismatches. Installed metadata is not fresh
attestation of original wheel archives, the host or a running service.

[Current source-bound static review](static-review.json),
[context/provenance triage](static-context-triage.json) and
[execution receipt](static-execution.json) retain explicit classifications,
accepted risks and scope. Reuse of an enclosing body is not proof that every
transitive callee is unchanged. These findings are heuristic flags, not471
confirmed vulnerabilities or an independent release approval.

## Evidence locations and preservation

External raw/archive roots under
`C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9`:

- `today-audit-20261031`: original baseline/docs/report hashes, policy-body
  coverage, raw static output/build-info, default checker result and final checks.
- `lp-accounting-audit-20261031`: original fixture, commands, pre/post pins,
  actual Forge JSON and17-method receipt.
- `backend-today-audit-20261031-5fd41a7b`: original lineage/publication failures,
  staged test receipts, exact Git source inventories and both isolated exports.
- `adaptable-policy-20261031/normal-final-0a0cac9f06`: unchanged compiler input,
  output and43 normal production gates reused here.

Compact receipts accompany this report. New evidence paths are exclusive; prior
failures and report bytes are not rewritten. Documentation/Todo/callable/link
checks and final preservation are recorded separately. No published CI success,
full regression, public signing, service/site/Anvil/journal change, broadcast,
deployment or sealing is claimed.
