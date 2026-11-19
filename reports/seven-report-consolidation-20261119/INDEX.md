# Seven-report finding and obligation index

This is a source/evidence disposition index. [The Todo](../../TODO.md) owns task status.

## Original64 IDs carried forward

| ID | Item | Current disposition | Source review |
| --- | --- | --- | --- |
| R01 | Manual review gas envelope was reported but not frozen | resolved_tool | Prior scope retained |
| R02 | Dangling output preflight missed occupied destination | resolved_tool | Prior scope retained |
| R03 | Converter control notes described wrong units | resolved_documentation | Changed source reinspected |
| R04 | Nested tuple notes lost field explanations | resolved_documentation | Prior scope retained |
| R05 | Shared struct examples reused another operation meaning | resolved_documentation | Prior scope retained |
| R06 | Empty artwork root could be sealed irreversibly | resolved_source | Prior scope retained |
| R07 | Slow keeper reads could miss newly due harvest or compound | resolved_source | Changed source reinspected |
| R08 | Canonical-preparation positive fixture failed before body | resolved_test_or_fixture | Prior scope retained |
| R09 | Royalty recovery fuzz allowed permanent remainder | resolved_test_or_fixture | Prior scope retained |
| R10 | Foreign-home Vault construction was accepted | resolved_source | Prior scope retained |
| R11 | Bare immutable artwork scheme consumed setup | resolved_source | Changed source reinspected |
| R12 | Wrong fresh reservation ID consumed permanent capacity | resolved_source | Prior scope retained |
| R13 | Between-anchor tests mutated the first pinned block | resolved_test_or_fixture | Prior scope retained |
| R14 | Exact-source import test lacked a negative tamper case | resolved_test_or_fixture | Prior scope retained |
| R15 | Legacy annotation compatibility checked only two fields | resolved_test_or_fixture | Prior scope retained |
| R16 | Documentation semantic assertions searched whole page | resolved_test_or_fixture | Prior scope retained |
| R17 | Enabled harvest test did not assert due submission | resolved_test_or_fixture | Prior scope retained |
| R18 | Seal tests accepted unrelated reverts | resolved_test_or_fixture | Prior scope retained |
| R19 | Payout and callback tests omitted economic rollback state | resolved_test_or_fixture | Prior scope retained |
| R20 | Tiny royalty coverage lacked tranche rotation and transfer | resolved_test_or_fixture | Prior scope retained |
| R21 | Current financial venue fixtures lacked execution readers | resolved_test_or_fixture | Prior scope retained |
| R22 | Native balance cheatcodes invalidated rollback modeling | resolved_test_or_fixture | Prior scope retained |
| R23 | Invariant replacement plans lacked validation child | resolved_test_or_fixture | Prior scope retained |
| R24 | Positive fixtures retained bare artwork schemes | resolved_test_or_fixture | Changed source reinspected |
| R25 | Normal profile validator rejected approved read permission | resolved_tool | Prior scope retained |
| R26 | Pre-seal readiness requested private storage getter | resolved_tool | Changed source reinspected |
| R27 | Current trusted build admission and stale test family labels | resolved_tool | Changed source reinspected |
| R28 | Last manual head could orphan final simulated anchor | resolved_tool | Prior scope retained |
| R29 | Default97% test wrongly rejected98% deployment | resolved_test_or_fixture | Prior scope retained |
| R30 | Explicit99% policy test wrongly rejected99% deployment | resolved_test_or_fixture | Prior scope retained |
| R31 | Native donation assertion omitted19 earned units | resolved_test_or_fixture | Prior scope retained |
| R32 | Royalty window test was named FullDay | resolved_test_or_fixture | Prior scope retained |
| R33 | Repairing fixtures did not prove dependent economic behavior | resolved_selected_verification | Prior scope retained |
| R34 | New pre-seal planner dereferenced unknown SeaDrop terms | resolved_tool | Changed source reinspected |
| R35 | Enabled composite execution source allowed8decimals | resolved_tool | Changed source reinspected |
| R36 | Mutually matching wrong native pins passed offline plan | resolved_tool | Changed source reinspected |
| R37 | Protocol implementations could masquerade as external feeds/VRF | resolved_tool | Changed source reinspected |
| L01 | Extra compound waiting rule is service-only | accepted_policy | Changed source reinspected |
| L02 | Unallocated royalty recovery uses inclusion-time active weights | accepted_policy | Changed source reinspected |
| L03 | Terminal principal sends ETH and ZZZ atomically per NFT | structural_limit | Prior scope retained |
| L04 | Opening/zero-cohort/unadmitted royalties are not always immediately allocated | accepted_policy | Changed source reinspected |
| L05 | LP dust barrier is a split exception | accepted_policy | Prior scope retained |
| L06 | Emergency governance may omit financial protections | accepted_policy | Prior scope retained |
| L07 | Per-operation caps do not bound cumulative turnover losses | accepted_policy | Prior scope retained |
| L08 | Generic seal does not prove selected SeaDrop/converter release binding | structural_limit | Prior scope retained |
| L09 | Expired nonzero mint end cannot be reopened | accepted_policy | Changed source reinspected |
| L10 | Wrong-but-nonempty content or fixed venue/token graph is irreversible | structural_limit | Changed source reinspected |
| L11 | Pending unanswered VRF can block rotation and replacement | structural_limit | Changed source reinspected |
| L12 | Permanent reservation, terminal exit and canonical retirement do not unpause open | accepted_policy | Prior scope retained |
| L13 | Arbitrary tokens and rejecting receivers cannot be forced to work | structural_limit | Changed source reinspected |
| L14 | Raw fixed-ZZZ LP claims remain deliberate recovery | accepted_policy | Prior scope retained |
| L15 | Own-swap proof and jitter do not provide manipulation immunity | structural_limit | Changed source reinspected |
| L16 | Generic revert, staged metadata and missing raw logs limit assurance | historical_evidence_limit | Prior scope retained |
| L17 | Old wrapped/Pons fork and royalty-converting cases remain historical | historical_evidence_limit | Prior scope retained |
| Q01 | Independent ETH/ZZZ sources and usable bidirectional routes/depth | release_qualification_open | Prior scope retained |
| Q02 | Complete target fees, RPC capacity and final constructor/operation gas | release_qualification_open | Prior scope retained |
| Q03 | Maximum-state gas and activation/currency/claim workload | release_qualification_open | Prior scope retained |
| Q04 | Authorities and contract-wallet envelopes | release_qualification_open | Prior scope retained |
| Q05 | OpenSea, VRF and immutable content delivery | release_qualification_open | Prior scope retained |
| Q06 | Integration rollout, hosting and restart/backup/recovery operation | release_qualification_open | Prior scope retained |
| Q07 | Independent audit and release remediation/approval | release_qualification_open | Prior scope retained |
| Q08 | Tight runtime/initcode headroom | structural_limit | Prior scope retained |
| N01 | Passing count alone could admit substituted evidence methods | resolved_this_consolidation | Prior scope retained |
| N02 | Complete pre-seal input omitted disabled ordinary-pool stop | resolved_this_consolidation | Changed source reinspected |

