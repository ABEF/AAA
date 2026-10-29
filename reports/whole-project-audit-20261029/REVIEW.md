# Whole-project review and implemented improvements

Reviewed2026-10-29 Paris. Baselines: contract main`781fcc9d224f77a4a54d278878ffc3b002b71e26`,
website main`e5bb2163e0af0019bd917f65711c1f669b2d6224`. This internal source review
is not production approval, an independent audit or a claim of exhaustive proof.
The [brief](../../docs/WHOLE_PROJECT_AUDIT_PROMPT.md) was drafted after actual
[understanding](UNDERSTANDING.md), [knowledge selection](KNOWLEDGE.md) and
[two sequential challenges](PROMPT_REVIEW.md), then executed.

## Material findings and repairs

| Finding | Reachability / consequence | Implemented repair and tradeoff |
| --- | --- | --- |
| F1: optional-currency fault hid ownership | Wallet inventory required optional token runtime/decimals reads; one failing currency could block the portfolio's initial ownership request despite healthy LP/native balances. No drain was demonstrated. | Ownership-only inventory uses the existing per-asset health-isolation path. Admitted addresses, core/runtime/lifecycle/history, owner/count, final canonical depth and work budget stay strict. No financial value is returned by this endpoint. |
| F2: permissive stored-history parsing | The read API accepted duplicate JSON fields/nonfinite metadata and missing raw envelope fields that its writer rejects. Parser resource failure could escape the explicit unavailable-history path. Local DB corruption is the precondition, not proof an outsider can edit it. | Strict shared JSON hooks, explicit `removed:false`, well-formed byte data even for unknown events, and bounded error translation. Valid claims/earnings/fractions remain exact; no extra RPC/write/financial operation. Coherently forged DB/provider remains a separate trust limit. |
| F3: metadata starvation across restart | Metadata priority changed only in memory before optional RPC. Repeated process loss before a later save could repeatedly select metadata ahead of LP maintenance. | Copy-on-write durable priority save precedes optional work after pending recovery. Failed save stops before work; only the scheduling bit may advance after an atomic-replace/post-write fault. One extra journal save per reached enabled turn; real host/disk/watchdog rehearsal remains required. |
| F4: targeted keeper CI omitted regressions | New confirmation/checkpoint/cadence/principal/telemetry and related modules were absent from the dedicated list; full verification did discover them separately. | Complete explicit module list, defined-class deduplication, fail-closed empty/duplicate/identity checks and inventory-only CLI. A selection count is not a new successful test campaign. |
| F5: current-labelled fork job used old fixtures | Published workflow source invoked the historical runner, not the independent current native-pool harness. | Current runner plus checksum-pinned official compiler and current receipt retention. Static wiring was checked; no compiler download, GitHub job or live RPC/fork was run here. |
| F6: operating prose contradicted source | Guides conflated historical hourly/five-minute schedules, outer polling and confirmed samples; an instruction denied the deliberately added final conversion head read. Handoff docs omitted lifetime alias workload. | Correct current timing/authority/dependency boundaries, preserve the final head guard and document actual six-domain row/call formulas and restart/rollback limits. Historical reports retain original bytes and scope. |

### Explicitly approved schedule improvement

After explaining polling/inclusion delays and tradeoffs, the user approved
**240-second service checks**, keeping the **900-second confirmation window and
strict300-second on-chain maximum gap unchanged**. No Solidity change is needed.
Original300-second journal schedules remain validated and untouched on load;
normal evaluation can check by `last_checked_at+240` and writes the new schedule.
Pending nonce/hash/spend/original review/reset/jitter are preserved. Config needs
poll60-240 and matching health writer/checker; no installed service was changed.

The roughly60-second margin reduces avoidable resets, not manipulation proof or
guaranteed inclusion. With four-minute samples, a clean new window is normally
next evaluated at about minute16, then jitter/execution. The user also requested
a **proposed Todo improvement**: evaluate observations during cooldown while
retaining the12-hour execution minimum, all identity/reset rules and final guards.
That is not implemented; current confirmation starts after cooldown. One present
price cannot prove an earlier four-hour range exit.
The user subsequently requested a higher-liquidity independent reference.
Current spot-versus-oracle agreement is implemented; a deeper-market/TWAP adapter
and requiring the reference itself to remain outside are not. The existing Todo
records market/window qualification and the pending agreement-only versus
same-side-reference trigger choice. No physical tick or USD safeguard was replaced.

