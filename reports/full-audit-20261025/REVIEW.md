# Full current-candidate internal audit

**Production NOT APPROVED.** This is a broad internal source/call-path audit,
fresh static analysis and focused remediation. It is not an independent audit,
formal verification, a fresh full release regression or a guarantee of no bugs.
The user authorized auditing/improving the project, not deploying contracts,
changing running services or extending wallet signing.

## Scope and coverage

Initial main is `e32e9669d79bc3c576175f51f72d8277f6fa48f9`, including implementation
`fbf31c6`. Production Solidity still equals reference35007db. The current release
is native ETH/fixed ZZZ, accounting3, direct governance2 and local canonicalV4.
Historical versions and existing Anvil deployments/journals are not upgraded.
Fourteen unrelated dirty files and unrelated untracked artifacts are excluded;
owned additions to dirty documents are staged separately from their original bytes.

| Area | Review performed | Evidence / boundary |
| --- | --- | --- |
| Principal, shares, prices and physical LP | Entry→pricing→Vault→budget→Manager/typed executor; old fees/compound attribution, exact debits/refunds, immutable context, spot/price fingerprints, actual LP identity/ticks/deltas, ranges and maintenance | [Principal review](PRINCIPAL.md). Real provider/venue economics, gas and token behavior remain unqualified. |
| NFT ownership, LP rewards and royalties | Mint/reveal/quotas, current-owner claims/callback transfers, fractions/indexes, equal active collective shares,80/10/5/5 and separate rarity-weighted funded royalties, conversion and fixed-ZZZ burn | [Rights review](RIGHTS.md). No new unprivileged theft/double claim confirmed in inspected paths; not proof of absence. |
| Authority, pool movement and custody | Direct governance, fixed seal bindings, pause/preparation/retirement, same-pair moves, normal/raw principal exit, royalty custody, exact funding/abort and all six same-chain handoff domains | [Rights review](RIGHTS.md) and [principal review](PRINCIPAL.md). External custody is a real privileged fund-movement trust; source cannot force return. |
| API, RPC, history, indexer and unsigned preparation | Typed addresses/ABI, current-profile state, canonical snapshots, exact approvals, bounded traces/fees, raw log provenance/history, request/worker budgets and independent provider comparison | [Services review](SERVICES.md), including three reproduced/fixed integration defects. Synthetic responses are not actual service qualification. |
| Keeper, operational recovery and keys | Chain-state discovery, intent/nonce/receipt journal, bounded simulation/review, no automatic resend or guessed limits; admission/HTTP/DB/backup boundaries | [Service traces](SERVICES.md). No existing journal, process, signing policy or monitoring schedule changed. |
| Website integration | Read-only review of six critical deployment/client/wallet/transaction consumer files | Current native reader is still accounting2-only and rejects current3. Public DEPLOYMENT remains null and signing Anvil-only; website rollout/implementation remains open. |
| Build, dependencies, static analysis and docs | Fresh closed86-source solc output; actual Slither0.11.6 run; every399finding manually triaged in three source-specific slices; current47-source/build review replaces stale triage. Actual installed48Python versions match lock | [Verification](VERIFICATION.md), [static decisions](static-review-verification.json), [upstream check](UPSTREAM.md). No green published CI or independent compiler/venue approval claimed. |

The44production source units are covered by the financial/manual slices, helper
and interface checks and the full analyzer source inventory. The callable ABI
has31concrete contracts/608functions/13receive hooks; those counts are not608
new execution tests. Hash manifests bind reviewed files and executed evidence,
not a claim that every schedule in every source file was exercised. See
[coverage and preservation](COVERAGE.md).

## Confirmed defects fixed

All three have **P2 functional impact and high confidence**. They prevent valid
operations/qualification; none demonstrated stolen funds or relaxed authorization.
The exact unchanged pre-fix fixtures fail and corrected fixtures pass.

### S-P2-1: activation preparation used the obsolete dormant status

