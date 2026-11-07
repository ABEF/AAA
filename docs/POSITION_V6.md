# Historical accounting6: adaptable policy with bounded LP custody

This is the retained profile6 boundary. Fresh exact-unit LP source uses
[accounting7](POSITION_V7.md); do not relabel an installed6/V8 runtime or journal.

The [moving-market source follow-up](../reports/moving-market-flows-20261106/VERIFICATION.md)
retains existing ABI/storage/capability/profile shapes and changes the exact
Manager runtime/creation pins. Guarded paused same-main routing filters active
candidates; ordinary growth/compound/force remain distinct. Authenticate current
compiler/runtime bindings before any fresh deployment; do not relabel existing
Anvil, service, inventory or journal identities as this source.

Fresh undeployed source; **production NOT APPROVED**. This extends the explicit
[accounting5 shape](POSITION_V5.md), not its deployed runtime, configuration or
saved transaction profile. Existing Anvil services and journals remain unchanged.

| Capability | Fresh value |
| --- | --- |
| Vault accounting / shared policy | `ACCOUNTING_VERSION()==6` / `PROTOCOL_POLICY_VERSION()==1` |
| Strategy / Manager / PortfolioPolicy portfolio |2 /2 /2 |
| Maintenance / confirmation / compound |3 /3 /4 |
| Migration custody / emergency / residual close |5 /2 /1 |
| Same-main residual reinvestment | `RESIDUAL_REINVEST_VERSION()==1` on Migration/Vault/Budget/Policy/Pricing; governance-only. Schema14 and older omit this capability and remain inspection-only. |
| LP routing / position child / math child |2 /1 /1 |
| Pricing / Entry routing / reviewed Entry |2 /3 /2 |
| Governance / fee intake / execution quality |2 /1 /1 |
| Royalty unallocated recovery | `ROYALTY_SETTLEMENT_VERSION()==4` / `ROYALTY_RECOVERY_VERSION()==2`; original-currency allocation, no converter; fresh runtime/storage required |
| Production inventory | Schema15,17 modules/18 callable helpers plus2 inert Factory data children; exact allocator remains internal code |
| Same-chain handoff admission | `ZZZ_CANONICAL_SAME_CHAIN_EXACT_ROYALTIES_V8` |

Entry-routing3 removes pre-Vault contribution conversion and its child. Read
[the direct tuple](ACTIVATION_ENTRY.md). Historical schema8/Entry-routing2 remains
a separate explicit runtime/configuration profile; review-policy2 is unchanged.

Custody5 adds governance-only terminal allocation and push distribution; it
retains custody4's principal/parking formats and account6. Fresh canonicalV8
carries exact-unit ticket/cursor rights and the opening/capacity header; older peers are rejected.
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

Canonical admission is explicitly V8: source/destination must support exact
whole-unit royalty rows, original ticket identity, cursor, policy commitments and
visual-threshold compatibility before migration starts. Old profiles and receipt recovery remain
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
| Inventory schema15 | Fresh17module/18helper release observation and explicit reinvest1/raw-exit1 admission. Schema14 and earlier profiles remain inspection-only. Schema10 royalty-converting/custody5, schema9/custody4/direct Entry3 and schema8/routed Entry2 remain historical inspection profiles. |
| Canonical V8 | Exact-unit royalty rows and matching same-chain source/backing rules; V7/V6 peers are incompatible. |
| Read API schema2 / activation config schema1 | Existing envelope/config schema families with separately explicit capability versions and runtime pins. |
| Source8 | Shorthand for fresh custody5/direct Entry3 sources; ACCOUNTING_VERSION remains6. Historical source7 used custody4/schema9. |
| Served current3 | Older separate poplint website reader/unsigned profile. It is not the current contract generation or a source8 rollout. |

Use exact getters, code/config/dependency hashes and the [current preflight](PRODUCTION_PREFLIGHT.md),
not a shared numeric suffix, to establish compatibility. [Current findings](AUDIT_FINDINGS.md)
and [environment map](SITE_ENVIRONMENTS.md) explain evidence and serving boundaries.

## Original-currency royalties: fresh settlement4

Fresh royalty settlement4/recovery2 pays admitted currencies as received using
[exact-unit allocation](EXACT_ROYALTY_ALLOCATION.md). GCD-normalized rarity weights
retain exact whole-number proportional shares; indivisible units follow a saved
deterministic rotating cursor. All allocated raw units are assigned, with no
scaled-index/fraction reserve after final claims. LP fractions are separate.

There is no royalty converter, swap or unwrap. Current owners inherit unpaid
ticket and imported accrued rights. Governance may allocate only reviewed admitted
unallocated units in the SAME currency at current active rarity weights. Initial
opening pools, earned rights, prefunds and zero-cohort recovery stay distinct.
Unsupported currencies require review/admission; capacity starts16ERC20 and may
increase to64 plusETH after gas/service review. Raw claims need no price feed;
USD reporting and LP reward conversion remain separate.

Schema15 retains18helpers: the bounded allocator is internal library code compiled
into the ledger, not another deployed contract or authority. Reporting5/converter:null
and explicit keeper royalty_settlement_version4 select the fresh behavior. New
storage/runtime/canonical rows need new reviewed bindings and checkpoint rebuilds;
old deployments, readers and transaction journals are never relabeled.

The one-hour sale-close activation window, no deadline on dormant cards, initial
cutoff cohort and original-currency outage isolation remain. Optional royalty sync
defaults to1,000,000gas within the existing governed100,000–1,000,000 bounds. The
new ceiling and64-currency capacity are not target gas/workload qualification.
See [launch rules](ROYALTY_LAUNCH_WINDOW.md), [current audit](../reports/last24h-audit-20261105/REVIEW.md)
and [settlement](ROYALTY_SETTLEMENT.md). OpenSea/time binding, expanded service
acceptance, token-failure recovery limits and independent approval remain open.