## Architecture and financial conclusions

No independently reproduced Solidity defect requiring a source edit was found
in this pass. No ABI, storage, economic allocation, holder entitlement, custody,
governance authority or dependency/toolchain pin changed. [Contract review](CONTRACTS.md)
reconstructs original-budget entry, factual marginal LP/share issuance, physical
range management,20-unit16/2/1/1 fees, owner boundary dust, index/fraction backing,
royalty cohorts, claims/conversion, holder return and full six-domain replacement.

LP claims do not harvest or compound/burn. Royalty claims can index already
received pending royalties before paying. Whole claimables need not equal
liabilities because fractions/division residue remain backed. Actual holder
return includes principal/compound, keeping earned rewards and buyback separate.
Current-owner callbacks can validly affect later payments. Governance/dependency
trust, IL, repeated permitted loss and public MEV remain real economic risks.

Same-chain replacement has8019rows/2028direct calls in the1000NFT, onebucket,
onealias, twoLP-currency/one-royalty example, before setup/retries. Lifetime aliases
grow separately from four permanent bucket slots. The new
[workload calculation](../../docs/CANONICAL_HANDOFF.md#workflow-size-and-relay-budget)
supports operating budgets/resumption without deleting history or adding overrides.

## Remaining findings, decisions and boundaries

- **Fresh Entry-v3 cleanup candidate:** useful principal execution is unreachable
  for its ERC20-only distinct-pair branch under fixed nativeETH/ZZZ. Removal needs
  a fresh explicit routing ABI/profile and all consumers. It is not a demonstrated
  drain. Separate royalty-v3 wrapper conversion remains valid and must not be
  removed as a principal-input cleanup.
- **Website example metadata:**696dormant downloadable JSONs have trait0 rather
  than fixed rarity1/2/3. A generator patch and12temp-copy scenarios are prepared,
  not applied. Existing metadata descriptions/manifests still need authorized
  regeneration. Current3 upgrade audio/effects and fresh4 browser integration
  remain separate gaps; the website/signer/build/dist/server stayed unchanged.
- **Compiler/dependencies:** [applicability screen](COMPILER_DEPENDENCIES.md)
  checks77exact inputs and official predicates; no automatic upgrade or false
  whole-compiler certification. Generated/virtual lowering sign-off and independent
  audit remain required, alongside exact constructor/maximal gas qualification.
- **Coverage depth:** [ledger](COVERAGE.md) distinguishes reconstructed components,
  critical-path traces, individual-body pending work, fresh verification and exact
  source-bound reuse.711callable entries/22scenario groups are not executed tests;
 494individual-body entries retain pending depth, not an “all audited” label.
- **External release gates:** independent feeds, feasible conversion/activation
  routes, supported VRF, authorities, token controls/burn, OpenSea primary mint,
  authentic history, immutable hosting/marketplace refresh, real wallet/escrow,
  sustained strict-timing/Linux/old-host/backup/gas/alert rehearsals and independent
  audit/remediation remain open in the existing task IDs.

## Delivery and verification

[Verification](VERIFICATION.md) records five exact current canonical composition
passes, scoped Python/metadata checks and exact unchanged EVM/build reuse. Failed
controls/fixtures and a vacuous zero-selected Forge attempt are retained, not
counted as passes. A meaningful exact-selection check rejected that attempt.

Relevant operator/specialist guides, sole ledger/generated Todo, feature/evidence,
roadmap, release record and repository context are synchronized. Stale current
instructions are replaced; old report bytes and four unrelated dirty drafts are
preserved. Main publication is separate from deployment. Public signing remains
disabled, browser signer Anvil-only, sites unmodified, heartbeat paused and
production **NOT APPROVED**.
