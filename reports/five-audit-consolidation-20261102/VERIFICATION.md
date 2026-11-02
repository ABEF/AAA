# Verification and historical evidence boundaries

Baseline main `c6fb1907787af289f5b25c6f8ea6d5cdd38c8cd6`, November 2, 2026.
[Findings](REVIEW.md), [dispositions](findings.json),
[executions](test-verification.json), [method identities](method-ledger.json),
[artifact integrity](evidence-integrity.json).

## Fresh checks and preserved failures

| Stage | Actual result |
| --- | --- |
| New health-admission negatives | Three new methods produced 47 failed assertions/subcases against the original implementation, zero errors/skips. The health-command case demonstrates an actual false-green result, not merely a different diagnostic. Original log retained. |
| Affected profile/confirmation checks | 67 methods pass, including the three new regressions, current/historical profile checks, confirmation evidence and policy/report cases. An initial selection also named two nonexistent test modules: those two loader errors executed no bodies and are not counted as passes. |
| Existing health/operations/telemetry checks | 52 methods executed: 50 pass and two existing fixture cases fail. Both failures reproduce with the original saved health body in a separate process, establishing they were not introduced by the admission fix. |
| Corrected existing cases | Both targeted methods pass after fixture-only corrections. The policy-change race now isolates compound eligibility, proves gas estimation and the changed policy were reached, and checks the precise pre-signing capability-refusal error. Its strengthened assertion has one additional targeted pass, not another distinct method. |
| Final identity accounting | 119 distinct affected methods reach success across these stages; no final skip is counted as success. This is not a single final 119-method execution, a full keeper suite or published CI. Other earlier test campaigns are not added to this count. |

The tests use inert read providers and temporary files. Production change is
limited to `keeper/health.py`; the Keeper/signing/nonce/receipt code is unchanged.
The corrected delayed-receipt case preserves canonical checkpoint ordering rather
than relaxing its guard. The telemetry race deliberately isolates unrelated
compound eligibility, so it is not claimed as full compound-flow verification.
No actual public RPC/provider/transaction, service process or Solidity test ran.

## Reconciliation and unchanged Solidity reuse

All 85 artifact entries in the five original report-local manifests match their
hashes. Both historical manifest formats (`files` and `artifacts`) are checked;
empty/unknown inventories fail rather than passing vacuously. All 10 explicitly
listed external evidence files are present and match. All 90 historical files and
four protected unrelated dirty files retain their baseline bytes.

This proves integrity of those recorded artifacts, not correctness of every
historical assertion or present applicability of old source pins. Source5
callables, 42 gates and 463 static contexts are historical. The current policy6
normal build remains exact: all 83 input contents (52 production sources and 31
dependencies) match `normal-final-0a0cac9f06` byte for byte. Initial scratch reuse
checking mistakenly normalized three CRLF source files when comparing them to
raw compiler strings; that failed attempt is retained. The corrected checker
compares UTF-8 raw bytes and confirms equality. No source was changed to pass.

The 43 normal runtime/initcode gates are reused, not rebuilt. Compiler/settings,
current 37-contract/826-function reference and production source remain unchanged;
Vault/Budget/Migration runtime margins remain 635/237/20 bytes at those pins.
The strict current static-review checker accepts the existing 471-context Slither
record at current source pins. No new analyzer execution or clean-analyzer claim
is made. The callable-reference checker verifies current generated data without
recompilation. Exact deployment arguments, chain gas and populated operating
economics remain unqualified.

## Documentation, publication and preservation

The single central ledger retains its task IDs/statuses; three existing acceptance
records link this reconciliation, health fix and open routing issue. Generated
Todo, callable reference, changed Markdown links/anchors, whitespace and exact
staged Python publication closure are checked separately from method execution.
The final [checks](final-checks.json) and [artifact manifest](artifact-manifest.json)
record those results. Git publication is separate from deployment and approval.

Current instructions/context/handoff, README, feature/evidence, roadmap, release
record, report navigation and the operator/recovery procedures are synchronized.
Original report families are unchanged; no old deployments, websites, Anvil,
NFT/LP balances, journals, signers, services or paused heartbeat are altered.

External originals, raw attempts, logs and helper scripts are retained at:
`C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/five-audit-consolidation-20261102`.

## Limits

The grouped disposition matrix is not exhaustive new function-level coverage.
It reconciles the five selected audits and their material open boundaries against
current source. A stored health file cannot authenticate an operator/provider or
prove running-code identity. The strengthened admission is diagnostic, not new
financial enforcement or deployment qualification. Route-candidate viability,
actual feeds/routes/VRF/authorities, source6 site/service rollout, OpenSea/storage,
maximum gas/timing/recovery/market rehearsal and independent audit/remediation
remain open. Production is **NOT APPROVED**.
