# Whole-project audit execution

Reviewed2026-10-29. Contract baseline main2feee92f plus the saved intentional
confirmation2/emergency1 candidate; website baseline maine5bb2163. The current
[canonical brief](../../docs/THIRD_PASS_AUDIT_PROMPT.md) now covers the entire
project. Understanding preceded drafting; two separate challenges corrected
coverage and six source-specific factual mistakes before implementation.
[Understanding](UNDERSTANDING.md), [prompt review](PROMPT_REVIEW.md),
[coverage](COVERAGE.md) and [verification](VERIFICATION.md) distinguish actual
reads, execution, reuse and unresolved qualification. **Production NOT APPROVED.**

## Implemented repairs

| Area | Confirmed defect and correction | Practical boundary |
| --- | --- | --- |
| Keeper scheduling | Optional conversion/buyback/metadata work could consume a renewal deadline; unrelated degraded work could stretch240-second checks to480seconds. Existing confirmation renewals/resets now take deadline priority after pending recovery and common authorization. Unrelated optional degradation keeps its telemetry without stretching a known window. Regressing primary/secondary clocks invalidate evidence before optional work. | No timer/cap/permission relaxation, new nonce lane or journal rewrite. True global failures still back off. Cold windows retain ordinary fairness. |
| History provenance | Contradictory transaction-index/hash groups could enter confirmed ingestion and stored earnings replay. A shared ordered-transaction validator rejects duplicate/conflicting indices and hash reentry before commit/projection. | Numeric gaps and absent optional historical indices remain valid. This checks consistency, not completeness or honesty of an RPC/database. |
| Final observation | A final head retreat could remove required confirmation depth while retaining the anchor. Observer finish now rechecks final head/depth/chronology as well as anchor/genesis/chain. | Current and historical read-only observers inherit the check. Actual finality/provider guarantees remain unqualified. |
| Transaction gas evidence | A legacy/type1 receipt could report an effective gas price different from signed gasPrice and still be accepted by shared read-only observation. Contradictions now reject in both directions. | Missing/ambiguous evidence remains unavailable; dynamic-fee behavior and signing are preserved. |
| Durable/config JSON | Duplicate fields and nonfinite/overflowing floats could silently change effective configuration or durable intent/spend state. Shared JSON reads now reject these; writes reject nonfinite values before replacing old state. Keeper CLI uses that reader before construction. | Valid historical journal bytes and missing-file defaults retain their meaning. No state reset/migration or new signer capability. |
| Selected-pool reproducer | The documented observer accepted duplicate JSON fields and impossible sqrtPrice/tick combinations. It now uses strict shared JSON and exact TickMath validation, including valid downward-boundary ticks. | Mocked read-only transport verification; no new public RPC qualification. |
| Release review bundle | Default handoff instructions still described historical configuration/bridge/external custody behavior. New schema2 instructions describe the current fixed-token/holder-return candidate. | Existing schema1 archives still verify and retain their exact old template/bytes. Excluding repository memory files remains deliberate. |
| Artwork upload tooling | XML processing instructions were discarded before inspection; XML base, encoded DTDs, CSS escapes/styles and incomplete animation bans could contradict self-contained static artwork. Parser-level and approved-format checks now reject them. Duplicate/nonfinite catalogue/manifest/reference JSON also rejects. | Approved2784SVGs pass with unchanged hashes. This is format/resource validation, not proof of arbitrary browser sanitization or an IPFS pin. |
| Artwork reference semantics | Downloadable dormant examples encoded royalty trait0 and the preview described weight changing at activation. Generator,2784reference descriptions and696dormant numerical traits now keep fixed rarity1/2/3 separate from activation eligibility. | Images, manifest, effective example accounting, on-chain ledgers, signer and null public configs unchanged. No site rollout.72historical metadata files remain untouched. |
| Catalogue admission | Runtime safety assertions could disappear under Python-O, admitting invalid catalogue supply/hash/code. Explicit checks now reject with optimization enabled; valid Solidity output is unchanged. | Offline generation only; no production library or image regenerated. |
| Callable documentation |122output positions lacked dedicated explanations. Source-reviewed notes now explain units, unset/default meaning, nested tuple fields and authority/identity limitations. | Existing notes retained, exact ABI/source/build pins unchanged; documentation generation calls no contract. |

[Backend reasoning](BACKEND.md), [keeper reasoning](KEEPER.md),
[contract reasoning](CONTRACTS.md) and [tooling coverage](TOOLING.md) retain
negative controls, legitimate compatibility cases and scope limits. No newly
confirmed production-Solidity exploit was established; that is not a guarantee
of absence. Production Solidity/economic policy was not changed in this audit.

## Findings deliberately not changed

- Governance's explicit emergency financial bypass is accepted trust, not keeper
  permission. Masks can authorize near-total loss; structural exact custody,
  liabilities, canonical and terminal locks remain mandatory. Two new composed
  EVM methods test non-vacuous bypass success and retained-policy callback rollback.
- Raw rebalance priority can block compounding while reference disagreement
  blocks rebalancing. Switching to ready-only priority would let compounding
  bypass the intended price-confirmation policy. Keep this economic decision
  explicit rather than silently weakening it.
- Unrelated bucket share-inventory RPC failure must block affected execution
  without resetting valid physical/reference evidence. A proposed broader reset
  was rejected after checking the explicit existing policy/test.
- Strict300-second confirmed gaps, one serial pending lane, multiple custody
  windows and real confirmation latency can still prevent timely samples. The
  scheduler repair removes avoidable queue delay; it does not prove capacity.
  Old scheduling-only records may add bounded cooldown reads, without authority.
- Coherent dishonest prices/logs/databases, correlated USD sources, token issuer
  behavior and real liquidity/ordering economics require independent evidence.
  Consistency checks cannot authenticate them. More controls are not a substitute
  for actual market qualification.
- No passive inventory/40%trigger, observation-during-cooldown feature, bridge,
  custodian exit, new role, public signing, deployment or service change was added.

## Remaining release decisions

Actual independent feeds/reference venues, conversion routes/depth, VRF and
production authority addresses; OpenSea gross-price/drop compatibility; fresh4
website/API hosting and native transaction integration within approved signing
boundaries; real Linux/finality/gas/load/recovery/escrow rehearsals; immutable
artwork hosting/CID/marketplace refresh; exact constructor bytes; compiler
applicability sign-off; and independent audit/remediation remain open in the
[sole Todo](../../TODO.md). Minimum initcode margin is37bytes on Manager; do not
infer that arbitrary deployment arguments fit. No test gate was relaxed.
