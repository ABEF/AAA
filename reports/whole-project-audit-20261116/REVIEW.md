# Whole-project audit and implemented improvements

Reviewed16 November2026 against contract `59d02d40afac785c04cd4a5da2dfc6e4174c6880`
and website `2a528696d5eaea5ebb42cfeb313836840fff5e97`, plus the explicitly recorded
changes in this report. **Internal review; production NOT APPROVED.**

## What improved

| Finding | Correction | Practical limit |
| --- | --- | --- |
| Deployment authority inputs admitted governance at known protocol/dependency addresses. | Reject collisions with planned instances and fixed venue/token/SeaDrop dependencies before artifact preparation. Preserve the existing controller-specific error. | Unknown EOA/contract-wallet control, factory children and actual deployment addresses still need live review. This is planner hardening, not an on-chain authority fix. |
| The generic state reader confused a dangling path with an absent file. | Inspect the directory entry; default only on `FileNotFoundError`, propagate present-file read/parse/access errors. Register focused checks in the keeper runner. | The live keeper already had stronger Unix/path/nonce checks. No demonstrated live nonce bypass. Trusted parent directories and operating recovery remain necessary. |
| Direct construction could bypass the UI's unsigned-profile boundary. | The website transaction coordinator admits only legacy local schemas1–3 before provider access. Source9/schema4, source10/schema5 and unknown schemas reject. | The reproduced source9 path was local Anvil only; source10 also had an independent target-count refusal. No public-signing or fund-loss exploit was established. The shared signer is unchanged. |
| Frozen audit exports omitted operator-call examples and gave unusable Git-dependent reproduction advice. | Fresh review-bundle schema4 includes the exact examples and validates operator-input closure. Instructions require an independently authenticated matching Git checkout for Git-dependent checks. | Historical schemas1/2/3 retain their exact instructions/admission/exclusion semantics. The archive remains non-self-contained; dependencies, excluded evidence and real release configuration are not qualified. |
| The maintained website command omitted thirteen existing metadata checks. | Register the existing metadata module and the new signing-profile checks. | The thirteen unchanged tests were not rerun or counted as fresh passes. |
| Current audit/API guidance described retired accounting and capacity limits. | Correct main+optional-residual geometry, ETH/fixed-ZZZ LP books, separate expandable royalty capacity, exact-unit rights, current API profiles and callable count. | Historical reports keep original bytes, counts and source scopes. |

No production Solidity, ABI/storage, economic right, permission, financial cap,
gas default, compiler profile, artwork or live environment was changed. The
review found **no newly confirmed executable financial defect in the paths
examined**. That statement is narrower than exploit absence or production safety.

## Understanding and scope challenges

The supplied29-section prompt is retained in [AUDIT_PROMPT.md](AUDIT_PROMPT.md).
It was applied as a system review, rather than turning every old observation into
a new code requirement. Two scope challenges guided execution:

1. Establish current source/deployment/consumer boundaries first. Forty concrete
   callable contracts are not the same count as61 production Solidity files;
   one logical share bucket may contain two physical positions. Current LP
   exact-unit and royalty exact-unit accounting differ from old fractional
   codecs. Source9/source10 remain unsigned even on Anvil. Actual market inputs
   cannot be invented to make integration or deployment appear complete.
2. Review interactions and completion criteria independently. A valid archive
   hash does not ensure fixture completeness or a usable reproduction procedure;
   a safe UI entry point does not constrain a directly imported coordinator;
   an absent-file default must not hide a present broken path. Preserve original
   failures, historical archives, accepted emergency powers and deferred external
   qualification. Avoid rerunning unchanged suites merely to renew a date.

The component/function, financial/lifecycle/authority and verification maps are
in [COVERAGE.md](COVERAGE.md) and the linked source-pinned ledgers. Counts are
inventories, not proof of path coverage. Contract families were manually reviewed;
backend and frontend records explicitly distinguish complete-file reads, selected
families, historical evidence and inventory-only files. This is not a formal
proof, independent audit, full-regression run or fresh semantic audit of every
historical finding.

