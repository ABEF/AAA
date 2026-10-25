# Coverage and critical decision review

This is a risk-led improvement pass, not an independent comprehensive audit.
Rows identify inspected boundaries and reused records; a listed file is not a
claim that every line, dependency or live service was freshly verified.

| Area from original prompt | Actual scope and evidence boundary |
| --- | --- |
| 1 Requirements | README, sole Todo, current handoff and user decisions reconciled; undeployed candidate distinguished from historical Anvil/public simulation. |
| 2 Architecture | Entry/Pricing/Registry constructor coupling and schema boundaries inspected; normal deployment sizes are mandatory. |
| 3 User journeys | Contribution review through actual entry, ownership and metadata; wallet acceptance stays historical/local and public signing disabled. |
| 4 Lifecycle | Activation/reveal/eligibility and reorg reconciliation inspected; canonical/custody lifecycle evidence reused, not globally rerun. |
| 5 Inputs | New reviewed-cap bounds and RPC header shape/identity boundaries receive focused checks. Existing typed token/route admission retained. |
| 6 Mathematics/units | Bps, cap comparison and existing conservative upper-input/lower-LP floors inspected; LP/royalty ledgers remain distinct. |
| 7 Time/ordering | Review versus inclusion policy, canonical ancestry, reveal versus activation and current-holder rights. |
| 8 Concurrency/atomicity | Before-pull policy check; history rollback requires a proven ancestor before atomic mutation. No service journals reset. |
| 9 Errors/retries | Missing/malformed RPC data must report unavailable, never authorize destructive history rollback. Refused redirects and HTTP error bodies close before bounded retry/failover. |
| 10 Persistence | SQLite cursor/events rollback boundary inspected; no existing live DB or chain modified. |
| 11 APIs/schemas | Explicit reviewed Entry version and selector/trace/pin compatibility; no runtime-driven silent downgrade. |
| 12 Dependencies | Reviewed on-chain pins and fail-closed reads retained; actual providers/routes/feeds/VRF remain unqualified. |
| 13 Authorization | Fixed Entry/Pricing/Registry callers, governance and immutable helper bindings inspected for changed paths. |
| 14 Keys/signatures | No key access/broadcast; signer remains Anvil-only. Existing nonce/recovery evidence reused within original scope. |
| 15 Infrastructure | Existing bounded HTTP/RPC and service isolation records consulted; no new live security scan or service action. |
| 16 Supply chain | Exact dependency versions/lock, pinned Actions SHAs and read-only CI permissions inspected. No dependency upgrade introduced. |
| 17 Contract execution | Affected callbacks, floor capture, revert order and normal runtime/initcode gates inspected/tested. Broader accounting evidence reused. |
| 18 Interoperability | ETH versus WETH/historical profiles and revealed metadata semantics inspected. Exotic token behavior remains conditional admission. |
| 19 Adversaries | Governance-policy races, invalid RPC ancestors, dormant/unrevealed traits and legacy-selector misuse considered. No universal exploit-absence claim. |
| 20 Oracles | Dual-source/freshness/conservative-bound design and existing evidence consulted; two addresses do not establish source independence. |
| 21 MEV | Reviewed maximum prevents policy widening at inclusion; it does not fix a range, prevent sandwiching or guarantee pool depth. |
| 22 Economics | 80/10/5/5 and royalty weighting retained; high selected-pool fee and cheaper conversion-route qualification stay open. |
| 23 Accounting | No principal/reward/custody classification change; metadata display separated from eligible economic weight. |
| 24 Shares/dilution | Existing marginal deployed-LP and incumbent-preservation evidence reused; no share formula or membership policy changed. |
| 25 NFT rights | Rarity trait remains visible dormant without granting rewards; transfers keep original current-owner accounting. |
| 26 Scoring/eligibility | No Power/gamification system; known rarity versus activation entitlement explicitly separated. |
| 27 AMM lifecycle | Actual v4 local composition evidence reused; no real provider/depth/target-chain qualification inferred. |
| 28 Maintenance | Buyback USD ceiling now uses upper input bounds rounded upward. Prior bounded two-pass/idle/range implementation and scoped tests retained. Range drift is not continuous volatility. |
| 29 Keeper | New maintenance/range suites included in the focused Linux CI selection; current journals and services untouched. |
| 30 Governance | Immediate authority/no timelock is an accepted risk; avoid treating reviewed caps as a defence against arbitrary approved dependencies/custodians. |
| 31 Locking/custody | No holder redemption; approved external custody is trusted and source cannot force return. No sweep added. |
| 32 Upgrades/compatibility | Candidate is undeployed; immutable sealed code cannot acquire new selectors through configuration. New version needs new code/inventory. |
| 33 Migration | Local moves and external custody/same-chain handoff remain; integrated bridges and remote ledgers deferred, not newly required. |
| 34 RPC/indexers/finality | Concrete missing-header rollback defect fixed; bounded proven ancestry distinguishes reorg from outage. Finality/provider honesty still external. |
| 35 Capacity | Normal bytecode/initcode limits measured for changed production objects. Existing cold gas evidence reused only when inputs match. |
| 36 Cost | Remove unused stale bootstrap admission rather than add a deployment factory; no unnecessary full-suite reruns or background work. |
| 37 Diagnostics | Precise reviewed-cap/version and unavailable ancestry errors; preserve raw evidence and scoped failures without keys. |
| 38 Metrics | Existing keeper/indexer health/runbooks inspected by area reviewer; no claim of live uptime or production SLO acceptance. |
| 39 Alerts | Paused monitoring respected; no new schedules/notifications created. Operator outage actions documented. |
| 40 Recovery | Failed ancestry probes leave durable history intact; recovery/backups remain operator/provider qualification, not invented fallback. |
| 41 Release provenance | Main-only selective publication; old dirty drafts excluded, exact bindings and separate publication receipt required. |
| 42 UX/accessibility | Financial wording/profile mismatch inspected; historical 1% Anvil profile must not be reinterpreted as new 2% native V2. Actual extension/native V2 UX remains open. |
| 43 Privacy | No wallet secrets, browser storage or user live journals read. Reports contain public code/configuration and sanitized fixture diagnostics. |
| 44 Maintainability | Explicit small capability versions and removal of stale automatic wrapper trust; no generic executor/framework added. |
| 45 CI/testing | Focused Linux keeper suite selection and changed-surface checks; unchanged prior evidence identified instead of inflated counts. |
| 46 Docs/handover | Single Todo/features/operator and memories maintained; historical reports keep original scope. |
| 47 Continuity | Whole-protocol replacement needs funded canonical handoff; external LP custody alone cannot relocate NFT ownership/reward ledgers. Post-halt recovery remains deferred. |
| 48 AI | No autonomous production AI/LLM execution subsystem. Deterministic keeper and human-reviewed code provenance are relevant; model safety evaluations are not applicable. |