`frontend_api/activation.py` required literal5 for dormant NFTs. Current accounting3
uses3, already exposed by validated `Projection.dormant_status`. A valid freshly
minted current NFT therefore failed preparation before obtaining an unsigned
activation review. Preparation now uses that explicit profile value; it does
not guess a version or accept both statuses. Active growth still requires1.

### S-P2-2: native ETH was rejected in a required source-policy call

Current source verification must call `isContributionAsset(address(0))` for ETH.
The generic address codec forbids zero, and this predicate's one native asset
argument was missing from `Projection._call`'s typed allowlist. Thus current
activation/growth still failed after passing the status check. Only that exact
argument0/selector is admitted for native profiles2/3. Zero contract/owner targets,
unknown selectors, old incompatible profiles and arbitrary call endpoints remain
rejected. No writer or public signing capability is added.

### S-P2-3: independent history audit rejected the real RPC adapter

`HistoryAudit.run` expected hexadecimal wire text for `eth_chainId`, whereas
the actual reviewed `Rpc.call` deliberately returns a checked integer. Existing
fixtures returned wire hex, hiding the composition defect. The audit now accepts
exact checked integers or canonical hex from explicitly injected transports,
rejecting Boolean/floating/malformed values. New offline tests use the actual
RPC adapter with only its HTTP transport replaced and real temporary SQLite.
No live network or original database is touched.

[Service evidence](SERVICES.md) records9new methods plus2affected compatibility
controls, all11passing across the exact scopes. Original six activation subcase
errors and the actual history-transport failure remain archived. This is real
production-source preparation/tooling improvement, not a demo-only patch.

### S-P3-4: example website copy still reflects retired contribution rules

The read-only frontend follow-up finds that `app.js`'s example liquidity form
still offers USDC/USDG and describes99%deployment. Current contracts accept
ETH/fixed ZZZ only and default to98%deployment. The form labels its amounts as
examples and moves no real assets; no public transaction or approval is enabled.
This is a **P3 product/integration inconsistency**, not a financial bypass.
It remains open with explicit current3website acceptance: source/build/server
and signing policy are preserved in this audit. Align those labels/selectors
and current-profile readers before a separately authorized website release.
The [read-only snapshot](website-copy-bindings.json) binds the actual source;
it is not a claim that a deployed server bundle was fetched or changed.

## Static analysis: stale gate replaced by actual current analysis

The analyzer completed successfully with399flags:77High,57Medium,193Low,
54Informational and18Optimization labels. These labels are not399confirmed
vulnerabilities. All fingerprints were reviewed against actual source/callers:
165false positives,152accepted design/availability risks and82informational
items. [Exact decisions and gate](static-review-verification.json) match the
new checked-in `reports/production/slither-review.json` and all47required
source/build bindings. **Current internal static-review coverage gate now passes.**

Principal143, rights165 and root91rows are independently partitioned with no
missing/duplicate fingerprint. Reentrancy/balance warnings predominantly concern
deliberate original-balance conservation checks inside fixed-caller locked paths;
replacing those baselines after callbacks would weaken protection. Arbitrary
custody sends remain accepted privileged risk, not mislabeled immutability.
Bounded loops retain real gas/token-liveness release requirements. Informational
complexity/caching suggestions do not justify removing financial checks or
changing near-limit code merely to silence a detector.

Solc succeeded in74.57s and emitted complete86-input ABI/AST/bytecode. Forge then
failed while creating its host local-signature cache; that CLI failure is not
relabeled as a successful Forge build. Slither reads the complete captured output.
Its first bootstrap lacked Forge in subprocess PATH; that failure is preserved,
and a task-local PATH repair allowed one completed detector run without recompiling.
The fresh37production object lengths equal the saved normal75-input capture;
normal limits pass their original scope. Exact release dynamic arguments remain
unqualified. [Execution record](static-execution.json) preserves every limitation.

## Gas concern investigated instead of assumed

