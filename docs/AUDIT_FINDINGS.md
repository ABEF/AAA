# Consolidated audit findings

The single current findings register; consolidation baseline `fdd599c7698d0e1c0709a4a8b50130e5557ba508`, with wallet follow-through against `4ecfadf3`, reviewed27 November2026.
The [sole Todo](../TODO.md) owns all83 task statuses (35done/40progress/7todo/1excluded). Finding IDs below are stable provenance, not a new vulnerability or test count. Historical checks were not rerun for consolidation. The subsequent affected wallet checks and new isolated F6/provider observations have separate source scopes in the current review; they do not relabel old results.

## Current actionable findings and qualification

| Stable ID | Current status and exact remaining action | Owning Todo |
| --- | --- | --- |
| Q01 | **Open external qualification; pool choice deferred.** Two genuinely independent ETH/fixed-ZZZ exposures, updater/control/freshness and useful bidirectional execution at post-withdrawal depth. Two proxies of one aggregator or two ETH feeds through one ZZZ pool do not supply independence. Keep spot/no-TWAP and the operator-deferred production-pool choice; the supplied pool remains an isolated test target. Aliases: `MRQ01–04, MARKET-MR-02–14, G1–G2, E16`. | [dual-price-qualification](../TODO.md#task-dual-price-qualification), [creator-zzz-price](../TODO.md#task-creator-zzz-price), [pons-qualification](../TODO.md#task-pons-qualification), [creator-market-controls](../TODO.md#task-creator-market-controls), [creator-input-liquidity](../TODO.md#task-creator-input-liquidity), [lp-execution-routing](../TODO.md#task-lp-execution-routing) |
| Q02 | **Open actual provider/release envelope.** Qualify exact current constructor arguments/immutables, real transaction/call/estimate/trace capacity, complete L1/L2 fees and funding. The selected non-live32M/full20% contribution candidate does not change12M legacy defaults,24M/full25% maintenance,12M/full20% claims or profile2 adoption requirements. Fresh local F6 construction is complete within its controlled scope; public release inputs and provider acceptance are separate. Aliases: `E15–17, DEPLOY-DEP-19–21, G3/G8`. | [deployment-initcode](../TODO.md#task-deployment-initcode), [native-production-preflight](../TODO.md#task-native-production-preflight), [testnet-rehearsal](../TODO.md#task-testnet-rehearsal), [authorities-prices](../TODO.md#task-authorities-prices) |
| Q03 / MW01 | **Open direct cold maximum-state capacity.** The64-slow-currency/two-LP opening-ZZZ case estimates27,142,801; full20% is32,571,362 against32M. At least476,135 estimate reduction remains. Separately paid sync then fresh activation fits its two budgets, but does not fix the direct cold path. Qualify remaining currency/order/lifetime/full-operation rectangles and gas-sized claim subsets;32 entries is not universal gas admission. Aliases: `LPQ05, NCA06, RA05, E12–15, G9`. | [activation-assets](../TODO.md#task-activation-assets), [activation-quotes](../TODO.md#task-activation-quotes), [native-production-preflight](../TODO.md#task-native-production-preflight), [security-share-accounting](../TODO.md#task-security-share-accounting), [mainnet-fork](../TODO.md#task-mainnet-fork) |
| Q04 | **Open actual authority and dependency controls.** Select actual governance/bootstrap/keeper/guardian/payee identities, contract-wallet outer envelopes, key recovery and fixed-token/periphery/proxy powers. Immediate governance and paused explicit emergency trust remain approved design choices; hashes do not remove key loss or malicious-configuration risk. Aliases: `L06, G4, DEPLOY-DEP-13/15`. | [authorities-prices](../TODO.md#task-authorities-prices), [security-governance](../TODO.md#task-security-governance), [security-dependencies](../TODO.md#task-security-dependencies), [creator-market-controls](../TODO.md#task-creator-market-controls) |
| Q05 | **Open platform/content qualification; custom Merkle selected.** Qualify actual custom OpenSea intake, exact free TEAM/paid prices, payer/caller/stage/gross-fee-net terms, immutable content and observed metadata delivery. Standard Studio Merkle incompatibility is known; signed adaptation remains unselected. Qualify original-request VRF ABI/proof/funding/callback/rotation and same-result retry; a pinned OpenVRF lead is not an adopted provider. V10 peers require the same SeaDrop address/runtime/mint plan, so canonical replacement cannot rotate failed mint transport. NFT/helper completion precedes upstream payment callbacks; cached payouts and the upstream guard are the boundary, not a claimed post-payment NFT fingerprint check. Aliases: `RA03–04, META-MANUAL-M8, DEPLOY-DEP-14/17/18, L09–11`. | [opensea-mint](../TODO.md#task-opensea-mint), [fair-draw](../TODO.md#task-fair-draw), [authorities-prices](../TODO.md#task-authorities-prices), [metadata-ops](../TODO.md#task-metadata-ops) |
| Q06 | **Open matching consumer and operating adoption.** Prepare/review/re-pin matching checkpoints, writer/checker/tools and policies; preserve exact original journals/packages/releases. Public activation/growth/claim submission remains undecided; shared browser signing stays Anvil-only. Finite stock Cast, timer, key, storage and desktop-kit recovery proofs do not close physical second-host/OS/signer recovery, old-host/restart fencing, actual providers/channels, power-loss durability or sustained operation. Spending counters remain per-sender journal, so rotation must review combined old/new spending and unresolved commitments; a new journal does not reset project-wide exposure. Idle-only scheduling/backlog economics and long-term gas/archive/service funding remain operating choices; perpetual rights do not fund perpetual services. Heartbeat stays user-paused. Aliases: `E19, K26-H1, CWR08, G9, F03/F08, HR1111-19`. | [wallet](../TODO.md#task-wallet), [portfolio](../TODO.md#task-portfolio), [transaction-ui](../TODO.md#task-transaction-ui), [host-services](../TODO.md#task-host-services), [keeper-guardrails](../TODO.md#task-keeper-guardrails), [keeper-recovery](../TODO.md#task-keeper-recovery), [financial-history](../TODO.md#task-financial-history) |
| Q07 | **Open independent audit and release sign-off.** Review exact final source/build/dependency/workload and authority artifacts independently, remediate findings and approve deployment, sealing and public opening separately. Static inventories, historical pass totals and local source publication are not release approval. Aliases: `G10, E11`. | [audit-release](../TODO.md#task-audit-release), [security-integration](../TODO.md#task-security-integration), [testnet-rehearsal](../TODO.md#task-testnet-rehearsal) |
| CWR07 / NCA04 | **Open complete-wallet freshness, maximum normal F6, lineage, provider and adoption.** The actual normal32-NFT F6 fixture exposed a valid304131-gas LP view above the old250k helper cap. Approved500k LP views/three-NFT groups keep24M total and all API/financial/transaction limits; source correction and staged affected/new verification are recorded in the current review. The1000-NFT/66-descriptor affected model fits every request (max603logical reads/173175bytes/7.437s), but17independent earnings pages take121.438s with zero physicalHTTP. 80coreGETs alone do not qualify120s. The historical source9 run98.834s/finalage116.018s keeps its thin3.982s margin and original scope. The old1000-NFT substitute Access/Registry snapshot cannot supply normal fullgraph/history proof. Latest request/digest reuse qualifies only the actual32-NFT/66-descriptor wallet plus eight cards in83.708s/36GETs; all final checks run, and CWR09 remains a separate moving-head gap. Provider constructor wire/archive observations and actual32-NFT Ubuntu/source10 work stay separately scoped; matching checkpoints and service rollout require review. Aliases: `LPQ03, NCA02/04, WG02`. | [portfolio](../TODO.md#task-portfolio), [financial-history](../TODO.md#task-financial-history), [live-history-ui](../TODO.md#task-live-history-ui), [wallet](../TODO.md#task-wallet), [host-services](../TODO.md#task-host-services) |
| CWR09 | **Confirmed moving-head card availability gap.** Source10 reads NFT detail and its earnings through separate latest-state GETs, then correctly requires equal block hashes. A newly confirmed block between them can therefore leave card earnings unavailable. Preserve exact anchor matching; prepare an explicit fixed-block earnings/card capability with live canonical/depth/age checks. A fixed-head local latency pass would not close this gap or qualify a live moving chain. No NFT rights or accounting error is inferred. | [portfolio](../TODO.md#task-portfolio), [live-history-ui](../TODO.md#task-live-history-ui), [financial-history](../TODO.md#task-financial-history) |
| E18 | **Open complete fresh canonical cutover.** Actual ledger/child/component and current-semantic offline history proofs retain their finite scopes. Complete fresh latest-codec coordinator capture/import/backing/abort, contract-holder successor compatibility and target operating cutover still need qualification. Preserve logical full-width phases; never flatten old physical slots or relabel historical deployments/checkpoints. Aliases: `historical/HC-06–09, G9`. | [security-chain-recovery](../TODO.md#task-security-chain-recovery), [migration-framework](../TODO.md#task-migration-framework), [destination-slots](../TODO.md#task-destination-slots), [custody-composition](../TODO.md#task-custody-composition) |
| CF-DEP-01 | **Unverified dependency-qualified accounting question.** Review whether an actually reachable admitted token/Permit2/periphery callback after the last harvest and before increase can net a late fee credit against principal debt/refunded idle; the specific increase effect is not reproduced. Related late pre-close/burn fees can enter principal under compromised dependencies. Ordinary outside transactions cannot interleave inside the atomic conventional-token/hookless flow. Establish real powers/reachability before any guard/design change. Aliases: `daily-contract-question, residual-boundary-1, harvesting-late-fees`. | [security-dependencies](../TODO.md#task-security-dependencies), [security-share-accounting](../TODO.md#task-security-share-accounting), [creator-market-controls](../TODO.md#task-creator-market-controls) |
| Q08 / E21 / WPA-comments | **Fits now; editorial follow-up deferred.** Tight source/runtime/initcode headroom is a future-change constraint, not another failing size gate. Royalty status sketch10/12/12 versus actual16/16/16+48, ActivationAssets WETH example and IZZZ portfolio1 label remain comment-only follow-ups for the next justified frozen-source revision and fresh pins. Current operating descriptions use actual behavior. Aliases: `WPA-06, E21`. | [audit-release](../TODO.md#task-audit-release), [callable-reference](../TODO.md#task-callable-reference), [deployment-initcode](../TODO.md#task-deployment-initcode) |
| EV-SCOPE | **Historical evidence limits retained.** Keep failed/interrupted stages, source-specific reused results, missing raw artifacts, request-alias limits and synthetic seams explicit. c811 aggregate remains NONPASS with missing final physical reads; its core saved-hash recovery is separately reconciled. Later successful c814/c828 proofs do not retroactively supply that missing evidence. New documentation consolidation executes no unchanged tests or operating campaign. Aliases: `L16–17, K26-E1/E2, DEPLOY-DEP-09`. | [historical-findings](../TODO.md#task-historical-findings), [local-verification](../TODO.md#task-local-verification), [audit-release](../TODO.md#task-audit-release), [keeper-recovery](../TODO.md#task-keeper-recovery) |

The current output/storage fixes compact every log event/field and health, bound the two confirmation ID previews with full count/completeness/full-list digest, and refuse oversized selection/export/archive publication without deleting originals. The source-scoped29-new-method result and original staged Windows failures belong to the consolidated current review; they do not become fresh historical regressions. Full journal inventories, pending/accounting, default serialization, durable write order and all economic/resource limits remain. Source13/19 membership stays, but current file pins change; old packages still need their original matching release/configuration/policy. A source migration is not an operational `rebind`, and publication approves no service/heartbeat restart.

The previous-source Source10 failure remains precise: after correcting the
isolated package's missing pure physical-reader dependency, its wallet page
passes511reads/1,019POST/3.025s. The complete32-NFT/66-descriptor journey reaches
33GETs/117.628s and refuses at the120-second snapshot boundary in card history.
Its20core API replies finished by76.450s; final complete-wallet/independent-total
checks were not reached at that old source. New bounded request/digest reuse now
completes the affected32-NFT/66-descriptor wallet plus all eight cards in83.708s,
with36GETs,96 independent total reads, card checks and final identity/freshness.
The first83.825s digest-candidate run remains NONPASS from evidence size; only
the final output partition changed, keeping each artifact1MiB and all assertions.
CWR07 remains open for full normal1000-NFT/lineage/provider/adoption; CWR09
separately requires coherent NFT/earnings anchors on a moving chain. Neither the
historical timeout nor incomplete evidence is relabelled as a PASS.

## Retained policies and structural limits

| Stable IDs | Retained boundary; no automatic redesign |
| --- | --- |
| L01 | Extra compound waiting is software policy. Authorized alternate software can use contract-permitted compounding; no new on-chain restriction is implied. |
| L02/L04 | Unallocated royalty recovery uses active weights at inclusion; opening/zero-cohort/unadmitted funds may remain held. reviewHash is not a frozen beneficiary cohort. |
| L03/L13/E20 | Arbitrary tokens, broken dependencies and rejecting receivers cannot be forced to transfer. Terminal ETH+ZZZ payment is atomic per NFT and can defer healthy ETH too; funded rights remain. |
| L05 | Complete20-unit baskets retain80/10/5/5; sub20 barrier dust goes100% to incumbent individual owners. Exact current LP allocation supersedes the old allocated-fraction H05 concern, not upstream truncation. |
| L06/L07 | Explicit paused governance emergency may waive financial guards and accept severe loss. Per-operation ceilings do not impose a declined cumulative turnover-loss cap. No keeper force fallback. |
| L08/L10 | Generic seal does not qualify the chosen immutable helper/token/venue/content graph. Wrong nonempty content and fixed identity can be irreversible. |
| L09/L11 | Expired nonzero mint end cannot be reopened; exact equality retains its defined setter boundary. Unanswered original VRF requests can block rotation; retry/replay never permits reroll. |
| L12 | Four historical buckets/reservations, terminal return and canonical retirement remain permanent lifecycle choices, not generic unpause/reset operations. Current handoff is same-chain and requires truthful source/dependency availability; it does not solve permanent source-chain loss or restore a bridge. |
| L14 | Direct raw fixed-ZZZ LP entitlement remains deliberate recovery; normal LP ETH conversion is separate. Royalties remain original-currency rights with no restored royalty-conversion requirement. |
| L15 | Sampled confirmation/jitter and own-swap proof are not continuous price history, economic independence or MEV immunity.60/40 residual placement is not continuous or optimal rebalancing. |
| L16/L17 | Missing raw artifacts, generic revert controls and legacy wrapped/Pons/synthetic seams limit original evidence. Skipped/old tests never qualify current markets. Old nonce35/browser incidents have no retroactively proven completion or nonce/history/reset authority. |
| CLP-20 | Raw residual close/released incumbent compound can leave attributed idle above the governed ceiling; a new contribution correctly refuses instead of spending entrant funds on incumbent assets. Use eligible maintenance or explicit reviewed recovery; no automatic bypass. |

The profile2 offline checkpoint follow-through also removes repeated canonical
RPC work inside one build using the existing bounded cache. It preserves all
economic comparisons and live header/chain/final checks; legacy0 and all budgets
remain. Four new hook tests cover reuse, cleanup, old source refusal and limits;
actual economic/F6/HTTP acceptance has its own source-scoped evidence. This is
a source improvement, not closure of Q06/CWR07 or permission to adopt old seeds.

## Resolved, superseded and scoped advances

- Wallet profile2 review also binds each accounting7 live ordinal/inverse pair to complete mint history, rejects contradictory prefetched replies as integrity failures, indexes conversion history once per NFT and avoids materializing unselected paid-currency rows. These are current source fixes with targeted new/affected verification; old historical results are not relabelled.

- R01–R37 and N01–N02 retain their original tool/source/documentation/fixture dispositions; no fresh rerun or blanket all-source closure is inferred. Stop-before-sign, watchdog failover, nonzero signer hashes, protected locks, original fee/receipt anchor checks and the newer resource bounds remain source fixes with finite evidence.
- E03/E10 matched F6 cold/component gas refusals closed for the exact recorded workloads. MW01 remains the separate maximum-state direct cold refusal. Optional paid sync is an operating option, not a cheaper single transaction.
- E17 local construction, LPQ03 normal admission, and E19 stock recovery gained later finite evidence as described above. The broader external/deployment/operating gates remain open. RA03 signed adaptation remains unselected; qualifying current custom Merkle is the chosen platform work.
- Power, creator inboxes, USDG/USDC/WETH principal input, integrated bridge/remote custody, arbitrary external custody-address exit, timelock/executor and fresh royalty-conversion requirements are superseded architectures. General callback, authority, dependency, conservation and lifecycle risks survive where current paths still exercise them.

## Legacy64 registry: exact IDs and source scopes

Registry A: `reports/five-report-consolidation-20261117/RECONCILIATION.json`, SHA-256 `a0c66ab2ae7aa2eaa0990bf28f195352ecbb4a9be9fd9acaf0255311b7487e76`,64 rows. Registry B: `reports/seven-report-consolidation-20261119/RECONCILIATION.json`, SHA-256 `bf7907f397057cd7a62ee00c1148be0f737339756eb9988825c87f1fcf065c44`,64 carried rows plus24 separate later assessments. Both are retrievable from the Git baseline above; old JSON/Markdown need not remain duplicate current guidance. The explicit current overlays in this document do not rewrite the original dispositions.

| ID | Original classification | Finding |
| --- | --- | --- |
| R01 | resolved_tool | Manual review gas envelope was reported but not frozen |
| R02 | resolved_tool | Dangling output preflight missed occupied destination |
| R03 | resolved_documentation | Converter control notes described wrong units |
| R04 | resolved_documentation | Nested tuple notes lost field explanations |
| R05 | resolved_documentation | Shared struct examples reused another operation meaning |
| R06 | resolved_source | Empty artwork root could be sealed irreversibly |
| R07 | resolved_source | Slow keeper reads could miss newly due harvest or compound |
| R08 | resolved_test_or_fixture | Canonical-preparation positive fixture failed before body |
| R09 | resolved_test_or_fixture | Royalty recovery fuzz allowed permanent remainder |
| R10 | resolved_source | Foreign-home Vault construction was accepted |
| R11 | resolved_source | Bare immutable artwork scheme consumed setup |
| R12 | resolved_source | Wrong fresh reservation ID consumed permanent capacity |
| R13 | resolved_test_or_fixture | Between-anchor tests mutated the first pinned block |
| R14 | resolved_test_or_fixture | Exact-source import test lacked a negative tamper case |
| R15 | resolved_test_or_fixture | Legacy annotation compatibility checked only two fields |
| R16 | resolved_test_or_fixture | Documentation semantic assertions searched whole page |
| R17 | resolved_test_or_fixture | Enabled harvest test did not assert due submission |
| R18 | resolved_test_or_fixture | Seal tests accepted unrelated reverts |
| R19 | resolved_test_or_fixture | Payout and callback tests omitted economic rollback state |
| R20 | resolved_test_or_fixture | Tiny royalty coverage lacked tranche rotation and transfer |
| R21 | resolved_test_or_fixture | Current financial venue fixtures lacked execution readers |
| R22 | resolved_test_or_fixture | Native balance cheatcodes invalidated rollback modeling |
| R23 | resolved_test_or_fixture | Invariant replacement plans lacked validation child |
| R24 | resolved_test_or_fixture | Positive fixtures retained bare artwork schemes |
| R25 | resolved_tool | Normal profile validator rejected approved read permission |
| R26 | resolved_tool | Pre-seal readiness requested private storage getter |
| R27 | resolved_tool | Current trusted build admission and stale test family labels |
| R28 | resolved_tool | Last manual head could orphan final simulated anchor |
| R29 | resolved_test_or_fixture | Default97% test wrongly rejected98% deployment |
| R30 | resolved_test_or_fixture | Explicit99% policy test wrongly rejected99% deployment |
| R31 | resolved_test_or_fixture | Native donation assertion omitted19 earned units |
| R32 | resolved_test_or_fixture | Royalty window test was named FullDay |
| R33 | resolved_selected_verification | Repairing fixtures did not prove dependent economic behavior |
| R34 | resolved_tool | New pre-seal planner dereferenced unknown SeaDrop terms |
| R35 | resolved_tool | Enabled composite execution source allowed8decimals |
| R36 | resolved_tool | Mutually matching wrong native pins passed offline plan |
| R37 | resolved_tool | Protocol implementations could masquerade as external feeds/VRF |
| L01 | accepted_policy | Extra compound waiting rule is service-only |
| L02 | accepted_policy | Unallocated royalty recovery uses inclusion-time active weights |
| L03 | structural_limit | Terminal principal sends ETH and ZZZ atomically per NFT |
| L04 | accepted_policy | Opening/zero-cohort/unadmitted royalties are not always immediately allocated |
| L05 | accepted_policy | LP dust barrier is a split exception |
| L06 | accepted_policy | Emergency governance may omit financial protections |
| L07 | accepted_policy | Per-operation caps do not bound cumulative turnover losses |
| L08 | structural_limit | Generic seal does not prove selected SeaDrop/converter release binding |
| L09 | accepted_policy | Expired nonzero mint end cannot be reopened |
| L10 | structural_limit | Wrong-but-nonempty content or fixed venue/token graph is irreversible |
| L11 | structural_limit | Pending unanswered VRF can block rotation and replacement |
| L12 | accepted_policy | Permanent reservation, terminal exit and canonical retirement do not unpause open |
| L13 | structural_limit | Arbitrary tokens and rejecting receivers cannot be forced to work |
| L14 | accepted_policy | Raw fixed-ZZZ LP claims remain deliberate recovery |
| L15 | structural_limit | Own-swap proof and jitter do not provide manipulation immunity |
| L16 | historical_evidence_limit | Generic revert, staged metadata and missing raw logs limit assurance |
| L17 | historical_evidence_limit | Old wrapped/Pons fork and royalty-converting cases remain historical |
| Q01 | release_qualification_open | Independent ETH/ZZZ sources and usable bidirectional routes/depth |
| Q02 | release_qualification_open | Complete target fees, RPC capacity and final constructor/operation gas |
| Q03 | release_qualification_open | Maximum-state gas and activation/currency/claim workload |
| Q04 | release_qualification_open | Authorities and contract-wallet envelopes |
| Q05 | release_qualification_open | OpenSea, VRF and immutable content delivery |
| Q06 | release_qualification_open | Integration rollout, hosting and restart/backup/recovery operation |
| Q07 | release_qualification_open | Independent audit and release remediation/approval |
| Q08 | structural_limit | Tight runtime/initcode headroom |
| N01 | resolved_this_consolidation | Passing count alone could admit substituted evidence methods |
| N02 | resolved_this_consolidation | Complete pre-seal input omitted disabled ordinary-pool stop |

| Later ID | Original source-scoped classification | Finding / current overlay |
| --- | --- | --- |
| E01 | resolved_source | Stop after durable intent could launch the signer |
| E02 | resolved_source | Completed bounded RPC failover could falsely expire watchdog |
| E03 | resolved_finite_workload | Matched cold activation gas refusals |
| E04 | implemented_source | Receipt-tree cost replaced by bounded exact royalty rounds |
| E05 | resolved_source | Faulty activation reads and caller-manufactured deferral |
| E06 | resolved_source | Synchronized replacement prefunds counted twice |
| E07 | implemented_source | Compact LP/royalty codecs and full-width rights |
| E08 | implemented_source | Transaction Pricing and static proof/Oracle optimizations |
| E09 | retained_behavior_difference | Impossible feed values have different failure precedence |
| E10 | resolved_finite_workload | Intermediate zero-fee component regression |
| E11 | resolved_source | Current static CI/source-build wiring |
| E12 | qualification_open | Maximum whole-operation workload. Later maximum-workload and claim partitions advance finite coverage; MW01 direct cold gas and remaining full rectangles stay open. |
| E13 | retained_limit_qualification_open | Claim entry count versus cold batch gas. Later exact cold batch/normal admission evidence supplies finite current-source cases;12M/full20% and gas-aware subset admission remain. |
| E14 | retained_policy | Optional royalty pre-sync and growth behavior |
| E15 | accepted_policy | Selected32M gas-only contribution profile |
| E16 | qualification_open | Synthetic header versus actual execution/provider/fee capacity |
| E17 | qualification_open | Fresh F6 construction, consumers and rollout. Fresh controlled F6 construction subsequently completed; exact public-release inputs/provider/whole-cutover qualification remains open under Q02/Q04/Q06. |
| E18 | qualification_open | Latest-codec full canonical coordinator cutover |
| E19 | qualification_open | Actual release-specific keeper recovery. Later finite normal stock Cast/key/storage/timer/desktop-kit recovery evidence advances this old inert-only description; actual host loss/fencing/channels/soak remains open. |
| E20 | retained_structural_limit | Failed external currencies and recipients |
| E21 | deferred_editorial | Deferred inaccurate royalty status comment |
| E22 | retired_proposal | Rejected engineering branches |
| E23 | resolved_documentation | Stale current guidance and sale-end boundary |
| E24 | implemented_preparation_qualification_open | Capacity/admission and pre-seal checklist versus readiness |

## Original310 records: split classifications and provenance

Registry C: `reports/whole-project-audit-20261116/HISTORY_DISPOSITIONS.json`, SHA-256 `41720318e7354676dae8717cd69b66a3c4ad2e877c896ea35e080ba9cd134cf8`. Each `C:n` below is exact JSON pointer `/all_original_record_dispositions/n`; that record retains original matrix/pointer/record hash and prior individual assessments. These310 overlapping records are **not310 open bugs or310 closures**. The current topical actions above are an overlay, not a new individual semantic re-audit.

Codes preserve prior split-assessment labels: **I** implemented/fixed/preserved with source-scoped evidence; **O** explicitly open qualification; **S** superseded requirement; **L** accepted risk/structural limit; **B** remaining action or retained boundary not collapsed into a binary status; **H** historical assessment only. A record can have multiple codes. Current Todo status is independent.

| Prior family | Split codes | Original IDs and exact registry positions |
| --- | --- | --- |
| authority | B/I/O | `historical/HC-02` (C:29), `historical/HC-36` (C:63), `historical/HC-52` (C:79) |
| backend | H | `historical/OPS-RS-46-5` (C:207) |
| backend | I | `historical/FB-03` (C:2), `historical/FB-04` (C:3), `historical/HC-42` (C:69), `historical/OP-14` (C:94), `historical/OP-35` (C:115), `historical/OPS-RS-20-3` (C:155) |
| backend | I | `historical/OPS-RS-46-4` (C:206), `historical/RO-13` (C:227), `later/N01` (C:235), `later/N04` (C:238), `later/T01` (C:243), `later/T02` (C:244) |
| backend | I | `later/M03` (C:255), `later/D01` (C:257), `later/K04` (C:304), `later/T10-01` (C:308), `later/T10-02` (C:309) |
| backend | L | `historical/FB-25` (C:24), `historical/FB-28` (C:27), `historical/OPS-RS-03-1` (C:128), `historical/OPS-RS-08-1` (C:135), `historical/OPS-RS-27-1` (C:166), `historical/OPS-RS-39-1` (C:186) |
| backend | L | `later/K07` (C:307) |
| canonical | B/I/O | `historical/FB-15` (C:14), `historical/FB-22` (C:21), `historical/HC-07` (C:34), `historical/HC-09` (C:36), `historical/OP-25` (C:105), `historical/OP-31` (C:111) |
| canonical | I/L/O | `historical/HC-06` (C:33), `historical/OPS-RS-45-3` (C:201) |
| compound | H | `historical/OP-22` (C:102), `historical/OPS-RS-45-4` (C:202), `later/Q04` (C:269) |
| compound | I | `historical/HC-28` (C:55), `historical/HC-32` (C:59), `historical/HC-33` (C:60), `historical/OP-03` (C:83), `historical/OP-05` (C:85), `historical/OP-08` (C:88) |
| compound | I | `historical/OP-10` (C:90), `historical/OP-11` (C:91), `historical/OP-17` (C:97), `historical/OP-32` (C:112), `later/N03` (C:237), `later/M02` (C:254) |
| compound | I | `later/C01` (C:263), `later/C05` (C:289), `later/K03` (C:303) |
| compound | I/L/O | `historical/OP-09` (C:89), `later/K01` (C:301) |
| compound | I/O | `historical/OP-15` (C:95) |
| compound | L | `historical/OP-34` (C:114) |
| compound | O | `later/C11` (C:295) |
| compound | S | `historical/OPS-RS-31-4` (C:176), `historical/OPS-RS-44-5` (C:198), `historical/OPS-RS-47-3` (C:210), `later/T04` (C:246) |
| confirmation | B/I | `later/P05` (C:284), `later/C04` (C:288), `later/K02` (C:302) |
| confirmation | B/I/L | `historical/RO-01` (C:215) |
| confirmation | B/I/O | `historical/HC-30` (C:57), `historical/HC-31` (C:58), `historical/HC-34` (C:61), `historical/HC-35` (C:62), `historical/HC-37` (C:64), `historical/OP-16` (C:96) |
| confirmation | B/I/O | `historical/OP-21` (C:101), `historical/OPS-RS-09-3` (C:138), `historical/OPS-RS-17-1` (C:148) |
| entry | B/I | `historical/OPS-RS-44-1` (C:194), `historical/OPS-RS-44-2` (C:195), `historical/OPS-RS-46-1` (C:203), `historical/OPS-RS-46-2` (C:204), `historical/RO-04` (C:218) |
| entry | B/I/O | `historical/FB-01` (C:0), `historical/HC-20` (C:47), `historical/HC-50` (C:77), `historical/OPS-RS-12-1` (C:141), `historical/OPS-RS-12-2` (C:142), `historical/OPS-RS-15-1` (C:145) |
| entry | B/I/O | `historical/OPS-RS-20-2` (C:154), `historical/OPS-RS-43-1` (C:193) |
| evidence | B/I | `historical/FB-27` (C:26), `historical/HC-39` (C:66), `historical/HC-40` (C:67), `historical/OP-01` (C:81), `historical/OP-19` (C:99), `historical/OP-20` (C:100) |
| evidence | B/I | `historical/OP-24` (C:104), `historical/OP-40` (C:120), `historical/OPS-RS-05-1` (C:131), `historical/OPS-RS-07-1` (C:134), `historical/OPS-RS-10-1` (C:139), `historical/OPS-RS-13-1` (C:143) |
| evidence | B/I | `historical/OPS-RS-14-1` (C:144), `historical/OPS-RS-16-1` (C:147), `historical/OPS-RS-18-1` (C:150), `historical/OPS-RS-22-1` (C:158), `historical/OPS-RS-23-1` (C:159), `historical/OPS-RS-24-1` (C:160) |
| evidence | B/I | `historical/OPS-RS-24-2` (C:161), `historical/OPS-RS-24-3` (C:162), `historical/OPS-RS-25-1` (C:163), `historical/OPS-RS-26-2` (C:165), `historical/OPS-RS-29-2` (C:170), `historical/OPS-RS-30-1` (C:172) |
| evidence | B/I | `historical/OPS-RS-32-1` (C:177), `historical/OPS-RS-34-1` (C:179), `historical/OPS-RS-35-1` (C:180), `historical/OPS-RS-35-2` (C:181), `historical/OPS-RS-36-1` (C:182), `historical/OPS-RS-37-1` (C:183) |
| evidence | B/I | `historical/OPS-RS-37-2` (C:184), `historical/OPS-RS-41-4` (C:191), `historical/OPS-RS-42-1` (C:192), `historical/OPS-RS-48-1` (C:211), `historical/OPS-RS-49-1` (C:212), `historical/OPS-RS-49-2` (C:213) |
| evidence | B/I | `historical/RO-06` (C:220), `historical/RO-07` (C:221), `historical/RO-12` (C:226), `historical/RO-18` (C:232), `historical/RO-20` (C:234), `later/N05` (C:239) |
| evidence | B/I | `later/N06` (C:240), `later/N07` (C:241), `later/T03` (C:245), `later/A01` (C:248), `later/A02` (C:249), `later/A03` (C:250) |
| evidence | B/I | `later/M01` (C:253), `later/D04` (C:260), `later/C02` (C:264), `later/Q06` (C:271), `later/R01` (C:276), `later/P06` (C:285) |
| evidence | B/I | `later/P07` (C:286), `later/C07` (C:291), `later/C08` (C:292), `later/H03` (C:297), `later/H04` (C:298), `later/H06` (C:300) |
| evidence | B/I/L | `historical/FB-21` (C:20), `later/B01` (C:272), `later/B02` (C:273), `later/B04` (C:275), `later/R02` (C:277), `later/C12` (C:296) |
| evidence | B/I/S | `historical/OP-33` (C:113), `historical/OPS-RS-26-1` (C:164), `historical/OPS-RS-28-1` (C:167), `later/H01` (C:261), `later/H02` (C:262) |
| evidence | I | `historical/FB-11` (C:10) |
| evidence | I/L/O | `later/Q03` (C:268), `later/C10` (C:294) |
| evidence | I/O | `historical/HC-51` (C:78), `historical/OP-28` (C:108), `historical/RO-11` (C:225), `later/T05` (C:247), `later/Q05` (C:270) |
| evidence | L | `historical/HC-49` (C:76), `later/N08` (C:242) |
| frontend | B/I | `historical/FB-05` (C:4), `historical/FB-06` (C:5), `historical/FB-07` (C:6), `historical/FB-08` (C:7), `historical/FB-10` (C:9), `historical/OP-29` (C:109) |
| frontend | B/I | `historical/OPS-RS-01-2` (C:125), `historical/OPS-RS-02-2` (C:127), `historical/OPS-RS-40-1` (C:187), `historical/OPS-RS-44-4` (C:197) |
| frontend | H | `historical/FB-09` (C:8) |
| frontend | I/O | `historical/FB-19` (C:18) |
| history | I | `historical/FB-12` (C:11), `historical/FB-13` (C:12), `historical/FB-14` (C:13), `historical/FB-20` (C:19), `historical/FB-26` (C:25), `historical/HC-16` (C:43) |
| history | I | `historical/HC-43` (C:70), `historical/OP-37` (C:117), `historical/OPS-RS-00-1` (C:121), `historical/OPS-RS-01-1` (C:124), `historical/OPS-RS-02-1` (C:126), `historical/OPS-RS-04-1` (C:129) |
| history | I | `historical/OPS-RS-44-3` (C:196), `historical/OPS-RS-46-3` (C:205), `later/C06` (C:290) |
| history | I/O | `later/C09` (C:293) |
| history | L | `historical/OPS-RS-00-3` (C:123), `historical/OPS-RS-04-2` (C:130) |
| history | S | `historical/OPS-RS-29-1` (C:169), `historical/OPS-RS-31-2` (C:174), `historical/OPS-RS-33-1` (C:178) |
| identity | B/I/O | `historical/HC-01` (C:28), `historical/HC-03` (C:30), `historical/HC-05` (C:32), `historical/HC-12` (C:39), `historical/HC-38` (C:65), `historical/OP-27` (C:107) |
| identity | B/I/S | `historical/RO-08` (C:222) |
| identity | I/L/S | `historical/FB-02` (C:1), `historical/FB-24` (C:23), `historical/HC-04` (C:31), `historical/OP-23` (C:103), `later/H05` (C:299) |
| marketplace | B/I | `historical/OP-38` (C:118) |
| marketplace | I/O | `historical/FB-17` (C:16), `historical/HC-44` (C:71), `historical/RO-17` (C:231) |
| metadata | B/I | `historical/FB-23` (C:22), `historical/OP-12` (C:92), `historical/OP-39` (C:119), `historical/OPS-RS-09-1` (C:136), `historical/RO-10` (C:224) |
| operations | H | `historical/HC-41` (C:68), `historical/OP-07` (C:87) |
| operations | I | `historical/OP-02` (C:82), `historical/OP-04` (C:84), `historical/OP-06` (C:86), `historical/RO-05` (C:219) |
| operations | L | `historical/OPS-RS-17-2` (C:149) |
| operations | S | `historical/OPS-RS-06-2` (C:133) |
| portfolio | B/I | `later/P01` (C:280) |
| randomness | B/I | `later/A04` (C:251) |
| randomness | I/O | `historical/HC-08` (C:35), `historical/RO-16` (C:230), `later/Q02` (C:267) |
| recovery | B/I | `historical/RO-09` (C:223) |
| recovery | B/I/O | `historical/HC-10` (C:37), `historical/HC-11` (C:38), `historical/OP-13` (C:93), `historical/OPS-RS-06-1` (C:132) |
| recovery | I/L/O | `historical/OP-26` (C:106) |
| release | H | `historical/OPS-RS-19-2` (C:152), `historical/OPS-RS-29-3` (C:171), `later/Q01` (C:266) |
| release | I | `historical/OP-18` (C:98), `historical/OP-36` (C:116), `later/N02` (C:236), `later/D02` (C:258), `later/K05` (C:305) |
| release | I/L/O | `historical/HC-45` (C:72) |
| release | L | `historical/OPS-RS-19-1` (C:151), `historical/OPS-RS-20-1` (C:153), `historical/OPS-RS-49-3` (C:214), `historical/RO-19` (C:233) |
| release | S | `historical/FB-18` (C:17), `historical/OPS-RS-21-1` (C:156), `historical/OPS-RS-28-2` (C:168), `historical/OPS-RS-38-1` (C:185), `historical/OPS-RS-41-3` (C:190), `historical/RO-02` (C:216) |
| release | S | `later/A05` (C:252) |
| revenue | B/I | `historical/OPS-RS-45-1` (C:199), `historical/OPS-RS-47-1` (C:208) |
| revenue | B/I/O | `historical/HC-13` (C:40), `historical/HC-17` (C:44), `historical/HC-47` (C:74), `historical/OPS-RS-00-2` (C:122), `historical/OPS-RS-31-1` (C:173) |
| routing | B/I | `historical/RO-03` (C:217), `historical/RO-15` (C:229), `later/M04` (C:256), `later/D03` (C:259), `later/R03` (C:278), `later/P02` (C:281) |
| routing | B/I | `later/P03` (C:282), `later/P04` (C:283), `later/C03` (C:287) |
| routing | B/I/L | `later/B03` (C:274), `later/K06` (C:306) |
| routing | B/I/O | `historical/HC-19` (C:46), `historical/HC-24` (C:51), `historical/HC-25` (C:52), `historical/HC-26` (C:53), `historical/HC-29` (C:56), `historical/OP-30` (C:110) |
| routing | B/I/O | `historical/OPS-RS-09-2` (C:137), `historical/OPS-RS-11-1` (C:140), `historical/OPS-RS-21-2` (C:157), `later/I01` (C:265) |
| routing | I/L/O | `later/R04` (C:279) |
| royalties | B/I/O | `historical/OPS-RS-31-3` (C:175) |
| royalties | I/O/S | `historical/FB-16` (C:15), `historical/HC-14` (C:41), `historical/HC-15` (C:42) |
| shares | B/I | `historical/OPS-RS-47-2` (C:209) |
| shares | B/I/O | `historical/HC-27` (C:54), `historical/HC-46` (C:73), `historical/HC-53` (C:80), `historical/OPS-RS-41-1` (C:188) |
| shares | B/I/S | `historical/OPS-RS-45-2` (C:200) |
| shares | I/L/O/S | `historical/HC-18` (C:45) |
| valuation | B/I | `historical/RO-14` (C:228) |
| valuation | B/I/O | `historical/HC-21` (C:48), `historical/HC-23` (C:50), `historical/HC-48` (C:75), `historical/OPS-RS-15-2` (C:146), `historical/OPS-RS-41-2` (C:189) |
| valuation | I/L/O | `historical/HC-22` (C:49) |

## Latest57 and later finding IDs

The separate57 source-scoped rows use Registry C `/latest57_dispositions_separate/n` and remain distinct from the310 original rows. Later resolved/open labels below keep their original evidence tier; custom-platform, market, constructor and operating advances use only the explicit current overlays above.

| Scoped ID | Prior disposition | Provenance |
| --- | --- | --- |
| META-MANUAL-M1 | resolved_before | C latest57:0 |
| META-MANUAL-M2 | resolved_before | C latest57:1 |
| META-MANUAL-M3 | resolved_before | C latest57:2 |
| META-MANUAL-M4 | resolved_before | C latest57:3 |
| META-MANUAL-M5 | accepted_limit | C latest57:4 |
| META-MANUAL-M6 | resolved_before | C latest57:5 |
| META-MANUAL-M7 | accepted_limit | C latest57:6 |
| META-MANUAL-M8 | open_external | C latest57:7 |
| META-MANUAL-MW1 | resolved_before | C latest57:8 |
| META-MANUAL-MR1 | resolved_before | C latest57:9 |
| META-MANUAL-MR2 | accepted_limit | C latest57:10 |
| META-MANUAL-MR3 | open_external | C latest57:11 |
| META-MANUAL-MR4 | open_external | C latest57:12 |
| META-MANUAL-MR5 | accepted_limit | C latest57:13 |
| META-MANUAL-MR6 | superseded | C latest57:14 |
| META-MANUAL-MR7 | accepted_limit | C latest57:15 |
| META-MANUAL-D1 | fixed_now | C latest57:16 |
| META-MANUAL-D2 | fixed_now | C latest57:17 |
| MARKET-MR-01 | fixed_now | C latest57:18 |
| MARKET-MR-02 | open_external | C latest57:19 |
| MARKET-MR-03 | open_external | C latest57:20 |
| MARKET-MR-04 | open_external | C latest57:21 |
| MARKET-MR-05 | open_external | C latest57:22 |
| MARKET-MR-06 | open_external | C latest57:23 |
| MARKET-MR-07 | open_external | C latest57:24 |
| MARKET-MR-08 | open_external | C latest57:25 |
| MARKET-MR-09 | open_external | C latest57:26 |
| MARKET-MR-10 | accepted_limit | C latest57:27 |
| MARKET-MR-11 | resolved_before | C latest57:28 |
| MARKET-MR-12 | open_external | C latest57:29 |
| MARKET-MR-13 | accepted_limit | C latest57:30 |
| MARKET-MR-14 | open_external | C latest57:31 |
| MARKET-MR-15 | accepted_limit | C latest57:32 |
| DEPLOY-DEP-01 | fixed_now | C latest57:33 |
| DEPLOY-DEP-02 | fixed_now | C latest57:34 |
| DEPLOY-DEP-03 | fixed_now | C latest57:35 |
| DEPLOY-DEP-04 | fixed_now | C latest57:36 |
| DEPLOY-DEP-05 | fixed_now | C latest57:37 |
| DEPLOY-DEP-06 | fixed_now | C latest57:38 |
| DEPLOY-DEP-07 | resolved_before | C latest57:39 |
| DEPLOY-DEP-08 | resolved_before | C latest57:40 |
| DEPLOY-DEP-09 | accepted_limit | C latest57:41 |
| DEPLOY-DEP-10 | resolved_before | C latest57:42 |
| DEPLOY-DEP-11 | fixed_now | C latest57:43 |
| DEPLOY-DEP-12 | accepted_limit | C latest57:44 |
| DEPLOY-DEP-13 | open_external | C latest57:45 |
| DEPLOY-DEP-14 | open_external | C latest57:46 |
| DEPLOY-DEP-15 | open_external | C latest57:47 |
| DEPLOY-DEP-16 | open_external | C latest57:48 |
| DEPLOY-DEP-17 | open_external | C latest57:49 |
| DEPLOY-DEP-18 | open_external | C latest57:50 |
| DEPLOY-DEP-19 | open_verification | C latest57:51 |
| DEPLOY-DEP-20 | open_external | C latest57:52 |
| DEPLOY-DEP-21 | open_external | C latest57:53 |
| DEPLOY-DEP-22 | open_external | C latest57:54 |
| DEPLOY-DEP-23 | open_external | C latest57:55 |
| DEPLOY-DEP-24 | resolved_before | C latest57:56 |
| `WG01, WG02, WG03, WG04, WG05` | Source-scoped advances; open actions remain Q01–Q07/MW01/CWR07. | `reports/whole-workload-review-20261119/FINDINGS.json` at Git baseline; identify by stable ID. |
| `MW01, MW02, MW03, MW04, MW05` | Source-scoped advances; open actions remain Q01–Q07/MW01/CWR07. | `reports/maximum-workload-20261119/FINDINGS.json` at Git baseline; identify by stable ID. |
| `RA01, RA02, RA03, RA04, RA05` | Source-scoped advances; open actions remain Q01–Q07/MW01/CWR07. | `reports/readiness-advance-20261120/FINDINGS.json` at Git baseline; identify by stable ID. |
| `LPQ01, LPQ02, LPQ03, LPQ04, LPQ05` | Source-scoped advances; open actions remain Q01–Q07/MW01/CWR07. | `reports/lp-claims-maximum-20261120/FINDINGS.json` at Git baseline; identify by stable ID. |
| `NCA01, NCA02, NCA03, NCA04, NCA05, NCA06` | Source-scoped advances; open actions remain Q01–Q07/MW01/CWR07. | `reports/full-claim-admission-20261120/FINDINGS.json` at Git baseline; identify by stable ID. |
| `MRQ01, MRQ02, MRQ03, MRQ04, MRQ05` | Source-scoped advances; open actions remain Q01–Q07/MW01/CWR07. | `reports/market-route-qualification-20261120/FINDINGS.json` at Git baseline; identify by stable ID. |
| `CWR01, CWR02, CWR03, CWR04, CWR05, CWR06, CWR07, CWR08` | Source-scoped advances; open actions remain Q01–Q07/MW01/CWR07. | `reports/compact-wallet-20261121/FINDINGS.json` at Git baseline; identify by stable ID. |
| `K26-01, K26-02, K26-03, K26-04, K26-E1, K26-E2, K26-H1` | Source-scoped advances; open actions remain Q01–Q07/MW01/CWR07. | `reports/keeper-full-audit-20261126/FINDINGS.json` at Git baseline; identify by stable ID. |

## Reading deleted historical narratives

Canonical current interpretation belongs here and in `reports/CURRENT_REVIEW.md`; task status belongs only to Todo. Before removing superseded checked-out narratives, preserve their exact Git path/blob/commit and any indispensable machine evidence. Retrieve an original without rerunning it, for example:

```text
git show fdd599c7698d0e1c0709a4a8b50130e5557ba508:reports/whole-project-audit-20261116/HISTORY_DISPOSITIONS.json
git show fdd599c7698d0e1c0709a4a8b50130e5557ba508:reports/daily-reconciliation-audit-20261111/contracts/REVIEW.md
```

The cache-only reconciliation crosswalk is preparation evidence, not another published findings ledger. Old failed stages, hashes and historical scope remain recoverable through Git; source or metadata equality is never new execution or release approval.

## Full report-corpus scope

The consolidation read all818 baseline report Markdown files (5,367,378bytes) and triaged4,500 unresolved/failure/limitation/candidate marker paragraphs, including701 under unresolved-style headings. These are text-navigation counts, not bug counts or proof every old claim is solved. Specific unledgered candidates were compared with current guards/guidance; generic historical qualification limits map to the current actions above. The old wrapper-native exit gap, royalty-forwarding admission gap, LP fraction prototype-only label and active-main viability gap are superseded at their respective later source stages; no historical failure is rewritten. Per-file path/blob/hash/marker/disposition preparation stays cache-only.

## All40 historical human ledgers

The following exact source/ID sets cover all40 JSON files independently classified as historical human assessment/taxonomy/context. Ranges are consecutive observed IDs only; IDs are scoped to their source path, so identical short labels are not conflated. Original statuses and subclaims remain recoverable at the Git baseline. Resolved/source-implemented labels keep scoped evidence; Q01–Q07/MW01/CWR07/E18 and retained L boundaries remain open/accepted as stated above. The31 separately classified raw/active inputs—including actual financial/state/host reconciliation and the current601-entry analyzer review—are outside this taxonomy-removal set and remain exact.

| File / exact Git provenance | Original IDs or positional identities | Current interpretation |
| --- | --- | --- |
| `reports/artwork-palette/new-findings-review.json` · blob `dcef9d2fbde05fe16a57ce86de2bd8a9c1ff8c6f` | `No named IDs; original schema/list positions retain identity` | Positions0–2: default-zero renderer counter false-positive; two packed artwork literal informational records. Content/VRF/external approval stays Q05/Q07. |
| `reports/compact-wallet-20261121/FINDINGS.json` · blob `4b3a0d1949e9c8bb198e73dfcaf5a03dac18f533` | `CWR01–CWR08` | Original split dispositions retained; current action/limit overlay above; not all closed. |
| `reports/comprehensive-popl-20261029/operations-admission-findings.json` · blob `0851abfeb02789bf7412b0e17e1c00e25d5da736` | `OPS2-03` | OPS2 source/evidence admission fixes retain their scoped controls; OPR operating obligations remain Q06. |
| `reports/comprehensive-popl-20261029/operations-findings.json` · blob `7ce9452f1fe232f6406d1d20d6776f4593bcf816` | `OPR-01–OPR-07; OPS2-01–OPS2-03` | OPS2 source/evidence admission fixes retain their scoped controls; OPR operating obligations remain Q06. |
| `reports/daily-reconciliation-audit-20261111/backend/FINDINGS.json` · blob `81ab298282137a62862acee18c2ea7f97babbc98` | `ABI-EXACT-INPUT; HISTORICAL-PROFILES-DIAGNOSTICS; INDEXER-CONTRACT-INVENTORY; KEEPER-LATE-DAY-DEADLINE-OUTPUT; LIFETIME-ARCHIVE-ROYALTY-RESTORE; REFERENCE-SWAP-COUPLING; DAILY-BE-01–DAILY-BE-04` | Original split dispositions retained; current action/limit overlay above; not all closed. |
| `reports/daily-reconciliation-audit-20261111/history/CURRENT_REASSESSMENTS.json` · blob `d700589f63f2b96a5145f759df753235c8342a23` | `HR1111-01–HR1111-25` | Named historical overlays; H05/architecture/source advances separated from actual qualification and unproven local incident. |
| `reports/daily-reconciliation-audit-20261111/history/FOLLOWUP_MATRIX.json` · blob `1a0dcace9486b403ebcf91d72d785503ebe423df` | `F01–F12` | F04 service wait is now an accepted decision; F11 later individually assessed; F12 remains user-deferred; other external actions map to Q/L above. |
| `reports/daily-reconciliation-audit-20261111/history/inherited-310-findings.json` · blob `ee522efe920aab748d1d814e816b253df9e53c51` | `A01–A05; B01–B04; C01–C12; D01–D04; FB-01–FB-28; H01–H06; HC-01–HC-53; I01; K01–K07; M01–M04; N01–N08; OP-01–OP-40; OPS-RS-00-1–OPS-RS-00-3; OPS-RS-01-1, OPS-RS-01-2; OPS-RS-02-1, OPS-RS-02-2; OPS-RS-03-1; OPS-RS-04-1, OPS-RS-04-2; OPS-RS-05-1; OPS-RS-06-1, OPS-RS-06-2; OPS-RS-07-1; OPS-RS-08-1; OPS-RS-09-1–OPS-RS-09-3; OPS-RS-10-1; OPS-RS-11-1; OPS-RS-12-1, OPS-RS-12-2; OPS-RS-13-1; OPS-RS-14-1; OPS-RS-15-1, OPS-RS-15-2; OPS-RS-16-1; OPS-RS-17-1, OPS-RS-17-2; OPS-RS-18-1; OPS-RS-19-1, OPS-RS-19-2; OPS-RS-20-1–OPS-RS-20-3; OPS-RS-21-1, OPS-RS-21-2; OPS-RS-22-1; OPS-RS-23-1; OPS-RS-24-1–OPS-RS-24-3; OPS-RS-25-1; OPS-RS-26-1, OPS-RS-26-2; OPS-RS-27-1; OPS-RS-28-1, OPS-RS-28-2; OPS-RS-29-1–OPS-RS-29-3; OPS-RS-30-1; OPS-RS-31-1–OPS-RS-31-4; OPS-RS-32-1; OPS-RS-33-1; OPS-RS-34-1; OPS-RS-35-1, OPS-RS-35-2; OPS-RS-36-1; OPS-RS-37-1, OPS-RS-37-2; OPS-RS-38-1; OPS-RS-39-1; OPS-RS-40-1; OPS-RS-41-1–OPS-RS-41-4; OPS-RS-42-1; OPS-RS-43-1; OPS-RS-44-1–OPS-RS-44-5; OPS-RS-45-1–OPS-RS-45-4; OPS-RS-46-1–OPS-RS-46-5; OPS-RS-47-1–OPS-RS-47-3; OPS-RS-48-1; OPS-RS-49-1–OPS-RS-49-3; P01–P07; Q01–Q06; R01–R04; RO-01–RO-20; T01–T05; T10-01, T10-02; historical/FB-01–historical/FB-28; historical/HC-01–historical/HC-53; historical/OP-01–historical/OP-40; historical/OPS-RS-00-1–historical/OPS-RS-00-3; historical/OPS-RS-01-1, historical/OPS-RS-01-2; historical/OPS-RS-02-1, historical/OPS-RS-02-2; historical/OPS-RS-03-1; historical/OPS-RS-04-1, historical/OPS-RS-04-2; historical/OPS-RS-05-1; historical/OPS-RS-06-1, historical/OPS-RS-06-2; historical/OPS-RS-07-1; historical/OPS-RS-08-1; historical/OPS-RS-09-1–historical/OPS-RS-09-3; historical/OPS-RS-10-1; historical/OPS-RS-11-1; historical/OPS-RS-12-1, historical/OPS-RS-12-2; historical/OPS-RS-13-1; historical/OPS-RS-14-1; historical/OPS-RS-15-1, historical/OPS-RS-15-2; historical/OPS-RS-16-1; historical/OPS-RS-17-1, historical/OPS-RS-17-2; historical/OPS-RS-18-1; historical/OPS-RS-19-1, historical/OPS-RS-19-2; historical/OPS-RS-20-1–historical/OPS-RS-20-3; historical/OPS-RS-21-1, historical/OPS-RS-21-2; historical/OPS-RS-22-1; historical/OPS-RS-23-1; historical/OPS-RS-24-1–historical/OPS-RS-24-3; historical/OPS-RS-25-1; historical/OPS-RS-26-1, historical/OPS-RS-26-2; historical/OPS-RS-27-1; historical/OPS-RS-28-1, historical/OPS-RS-28-2; historical/OPS-RS-29-1–historical/OPS-RS-29-3; historical/OPS-RS-30-1; historical/OPS-RS-31-1–historical/OPS-RS-31-4; historical/OPS-RS-32-1; historical/OPS-RS-33-1; historical/OPS-RS-34-1; historical/OPS-RS-35-1, historical/OPS-RS-35-2; historical/OPS-RS-36-1; historical/OPS-RS-37-1, historical/OPS-RS-37-2; historical/OPS-RS-38-1; historical/OPS-RS-39-1; historical/OPS-RS-40-1; historical/OPS-RS-41-1–historical/OPS-RS-41-4; historical/OPS-RS-42-1; historical/OPS-RS-43-1; historical/OPS-RS-44-1–historical/OPS-RS-44-5; historical/OPS-RS-45-1–historical/OPS-RS-45-4; historical/OPS-RS-46-1–historical/OPS-RS-46-5; historical/OPS-RS-47-1–historical/OPS-RS-47-3; historical/OPS-RS-48-1; historical/OPS-RS-49-1–historical/OPS-RS-49-3; historical/RO-01–historical/RO-20; later/A01–later/A05; later/B01–later/B04; later/C01–later/C12; later/D01–later/D04; later/H01–later/H06; later/I01; later/K01–later/K07; later/M01–later/M04; later/N01–later/N08; later/P01–later/P07; later/Q01–later/Q06; later/R01–later/R04; later/T01–later/T05; later/T10-01, later/T10-02` | Original split dispositions retained; current action/limit overlay above; not all closed. |
| `reports/daily-reconciliation-audit-20261111/history/structured-findings-index.json` · blob `bf857d2c891d77085a7cc72438681b7dd5ab1155` | `No named IDs; original schema/list positions retain identity` | Schema/positional human assessment/context records (or explicit empty list), not new bugs; current analyzer/evidence inputs are preserved separately. |
| `reports/five-audit-consolidation-20261102/findings.json` · blob `197769f733e9bdfd2ec2af95bf904e7c64c7ee72` | `A01–A05; B01–B04; C01, C02; D01–D04; H01, H02; I01; M01–M04; N01–N08; Q01–Q06; T01–T05` | Original split dispositions retained; current action/limit overlay above; not all closed. |
| `reports/five-audit-reconciliation-20261116/FINDINGS.json` · blob `efe9d40ad777a845c17dae84d6c137a23b25b4d7` | `D1, D2; DEP-01–DEP-24; DEPLOY-DEP-01–DEPLOY-DEP-24; G1–G9; G10; M1–M8; MARKET-MR-01–MARKET-MR-15; META-MANUAL-D1, META-MANUAL-D2; META-MANUAL-M1–META-MANUAL-M8; META-MANUAL-MR1–META-MANUAL-MR7; META-MANUAL-MW1; MR1–MR7; MR-01–MR-15; MW1` | Original split dispositions retained; current action/limit overlay above; not all closed. |
| `reports/five-report-consolidation-20261117/CONTRACT_LP_FINDINGS.json` · blob `c75424e948b03e1eec0f08b169c85ab598056bfb` | `CLP-01–CLP-30` | CLP resolved/accepted/open subclaims map to R/L/Q; CLP20 idle/entry boundary explicitly retained. |
| `reports/five-report-consolidation-20261117/RECONCILIATION.json` · blob `4829020f030e5769b0a7c508784ab048cfed712b` | `L01–L17; N01, N02; Q01–Q08; R01–R37` | Original split dispositions retained; current action/limit overlay above; not all closed. |
| `reports/five-report-consolidation-20261117/TOOL_FINDINGS.json` · blob `a34202910feae435224f9b9587c14410c5a09343` | `BARE_ARTWORK; EOA_ENVELOPE; LATE_MANUAL_ANCHOR; NORMAL_READ_PERMISSION; PRESEAL_EXECUTION_DECIMALS; PRESEAL_NATIVE_PINS; PRESEAL_OLD_FAMILY; PRESEAL_PROTOCOL_DEPENDENCIES; PRESEAL_STOP_DISCLOSURE; PRESEAL_UNKNOWN_TERMS; PRIVATE_OPENING_GETTER; RESERVATION_IDENTITY; RPC_MARKETS_FEES_OPERATIONS; SERVICE_COMPOUND_WAIT; TEST_HOOK_TIMING; WRONG_HOME; KEEPER-01; SEAL-01; TOOL-01, TOOL-02` | Resolved tool/fixture IDs alias R/N source fixes; SERVICE_COMPOUND_WAIT accepted; EOA_ENVELOPE is a client restriction, not revoked on-chain wallet authority. |
| `reports/full-claim-admission-20261120/FINDINGS.json` · blob `0d348138a79f781dbf30c0da9f7af8197d10a6c3` | `NCA01–NCA06` | NCA01 fixed; NCA02 finite normal admission; NCA04–06 and complete external/workload qualification remain open. |
| `reports/full-history-reconciliation-20261104/FINDINGS.json` · blob `53fa2e99347de9703945a9b491c727d262faf6f3` | `authority; backend; canonical; compound; confirmation; entry; evidence; frontend; history; identity; marketplace; metadata; operations; randomness; recovery; release; revenue; routing; royalties; shares; valuation; A01–A05; B01–B04; C01–C12; C3-01–C3-04; D01–D04; DE-01; FB-01–FB-28; H01–H06; HC-01–HC-53; I01; K01–K07; M01–M04; N01–N08; OP-01–OP-40; OPS-RS-00-1–OPS-RS-00-3; OPS-RS-01-1, OPS-RS-01-2; OPS-RS-02-1, OPS-RS-02-2; OPS-RS-03-1; OPS-RS-04-1, OPS-RS-04-2; OPS-RS-05-1; OPS-RS-06-1, OPS-RS-06-2; OPS-RS-07-1; OPS-RS-08-1; OPS-RS-09-1–OPS-RS-09-3; OPS-RS-10-1; OPS-RS-11-1; OPS-RS-12-1, OPS-RS-12-2; OPS-RS-13-1; OPS-RS-14-1; OPS-RS-15-1, OPS-RS-15-2; OPS-RS-16-1; OPS-RS-17-1, OPS-RS-17-2; OPS-RS-18-1; OPS-RS-19-1, OPS-RS-19-2; OPS-RS-20-1–OPS-RS-20-3; OPS-RS-21-1, OPS-RS-21-2; OPS-RS-22-1; OPS-RS-23-1; OPS-RS-24-1–OPS-RS-24-3; OPS-RS-25-1; OPS-RS-26-1, OPS-RS-26-2; OPS-RS-27-1; OPS-RS-28-1, OPS-RS-28-2; OPS-RS-29-1–OPS-RS-29-3; OPS-RS-30-1; OPS-RS-31-1–OPS-RS-31-4; OPS-RS-32-1; OPS-RS-33-1; OPS-RS-34-1; OPS-RS-35-1, OPS-RS-35-2; OPS-RS-36-1; OPS-RS-37-1, OPS-RS-37-2; OPS-RS-38-1; OPS-RS-39-1; OPS-RS-40-1; OPS-RS-41-1–OPS-RS-41-4; OPS-RS-42-1; OPS-RS-43-1; OPS-RS-44-1–OPS-RS-44-5; OPS-RS-45-1–OPS-RS-45-4; OPS-RS-46-1–OPS-RS-46-5; OPS-RS-47-1–OPS-RS-47-3; OPS-RS-48-1; OPS-RS-49-1–OPS-RS-49-3; P01–P07; Q01–Q06; R01–R04; RO-01–RO-20; T01–T05; T10-01, T10-02; historical/FB-01–historical/FB-28; historical/HC-01–historical/HC-53; historical/OP-01–historical/OP-40; historical/OPS-RS-00-1–historical/OPS-RS-00-3; historical/OPS-RS-01-1, historical/OPS-RS-01-2; historical/OPS-RS-02-1, historical/OPS-RS-02-2; historical/OPS-RS-03-1; historical/OPS-RS-04-1, historical/OPS-RS-04-2; historical/OPS-RS-05-1; historical/OPS-RS-06-1, historical/OPS-RS-06-2; historical/OPS-RS-07-1; historical/OPS-RS-08-1; historical/OPS-RS-09-1–historical/OPS-RS-09-3; historical/OPS-RS-10-1; historical/OPS-RS-11-1; historical/OPS-RS-12-1, historical/OPS-RS-12-2; historical/OPS-RS-13-1; historical/OPS-RS-14-1; historical/OPS-RS-15-1, historical/OPS-RS-15-2; historical/OPS-RS-16-1; historical/OPS-RS-17-1, historical/OPS-RS-17-2; historical/OPS-RS-18-1; historical/OPS-RS-19-1, historical/OPS-RS-19-2; historical/OPS-RS-20-1–historical/OPS-RS-20-3; historical/OPS-RS-21-1, historical/OPS-RS-21-2; historical/OPS-RS-22-1; historical/OPS-RS-23-1; historical/OPS-RS-24-1–historical/OPS-RS-24-3; historical/OPS-RS-25-1; historical/OPS-RS-26-1, historical/OPS-RS-26-2; historical/OPS-RS-27-1; historical/OPS-RS-28-1, historical/OPS-RS-28-2; historical/OPS-RS-29-1–historical/OPS-RS-29-3; historical/OPS-RS-30-1; historical/OPS-RS-31-1–historical/OPS-RS-31-4; historical/OPS-RS-32-1; historical/OPS-RS-33-1; historical/OPS-RS-34-1; historical/OPS-RS-35-1, historical/OPS-RS-35-2; historical/OPS-RS-36-1; historical/OPS-RS-37-1, historical/OPS-RS-37-2; historical/OPS-RS-38-1; historical/OPS-RS-39-1; historical/OPS-RS-40-1; historical/OPS-RS-41-1–historical/OPS-RS-41-4; historical/OPS-RS-42-1; historical/OPS-RS-43-1; historical/OPS-RS-44-1–historical/OPS-RS-44-5; historical/OPS-RS-45-1–historical/OPS-RS-45-4; historical/OPS-RS-46-1–historical/OPS-RS-46-5; historical/OPS-RS-47-1–historical/OPS-RS-47-3; historical/OPS-RS-48-1; historical/OPS-RS-49-1–historical/OPS-RS-49-3; historical/RO-01–historical/RO-20; later/A01–later/A05; later/B01–later/B04; later/C01–later/C12; later/D01–later/D04; later/H01–later/H06; later/I01; later/K01–later/K07; later/M01–later/M04; later/N01–later/N08; later/P01–later/P07; later/Q01–later/Q06; later/R01–later/R04; later/T01–later/T05; later/T10-01, later/T10-02` | Original split dispositions retained; current action/limit overlay above; not all closed. |
| `reports/historical-reconciliation-20261029/FINDINGS.json` · blob `ec7d83270599ae58ca8c3ce4e735dae4be1e299a` | `HR-01–HR-03` | Original split dispositions retained; current action/limit overlay above; not all closed. |
| `reports/historical-reconciliation-20261029/READ_SERVICES_LEDGER.json` · blob `d446c1430b0ac680d3e6fb8a5667f801b779ad55` | `FB-01–FB-28` | Original split dispositions retained; current action/limit overlay above; not all closed. |
| `reports/historical-reconciliation-completion-20261029/FINDINGS.json` · blob `06a72989444a02a39b9567ee470f37ec27660c16` | `FB-01–FB-28; HC-01–HC-53; HR-C-01–HR-C-05; OP-01–OP-40; OPS-RS-00-1–OPS-RS-00-3; OPS-RS-01-1, OPS-RS-01-2; OPS-RS-02-1, OPS-RS-02-2; OPS-RS-03-1; OPS-RS-04-1, OPS-RS-04-2; OPS-RS-05-1; OPS-RS-06-1, OPS-RS-06-2; OPS-RS-07-1; OPS-RS-08-1; OPS-RS-09-1–OPS-RS-09-3; OPS-RS-10-1; OPS-RS-11-1; OPS-RS-12-1, OPS-RS-12-2; OPS-RS-13-1; OPS-RS-14-1; OPS-RS-15-1, OPS-RS-15-2; OPS-RS-16-1; OPS-RS-17-1, OPS-RS-17-2; OPS-RS-18-1; OPS-RS-19-1, OPS-RS-19-2; OPS-RS-20-1–OPS-RS-20-3; OPS-RS-21-1, OPS-RS-21-2; OPS-RS-22-1; OPS-RS-23-1; OPS-RS-24-1–OPS-RS-24-3; OPS-RS-25-1; OPS-RS-26-1, OPS-RS-26-2; OPS-RS-27-1; OPS-RS-28-1, OPS-RS-28-2; OPS-RS-29-1–OPS-RS-29-3; OPS-RS-30-1; OPS-RS-31-1–OPS-RS-31-4; OPS-RS-32-1; OPS-RS-33-1; OPS-RS-34-1; OPS-RS-35-1, OPS-RS-35-2; OPS-RS-36-1; OPS-RS-37-1, OPS-RS-37-2; OPS-RS-38-1; OPS-RS-39-1; OPS-RS-40-1; OPS-RS-41-1–OPS-RS-41-4; OPS-RS-42-1; OPS-RS-43-1; OPS-RS-44-1–OPS-RS-44-5; OPS-RS-45-1–OPS-RS-45-4; OPS-RS-46-1–OPS-RS-46-5; OPS-RS-47-1–OPS-RS-47-3; OPS-RS-48-1; OPS-RS-49-1–OPS-RS-49-3; RO-01–RO-20` | Original split dispositions retained; current action/limit overlay above; not all closed. |
| `reports/keeper-full-audit-20261126/FINDINGS.json` · blob `912851b10c79b94c91a1247292af6dc78a003734` | `K26-01–K26-04; K26-E1, K26-E2; K26-H1` | Original split dispositions retained; current action/limit overlay above; not all closed. |
| `reports/lp-claims-maximum-20261120/FINDINGS.json` · blob `18da0215365a36aeeef639c1218b8346e2b7feb4` | `LPQ01–LPQ05` | Original split dispositions retained; current action/limit overlay above; not all closed. |
| `reports/market-route-qualification-20261120/FINDINGS.json` · blob `d56da13dd9e8c8c1cc3f587206e0a45f8173014a` | `MRQ01–MRQ05` | Original split dispositions retained; current action/limit overlay above; not all closed. |
| `reports/maximum-workload-20261119/FINDINGS.json` · blob `bcf0025059e88b6c9f52fdbb37f782954d612a23` | `MW01–MW05` | Original split dispositions retained; current action/limit overlay above; not all closed. |
| `reports/project-consolidation-20261103/FINDINGS.json` · blob `f9c8976b112b96ccb448830d4fcf8f08f60a60a2` | `authority; backend; canonical; compound; confirmation; entry; evidence; frontend; history; identity; marketplace; metadata; operations; randomness; recovery; release; revenue; routing; royalties; shares; valuation; C3-01–C3-04; DE-01; historical/FB-01–historical/FB-28; historical/HC-01–historical/HC-53; historical/OP-01–historical/OP-40; historical/OPS-RS-00-1–historical/OPS-RS-00-3; historical/OPS-RS-01-1, historical/OPS-RS-01-2; historical/OPS-RS-02-1, historical/OPS-RS-02-2; historical/OPS-RS-03-1; historical/OPS-RS-04-1, historical/OPS-RS-04-2; historical/OPS-RS-05-1; historical/OPS-RS-06-1, historical/OPS-RS-06-2; historical/OPS-RS-07-1; historical/OPS-RS-08-1; historical/OPS-RS-09-1–historical/OPS-RS-09-3; historical/OPS-RS-10-1; historical/OPS-RS-11-1; historical/OPS-RS-12-1, historical/OPS-RS-12-2; historical/OPS-RS-13-1; historical/OPS-RS-14-1; historical/OPS-RS-15-1, historical/OPS-RS-15-2; historical/OPS-RS-16-1; historical/OPS-RS-17-1, historical/OPS-RS-17-2; historical/OPS-RS-18-1; historical/OPS-RS-19-1, historical/OPS-RS-19-2; historical/OPS-RS-20-1–historical/OPS-RS-20-3; historical/OPS-RS-21-1, historical/OPS-RS-21-2; historical/OPS-RS-22-1; historical/OPS-RS-23-1; historical/OPS-RS-24-1–historical/OPS-RS-24-3; historical/OPS-RS-25-1; historical/OPS-RS-26-1, historical/OPS-RS-26-2; historical/OPS-RS-27-1; historical/OPS-RS-28-1, historical/OPS-RS-28-2; historical/OPS-RS-29-1–historical/OPS-RS-29-3; historical/OPS-RS-30-1; historical/OPS-RS-31-1–historical/OPS-RS-31-4; historical/OPS-RS-32-1; historical/OPS-RS-33-1; historical/OPS-RS-34-1; historical/OPS-RS-35-1, historical/OPS-RS-35-2; historical/OPS-RS-36-1; historical/OPS-RS-37-1, historical/OPS-RS-37-2; historical/OPS-RS-38-1; historical/OPS-RS-39-1; historical/OPS-RS-40-1; historical/OPS-RS-41-1–historical/OPS-RS-41-4; historical/OPS-RS-42-1; historical/OPS-RS-43-1; historical/OPS-RS-44-1–historical/OPS-RS-44-5; historical/OPS-RS-45-1–historical/OPS-RS-45-4; historical/OPS-RS-46-1–historical/OPS-RS-46-5; historical/OPS-RS-47-1–historical/OPS-RS-47-3; historical/OPS-RS-48-1; historical/OPS-RS-49-1–historical/OPS-RS-49-3; historical/RO-01–historical/RO-20; later/A01–later/A05; later/B01–later/B04; later/C01–later/C12; later/D01–later/D04; later/H01–later/H06; later/I01; later/K01–later/K07; later/M01–later/M04; later/N01–later/N08; later/P01–later/P07; later/Q01–later/Q06; later/R01–later/R04; later/T01–later/T05; later/T10-01, later/T10-02` | Original split dispositions retained; current action/limit overlay above; not all closed. |
| `reports/q06-keeper-recovery-20261117/FINDINGS.json` · blob `4743fc400be8d2dfac4e37bbc7a2ecbf7724a844` | `Q06-F01, Q06-F02` | Original split dispositions retained; current action/limit overlay above; not all closed. |
| `reports/readiness-advance-20261120/FINDINGS.json` · blob `0ddff721ae0ff3cd0590452f0ba71f969d890bea` | `RA01–RA05` | RA03 signed adaptation unselected after custom-Merkle choice; RA04 lead unqualified; RA05/MW01 direct gas remains open. |
| `reports/release-hardening/static-analysis/changed-findings-review.json` · blob `c1a03de7825a5dd094ea8eee269632989a80b87a` | `No named IDs; original schema/list positions retain identity` | Positions0–3: mint/notify reentrancy false-positives, unused baseURI and numeric VRF bounds informational; actual provider qualification remains Q05. |
| `reports/release-hardening/static-analysis/new-findings-review.json` · blob `fe51488c7066f6687ef680d6bfaa4f7768ef205c` | `No named IDs; original schema/list positions retain identity` | Schema/positional human assessment/context records (or explicit empty list), not new bugs; current analyzer/evidence inputs are preserved separately. |
| `reports/remaining-271-20261111/backend/CORRECTIONS.json` · blob `3f34571950e2057d00ef680cf9c77853310d77ef` | `BE-REMAIN-01–BE-REMAIN-04` | BE-REMAIN source/fixture corrections; DAILY-BE-02 advanced, external qualification stays open. |
| `reports/remaining-271-20261111/backend/FINDINGS.json` · blob `21dee01e26d7df845b6b4653dc106483755bff5a` | `historical/FB-03, historical/FB-04; historical/FB-12–historical/FB-14; historical/FB-18; historical/FB-20; historical/FB-25, historical/FB-26; historical/FB-28; historical/HC-16; historical/HC-28; historical/HC-32, historical/HC-33; historical/HC-41–historical/HC-43; historical/OP-02–historical/OP-08; historical/OP-10, historical/OP-11; historical/OP-14; historical/OP-17, historical/OP-18; historical/OP-22; historical/OP-32; historical/OP-35–historical/OP-37; historical/OPS-RS-00-1; historical/OPS-RS-00-3; historical/OPS-RS-01-1; historical/OPS-RS-02-1; historical/OPS-RS-03-1; historical/OPS-RS-04-1, historical/OPS-RS-04-2; historical/OPS-RS-06-2; historical/OPS-RS-08-1; historical/OPS-RS-17-2; historical/OPS-RS-19-1, historical/OPS-RS-19-2; historical/OPS-RS-20-1; historical/OPS-RS-20-3; historical/OPS-RS-21-1; historical/OPS-RS-27-1; historical/OPS-RS-28-2; historical/OPS-RS-29-1; historical/OPS-RS-29-3; historical/OPS-RS-31-2; historical/OPS-RS-31-4; historical/OPS-RS-33-1; historical/OPS-RS-38-1; historical/OPS-RS-39-1; historical/OPS-RS-41-3; historical/OPS-RS-44-3; historical/OPS-RS-44-5; historical/OPS-RS-45-4; historical/OPS-RS-46-3–historical/OPS-RS-46-5; historical/OPS-RS-47-3; historical/OPS-RS-49-3; historical/RO-02; historical/RO-05; historical/RO-13; historical/RO-19; later/A05; later/C01; later/C05, later/C06; later/D01, later/D02; later/K03–later/K05; later/K07; later/M02, later/M03; later/N01–later/N04; later/Q01; later/Q04; later/T01, later/T02; later/T04; later/T10-01, later/T10-02` | Original split dispositions retained; current action/limit overlay above; not all closed. |
| `reports/remaining-271-20261111/contracts-supplement/FINDINGS.json` · blob `aacba47f2ddb377f33c5164674cae074374ec428` | `historical/OPS-RS-44-1, historical/OPS-RS-44-2; historical/OPS-RS-45-1, historical/OPS-RS-45-2; historical/OPS-RS-46-1, historical/OPS-RS-46-2; historical/OPS-RS-47-1, historical/OPS-RS-47-2; historical/RO-01; historical/RO-03, historical/RO-04; historical/RO-08, historical/RO-09; historical/RO-14, historical/RO-15; later/A04; later/B03; later/C03, later/C04; later/D03; later/I01; later/K02; later/K06; later/M04; later/P01–later/P05; later/R03` | Original split dispositions retained; current action/limit overlay above; not all closed. |
| `reports/remaining-271-20261111/contracts/FINDINGS.json` · blob `5f6d41c5eb00a9218a6ab456e1bb2d7b8e6aaaf1` | `historical/FB-01; historical/FB-15; historical/FB-22; historical/HC-01–historical/HC-03; historical/HC-05; historical/HC-07; historical/HC-09–historical/HC-13; historical/HC-17; historical/HC-19–historical/HC-21; historical/HC-23–historical/HC-27; historical/HC-29–historical/HC-31; historical/HC-34–historical/HC-38; historical/HC-46–historical/HC-48; historical/HC-50; historical/HC-52, historical/HC-53; historical/OP-13; historical/OP-16; historical/OP-21; historical/OP-25; historical/OP-27; historical/OP-30, historical/OP-31; historical/OPS-RS-00-2; historical/OPS-RS-06-1; historical/OPS-RS-09-2, historical/OPS-RS-09-3; historical/OPS-RS-11-1; historical/OPS-RS-12-1, historical/OPS-RS-12-2; historical/OPS-RS-15-1, historical/OPS-RS-15-2; historical/OPS-RS-17-1; historical/OPS-RS-20-2; historical/OPS-RS-21-2; historical/OPS-RS-31-1; historical/OPS-RS-31-3; historical/OPS-RS-41-1, historical/OPS-RS-41-2; historical/OPS-RS-43-1` | Original split dispositions retained; current action/limit overlay above; not all closed. |
| `reports/remaining-271-20261111/evidence-frontend/FINDINGS.json` · blob `7c9a0cf52ebb70dc5cffbee5f9c0445b3a8bd6e4` | `historical/FB-05–historical/FB-08; historical/FB-10; historical/FB-21; historical/FB-23; historical/FB-27; historical/HC-39, historical/HC-40; historical/OP-01; historical/OP-12; historical/OP-19, historical/OP-20; historical/OP-24; historical/OP-29; historical/OP-33; historical/OP-38–historical/OP-40; historical/OPS-RS-01-2; historical/OPS-RS-02-2; historical/OPS-RS-05-1; historical/OPS-RS-07-1; historical/OPS-RS-09-1; historical/OPS-RS-10-1; historical/OPS-RS-13-1; historical/OPS-RS-14-1; historical/OPS-RS-16-1; historical/OPS-RS-18-1; historical/OPS-RS-22-1; historical/OPS-RS-23-1; historical/OPS-RS-24-1–historical/OPS-RS-24-3; historical/OPS-RS-25-1; historical/OPS-RS-26-1, historical/OPS-RS-26-2; historical/OPS-RS-28-1; historical/OPS-RS-29-2; historical/OPS-RS-30-1; historical/OPS-RS-32-1; historical/OPS-RS-34-1; historical/OPS-RS-35-1, historical/OPS-RS-35-2; historical/OPS-RS-36-1; historical/OPS-RS-37-1, historical/OPS-RS-37-2; historical/OPS-RS-40-1; historical/OPS-RS-41-4; historical/OPS-RS-42-1; historical/OPS-RS-44-4; historical/OPS-RS-48-1; historical/OPS-RS-49-1, historical/OPS-RS-49-2; historical/RO-06, historical/RO-07; historical/RO-10; historical/RO-12; historical/RO-18; historical/RO-20; later/A01–later/A03; later/B01, later/B02; later/B04; later/C02; later/C07, later/C08; later/C12; later/D04; later/H01–later/H04; later/H06; later/M01; later/N05–later/N07; later/P06, later/P07; later/Q06; later/R01, later/R02; later/T03` | Original split dispositions retained; current action/limit overlay above; not all closed. |
| `reports/seven-report-consolidation-20261119/RECONCILIATION.json` · blob `88ca9c185ec0c655fe903d547c4d02e6241f38bb` | `E01–E24; L01–L17; N01, N02; Q01–Q08; R01–R37` | Original split dispositions retained; current action/limit overlay above; not all closed. |
| `reports/ten-audit-consolidation-20261102/findings.json` · blob `a1ab0c7cd29f4a005a71f82bd1a779f2b91eac82` | `A01–A05; B01–B04; C01–C12; D01–D04; H01–H06; I01; K01–K07; M01–M04; N01–N08; P01–P07; Q01–Q06; R01–R04; T01–T05; T10-01, T10-02` | Original split dispositions retained; current action/limit overlay above; not all closed. |
| `reports/whole-project-audit-20261116/FINDINGS.json` · blob `46ada461a5e8865b15b3287b2e1e4730feecd2e3` | `WPA-01–WPA-06` | WPA01–06 source/document/runner corrections; no fresh whole-project clearance. Deferred comments remain explicit. |
| `reports/whole-project-audit-20261116/HISTORY_DISPOSITIONS.json` · blob `c8c385aa34dab7d14c47ab17eb38fcfb67d6398e` | `D1, D2; DEP-01–DEP-24; DEPLOY-DEP-01–DEPLOY-DEP-24; G1–G9; G10; HR1111-01–HR1111-13; HR1111-15–HR1111-22; M1–M8; MARKET-MR-01–MARKET-MR-15; META-MANUAL-D1, META-MANUAL-D2; META-MANUAL-M1–META-MANUAL-M8; META-MANUAL-MR1–META-MANUAL-MR7; META-MANUAL-MW1; MR1–MR7; MR-01–MR-15; MW1; historical/FB-01–historical/FB-28; historical/HC-01–historical/HC-53; historical/OP-01–historical/OP-40; historical/OPS-RS-00-1–historical/OPS-RS-00-3; historical/OPS-RS-01-1, historical/OPS-RS-01-2; historical/OPS-RS-02-1, historical/OPS-RS-02-2; historical/OPS-RS-03-1; historical/OPS-RS-04-1, historical/OPS-RS-04-2; historical/OPS-RS-05-1; historical/OPS-RS-06-1, historical/OPS-RS-06-2; historical/OPS-RS-07-1; historical/OPS-RS-08-1; historical/OPS-RS-09-1–historical/OPS-RS-09-3; historical/OPS-RS-10-1; historical/OPS-RS-11-1; historical/OPS-RS-12-1, historical/OPS-RS-12-2; historical/OPS-RS-13-1; historical/OPS-RS-14-1; historical/OPS-RS-15-1, historical/OPS-RS-15-2; historical/OPS-RS-16-1; historical/OPS-RS-17-1, historical/OPS-RS-17-2; historical/OPS-RS-18-1; historical/OPS-RS-19-1, historical/OPS-RS-19-2; historical/OPS-RS-20-1–historical/OPS-RS-20-3; historical/OPS-RS-21-1, historical/OPS-RS-21-2; historical/OPS-RS-22-1; historical/OPS-RS-23-1; historical/OPS-RS-24-1–historical/OPS-RS-24-3; historical/OPS-RS-25-1; historical/OPS-RS-26-1, historical/OPS-RS-26-2; historical/OPS-RS-27-1; historical/OPS-RS-28-1, historical/OPS-RS-28-2; historical/OPS-RS-29-1–historical/OPS-RS-29-3; historical/OPS-RS-30-1; historical/OPS-RS-31-1–historical/OPS-RS-31-4; historical/OPS-RS-32-1; historical/OPS-RS-33-1; historical/OPS-RS-34-1; historical/OPS-RS-35-1, historical/OPS-RS-35-2; historical/OPS-RS-36-1; historical/OPS-RS-37-1, historical/OPS-RS-37-2; historical/OPS-RS-38-1; historical/OPS-RS-39-1; historical/OPS-RS-40-1; historical/OPS-RS-41-1–historical/OPS-RS-41-4; historical/OPS-RS-42-1; historical/OPS-RS-43-1; historical/OPS-RS-44-1–historical/OPS-RS-44-5; historical/OPS-RS-45-1–historical/OPS-RS-45-4; historical/OPS-RS-46-1–historical/OPS-RS-46-5; historical/OPS-RS-47-1–historical/OPS-RS-47-3; historical/OPS-RS-48-1; historical/OPS-RS-49-1–historical/OPS-RS-49-3; historical/RO-01–historical/RO-20; later/A01–later/A05; later/B01–later/B04; later/C01–later/C12; later/D01–later/D04; later/H01–later/H06; later/I01; later/K01–later/K07; later/M01–later/M04; later/N01–later/N08; later/P01–later/P07; later/Q01–later/Q06; later/R01–later/R04; later/T01–later/T05; later/T10-01, later/T10-02` | Original split dispositions retained; current action/limit overlay above; not all closed. |
| `reports/whole-project-audit-20261116/HISTORY_RECONCILIATION_INPUTS.json` · blob `81875f0175c07a589e57714e52e26d30359ac32f` | `DEPLOY-DEP-01–DEPLOY-DEP-24; G1–G9; G10; HR1111-01–HR1111-13; HR1111-15–HR1111-22; MARKET-MR-01–MARKET-MR-15; META-MANUAL-D1, META-MANUAL-D2; META-MANUAL-M1–META-MANUAL-M8; META-MANUAL-MR1–META-MANUAL-MR7; META-MANUAL-MW1; historical/FB-01–historical/FB-28; historical/HC-01–historical/HC-53; historical/OP-01–historical/OP-40; historical/OPS-RS-00-1–historical/OPS-RS-00-3; historical/OPS-RS-01-1, historical/OPS-RS-01-2; historical/OPS-RS-02-1, historical/OPS-RS-02-2; historical/OPS-RS-03-1; historical/OPS-RS-04-1, historical/OPS-RS-04-2; historical/OPS-RS-05-1; historical/OPS-RS-06-1, historical/OPS-RS-06-2; historical/OPS-RS-07-1; historical/OPS-RS-08-1; historical/OPS-RS-09-1–historical/OPS-RS-09-3; historical/OPS-RS-10-1; historical/OPS-RS-11-1; historical/OPS-RS-12-1, historical/OPS-RS-12-2; historical/OPS-RS-13-1; historical/OPS-RS-14-1; historical/OPS-RS-15-1, historical/OPS-RS-15-2; historical/OPS-RS-16-1; historical/OPS-RS-17-1, historical/OPS-RS-17-2; historical/OPS-RS-18-1; historical/OPS-RS-19-1, historical/OPS-RS-19-2; historical/OPS-RS-20-1–historical/OPS-RS-20-3; historical/OPS-RS-21-1, historical/OPS-RS-21-2; historical/OPS-RS-22-1; historical/OPS-RS-23-1; historical/OPS-RS-24-1–historical/OPS-RS-24-3; historical/OPS-RS-25-1; historical/OPS-RS-26-1, historical/OPS-RS-26-2; historical/OPS-RS-27-1; historical/OPS-RS-28-1, historical/OPS-RS-28-2; historical/OPS-RS-29-1–historical/OPS-RS-29-3; historical/OPS-RS-30-1; historical/OPS-RS-31-1–historical/OPS-RS-31-4; historical/OPS-RS-32-1; historical/OPS-RS-33-1; historical/OPS-RS-34-1; historical/OPS-RS-35-1, historical/OPS-RS-35-2; historical/OPS-RS-36-1; historical/OPS-RS-37-1, historical/OPS-RS-37-2; historical/OPS-RS-38-1; historical/OPS-RS-39-1; historical/OPS-RS-40-1; historical/OPS-RS-41-1–historical/OPS-RS-41-4; historical/OPS-RS-42-1; historical/OPS-RS-43-1; historical/OPS-RS-44-1–historical/OPS-RS-44-5; historical/OPS-RS-45-1–historical/OPS-RS-45-4; historical/OPS-RS-46-1–historical/OPS-RS-46-5; historical/OPS-RS-47-1–historical/OPS-RS-47-3; historical/OPS-RS-48-1; historical/OPS-RS-49-1–historical/OPS-RS-49-3; historical/RO-01–historical/RO-20; later/A01–later/A05; later/B01–later/B04; later/C01–later/C12; later/D01–later/D04; later/H01–later/H06; later/I01; later/K01–later/K07; later/M01–later/M04; later/N01–later/N08; later/P01–later/P07; later/Q01–later/Q06; later/R01–later/R04; later/T01–later/T05; later/T10-01, later/T10-02` | Original split dispositions retained; current action/limit overlay above; not all closed. |
| `reports/whole-project-review-20261111/evidence/backend/findings-and-scope.json` · blob `6ba86b767f51c5bd9e825d23bee513c059249e01` | `ABI-EXACT-INPUT; INDEXER-CONTRACT-INVENTORY` | Original split dispositions retained; current action/limit overlay above; not all closed. |
| `reports/whole-workload-review-20261119/FINDINGS.json` · blob `1e2df1213751865570f7f98ea204beebba913061` | `WG01–WG05` | Original split dispositions retained; current action/limit overlay above; not all closed. |
