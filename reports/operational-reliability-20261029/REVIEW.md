# Operational reliability: code follow-up

Reviewed 2026-10-29 against main c2b82b0 and the complete
[normal-operation model](../normal-operation-design-20261029/REVIEW.md).
This pass fixes reproduced implementation defects without choosing a new timer,
compound policy or economic rule. **Production NOT APPROVED.**

| Area | Confirmed defect and implemented repair |
| --- | --- |
| Indexer confirmation | A chunk could be stored after its required confirming descendants disappeared. Recheck head depth after fetch/decode, then canonical tip before commit. Invalid data never advances the confirmed cursor. |
| Indexer concurrency | A second writer could reorg/reingest and restore the same cursor while changing the boundary parent. Recheck cursor and exact predecessor hash/parent/time inside the write transaction. |
| History chronology | Hash-linked new headers could regress time across a stored boundary or within a chunk, distorting time-window reporting. Compare already-fetched timestamps; equal timestamps remain valid. Unknown unindexed parent time is not invented. No extra RPC for this guard. |
| Keeper receipt recovery | Latest head time could precede the known checkpoint; a successor nonce receipt could move the saved anchor backwards. Reject height/time regressions and a changed hash or timestamp at the same checkpoint height before paid-state progression. Same-block/equal-time successors and permitted no-checkpoint inspection remain valid. No journal rewrite or new field. |
| Management JSON | Health/config/backup diagnostics could accept duplicate/nonfinite JSON despite strict operating journals. Use the shared strict parser and require top-level objects. Missing-file behavior and valid results remain; CLI already caught nonobject exceptions, so this is not described as an old uncaught CLI crash. |
| Sold-out mint reporting | At 1,000 minted, readiness could still say new minting was not stopped, while transaction preparation rejected it. Derived remaining supply/supply-stop now join the existing aggregate stop flag. Pending VRF/finalization remains readable at cap across supported profiles. No extra RPC. |
| Permanent reservations | Observation omitted the actual selected pool alias and canonical first-activation identity. An arbitrary permanent reservation could pass inventory consistency while first activation would revert. Schema 6 now observes exact getters/capacity and checks current custody, allowing initialized moved aliases. Unknown or contradicted selected data is unavailable; unrelated bucket faults do not falsify the selected partial status. |
| Test selection | Full Python discovery could rerun imported fixtures/aliases and produce noncanonical duplicate identities. Select locally defined canonical cases once, keep valid locally defined subclasses/inherited methods, and reject empty/duplicate/wrong-identity/custom-loader selections explicitly. Inventory-only mode executes no test bodies. |
| Verification evidence | Full verification overwrote old root reports and could use inherited compiler/test filters or weakened settings. Use exclusive new evidence paths, validate the effective normal profile/tool identity and filter/fuzz/invariant settings, and recheck at phase boundaries. Safe diagnostic messages identify known settings; raw config/provider errors are never echoed. |

The normal profile checker shares the existing current-fork configuration
validator. It invokes only local `--version`/`config`, keeps raw configuration in
memory and exports an allowlist. Tool file hashing and settings consistency are
not compiler authenticity, malicious-host attestation or target-chain qualification.
The complete workflow was not run during this affected campaign.

## Operating consequences

- Schema 6 inventories need fresh reservation observation. Null/missing is not an
  unreserved pool. `available_by_reservation` is a narrow consistency status, not
  prices/routes/admission/owner/gas/complete transaction approval.
- First activation uses the canonical bucket identity; deliberate moved buckets
  keep their original IDs. Successor header import requires an empty destination,
  so do not execute pre-reservations there. Import source aliases through the
  authenticated canonical records instead. Governance reservation consumes
  permanent capacity and is not an editable placeholder.
- On checkpoint contradictions, preserve the pending intent, signed hash, nonce
  and spending truth. Independently reconcile canonical evidence/catch up or use
  the reviewed endpoint/recovery procedure; do not delete state to clear an alert.
- Source changes need separately authorized matching worker/checker/API rollout.
  No service, website, old Anvil, journal, key, transaction or heartbeat was changed.
- Defaults/range/cooldown/900-second confirmation / 300-second maximum gap / 240-second checks/jitter, raw compound priority,
  standalone hourly harvest and incumbent-versus-entrant accounting stay unchanged.
  Early observation, no-swap compound, harvest coalescing and the universal
  operation report remain proposed. No guard/cap/permission was relaxed.

## Contract and independent review

The [contract pass](CONTRACTS.md) rechecked normal/canonical/terminal/membership/
conversion/dust and ownership boundaries. No new confirmed Solidity defect was
established. A proposed mint-completion concern was rejected because the assumed
pause-after-proceeds invariant was not established; authorized callback ordering
was not relabelled as an exploit just to add a guard. The reservation observer
was challenged independently, including moved/source-inherited aliases, selected
bad custody and malformed lifecycle evidence. Two nested diagnostic defects were
fixed before final verification. This is scoped internal review, not exploit absence.

See [verification](VERIFICATION.md), [backend](BACKEND.md), [keeper](KEEPER.md),
[exact methods/pins](verification-summary.json) and the [sole Todo](../../TODO.md).
Actual prices/routes/VRF/authorities/OpenSea, current4 integration/hosting,
target gas/latency/load/Linux recovery, immutable metadata hosting, compiler
qualification and independent audit/remediation remain separate release gates.
