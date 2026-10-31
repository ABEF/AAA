# Optional main/residual LP implementation and review

Local source implementation,30–31October2026 (Europe/Paris); production **NOT
APPROVED**. The user authorized the [recorded plan](../../docs/OPTIONAL_PORTFOLIO_IMPLEMENTATION.md)
before implementation. The final width decision replaces the earlier full side
with **half the corresponding main side**. Nothing was deployed or restarted.

## Resulting behavior

- Default single main; manually enabled optional active main>=60% and one residual
  <=40% of post-cost attributed principal after replacement. These are placement
  limits, not continuously maintained weights or proven optimal economics.
- Default residual width5000bps of the corresponding side, configurable1–10000;
  one full aligned tick-spacing away from spot. Main50–150 around100 means roughly
  75–100 or100–125 before gap/rounding. Full10000 remains a reviewed alternative.
- Ordinary trigger85%of actual centre-to-boundary human ZZZ-in-ETH price distance,
  physical/reference same side;600-second sampled confirmation/maxgap300,
  source checks240, then fresh durable60–300-second service jitter. Hard initial
  12hours remains; deliberate geometry changes are a cooldown-gated exception.
- Close both old legs before replacement. Use bounded approved actual-core quotes
  to swap only enough to meet the actual main floor; preserve loss/output/idle
  guards. No third residual, forced40% allocation or unsafe automatic fallback.
- Growth/activation increase main using entrant-only budgets, checkpoint old fees,
  value both physical legs and verify marginal main deployment before shares.
  Existing residual, centre and rebalance clock remain unchanged.
- Harvest both physical positions, combine actual receipts, then allocate80/10/5/5
  once per asset. Old rewards follow ownership; royalties remain separate.
- Disabling mode records desired single state; preserve both legs until guarded
  atomic merge. Parking, same-pair movement and holder return close both. Canonical
  parked V5 capture/import/activation requires no live residual.

## Architecture and fixes

Fresh accounting5/portfolio1/maintenance3/confirmation3/compound4/custody4/
emergency2/LP-routing2 and schema7 explicitly separate old deployments/readers.
Position remains eight words; main LP ID is real. Both physical NFTs stay Vault-owned.
Manager's fixed typed child has fixed recipients and individual NFT approvals;
Balancer's read-only math child reduces size. No generic executor, delegatecall,
custody address, input asset, token replacement, bridge or signing permission was added.
Standalone helper construction binds frozen Access modules in reviewed order.

Material defects corrected during implementation/review:

1. Same-pair movement rechecked the destination using a captured source policy.
   Budget now retains the actual sourcePool for that comparison.
2. Rounding headroom60.01% accidentally forced swaps for natural60–60.01% main
   placement. Natural>=60%now avoids a needless swap or empty-venue rejection;
   actual trade sizing keeps rounding headroom and final proof.
3. Narrow inverse-price bands could pass permitted reference deviation while
   the new main was physically inactive. Hybrid mint requires active stored ticks
   both before and after external mint/refund callbacks, even when sqrt is unchanged.
4. Observation throughout a12hour persistent trigger would spend unnecessarily.
   Keep raw checks, but enroll paid samples near earliest eligibility; pending
   recovery/resets remain first. No financial or confirmation guard was removed.

The [operator manual](../../docs/OPERATOR_MANUAL.md), callable reference, profile,
features, roadmap, sole Todo, context and handoff now describe the current source.
Earlier guide bytes are archived externally; historical reports retain their bytes.

## Verification and remaining risks

[Verification](VERIFICATION.md) distinguishes final actual local v4 tests,
synthetic guard/accounting/API/keeper evidence, earlier stages and failed attempts.
42normal compiler size gates pass. Vault runtime24562 leaves only14bytes;
its deployment limit is met but future code changes require particular care.

Actual ZZZ implementation/upgrade/callback behavior, independent dual feeds,
routes/depth, VRF, authorities, OpenSea, target gas/market economics, matching
keeper/API/website rollout, operating recovery and independent audit remain open.
At narrow governed geometries an own-pool candidate can be selected and later
safely rejected by the active-main guard despite a viable alternative venue;
candidate-ranking liveness is explicitly retained in Todo. Conditional late fees
from a market-changing ZZZ callback remain dependency qualification work, not a
confirmed exploit of the actual token. Caps do not guarantee profitability,
continuous liquidity, absence of MEV or protection from malicious governance.

No website source/build/server, old Anvil state, transaction journal, shared signer,
public transaction/deployment/sealing or paused heartbeat changed. Work is saved
locally and **not committed/pushed** by this task.
