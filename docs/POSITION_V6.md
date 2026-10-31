# Accounting6: adaptable policy with bounded LP custody

Fresh undeployed source; **production NOT APPROVED**. This extends the explicit
[accounting5 shape](POSITION_V5.md), not its deployed runtime, configuration or
saved transaction profile. Existing Anvil services and journals remain unchanged.

| Capability | Fresh value |
| --- | --- |
| Vault accounting / shared policy | `ACCOUNTING_VERSION()==6` / `PROTOCOL_POLICY_VERSION()==1` |
| Strategy / Manager / PortfolioPolicy portfolio |2 /2 /2 |
| Maintenance / confirmation / compound |3 /3 /4 |
| Migration custody / emergency / residual close |4 /2 /1 |
| LP routing / position child / math child |2 /1 /1 |
| Pricing / Entry routing / reviewed Entry |2 /2 /2 |
| Governance / fee intake / execution quality |2 /1 /1 |
| Production inventory | Schema8,17 modules and21 helpers |
| Same-chain handoff admission | `ZZZ_CANONICAL_SAME_CHAIN_ADAPTABLE_POLICY_V6` |

Position still has eight words: `poolId,lpTokenId,idle0,idle1,depositUSD,centerX96,
lastRebalance,status`. Status codes and physical main/residual ownership are
unchanged. Wire length alone never selects a profile or permits old handoff.
Both legs belong to Vault in the same native ETH/fixed-ZZZ pool; at most one
residual. Actual amounts, not summed raw liquidity, determine aggregate NAV.

The separately predeployed fixed-controller ProtocolPolicy is bound before
consumers. [Operating settings](ADAPTABLE_POLICY.md) are bounded and scoped;
mint/entry expected fingerprints are new required calldata fields. Core bindings,
economic allocation and holder rights remain fixed. Fresh readers authenticate
policy/runtime/revisions and per-pool allocation/gap rather than invent defaults.

The initial85% trigger,600-second confirmation,240-second checks/300-second
maximum gap,60–300-second service jitter, hard12-hour interval and hourly harvest
remain. Optional main allocation defaults60% with a hard60% floor; only raising
that floor is implemented. Manual widths remain subject to real pool/tick and
execution feasibility. Contributions never recenter or reset the LP clock.

Canonical admission is deliberately V6 even though records retain their wire
shape: source/destination must support policy commitments and visual-threshold
compatibility before migration starts. Old profiles and receipt recovery remain
explicitly historical. There is no automatic deployment, journal migration,
public signing, site rollout or readiness approval.