## Subsequent assessments

### E01 — Stop after durable intent could launch the signer

**resolved_source**; related original IDs: Q06.

An observed cooperative stop is checked immediately before signer subprocess launch. The hashless durable intent remains blocked for recovery.

Next: Retain pending-first recovery; instruction-level signal races are not eliminated.

Origins: [q06-keeper-recovery-20261117/REVIEW.md](../../reports/q06-keeper-recovery-20261117/REVIEW.md).

### E02 — Completed bounded RPC failover could falsely expire watchdog

**resolved_source**; related original IDs: Q06.

Actual completed HTTP attempts report main-thread watchdog progress; blocked I/O receives no fake pulse.

Next: Qualify real provider/normal loop and remaining stall forms; retain the exact warning/host observations.

Origins: [q06-keeper-recovery-20261117/REVIEW.md](../../reports/q06-keeper-recovery-20261117/REVIEW.md).

### E03 — Matched cold activation gas refusals

**resolved_finite_workload**; related original IDs: Q03.

Historical8 then6 padding refusals are superseded only for the matched F6 workload. All13controlled cold calls and financial checks pass20M/full20%; worst16,460,899raw/19,753,079padded.

Next: Keep the original failures and finite scope; do not repeat them just to rename the budget.

Origins: [royalty-rounds-20261118/REVIEW.md](../../reports/royalty-rounds-20261118/REVIEW.md), [activation-gas-20261118/REVIEW.md](../../reports/activation-gas-20261118/REVIEW.md), [activation-final-six-20261118/REVIEW.md](../../reports/activation-final-six-20261118/REVIEW.md).

