# Whole-project coverage and evidence depth

Baseline contract781fcc9, websitee5bb216; all current source edits are itemized
in [the review](REVIEW.md). [Understanding](UNDERSTANDING.md) was established
before drafting, with [primary knowledge](KNOWLEDGE.md) and [two prompt
challenges](PROMPT_REVIEW.md). The frozen brief's service300-second schedule was
later explicitly changed by the user to240; on-chain900/300 remains unchanged.

| Area | Actual review depth | New/reused evidence and remaining limit |
| --- | --- | --- |
| Architecture/authority/lifecycle | All33concrete components/46Solidity sources reconstructed; guards/setup/seal and cross-module paths traced. | [Contract partition](CONTRACTS.md), [detailed ledger](coverage.json). Not every individual callable body newly audited. Trusted governance/approved successor/dependency powers remain. |
| Entry/shares/principal/NAV | Original budget, independent bounds, marginal LP, incumbent NAV, rounding, callbacks, same-pair custody and terminal returns traced. | Exact matching earlier217-method EVM/39normal-size scope reused; no blanket current production proof. Exact constructor/maximal gas and actual feeds/routes remain open. |
| Fee/royalty/claim/history | Actual20-unit split/dust/fractions, membership/cohorts, claim side effects, conversion, transfers and backing traced; real SQLite reader corruption repaired. | Seven new stored-integrity methods plus21affected existing history/API/lineage/earnings methods; one method is an original unpublished local draft, retained and not staged. Not authentic provider/log-completeness proof. |
| LP/strategy/manipulation | Physical ranges, post-close bounded quotes/zero-one swap, multiple floors, timing/reset/jitter/compound/harvest/buyback interactions traced. | Exact unchanged affected EVM proof reused; fresh keeper240 transition evidence. No claim of profitable-attack absence, uninterrupted observation, optimal route or healthy operating economics. |
| Whole-collection and holder exit | All six row domains, cutoff/settlement/export/funding/abort/commit/multi-hop and current-owner payouts deeply traced; lifetime work quantified. | Five exact current-source composition methods pass. Unchanged217scope contains none of those canonical suites. Full Cartesian maximum gas, broken-asset/escrow/provider and host rehearsals remain open. |
| Keeper/recovery/observability | Main pending/nonce/spend/receipt/atomic state, fairness, reset, watchdog, health and operations traced. Metadata restart bug fixed. |23new and17affected existing methods; inert process-loss fixture, not real Linux kill/fencing/backup acceptance. Secondary historical CLI inventory is not full body coverage. |
| Indexer/financial data | Ingestion/ancestry/reorg transaction/strict header and raw-event storage/read/replay paths traced; malformed stored data now unavailable. | Narrow changed-reader regression, exact scoped earlier source evidence where applicable. Coherent dishonest provider/DB and real backup/history completeness remain external. |
| API/unsigned/ingress | Required lifecycle/bindings, snapshots, optional metric faults, ownership inventory, preparation, admission/process limits traced. | Seven new ownership-inventory methods; concrete limits/calls in [frontend review](FRONTEND.md). Real hosting, provider latency and100-user capacity not established. |
| Website/wallet/assets | All16feature families and complete receipt/account/chain/session/approval/card-total paths source-traced with actual profiles separate. | Source/read-only asset scan and12temp-copy metadata scenarios. Generator patch unapplied;696dormant examples stale0. No real browser/visual/extension/marketplace acceptance or fresh4 integration. |
| Build/CI/dependencies | Exact profiles/lockfiles/local-only deployment/size gates and actual runner selections traced. Selection/fork wiring repaired. |13new inventory/static-CI methods included in23, not extra counts. AST-only77-source compiler screen; explicit lowering/applicability and independent release sign-off still needed. GitHub/download/live fork unrun. |
| Documentation/management/release | Current operator instructions, sole ledger, evidence references and environment distinctions reconciled. | Links/Todo/function-reference/source preservation checks, exact pins and publication identities recorded separately. Source publication is not rollout or production approval. |

## Inventory is not proof

The callable ledger contains711entries:665functions,33constructors,13receivers.
Its217critical-path entries are recorded as cross-module traces;494remaining
individual-body entries explicitly retain pending/unreviewed depth. This is a
broad whole-project pass, not completion of exhaustive independent per-function
analysis. Static22scenario groups are not execution counts. Dedicated output
annotations remain absent for122ABI output positions; some meanings are in
purpose notes, and no missing semantics was guessed. Keep this distinction in
the existing independent-audit/integration tasks.

All eight full journeys in the brief have component/state/authority/failure
traces. Real provider, marketplace, wallet extension, escrow and installed-host
segments remain blocked/unverified rather than represented by successful mocks.
No excluded role/bridge/custody or new economic policy is introduced to fill a
matrix. User-requested observation during cooldown is a proposed future change.
