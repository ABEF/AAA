# October31 source and operating audit

Baseline `e4113b79526adec829c8b888b2ca7795fdf0008b`; reviewed publication window
`37577eb..e4113b7` includes the portfolio/accounting5 and adaptable/accounting6
work published together. [Final prompt and two critiques](PROMPT.md),
[knowledge](KNOWLEDGE.md), [verification](VERIFICATION.md).

**Production NOT APPROVED.** This is an internal source-scoped review and repair,
not an independent audit, live-service acceptance or proof that every possible
input/market/execution is safe.

## Findings and corrections

| Finding | Consequence | Correction |
| --- | --- | --- |
| Published API source omitted two imported readers | Local reads/tests could use untracked files while a fresh published checkout could not load portfolio5/6. | Publish the existing exact `frontend_api/portfolio_v5.py` and `portfolio_v6.py`. Add an exact Git-blob static import check, including staged-index review and an early verifier gate. Preserve the original failing HEAD evidence. |
| Predecessor admission treated shared Uniswap dependencies as reused PoPL deployments | Valid same-chain replacement inventories failed before lifetime claims/earnings could be reconstructed. | Allow only matching same-role/same-runtime `pool_manager`, `state_view`, `position_manager`, `permit2` identities. Keep distinct PoPL modules/helpers, exact profiles, retirement proof, complete history, runtime authentication and collision rejection. |
| Portfolio accounting fixture lacked source6 policy interfaces | Existing tests could revert at fixture admission rather than test intended accounting behavior. | Bind the real ProtocolPolicy and current main-floor getter in the isolated fixture. Add captured-policy change/restore and configurable80%-main/residual/idle cases; do not relax production checks. |
| Current recovery guidance still selected accounting5 and omitted required Policy1 selection | An operator following the fresh procedure could build a mismatched configuration and fail startup/recovery. | Correct fresh accounting6/Policy1 labels, terminal metadata/principal eligibility and current balance descriptions. Historical deployments remain explicitly historical. |
| Default static-review record was still pinned to October25 | Running fresh analysis against that record cannot establish current review coverage. | Retain the old evidence and provide a new source6 review record; use strict source/finding coverage rather than weakening the checker. |

No production Solidity repair was justified by the inspected paths. Fixed economic
rights, input identities, custody/terminal semantics, trigger/timing, financial
limits and governance permissions remain unchanged. No new calldata, ABI profile
or deployed-runtime label is introduced by these corrections.

## Reviewed behavior and failure paths

- **Mint/policy:** exact native price and captured future payee, sale+VRF scoped
  fingerprint, proposal/accept/cancel, change-and-restore revisions, callback
  rollback, bootstrap/seal/import locks and cosmetic/gas independence.
- **Reveal/canonical:** provider/request/epoch identities, ordered finite draw,
  exact supply/quotas/artwork mapping, runtime pins for new requests, original
  fulfillment, drained rotation, threshold compatibility, frozen mutation,
  retired-source inspection and backing/owner preservation.
- **Contributions:** incumbent checkpoints, entrant-only budgets, main-only
  increase, unchanged residual/clock, actual marginal deployed LP and aggregate
  NAV/share issuance. Existing idle/compound cannot pay entrant execution losses.
- **Portfolio upkeep:** actual ticks/amounts for both positions, captured main
  floor and idle policy, route/core fee and swap sizing, bounded one residual,
  ordinary active-main proof, sampled-reference/cooldown/jitter distinctions and
  no unsafe automatic fallback.
- **Revenue/recovery:** both-leg harvest before closure/increase, one funded
 80/10/5/5 allocation per asset, separate claimant/reserve ownership, residual-only
  close, full parking/movement, terminal current-owner delivery, isolated failures
  and backed retry. Claims do not invoke compound or buyback.
- **Service/data:** exact profile/source closure, same-block identity and complete
  lineage, price/unavailable distinctions, pending-first recovery, recorded receipt
  provenance, existing stop/restart boundaries, strict inputs and no guessed state.
- **Tooling/operations:** normal build pins/constructor limits, operator manifests
  and false-readiness flags, dependency-versus-protocol identities, source scopes,
  current/historical documentation and preserved unrelated work.

The source-body receipts identify the actual inspected files and conclusions.
This is not an individual-body claim for every historical function, every website
flow or all off-chain failure combinations. Existing source-matched evidence is
reused explicitly; scoped tests below verify the changed risks.

## Remaining risks and engineering tradeoffs

1. A provider outage can still block ordered reveals, planned provider rotation
   and whole-collection handoff. It does not introduce a dependency into ordinary
   LP operations or terminal holder return. No reroll/admin-selected fallback.
2. Two prices within3% agreement can still produce an unavailable contribution
   under its separate2% default loss floor. Upper-input/lower-deployment valuation
   and market fees are deliberately conservative; agreement is not execution
   feasibility. Do not widen a policy automatically.
3. Residual gaps, strict main floors or high idle after recovery can make new
   placement/contributions unavailable. Use guarded reinvestment, reviewed
   configuration or documented parking/holder return; never omit attributed funds.
4. Governed100k–1m subcall budgets are not full-batch qualification. Expensive
   currencies/receivers can require smaller bounded batches and actual target gas
   review; caller underfunding is not permission to lose accounting or backing.
5. Sampled600/240/300 timing and jitter do not establish continuous market history,
   inclusion guarantees or MEV immunity. Independent feeds, remaining depth after
   withdrawal, route costs and live strategy economics remain qualification work.
6. Governance/dependency compromise, proxy changes and incompatible contract-holder
   receivers remain explicit trust/operating risks. A reviewHash, codehash or local
   artifact hash does not prove safe management or a running binary.
7. Migration has only20 runtime bytes of headroom at the unchanged final0a source.
   Target constructor arguments/gas, current services/website integration, actual
   feeds/routes/VRF/authorities/OpenSea, operating recovery and independent audit
   remain open. Static detector disposition does not close these gates.

## Operator and preservation impact

Use the matching reviewed API release for the lineage repair. No data migration,
contract call, chain reset or journal edit is required. Before any future service
rollout, verify exact Git publication closure and runtime/config profiles, stop
through the existing runbook, recover pending transactions first, preserve the
database/journals and perform the separately authorized rollout/recovery checks.
An old service is not upgraded by changing an accounting label.

No service, site, Anvil, journal, signer, public transaction, deployment, sealing
or paused heartbeat was changed. Existing demos and integration sites remain
distinct. Original report bytes and the four unrelated dirty tracked files are
preserved. Publication state is recorded separately from these source conclusions.
