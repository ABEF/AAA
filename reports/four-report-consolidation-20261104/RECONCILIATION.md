# Findings from the latest four audits against current source

Baseline main5107954. Selected by publication history, not filesystem dates:
manual safeguards5107954, confirmation0b14aca, market/lifecycle cf39b14 and
whole-project supplement44f5fa7. Original36report files remain byte-preserved.
This is finding provenance, not another task ledger or a fresh full-project audit.

| Original finding / topic | Current assessment | Source and evidence |
| --- | --- | --- |
| Whole-project N04-01: mutable caller start anchor | Corrected. Constructor snapshots and validates parent identity; ingestion/reconciliation use the captured value. New startup follow-up also prevents rejected identity from committing setup changes. | [Original finding](../comprehensive-audit-20261104/REVIEW.md), [Indexer](../../indexer/monitor.py), [anchor regressions](../../tests_python/test_indexer_anchor_integrity.py). |
| Whole-project N04-02: entire ownership history materialized | Corrected. Ownership replay streams a cursor and closes it in finally. CPU/history growth remains; streaming is not an incremental materialized ownership ledger or a lifetime benchmark. | [Original scope](../comprehensive-audit-20261104/VERIFICATION.md), [Indexer.nft_owners](../../indexer/monitor.py), same anchor/streaming regressions. |
| Whole-project N04-03: stale current-looking documentation | Prior README/site alignment retained. This pass additionally removes stale current custody4/schema9/Entry-conversion wording from relevant Todo acceptance criteria and consolidates duplicated audit summaries. Historical converter/wrapper/codecs remain where genuinely needed. | [Original finding](../comprehensive-audit-20261104/REVIEW.md), [sole ledger](../../docs/project-todo.json), [profile](../../docs/POSITION_V6.md), [environment map](../../docs/SITE_ENVIRONMENTS.md). |
| Market finding1: operator required wrong custody version | Corrected in maintained deployment/permission guidance; fresh custody5, not4. Existing older deployments/journals are not relabelled. | [Original](../market-lifecycle-20261104/REVIEW.md), [operator](../../docs/OPERATOR_MANUAL.md), [permissions](../../docs/ACCESS_PERMISSIONS.md). |
| Market finding2: model USD/reward-fraction rounding | Test-model corrections, not production accounting fixes. Sum each asset's principal components before USD rounding; keep individual/collective fractions separate. No new model regression inferred from consolidation. | [Original model failures/corrections](../market-lifecycle-20261104/VERIFICATION.md), [actual-core scenarios](../../test/OptionalPortfolioCore.t.sol). |
| Market finding3/4: composed assurance and no new proven Solidity defect | New cohort/one-two-one/royalty/exit model remains useful at its exact source/test scope. It does not establish all markets, optimized60/40, MEV safety or a full current suite. Later manual views changed; earlier whole-source equality wording is historical. | [Coverage](../market-lifecycle-20261104/COVERAGE.md), [latest manual source pins](../manual-safeguard-audit-20261104/production-size-gates.json). |
| Confirmation C1: saved deadlines ignored by outer sleep | Corrected in actual poll_delay/main monotonic wait. Healthy saved deadlines cap sleep and subtract elapsed work; local estimates never authorize a transaction. Pending/global failures retain their recovery policy. | [Original](../confirmation-audit-20261104/REVIEW.md), [keeper](../../keeper/monitor.py), [wakeup tests](../../tests_python/test_keeper_confirmation_wakeup.py). |
| Confirmation C2: queued incident clear depends on swap telemetry | Corrected. Known reset precedes router metadata. Global reviewed runtime/authority/nonce/lifecycle/cost checks remain; this intentionally is not dependency-free signing. | [Original](../confirmation-audit-20261104/REVIEW.md), [priority tests](../../tests_python/test_keeper_confirmation_priority.py), [coordination](../../docs/KEEPER_COORDINATION.md). |
| Manual correction1: sampled mask16 silently retains raw/cooldown1 | Corrected ONLY on emergency view. Budget separately applies selected bit1; ordinary ready retains its hard clock. Live condition/reference/sample/control validation still binds16. | [Original](../manual-safeguard-audit-20261104/REVIEW.md), [Confirmation](../../src/ZZZRebalanceConfirmation.sol), [Budget](../../src/ZZZMigrationBudget.sol), [focused regression](../../test/RebalanceConfirmation.t.sol). |
| Manual correction2: two zero raw close floors rejected | Corrected for paused governance park/residual close. Positive floors/current-core principal proof/actual receipts/custody/rights remain. It accepts actual asset composition and does not promise value preservation. | [Original](../manual-safeguard-audit-20261104/REVIEW.md), [validator](../../src/ZZZCustodyValidation.sol), [parking](../../docs/CUSTODY_PARKING.md), [force matrix](../manual-safeguard-audit-20261104/SAFEGUARD_MATRIX.md). |
| Manual correction3: callback regression targets old Manager recipient | Test fixture corrected to actual typed child, with callback, atomic rollback and successful no-callback control. Current bytecode/ABI identity remains distinct from advertised capability versions. | [Retained failure and corrected scope](../manual-safeguard-audit-20261104/VERIFICATION.md), [NativeVaultFlows](../../test/NativeVaultFlows.t.sol). |