## Current operating and financial conclusions

- **Contributions:** native ETH or the one fixed ZZZ; checkpoint incumbents,
  deploy entrant funds into MAIN only, prove marginal deployed LP, then issue
  shares from aggregate NAV. Existing residual/idle/compound cannot subsidize
  entrant floors. A contribution does not recenter, change residual liquidity
  or reset the rebalance clock.
- **LP revenue:** actual collected receipts are split80/10/5/5 into individual,
  equal-active collective, compound and fixed-ZZZ buyback allocations. Harvest,
  claim, conversion, compound and burn remain separate. ETH and ZZZ books are
  real assets; pending ZZZ conversion must not be displayed as ETH received.
  Exact per-NFT allocation does not erase the separately documented20-unit
  upstream fee-split boundary rule or Uniswap collection rounding.
- **Royalties:** original currencies, rarity weights, sale-end+one-hour opening
  cohort, exact-unit allocation and outage/deferred entitlement remain. No
  royalty swap/unwrap/keeper worker is restored. Unreadable/untransferable tokens
  cannot be universally made safe by an accounting algorithm. Explicit
  unallocated recovery and zero-eligible decisions retain their permissions.
- **LP strategy:** one main plus at most one optional same-pool residual.
  Default main60%/residual40% is a replacement constraint, not a continuous ratio.
  Filled/mixed residuals still count in valuation/fees. Mode OFF schedules a
  guarded merge; raw residual close, same-main consolidation and full replacement
  have different effects. None drops backing or creates a third leg.
- **Ordinary upkeep:**85% of centre-to-boundary distance, physical/reference
  same-side corroboration,600-second sampled persistence,300-second maximum
  gap,240-second service checks, durable60–300-second jitter and hard12-hour
  initial interval remain separate controls. They do not prove continuous price
  history, best execution or no manipulation. Compound's in-range/threshold
  policy remains service-enforced as previously chosen.
- **Governance and recovery:** one human governance operator, a distinct limited
  keeper capability, guardian pause and temporary bootstrap. Paused emergency
  financial bypass remains explicit and may lose almost all principal; it is
  never automatic fallback. Terminal holder exit closes both legs, preserves
  reward/reserve backing and pays current owners in bounded isolated batches.
  Failed receivers retain backed recovery rights. Pre-exit V10 replacement is
  separate and trusts approved successor code.

The full state/operation interactions and conservation obligations are described
in [COVERAGE.md](COVERAGE.md). No claim/import/conversion is counted as new income;
missing prices/history remain unavailable rather than guessed zero.

## Historical reconciliation

[HISTORY_DISPOSITIONS.json](HISTORY_DISPOSITIONS.json) joins every original310
record to its prior individual assessment: earlier39 plus four disjoint
partitions totaling271. The latest57-record reconciliation is retained
separately, with explicit later metadata2 context where applicable. These are
not367 independent defects or367 fresh audits.

The ledger preserves origin IDs, exact pointers, hash encodings, prior subclaim
dispositions, task links and context-drift flags. It does not silently promote
an old assessment to proof of changed source.186 original records have at least
one changed/missing referenced file and124 have matching references; those are
reference comparisons, **not186 unresolved bugs or124 security approvals**.
Current family reviews, subsequent scoped source/size/rehearsal evidence and new
fixes are separate overlays. Retired bridge, external-custody, extra-contribution
asset, timelock and royalty-converter requirements stay retired.

Relevant remaining obligations continue under the existing Todo IDs. No task
status was changed merely because this audit or a historical join completed.

## Verification actually performed