### E04 — Receipt-tree cost replaced by bounded exact royalty rounds

**implemented_source**; related original IDs: Q03, L02, L04.

Constant-size receipt-credit rounds/cursor and at most1000cohort boundaries preserve exact original units, current-owner rights, one-hour/fault cohorts and logical V10 rows.

Next: Fresh logical import/runtime pins only; no old physical book copy.

Origins: [royalty-rounds-20261118/ROUND_ACCOUNTING_REVIEW.md](../../reports/royalty-rounds-20261118/ROUND_ACCOUNTING_REVIEW.md), [engineering/ROYALTY_REVIEW.md](../../reports/activation-final-six-20261118/engineering/ROYALTY_REVIEW.md).

### E05 — Faulty activation reads and caller-manufactured deferral

**resolved_source**; related original IDs: Q03, L13.

A separately governed50k initial balance read plus fixed one-word return is funded by a complete frame or independently by the read cap plus120k. Only the authenticated unavailable signal defers enrollment; other partial accounting failures revert.

Next: Qualify selected token behavior/capacity without silently skipping healthy expensive rights.

Origins: [royalty-rounds-20261118/REVIEW.md](../../reports/royalty-rounds-20261118/REVIEW.md).

### E06 — Synchronized replacement prefunds counted twice

**resolved_source**; related original IDs: L04, Q03.

Import clears old target opening classification and classifies actual prefunds once as orphaned, separately from earned imported backing; aggregate overflow/abort protections remain.

Next: Retain C07failure/C08success at their source; full fresh cutover remains separate.

Origins: [synced-prefund/REVIEW.md](../../reports/royalty-rounds-20261118/synced-prefund/REVIEW.md).

### E07 — Compact LP/royalty codecs and full-width rights

**implemented_source**; related original IDs: Q03.

LP MAX128spill and royalty223-bit compact/full256spill preserve logical full-width phases/coefficients. Status uses16/16/16fields and initialbit48.

Next: Require F6/private-codec exact pins; do not relabel payload5/old slots.

Origins: [activation-gas-20261118/REVIEW.md](../../reports/activation-gas-20261118/REVIEW.md), [activation-final-six-20261118/REVIEW.md](../../reports/activation-final-six-20261118/REVIEW.md).

### E08 — Transaction Pricing and static proof/Oracle optimizations

**implemented_source**; related original IDs: L15, Q03.

Transient contribution basis/marks are explicitly cleared; maintenance remains persistent. Adjacent proof sharing retains public/callback/final/source/mutable-boundary validation and exact49-word typed Oracle provenance.

Next: Preserve the verified compiler/identity/domain assumptions; no generic market cache or removed financial guard.

Origins: [royalty-rounds-20261118/PLACEMENT_PROOF_REUSE_REVIEW.md](../../reports/royalty-rounds-20261118/PLACEMENT_PROOF_REUSE_REVIEW.md), [activation-final-six-20261118/REVIEW.md](../../reports/activation-final-six-20261118/REVIEW.md).

### E09 — Impossible feed values have different failure precedence

**retained_behavior_difference**; related original IDs: L15.

Some impossible/out-of-domain quotes now fail as InvalidObservation instead of Panic; Oracle normalizes failed sources to InvalidPrice. No accepted-value defect is established.

Next: Keep explicit rejection semantics; do not claim all error bytes/ABI JSON are identical.

Origins: [activation-gas-20261118/REVIEW.md](../../reports/activation-gas-20261118/REVIEW.md), [activation-final-six-20261118/REVIEW.md](../../reports/activation-final-six-20261118/REVIEW.md).

### E10 — Intermediate zero-fee component regression

**resolved_finite_workload**; related original IDs: Q03.

F6 reports105,301component saving versus the intermediate packed codec that had added105,091in its selected zero-fee component.

Next: Retain the matched component scope; do not promise every operation is cheaper.

Origins: [activation-gas-20261118/REVIEW.md](../../reports/activation-gas-20261118/REVIEW.md), [activation-final-six-20261118/REVIEW.md](../../reports/activation-final-six-20261118/REVIEW.md).

