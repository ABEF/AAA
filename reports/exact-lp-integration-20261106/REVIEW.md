# Exact-unit LP host, claims and canonical integration

Reviewed 6–7 November 2026 from main `64f9bfb1b0db28c9c8eafc42394afad2263637b6`.
**Fresh source candidate; production NOT APPROVED.** This is an accounting/ABI
upgrade, not a behavior-preserving refactor or an upgrade of installed contracts.
[Verification](VERIFICATION.md) owns actual stages, failures and limitations;
[scope](PLAN.md) records the requested invariants.

## What changed

The prior internal exact-unit engine is now used by actual Rewards. Every
allocated ETH/ZZZ unit belongs to an NFT's whole individual or collective rights;
nonmonetary fairness phase cannot become stranded monetary backing. The fixed
80/10/5/5 split, per-bucket individual share weights, equal activated collective
membership, current-owner unpaid rights and separate royalty rarity rules remain.
FeeController sub20 carry/incumbent-dust exceptions, zero-cohort orphan funds,
prefunds and upstream Uniswap collection rounding retain their separate rules.
This does not promise that all unallocated or broken-token balances are payable.

| Boundary | Implementation and reason |
| --- | --- |
| Actual share changes | Vault writes new shares/totals then calls typed `syncShares`. Stored OLD weights settle both prior asset paths before installing the authenticated new weight. Mint ordinal inverse, bucket permanence, monotonic shares and exact total are verified. A failed hook rolls back the entire contribution. |
| Collective activation | Membership writes eligibility/count then calls one-time `syncMembership`. Dormant NFTs have no collective share; growth never adds another. Neither rarity nor the physical residual becomes an LP weight. |
| Claims | Whole component previews and direct credits; current-owner claim or fixed NFT router. Exact liabilities debit before payment, with atomic rollback and post-payment solvency. Claims remain independent of prices and ordinary LP pause. |
| Earned ZZZ conversion | Consume the selected NFTs' historical components; cumulatively allocate measured ETH back to the SAME NFT/components. No current-cohort reweighting, second fee allocation, new income or principal/reserve spending. |
| LP identity | Native ETH plus one fixed deployment ZZZ, admitted before seal. New LP third-currency admission is removed; marketplace royalty currencies remain independent. |
| Lossless replacement | CanonicalV9 preserves raw pending/high/low trees, authenticated weights and direct credits. ALL weights seed before nodes. Exact direct/tree liabilities, source identities and actual funding reconcile, excluding prefunds. Source books stay intact for funded abort. Flattening claimables while retaining old phase would change future rights and is explicitly avoided. |
| Code-size boundary | Rewards creates one immutable typed RewardsCanonical child. It has fixed parent/Access, three closed record-write domains and authenticated canonical funding calls. No arbitrary executor, delegatecall, configurable code or ordinary recipient is introduced. |
| Consumers | Explicit profile7/schema16/source9 authenticates LP-allocation1, parent/child runtime graph and V9. Raw history reconstructs exact trees and reconciles per-NFT bucket/components, direct books and liabilities. Actual Vault logs/getters are independently consumed. |
| Historical state | Earlier6/V8/F2 readers, journals and checkpoint1 remain under their actual identity. They are rejected as fresh7 rather than reinterpreting fractions or fabricating zero. The unchanged eight-word principal tuple is not runtime identity. |

## Material risks and limits

- **Costs increased:** exact phase/pending state makes some cold claims and
  exports more expensive. A32-entry router ceiling and8-row canonical ceiling
  are counts, not proof of fitting a live gas budget. Replan smaller claims or
  use individual claims without changing rights; measure actual pages and fees.
- A nonempty collection exports2023raw node rows, even with only one minted NFT:
  253node pages, plus headers/assets/NFT rows and other domains. This is bounded,
  resumable and lossless, but not yet a cheap or operationally qualified handoff.
  Sparse node optimization is deferred rather than guessed into monetary state.
- Final normal runtime headroom is **Vault133 / Rewards358 / Handoff32bytes**.
  No compiler or normal size limit was raised. Future edits need exact gates.
- Fresh7 complete raw earnings replay works. Checkpoint1 is6-only; reviewed
  exact-unit checkpoint2, bounded lifetime work, archive/rotation and restore
  remain open performance/operational requirements.
- Real token/venue callbacks, provider honesty, dual feeds/routes/VRF,
  authorities, OpenSea, maximum workloads/target costs, matching site/services,
  sustained operating recovery and independent audit/remediation remain open.
  Local controlled fixtures do not qualify these dependencies.

## Operator impact

There is no manual weight-setting job. Vault/Membership own the authenticated
hooks. Before a fresh deployment is sealed, bind the fixed ZZZ, verify the
constructor-created RewardsCanonical and admit the complete schema16 graph.
Use the coordinator's ordinary capture/settle/export/import/fund/commit or funded
abort workflow. Parent module-context seed/node/barrier reads and write/send hooks
are not operator balance-editing tools. See the maintained
[manual](../../docs/OPERATOR_MANUAL.md#exact-lp-codec-currency-and-recovery-controls),
[profile](../../docs/POSITION_V7.md) and
[V9 record/order/work budget](../../docs/CANONICAL_HANDOFF.md).

The source-bound function catalog and895short operator examples include all
844functions/38constructors/13receive hooks across38contracts, with zero missing
input/output explanations. Templates still report `ready_for_submission=false`.
The sole Todo distinguishes finished source integration from real qualification.

No deployment, sealing, public transaction, website rollout, running-service
restart, Anvil reset, signer extension or journal migration occurred. Popldemo
and served poplint remain separate existing environments; the user-paused
heartbeat stays paused. Original reports, unrelated drafts and the four protected
dirty files remain preserved. Publication is source/docs only.