See [VERIFICATION.md](VERIFICATION.md) for final focused counts, exact source
stages, failures, skips, mechanical checks and reuse boundaries. Baseline
regressions were recorded before the corresponding fixes. New checks cover
authority admission, state-file presence, direct signer-profile construction,
fresh bundle closure and immutable historical archive compatibility.

All61 production Solidity hashes match the accepted metadata2 source. The
existing48 normal size gates,569 source-scoped static records, changed metadata
constructor/read rehearsal and earlier LP/accounting/recovery evidence are reused
only at their documented exact scopes. No unchanged Solidity/browser suite,
compiler, static-analysis run, public RPC probe, public transaction or local-chain
rehearsal was executed for this audit. No new CI-green claim is made.

The existing thirteen metadata checks were registered without execution. Two
real filesystem symlink checks remain explicitly skipped because this Windows
account lacks that privilege; portable injected regressions are not a Unix
operating rehearsal. The baseline paths, original dirty documents and full tracked
file inventory were archived outside Git before source edits.

## What remains before production

| Obligation | Needed evidence / owning task |
| --- | --- |
| Independent markets | Two genuinely independent ETH/ZZZ valuation paths, publication/liveness/admin review, useful bidirectional external depth, source/venue/target compatibility. [Feeds](../../TODO.md#task-dual-price-qualification), [selected pool](../../TODO.md#task-pons-qualification). |
| Complete fees and operating budgets | Actual target/provider full-work estimates/traces/L1 components, operator ceilings, maximum-state/cold costs and explicit20M/24M adoption. Default12M stays. [Inventory](../../TODO.md#task-native-production-preflight). |
| Authorities and deployment | Real wallet control/rotation/recovery, exact release constructors/addresses/runtime bindings, configuration and independent sign-off. Offline input acceptance is insufficient. [Deployment](../../TODO.md#task-deployment-initcode). |
| VRF/OpenSea/content | Supported funded coordinator, sale/payer/platform settlement, timed cohort, real callbacks, metadata content/retrieval and notifications. [Mint](../../TODO.md#task-opensea-mint), [draw](../../TODO.md#task-fair-draw), [metadata](../../TODO.md#task-metadata-ops). |
| Services and recovery | Actual Unix single-signer fencing, RPC outages/reorgs, off-host backup/restore, alert delivery, contract-wallet/manual workflows and lifetime history. [Hosting](../../TODO.md#task-host-services), [recovery](../../TODO.md#task-keeper-recovery). |
| Matching integration | Actual current-profile read/unsigned consumer rollout and separately authorized wallet path; public signing remains disabled. Demo and poplint stay distinct. [Wallet](../../TODO.md#task-wallet). |
| Economic/operational limits | Repeated permitted losses/MEV, spot-reference manipulation/correlation, service-only compound policy, unsupported-token liveness, finite bucket/currency capacity, governance/successor trust and home-chain failure. [Security](../../TODO.md#security--audit). |
| Independent approval | Frozen exact source/configuration, independent audit/remediation and final release record. [Approval](../../docs/RELEASE_CHECKLIST.md). |

Oracle still has3 runtime bytes of headroom, Vault32 and Manager101 in the
accepted build. Two stale source comments (a WETH target example and portfolio1
label) are recorded for a coordinated build; changing comments alone would
invalidate compiler metadata/source pins without fixing executable behavior.

There is no evidence-backed reason here to relax safeguards, raise defaults,
restore removed features or ask a new economic question. Remaining unknowns are
qualification/accepted boundaries, not invented answers.

## Publication and environments

The central Todo, operator guide, feature reference, roadmap, current memory,
audit guidance and website documentation are updated together. Source/docs
publication is separate from installed adoption. Existing Anvil state, NFTs,
LP/balances, journals/checkpoints, artwork, dist overlays, popldemo, poplint and
services remain untouched. The shared signer is byte-identical/Anvil-only, both
public configurations remain null and the user-paused heartbeat stays paused.

Exact file/preservation and publication results accompany the final evidence.