## Previous decisions challenged

- **Immediate governance and trusted custody:** convenient recovery and same-day
  operations also allow dangerous dependencies or off-chain diversion. Local
  invariants cannot remove that trust. Preserve it explicitly; choose reviewed
  multisigs, separation and independent admission review before release.
- **Per-operation loss caps:** 3% each does not bound cumulative turnover losses,
  impermanent loss or future prices. The user declined a cumulative breaker.
  Preserve that decision and qualify strategy economics, cadence and alerts.
- **Two feeds and 3% disagreement:** correlated/manipulated sources can agree.
  Independently review upstreams, liquidity, proxy authority and stale-market
  behavior. Conservative bounds can reject contributions even inside 3%.
- **Keeper widths:** +/-25/50% does not ensure continuous fees or timely repair.
  Current drift from applied center is not historical volatility. Opt-in policy
  requires economic thresholds; do not invent production defaults.
- **Marketplace royalties:** ERC-2981 requests, not universally enforces, payment.
  Reveal fixes the royalty trait; activation begins eligible receipts. No promise
  of revenue before actual funded payments.
- **Nested deployment size:** 31 bytes of Registry initcode headroom is not a
  healthy evolution margin. Remove unused stale wrapper auto-admission before
  adding review binding; never weaken deployment limits or vault checks.
- **Frontend versions:** the current reviewed website profile intentionally
  assumes its historical 1%/old Entry ABI. It fails closed against new native V2;
  it must not be made compatible by relabeling addresses or relaxing validation.
