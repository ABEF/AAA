# Harvesting audit and improvement scope

6 November 2026; starting main `11e01571a20068d624d8f8a55076cf5068db6281`.
Production NOT APPROVED. This is the executed scope of the user's harvesting
audit prompt, not a claim that every possible state was tested.

## Objective and boundaries

Trace actual fees from both registered local-v4 positions to Vault receipts,
the fixed 80/10/5/5 split, individual/equal-collective claims, attributed compound
and fixed-ZZZ buyback backing. Investigate first, implement demonstrated defects,
verify their consequences and update operator/Todo/evidence guidance.

Read current instructions, context, README, sole Todo, handoff, economics and
operator procedures. Preserve unrelated work and original reports. Keep source
publication distinct from deployment, sealing, public transactions, services,
websites, existing Anvil state, journals, signing and the paused heartbeat.
Only the fresh source is evaluated; historical codecs/runtimes remain explicit.

## Investigation and verification

1. Inventory standalone collection and every implicit checkpoint: activation,
   growth, compound, replacement, residual close, same-main consolidation,
   move/resume, parking, terminal holder return and canonical cutoff/abort/import.
   Record permissions, lifecycle, both-leg behavior, receipt classification and
   failure rollback. One bucket is not one NFT; never add raw L across ranges.
2. Independently reconcile each asset's actual core fees, collected net receipts,
   FeeController dust, personal/equal-collective liabilities, claims, compound and
   buyback. Donations, principal, reserves, conversion and import are not new fee
   income. Verify exact native sender/deltas, ERC20 deltas, approvals and callbacks.
3. Check entrant/incumbent ordering, own-entry-swap fees, growth checkpoints,
   multi-NFT/current-owner transfers and partial/repeated claims. Different LP
   shares must not change equal collective or rarity-only royalty weights.
4. Measure rounding separately in core checkpoints, 20-unit splits, global reward
   indices and per-NFT fractions. Compare actual-v4 sparse and fragmented
   permissionless collection. Quantify finite final unclaimable units and the
   documented <=19-unit incumbent-owner dust exception. Do not silently change
   allocation fairness or copy exact-unit royalty rules into the LP ledger.
5. Check zero/tiny/large fees, active/outside/mixed/filled residuals, both-leg
   rollback, stale prices, route failures, pause and lifecycle restrictions.
   Separate ordinary qualified-token behavior from compromised-dependency late
   fees during collection/closure; no transaction interleaving is assumed inside
   an atomic call. Raw claims and fee-only collection do not need invented USD.
6. Audit hourly scheduling, overrides, slow reads, pending-first recovery,
   receipt/reorg/nonce/spend/save provenance and restart. Authenticated own
   internal harvesting may coalesce clocks; manual activity is not guessed.
   Missing optional clock proof must not strand a verified paid transaction.
7. Reconcile events and earnings outputs without counting fee receipt, allocation,
   claim, conversion or principal twice. Preserve today-price USD semantics and
   unavailable values. Check checkpoint/lineage boundaries against current code.
8. Use independent arithmetic and positive funded claims. New tests target gaps;
   rerun affected checks, not unchanged full suites. Record source hashes,
   toolchain, failures, fixtures and exact scopes; test envelopes are not normal
   deployment-size or target operating-gas approval.
9. Update current operator steps, economics, feature/evidence, sole Todo,
   roadmap/release/context where affected. Preserve historical source scopes.
   Report fixes, intentional policies, unresolved decisions and external gates.

## Knowledge used

The pinned installed `@uniswap/v4-core` and `v4-periphery` implementations govern
the local execution. Official guidance confirms zero-liquidity decrease for
collection; it does not prove PoPL entitlement, dust or keeper behavior:

- [Uniswap liquidity lifecycle](https://developers.uniswap.org/docs/protocols/v4/guides/managing-liquidity/overview)
- [Core position checkpoint implementation](https://github.com/Uniswap/v4-core/blob/main/src/libraries/Position.sol)

Online main-branch documentation is background; the recorded installed source
hashes, not a moving upstream branch, bind this campaign.