## New improvements derived from the combined review

| ID / scope | Reproduced gap | Implemented correction |
| --- | --- | --- |
| FC4-01, low/service integrity | Startup could change journal mode/recreate indexes before rejecting another deployment identity; failed executescript DDL could leave partial schema. | Explicit BEGIN IMMEDIATE transaction for schema/index setup, identity check and initial cursor insertion. Roll back on mismatch/setup failure. WAL negotiation only follows valid committed identity. |
| FC4-02, low/resource recovery | Schema/WAL/insert failures could leave an opened SQLite connection unreleased. | Close on every exception after connection creation. Test real rejected startup and successful retry without touching an operating database. |
| FC4-03, low/config admission | Integer parsing accepted values that SQLite cannot bind, or whose cursor/LIMIT arithmetic cannot fit. Failure could occur after files opened/created. | Reject unsupported chain/start/reorg values before filesystem/connection work, with a fixed diagnostic. Existing actual network values/defaults unchanged. |
| FC4-04, low/storage readiness | WAL request result was ignored; a silent refusal could be treated as a healthy service. Unsafe current journal modes cannot support the intended startup rollback/durability. | Require durable rollback-capable starting mode and actual wal result. Reject OFF/MEMORY/unknown modes; close failed connection. No automatic policy weakening. |

These are configuration/service defects and hardening, not demonstrated remote
theft or changes to contracts, user shares, fee allocation or authority. See
[new tests](../../tests_python/test_indexer_startup_atomicity.py) and
[verification](VERIFICATION.md) for causal controls and actual execution scope.

## Still valid limits and remaining work

| Topic | Current consequence / owning work |
| --- | --- |
| Normal financial guards overlap on purpose | Per-swap, aggregate, caller, marginal LP and idle checks protect different moments/quantities. They are not added percentages. No new removal is justified by report consolidation. [Manual matrix](../manual-safeguard-audit-20261104/SAFEGUARD_MATRIX.md). |
| Emergency trust and destination | Governance can lose near-total principal with optional financial bypass. Emergency redeploy is CURRENT-pool-only; ordinary reviewed destination moves remain guarded. Broken tokens/core and terminal lifecycle cannot be bypassed. [Manual recovery](../../TODO.md#task-manual-emergency-rebalance). |
| Sampling and serial nonce capacity |600/240/300, hard12hours and service60–300jitter remain. Sampling cannot observe every intervening tick; RPC/inclusion/nonce delays can restart windows. [Keeper qualification](../../TODO.md#task-host-services). |
| Tight code size | Migration39-byte runtime headroom remains. Do not change compiler/limits or perform speculative extraction merely to claim improvement. New on-chain edits need exact normal gates. [Release](../../docs/RELEASE_CHECKLIST.md). |
| Real economic dependencies | Actual independent ETH/ZZZ feeds, cheaper qualified routes/depth, token/proxy behavior, authority addresses, supported VRF and OpenSea primary mint remain unqualified. Team answers and source mechanisms are not operating approval. [Todo](../../TODO.md). |
| History longevity and recovery | Streaming and atomic startup do not prove complete ingestion, years of replay, storage capacity, power-loss safety, Unix filesystem locks, off-host restoration or sustained uptime. Qualify practical bounds before service acceptance. [History](../../TODO.md#task-financial-history), [hosting](../../TODO.md#task-host-services). |
| Website/runtime boundaries | Popldemo simulation, served poplint current3 and fresh source8 are distinct. No public signing, site/server rollout or journal migration. [Environment map](../../docs/SITE_ENVIRONMENTS.md). |
| Independent release audit | Current internal findings/evidence do not close independent audit/remediation, maximum target gas, key/recovery or frozen-release sign-off. [Release approval](../../docs/RELEASE_CHECKLIST.md). |

No implicit new requirement for bridges, creator inboxes, third contribution
assets, token replacement or external custody is revived. Deferred cumulative
loss/volatility/strategy proposals remain decisions rather than missing fixes.
