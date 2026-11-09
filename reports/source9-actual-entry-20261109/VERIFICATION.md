# Verification boundary

Baseline contract checkout: `949422e4b227f66ec661b2e6c3d00c5bdc303f3c`.
Website baseline: `b8d871b769117fd3b375811fb34a64ae93847663`.
Current source hashes and actual transaction/DTO/state evidence are recorded in
this directory's campaign manifest. No production Solidity changed.

## Distinct verification scopes

| Scope | Evidence |
| --- | --- |
| Fixed-ZZZ admission | 15fresh7 methods; separately15checkpoint2 API methods. Includes rejection of missing/wrong/malformed identity and no invented Registry getter. |
| Actual trace and helper | 20methods:8literal trace/strict epoch cases plus12API boundary/configuration methods. The12 include the earlier9; do not add them again. |
| Activation gas2 | 10new focused methods and94existing affected methods in disjoint modules. Defaults, canonical gas identity, bounds, headroom, fee and balance failures remain explicit. |
| Owned-fork orchestration | 11deployment/funding recovery methods,6fork-cache methods and6typed consumer-runner methods. Earlier6deployment and4runner stages overlap, so are not added. |
| Offline reconciliation | 5focused verifier controls and the final closed-artifact campaign check. Re-extracting/rechecking the bundle is a consistency check, not another EVM execution. |
| Website | 108focused source9 methods. A broader970-test attempt had969passes and one permission failure while creating a new isolated build; its separately authorized7-method integration rerun passed. This is not970fresh first-attempt passes. |
| Actual EVM pipeline | Four successful contributions, two exact ZZZ approvals, confirmed state/metadata witnesses, four typed unsigned rejection cases, expired-review simulation and one deliberately reverted stronger-floor transaction. These are not added to unit-test counts. |

Full local evidence root:
`C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/fresh-entry3-rehearsal-20261109-949422e`.
It retains failed attempts, exact fork hashes, transactions/receipts, traces,
configuration pins, source closure hashes, index/WAL files and original docs.
Selected immutable records are published alongside this report; no secret key,
password, keystore or credentialed endpoint belongs in either set.

Download/extract [campaign-evidence.zip](campaign-evidence.zip) into a new local
directory and run `scripts/check-source9-rehearsal-evidence.py --campaign DIR
--inputs DIR/evidence-plan.json --output NEW_JSON`. It performs no RPC or
transactions. The [campaign manifest](campaign-manifest.json) pins every bundled
file and the unchanged [production source closure](production-source-reuse.json).
Use a short extraction directory on Windows. The retained first extraction
attempt exceeded Windows path length; a shorter-path extraction and offline
verification passed without changing any evidence bytes or executing transactions.

The successful cases use synthetic external depth and controlled feed/VRF
fixtures described in [the review](REVIEW.md). The unmodified-depth rejection is
retained separately. Report checks, source equality and offline reconciliation
do not establish provider honesty, public gas cost, uptime, exhaustive coverage
or independent production approval.