A new composed capacity test applies16optional royalty-currency gas faults with
four buckets and33LP reward assets. The initial diagnostic incorrectly predicted
failure below12M; the actual activation succeeded, so that diagnostic assertion
failed. The new test was corrected to require success and protected accounting,
without changing a contract or gas limit. One final selected method passes.

The activation CALL uses **9,591,082raw gas under the unchanged12Mbudget**.
The14,347,040full-test gas includes subsequent16currency recovery and assertions,
so it is not compared to the activation budget. The existing cooling helper marks
accounts/storage cold. Exact debits, fair new shares, all16deferred cohorts,
native enrollment and no earlier LP/royalty theft are checked. Existing four
public test methods remain unchanged. This mocked venue/price/authority fixture
does not prove actual native Entry/Core/target-chain worst-case gas or affordability.
See [gas evidence](principal-gas-verification.json).

## Remaining risks and decisions

- **Governance and custody:** immediate governance can change admitted operational
  policy and approve external custody. A recipient can divert/withhold assets.
  That accepted power is a withdrawal path for governance; sealing does not
  remove it. No timelock, holder redemption or forced-return mechanism is added.
- **Actual dependency qualification:** real independent ETH/ZZZ USD sources,
  runtime/proxy/common-mode controls, supported VRF/updater, actual routes and
  selected native venue remain open. A valid3% feed agreement does not guarantee
  the tighter2% contribution floor; upper-input/lower-LP bounds plus venue costs
  can still reject it. The selected pool's fee exceeds the default1% conversion
  budget, so a cheaper qualified route is required.
- **Buyback:** actual fixed ZZZ must support exact `burn(uint256)` balance and
  totalSupply reductions. ERC20/pool compatibility alone is insufficient.
  A failed burn reverts and retains classified reserves; no automatic burn has
  been qualified on the real token.
- **Late unknown currencies:** retired royalty ledgers forward only admitted
  currencies and cannot admit new ones. A previously unadmitted token sent to
  an old receiver has no recovery path. Current support stays admitted-only;
  any bounded fixed-successor extension requires explicit policy/security/size
  review before seal. There is no arbitrary sweep. See [operator scope](../../docs/ROYALTY_SETTLEMENT.md#late-receipts-after-retirement).
- **Liveness and lost ownership:** pending randomness, unreadable admitted backing
  or unresolved custody can block complete collection handoff. Ordinary LP
  movement is separate from NFT reveal. Lost-key/dead-address NFTs retain their
  rights and eligibility; there is no proof-based lost-key recovery or forced
  redistribution. Chain halt/token blacklisting can defeat recovery despite
  correct code; post-halt canonical recovery is outside this release.
- **Marketplace/website/services:** custom direct mint still does not implement
  the required OpenSea gross0.05ETH/net-platform-fee flow. Current accounting3
  website/wallet acceptance, actual API/indexer/keeper hosting and operating
  rehearsals remain unqualified. Public signing stays disabled.
- **Release assurance:** normal RoyaltyFactory runtime has only69bytes margin;
  actual URI constructor arguments, maximal real gas/strategy economics, frozen
  complete release verification, compiler/dependency review and independent
  audit/remediation/sign-off remain required. No published CI green result or
  production readiness is inferred from internal triage.

No new unprivileged theft, share-dilution, double-claim or terminal-state replay
exploit was confirmed in inspected financial paths. This bounded conclusion
does not mean all such exploits have been disproved.

## Documentation and publication

The sole Todo, feature evidence, roadmap, release record, current policy headers,
operator/API/royalty guidance and repository memories are updated. Obsolete
current-task1%/USDG/USDC contribution and executor wording is corrected; genuinely
historical evidence retains its original scope. No ABI or callable permission
changed, so the current608-function reference is checked rather than regenerated
from new contract code that does not exist.

Only owned source/docs/tests/evidence are published on main; publication is
recorded separately after remote verification. No public RPC/financial
transaction/deployment/seal, website source/build/server/dist overlay,
existing8902/Anvil/NFT/LP/balance/journal, service or monitor operation occurred.
Public DEPLOYMENT remains null, signing Anvil-only and monitoring paused.
