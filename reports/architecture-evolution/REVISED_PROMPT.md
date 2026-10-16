# Architecture evolution review: corrected execution brief

2026-10-16. This is the execution specification for the user's architecture-review
attachment, not a second task list. Task status belongs in `docs/project-todo.json`.

## Challenge of the original prompt

The requested scope is relevant, but repeating a comprehensive audit in every
phase wastes work and can disguise missing evidence. Use a capability matrix,
explicit invariants and source-bound findings instead. "Future chain support"
must separate equivalent-asset bridging, actual asset conversion, new venue
support and migration of canonical NFT ownership/reward ledgers. These are four
different designs. A pool address or token mapping is not a swap. Neither a
timelock nor a code/review hash proves an arbitrary future custodian is safe.

The proposed three layers are a useful design hypothesis, not an existing hard
security boundary: authorized external custody and governance-controlled price
truth can defeat economic guarantees without violating local permissions.
Distinguish local enforcement from external trust. Do not promise recovery from
an irreversibly lost chain without an explicit recovery/finality authority.

Preserve the accepted fixed economics. Comparing configurable allocations does
not authorize a setter. The user's subsequent decision is **3% aggregate
migration execution loss, network gas separate**; activation/top-ups remain
**1%**. Do not apply a fresh 3% allowance to every leg, misclassify market movement
as execution loss, or describe a proposed floor as implemented.

Subsequent user direction on 2026-10-17: plan controlled whole-protocol migration
while the original chain still works; defer post-halt recovery. Specify bounded
freeze/export/import and single-successor rights, and identify the pre-seal
changes and unselected proof/finality dependencies. Do not infer approval for
an emergency recovery committee or claim that the existing LP bridge implements
canonical portability.

## Execute in this order

1. Read current context, source, deployment/service configuration, central Todo,
   both repository states and evidence. Record HEAD, branch, dirty changes and
   actual hash comparisons. Preserve unrelated unpublished work. Use an isolated
   `codex/` branch, without deployment, public signing or direct main publication.
2. Build a source-linked capability and authority map. Track funds separately:
   principal, attributed idle, compound reserve, buyback reserve, funded owner /
   collective claims, royalty liabilities, donations and in-flight funds.
3. Document and independently challenge an architecture before substantive edits.
   Evaluate immutable economic rights, bounded governance configuration and
   explicitly reviewed custody evolution. Compare at least the existing fixed
   home-pair system, a composition-epoch extension and a new canonical system.
   Explain why simply deploying a new Vault cannot rebind existing NFT ledgers.
4. Implement confirmed, bounded repairs whose invariants are understood. Do not
   remove asset checks, weaken loss/size/gas limits, introduce generic calls,
   sweeps, arbitrary recipients or proxy upgrades to claim broad adaptability.
   Leave undecided trust/architecture choices explicit while completing work
   that does not depend on them.
5. Add adversarial evidence for newly changed or previously uncovered behavior.
   Reuse unchanged tests only after checking their complete relevant source,
   dependency and configuration closure. A changed Vault invalidates prior
   whole-Vault fork/static receipts; it does not require rerunning unchanged
   unrelated keeper or frontend tests. Run affected regression/gas/size checks;
   keep failures and fix attempts, and identify mocks versus real dependencies.
6. Perform a second source review of the repair and resulting evidence. Record
   severity, actor/preconditions, source references, impact, reproduction,
   resolution and residual risk. Internal review is not independent audit.
7. Update the central ledger, generated Todo, capability/release reference and
   repository context. Preserve stable task IDs and clickable titles. Record
   deployment NO GO while required decisions/live qualifications remain open.
   Publish only the scoped work on the review branch and verify its identity.

## Required invariants and scenarios

- A holder cannot redeem principal. Current ownership carries then-unclaimed
  funded rights; a seller may claim before transfer. Rarity affects only the
  separate royalty pool. Preserve the fixed 80/10/5/5 allocation and raw-unit
  dust semantics, and do not split already allocated remote rewards twice.
- Stable NFT/bucket/share identity must survive custody changes. Old currencies
  and pending liabilities cannot be renamed, discarded or subsidized by another
  bucket or donations. All claims remain actually backed.
- Four permanent historical/admitted identities bound local settlement work.
  Destination admission must survive competing arrivals; returns and aliases
  reuse a slot. Reserved `None` state must be safe for all enumerators.
- Distinguish same-pair range change, same-pair new pool, different pair,
  reversed order/decimals, new DEX/hook, new EVM chain, repeated hops/returns and
  canonical-chain relocation. Test supported boundaries and retain rejection
  for unsupported transitions.
- Conversion needs typed restricted execution, fresh authenticated valuation,
  exact custody recipients, one aggregate budget, complete pending-fee handling
  and rollback/retry semantics. Cross-chain asynchrony cannot inherit an atomic
  USD-value guarantee without an explicit settlement policy.
- Challenge privileged actors and approved dependencies, not only unauthorized
  callers: bad feeds, malicious pinned providers/destinations, keeper churn,
  unavailable tokens/venues, lost keys, stuck VRF, partial delivery and home-chain
  disappearance. State which risks local code cannot eliminate.
- Review frontend uint256 identity/transaction pinning and backend receipt,
  backup, replay/reorg, RPC, fee and key boundaries without claiming that the
  simulated website or Anvil staging qualifies production behavior.

Deliver the corrected brief, architecture, implemented repair, actual targeted
evidence, prioritized findings, retained decisions and honest release status.
Do not claim all future technologies can be anticipated or every possible bug
can be excluded.
