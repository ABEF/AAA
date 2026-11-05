# Accounting6: adaptable policy with bounded LP custody

Fresh undeployed source; **production NOT APPROVED**. This extends the explicit
[accounting5 shape](POSITION_V5.md), not its deployed runtime, configuration or
saved transaction profile. Existing Anvil services and journals remain unchanged.

| Capability | Fresh value |
| --- | --- |
| Vault accounting / shared policy | `ACCOUNTING_VERSION()==6` / `PROTOCOL_POLICY_VERSION()==1` |
| Strategy / Manager / PortfolioPolicy portfolio |2 /2 /2 |
| Maintenance / confirmation / compound |3 /3 /4 |
| Migration custody / emergency / residual close |5 /2 /1 |
| LP routing / position child / math child |2 /1 /1 |
| Pricing / Entry routing / reviewed Entry |2 /3 /2 |
| Governance / fee intake / execution quality |2 /1 /1 |
| Royalty unallocated recovery | `ROYALTY_SETTLEMENT_VERSION()==2` / `ROYALTY_RECOVERY_VERSION()==2`; original-currency allocation, no converter; fresh runtime/storage required |
| Production inventory | Schema11,17 modules and18 helpers |
| Same-chain handoff admission | `ZZZ_CANONICAL_SAME_CHAIN_ADAPTABLE_POLICY_V6` |

Entry-routing3 removes pre-Vault contribution conversion and its child. Read
[the direct tuple](ACTIVATION_ENTRY.md). Historical schema8/Entry-routing2 remains
a separate explicit runtime/configuration profile; review-policy2 is unchanged.

Custody5 adds governance-only terminal allocation and push distribution; it
retains custody4's principal/parking formats, account6 and canonical V6 wire.
Owner reward/royalty claims and principal fallback are unchanged. Fresh APIs and
keepers declare custody_version5; schema9/custody4 remains historical. See
[authority boundaries](ACCESS_PERMISSIONS.md).

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

The [manual safeguard follow-up](../reports/manual-safeguard-audit-20261104/REVIEW.md)
changes runtime pins without changing ABI/storage or these capability getters.
Emergency bit16 no longer implies bit1 cooldown, and paused raw close accepts
explicit both-zero review floors. Verify exact current code pins; old instances
do not acquire this behavior. Ordinary safeguards and ownership remain.

## Version names are different boundaries

| Name | Current meaning |
| --- | --- |
| Accounting6 / PositionV6 | Eight-word local Position and current policy/portfolio-aware accounting semantics; not a deployed instance. |
| Entry routing3 | Seven-field direct ETH/ZZZ Request; no pre-Vault conversion. Review-policy2 and pricing2 remain separate. |
| LP routing2 | Vault balancing/router/math/typed physical-executor semantics; not Entry routing. |
| Inventory schema11 | Fresh17module/18helper release observation. Schema10 royalty-converting/custody5, schema9/custody4/direct Entry3 and schema8/routed Entry2 remain historical inspection profiles. |
| Canonical V6 | Explicit same-chain handoff schema and matching policy/backing rules; not permission to import an arbitrary old runtime. |
| Read API schema2 / activation config schema1 | Existing envelope/config schema families with separately explicit capability versions and runtime pins. |
| Source8 | Shorthand for fresh custody5/direct Entry3 sources; ACCOUNTING_VERSION remains6. Historical source7 used custody4/schema9. |
| Served current3 | Older separate poplint website reader/unsigned profile. It is not the current contract generation or a source8 rollout. |

Use exact getters, code/config/dependency hashes and the [current preflight](PRODUCTION_PREFLIGHT.md),
not a shared numeric suffix, to establish compatibility. [Current findings](AUDIT_FINDINGS.md)
and [environment map](SITE_ENVIRONMENTS.md) explain evidence and serving boundaries.

## Original-currency royalties: fresh settlement2

Fresh royalty settlement2/recovery2 pays each admitted currency as received.
There is no royalty converter, swap or unwrap. Governance may allocate only
reviewed admitted unallocated units in the SAME currency at current active
rarity weights using `allocateUnallocated(asset,amount,reviewHash)`. Previously
earned/deferred/fractional rights remain excluded. Unsupported currencies require
review/admission first;16ERC20 slots plus ETH remain. Original-currency claims
need no price feed; optional USD reporting and LP reward conversion are separate.
See [current settlement](ROYALTY_SETTLEMENT.md).

Removing the stored converter changes the fresh royalty storage layout. No existing immutable deployment is upgraded. Same-shaped canonical rows require matching runtime/capability/config commitments, not layout inference. Fresh schema11 has18helpers; legacy schema10 retains20. Reporting3/converter:null and keeper royalty_settlement_version2 explicitly select the no-swap behavior.
