# Improved request and execution brief

Audit and improve the current PoPL source candidate, starting at main44f2192.
Find reproducible defects, missing validation, operational inconsistencies and
unnecessary duplication; implement justified repairs, verify their effects and
keep the source, operator procedures and sole Todo consistent. “Execute” means
perform this work, not trigger an LP exit or any financial operation.

## Understand and prioritize

Read current instructions, context, README, Todo, handoff and relevant operator
procedures. Trace current6 contracts and their API/keeper/inventory consumers,
including all physical LP legs, economic owners, permissions, units, controls,
external calls, failure states, recovery and output semantics. Preserve current
financial rules and versioned historical readers/journals.

Use previous source-bound audits as evidence, not assumptions. The October31
review already covers exact unchanged production Solidity and static contexts;
do not repeat its compilation, detector run or test counts merely to create a
new report. Verify source/dependency/build pins before reuse and inspect changed
consumer interactions separately. Prioritize real current defects over generic
recommendations and claims of exhaustive safety.

## Review matrix

1. **State and accounting:** NFT detail, collection/wallet chunks, custody status,
   group identities/share denominators, parked/exited rights, principal versus
   earned/claimable/claimed, royalty outages, USD unavailability and exact history.
   A price outage may hide a financial metric; malformed custody evidence must
   not become an apparently valid unavailable value or zero.
2. **Current configuration versus creation history:** mutable policy, reviewed
   live getters, constructor provenance, runtime/module binding and same-block
   observations. Never repair an adjustable setting by rewriting immutable
   creation records or infer an absent current value from a historical default.
3. **Keeper diagnostics and recovery:** authenticated policy evidence, health
   field bounds/fingerprints, raw need versus timing/readiness/blocked/unavailable,
   independent harvest and pending-first recovery. A health/report success must
   not conceal missing required policy, and diagnostics must not gain signing,
   nonce, configuration or financial authority.
4. **Verification and publication:** exact Git source closure, Python package
   scopes, required current source helpers, meaningful negative cases, exclusive
   evidence outputs and strict tool/source provenance. Inventory, static syntax
   or source checks are not EVM tests or independent approval.
5. **Consolidation and operation:** share checks only where semantics are truly
   identical; use bounded per-request caches pinned to one block. Preserve
   historical profiles and avoid new global caches, silent fallback, duplicated
   task lists or unnecessary architectural layers. Reconcile current guide/Todo
   claims against actual build evidence, without modifying historical reports.

For each material path consider odd and adversarial inputs, concurrent requests,
faults between reads, stale/reorged state, callbacks, partial completion, service
restart, corrupt evidence, rejected receivers and dependency outages. Research
primary specifications only where needed; record what they support and what they
cannot establish. EIP1898 corroborates coherent block-specific reads, not provider
authenticity. Python AST traversal is syntactic, not module execution/scope proof.

## Challenge the prompt twice before executing repairs

**Coverage review:** the vague request omits backend trust boundaries and tools
which can report a false healthy/current result. Include those as well as code,
operational docs and tasks. Interpret consolidation as removing real duplication,
not removing independent security checks. Do not restore retired assets, bridges,
creator inboxes or custody-address exits. Keep verification proportional to the
changed risks, with no arbitrary test-count target.

**Feasibility review:** no finite campaign can prove all bugs/market behaviors
absent. Require concrete causal evidence, scoped fixes and explicit limitations.
Do not repeat unchanged tests, weaken a failing guard, turn unknown into zero,
count fixture sentinels as tests, or claim a source edit is a deployed fix. Static
evidence reuse requires exact pins; changed consumer behavior needs its own proof.
Current6 service inputs may tighten validation; old deployed journals/configs
must not be silently rewritten or relabeled.

## Execute and complete

Archive original current guides and affected source; preserve unrelated work.
Parallelize independent reviews, reproduce material failures, improve the relevant
regression checks and implement narrow repairs. Distinguish behavior-preserving
refactoring from stricter validation or a changed configuration schema. If a
financial/design decision is unresolved, ask a concrete question and continue
independent work; do not silently change ownership, rights or economic settings.

Run useful affected checks with actual IDs, source pins, failures and corrected
results. Reuse exact unchanged Solidity/build evidence. Update owning tasks,
generated Todo, features, roadmap/release scope, operator guide and repository
context as applicable. Publish only intended changes on main under the existing
workflow, verify remote identity and report what actually improved/ran/remains.

No deployment, public transaction, sealing, service/site change, Anvil reset,
journal modification, signer extension or paused-heartbeat restart is authorized.