### E11 — Current static CI/source-build wiring

**resolved_source**; related original IDs: Q07, R27.

The current static record covers601records:147current assessments and454exact-source reuses. F6 is the trusted default and inventory selects payload6.

Next: No601test or green published CI/independent approval claim; retain current exact artifacts.

Origins: [activation-final-six-20261118/STATIC_REVIEW.md](../../reports/activation-final-six-20261118/STATIC_REVIEW.md).

### E12 — Maximum whole-operation workload

**qualification_open**; related original IDs: Q03.

13current cases cover16ERC20s plusETH, one main, fixed entrant order and controlled depth/feeds/VRF. Component/setup allowances are not full operating budgets.

Next: Qualify selected currencies, expanded64/two-LP/order states and complete32M flows without unchanged reruns.

Origins: [launch-workload-20261117/REVIEW.md](../../reports/launch-workload-20261117/REVIEW.md), [q03-activation-gas-20261117/REVIEW.md](../../reports/q03-activation-gas-20261117/REVIEW.md), [activation-final-six-20261118/REVIEW.md](../../reports/activation-final-six-20261118/REVIEW.md).

### E13 — Claim entry count versus cold batch gas

**retained_limit_qualification_open**; related original IDs: Q03, L13.

Router32 is an entry count; fresh smaller batches preserve every right. Launch gas figures belong to older Rewards/Royalty sources, not fresh F6 cold batch proof. Activation32M does not raise claims12M.

Next: Use exact current simulations and healthy subsets; do not relabel same-test recovery as cold qualification.

Origins: [claims/REVIEW.md](../../reports/launch-workload-20261117/claims/REVIEW.md), [launch-workload-20261117/REVIEW.md](../../reports/launch-workload-20261117/REVIEW.md).

### E14 — Optional royalty pre-sync and growth behavior

**retained_policy**; related original IDs: Q03.

Growth skips activation enrollment. Operator-paid sync can move work but receipts/trading can intervene; it is not mandatory or guaranteed inclusion protection.

Next: Prepare the exact fresh entry; no required extra holder transaction or weakened cap.

Origins: [launch-workload-20261117/REVIEW.md](../../reports/launch-workload-20261117/REVIEW.md), [q03-activation-gas-20261117/REVIEW.md](../../reports/q03-activation-gas-20261117/REVIEW.md), [activation-final-six-20261118/REVIEW.md](../../reports/activation-final-six-20261118/REVIEW.md).

### E15 — Selected32M gas-only contribution profile

**accepted_policy**; related original IDs: Q02, Q03.

Existing schema2 accepts backend string32000000 and matching website integer32000000, with full20% padding/max estimate26,666,666. Seven original new injected checks pass;12Mdefaults and24Mmaintenance remain.

Next: Before separately authorized adoption qualify actual execution/provider limits and complete fees; do not remove ceilings based on later questions.

Origins: [contribution-gas32-20261119/REVIEW.md](../../reports/contribution-gas32-20261119/REVIEW.md).

### E16 — Synthetic header versus actual execution/provider/fee capacity

**qualification_open**; related original IDs: Q02.

Header clamp does not authenticate Nitro transaction capacity. Last observed execution32M is dated13November;19November identity refresh failed before state. Candidate fee approvals remainfalse/null.

Next: Freshly verify real transaction/block and call/estimate/trace bounds, complete Nitro fees and explicit ETH budgets.

Origins: [contribution-gas32-20261119/REVIEW.md](../../reports/contribution-gas32-20261119/REVIEW.md), [network/REVIEW.md](../../reports/gas-profiles-20261113/network/REVIEW.md).

### E17 — Fresh F6 construction, consumers and rollout

**qualification_open**; related original IDs: Q02, Q04, Q05, Q06.

Fresh private layouts/source/runtime/Factory6 pins need new exact construction and matching consumers. Older constructor receipts and source9/site profiles are not new F6 acceptance.

Next: Review only affected constructors/bindings/workloads; preserve all old deployments/journals and false approvals.

Origins: [activation-final-six-20261118/REVIEW.md](../../reports/activation-final-six-20261118/REVIEW.md), [royalty-rounds-20261118/CONSUMER_REVIEW.md](../../reports/royalty-rounds-20261118/CONSUMER_REVIEW.md).

### E18 — Latest-codec full canonical coordinator cutover

