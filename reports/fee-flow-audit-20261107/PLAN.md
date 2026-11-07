# LP conversion, claims and gas audit scope

Baseline main `c055684a558519eab308a24b81746bf1b9842d96`,7November2026.
Read actual source, current context/soleTodo/manual and prior exact-LP evidence.
Treat old progress messages as stages, not current approval. Source/docs only:
no deployment, service/site/Anvil/journal/signer changes or public transactions.

Trace actual ETH/ZZZ fee harvest→80/10/5/5→exact NFT books→keeper conversion→
same-NFT ETH credits→current-owner claim. Royalties remain original currencies.
Preserve principal/reserves, activation-time rights, old unclaimed rights,
transfer ordering, canonical backing/abort and ordinary pause/terminal behavior.
Separate internal ZZZ accounting from a normal ETH payout; do not imply conversion
happens inside a claim or that unavailable routes can be safely forced.

Audit integer rounding/no-op events, malformed input/return values, source/quote/
policy identity, callbacks/token/proxy faults, concurrent claims/transfers,
failed simulation, limited liquidity/feeds, daily/absolute/relative gas budgets,
oversized batches, cursor fairness, stale deadlines, UTC rollover, pending-first
recovery, restarts and review/configuration changes after sealing. Compare the
final native value, not only an intermediate wrapper's reference. Preserve
intent/calldata/floors; never invent zero, skip monetary rights or resend an
uncertain operation. Public signing remains disabled.

Implement concrete defects with before/after controls and focused regressions.
Where useful, add explicit reviewed backend gas flexibility with old policy1
unchanged and bounded opt-in policy2; no automatic limit increase or on-chain
governance setter is implied. Respect actual network/provider/consumer limits.
Reuse unchanged allocator/canonical evidence only within exact proven scope;
refresh real producer fixtures after actual source drift. Compile actual normal
contracts, triage actual static output without relaxed matching, bind artifacts/
references, preserve historical converter behavior explicitly and retain failures.
Update operator actions/reverse/restart boundaries, soleTodo, features, roadmap,
release and repository memory. Publish only the intended main changes.
