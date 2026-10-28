# Third-pass audit: three-day change and interaction review

Started2026-10-28; completed2026-10-29 Paris. Frozen source baseline:
`cb0aadfe61b0bdcebab1838adbcf1b5835215510`, main. The request-time window remains
**October26-28**, despite crossing midnight. [The prompt](../../docs/THIRD_PASS_AUDIT_PROMPT.md)
was written before execution; [the commit/path inventory](three-day-inventory.json)
records35reachable commits,19/8/8by day, and71distinct changed source/config paths.
**Production remains NOT APPROVED.**

## Prompt adaptations

The brief uses actual accounting4/custody3/V5, fixed ETH/ZZZ, holder return,
immediate governance, LP routing1/quality1/confirmation1 and current operating
decisions. It includes older callers/callees, rewards/history, callbacks, recovery,
provider consistency, authority and read/unsigned boundaries. It distinguishes
confirmed defects, defense-in-depth, accepted economics/liveness and real external
qualification. It forbids speculative redesign, gate relaxation, broad unchanged
test reruns and claims of exhaustive security proof.

No timelock, bridge, external custodian, mutable ZZZ, stablecoin contributions,
passive/40% trigger or public-signing feature was reintroduced. Those are outside
the selected release, not missing requirements to implement during an audit.

## Confirmed findings and repairs

| Finding | Evidence, effect and repair | Classification |
| --- | --- | --- |
| A used signer's initial checkpoint fault bypassed fresh-window invalidation | `cycle()` validates a prior receipt anchor in `poll_pending()` before reaching the later global raw-state boundary. With no saved intent, a failed head/anchor read left mature confirmation and jitter usable after recovery. The catch now invalidates known fresh windows only in that no-pending case. Original saved-intent recovery retains related-only interruption tracking; historical profiles and post-work health failures are unchanged. | Service-level sampled-evidence/recovery correctness; no demonstrated fund-drain exploit. [Source](../../keeper/monitor.py), [seven regressions](../../tests_python/test_keeper_checkpoint_confirmation.py). |
| Conversion snapshot parsing escaped worker isolation or accepted future time | The shared LP/royalty worker manually parsed headers; missing/null timestamps could raise `KeyError`/`TypeError` outside its deferral boundary. Its one-sided age check accepted a future cutoff. It now uses shared canonical parsing, timestamp ordering and confirmation/depth/age checks, including after the final price read. Quote-eligible conversions deliberately add one final head read and refresh their deadline; disabled/low-amount paths retain existing work. No broader catch; exact300-second age remains accepted and301rejected. Actual malformed-worker scheduling still permits an independently due harvest. | Optional-worker availability and read-admission correctness; on-chain converter floors/backing remain authoritative. [Source](../../keeper/royalties.py), [regressions](../../tests_python/test_keeper_conversion_headers.py). |
| Indexer head admission was weaker than header admission | `int(result,16)` accepted responses such as missing prefix, leading-zero zero, whitespace or uppercase prefix. Some malformed responses caused successful no-progress or admitted new ingestion rather than a fixed safety error. The existing canonical signed63-bit header-quantity validator now handles `eth_blockNumber`. Legitimate zero and confirmed ingestion are preserved. Separately proved reorganization rollback remains independent. | Ingestion consistency/observability; does not authenticate a dishonest provider. [Source](../../indexer/monitor.py), [two regressions](../../tests_python/test_indexer_head_safety.py). |

All three source changes are backend repairs. No Solidity, storage/ABI, economic
rights, price/slippage/loss policy, signer capability or pending journal schema
changed. Existing source balances, principal and reserve ownership are preserved.

## Workstream coverage and outcomes

| Workstream | Inspected interactions and outcome |
| --- | --- |
| Contracts, permissions and lifecycle | Exit/share/current-owner payouts, callback guards, pending compound, old rewards/royalties, canonical freeze/import/abort/retire, fixed source/seal identities. Extended review includes Oracle/Entry/assets, converter base/typed executor, VRF setup/reveal and actual installed v4 settlement. No new confirmed Solidity defect. Not every unchanged canonical record branch or all665callables was newly reconstructed or executed. |
| Financial accounting and history | Owner-index/share and equal-member index, rarity cohorts/fractions,20-unit fee allocation/dust, source-to-ETH credits, claims/transfer order, original-currency today's-price reporting and same-chain replay. Gross receipts/reserves/principal remain distinct from NFT earnings. No new confirmed financial misallocation in these traces; authentic complete historical logs remain required. |
| Routing, prices and manipulation | Actual-core post-withdrawal quotes, bounded venues/zero-or-one swap, entrant isolation, source bounds, captured floors, quality versus known fees, sampled readiness and manual-width exception. Existing guards are not proof that IL, keeper trading or external MEV is unprofitable. |
| Keeper and recovery | Receipt checkpoints, pending/hashless intent ordering, relevant versus unrelated failures, clear acknowledgements, clock/cooldown/sample/jitter/compound/harvest, paid-revert and principal retry/fairness, health/watchdog. Two additional defects above repaired; no broad configuration deferral was introduced. Invalid local configuration deliberately remains a startup failure. |
| Read/unsigned/API inventory | Exact approval amounts/spenders/value, full Entry trace, pinned snapshots/lifecycle/holdings/NAV, physical PoolKey/ticks, profile boundaries, client concurrency/worker deadlines and quarantine. No new confirmed defect beyond the ingestion path; coherent dishonest RPC and real capacity remain unqualified. |
| Tools, deployment and instructions | Current/historical observer dispatch, fixed read-only fork relay, normal profile/cleanup/result gates, holder CLI input bounds, rehearsal profile, service unit and current inventory examples. Changed hunks and constraints were inspected; no operating script/service/fork/public provider was executed for this pass. |

The35commits and their parents/paths are enumerated, then the current combined
changes and named earlier dependencies are reviewed. Intermediate historical
versions were not all compiled/executed again. Static inspected paths, scenarios
and commit rows are not test passes; [verification](VERIFICATION.md) states actual
fresh versus reused scopes.

## Documentation and operational corrections

Current earnings/indexer guidance now states accounting4/canonicalV5 and labels
historical3/V4 external-royalty-custody replay explicitly. The dependency table no
longer asks for an external custody recipient or treats served unconfigured
current3 poplint as fresh4 acceptance. The security plan no longer asks for the
retired two-pass balancer. Operator/recovery/conversion/indexer procedures explain
the new fault boundaries; Todo acceptance, feature/evidence reference, roadmap,
release limits, repository context and report map are synchronized.

One speculative concern was deliberately not implemented: intra-transaction NFT
NAV may be transient during contribution mutation. Confirmed-block readers do
not observe that state; a reachable current user-controlled callback or supported
external collateral consumer was not established. It is recorded as a future
external-consumer integration caveat, not a proved exploit, new release blocker
or reason to add an unverified Solidity guard. The original contract review
receipt was preserved before the extended note.

## Remaining limits

Strict300-second observation gaps still have the user-selected liveness tradeoff;
samples cannot prove continuous persistence. Broken tokens/venues can prevent
closure/payment. Proxy/issuer/governance trust, complete authentic logs, actual
prices/routes/VRF/authorities/OpenSea, fresh website/service acceptance, maximal
target gas/constructor arguments, Linux/host recovery and independent audit with
remediation remain open. No new production qualification is inferred.

No deployment, public transaction, funded-wallet use, service/site rollout,
preserved Anvil/NFT/LP/balance/journal change, signer expansion or paused-monitor
restart occurred. Four original dirty files and all historical receipts remain
byte-identical. Publication is a separate verified Git operation.