**qualification_open**; related original IDs: Q03, Q06.

Actual Rewards/canonical child export/import/abort proves finite logical rows/backing/current-owner properties; typed lifecycle seams do not qualify the complete deployed coordinator cutover.

Next: Qualify full fresh coordinator/backing/abort/contract-holder operation without flattening or relabeling old state.

Origins: [activation-final-six-20261118/REVIEW.md](../../reports/activation-final-six-20261118/REVIEW.md), [royalty-rounds-20261118/CONSUMER_REVIEW.md](../../reports/royalty-rounds-20261118/CONSUMER_REVIEW.md).

### E19 — Actual release-specific keeper recovery

**qualification_open**; related original IDs: Q06.

The recorded3implementation files still exactly match current source. Inert signer/recovery-only dispatcher,15stopped owned units and finite host observations retain their limits.

Next: Qualify actual Cast/keys/provider/full normal loop/DNS-body variants/disk/off-host fencing/restore/alerts/key rotation/soak.

Origins: [q06-keeper-recovery-20261117/REVIEW.md](../../reports/q06-keeper-recovery-20261117/REVIEW.md).

### E20 — Failed external currencies and recipients

**retained_structural_limit**; related original IDs: L03, L13.

Bounded reads and exact backing do not make arbitrary frozen/taxed/malicious tokens transferable or truthful. Their payouts/canonical completion can remain blocked; principal legs are atomic per NFT.

Next: Keep reviewed admission, healthy-subset claims, explicit unresolved assets and recovery; no universal payout promise.

Origins: [royalty-rounds-20261118/REVIEW.md](../../reports/royalty-rounds-20261118/REVIEW.md), [launch-workload-20261117/REVIEW.md](../../reports/launch-workload-20261117/REVIEW.md).

### E21 — Deferred inaccurate royalty status comment

**deferred_editorial**; related original IDs: Q07.

The inline sketch still says10/12/12 while actual fields are16/16/16+48; current external/operator descriptions are correct.

Next: Fix with the next justified source revision and exact new pins, not a comment-only invalidation of the frozen build.

Origins: [activation-final-six-20261118/REVIEW.md](../../reports/activation-final-six-20261118/REVIEW.md).

### E22 — Rejected engineering branches

**retired_proposal**; related original IDs: Q03.

Rejected LP fusion, old packing probes/slower codec or tick branches are engineering experiments, not unfinished product requirements. Later adopted F6 packing is a different separately reviewed design.

Next: Preserve failures; do not revive these as launch blockers.

Origins: [q03-activation-gas-20261117/REVIEW.md](../../reports/q03-activation-gas-20261117/REVIEW.md), [activation-gas-20261118/REVIEW.md](../../reports/activation-gas-20261118/REVIEW.md), [activation-final-six-20261118/REVIEW.md](../../reports/activation-final-six-20261118/REVIEW.md).

### E23 — Stale current guidance and sale-end boundary

**resolved_documentation**; related original IDs: R27, L09, Q08.

Consolidation replaces obsolete remaining20M/C08/Factory5/current-size prose; claims are source-labelled. Sale-end revision at exact old-end equality remains allowed if new end is future and opening is not finalized.

Next: Use current32M/F6 facts and exact setter boundaries; keep original reports and previous dirty docs archived.

Origins: [contribution-gas32-20261119/REVIEW.md](../../reports/contribution-gas32-20261119/REVIEW.md), [activation-final-six-20261118/REVIEW.md](../../reports/activation-final-six-20261118/REVIEW.md), [five-report-consolidation-20261117/RECONCILIATION.json](../../reports/five-report-consolidation-20261117/RECONCILIATION.json).

### E24 — Capacity/admission and pre-seal checklist versus readiness

**implemented_preparation_qualification_open**; related original IDs: Q03, Q05.

Capacity16 is not16admitted tokens. Planner currency/balance/sync-gas reads are explicit but unverified; source changed after the launch record. No unknown input creates approval.

Next: Qualify exact chosen list and current graph; do not count old pre-seal checks as new F6 execution.

Origins: [launch-workload-20261117/REVIEW.md](../../reports/launch-workload-20261117/REVIEW.md), [royalty-rounds-20261118/REVIEW.md](../../reports/royalty-rounds-20261118/REVIEW.md).
