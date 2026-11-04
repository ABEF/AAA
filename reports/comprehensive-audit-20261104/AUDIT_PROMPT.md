# Whole-project audit and justified improvement brief

Executed scope: November4,2026, starting at main e237aa72ec7fa09382d857ffab1a3fd96b286299.
This consolidates the user-approved whole-project prompt, the [previous broad
brief](../../docs/THIRD_PASS_AUDIT_PROMPT.md), the [contract/LP brief](../smart-contract-lp-audit-20261103/AUDIT_PROMPT.md)
and the current instructions. Those historical briefs do not override current policy.

## Objective and authority

Understand, challenge, audit and improve PoPL end to end. Produce justified code,
operating, documentation and usability improvements with reproducible evidence;
do not manufacture changes or stop at generic recommendations. Distinguish a
behavior-preserving refactor from a correction, removal, economic decision or
architectural change. Continue independent work when external decisions are open.

Use main only. Preserve unrelated work, immutable reports, existing Anvil8902,
NFTs/LP/balances, journals and website dist overlays. Keep browser signing local
to Anvil, public DEPLOYMENT null and the user-stopped heartbeat off. Source/docs
publication is separate from deployment, sealing, transactions, services, sites
and journal migration; none of those operating changes is authorized here.
Never expose credentials. Archive originals before editing maintained documents.

## 1. Establish evidence before proposing changes

Read AGENTS/context/handoff, both complete READMEs, sole Todo, current identity,
architecture, feature/evidence and operator guides. Verify actual Git state and
compiler/dependency/configuration pins. Inventory production contracts, fixed
children, interfaces, functions, events, tests, services, read/unsigned APIs,
indexer, frontend, artwork, deployment tooling and preserved historical profiles.
Map ownership, value, messages and data through every trust boundary. Separate
accepted policy, actual source, simulated examples, served releases and unknowns.

Reconcile previous reports by exact source and dependency scope. Reuse unchanged
evidence explicitly, without adding overlapping test counts. Keep original
failures, skips and superseded requirements; do not reopen retired designs.

## 2. Research and challenge the plan

Use primary Solidity/compiler-advisory, pinned OpenZeppelin/Uniswap source,
Uniswap settlement/math, VRF, marketplace and ERC standards. Apply relevant OWASP
and audit methodologies as checklists, not proof of security. Investigate
applicability to this compiler/settings/dependency combination, not just names.
External examples do not prove PoPL's strategy optimal, profitable or MEV-safe.

Perform two separate plan critiques: first find missing components/interactions;
then challenge assumptions, evidence reuse, proposed fixes, verification and
authorization. Reread both READMEs before the final coverage check. Explicitly
list remaining unknowns and excluded/retired mechanisms with reasons.

## 3. Preserve and evaluate the current product

Account for1000 ERC721s, finite prepared artwork, exact600/300/100 rarity quotas,
fair assignment rather than image generation, current-value evolution and current
owner rights. Only native ETH/fixed ZZZ enter principal. Activation/growth default
100/5USD, contribution2%, conversion1%, maintenance3%, governed ceilings10%, gas
separate; dual-source agreement3% and fee-adjusted additional1% are distinct.
Future-governed terms do not rewrite old payments, claims or ownership.

Assess fixed80/10/5/5 funded LP allocation and separate rarity-weighted received
royalties. No Power, arbitrary custody recipient, integrated bridge, creator
inbox, token replacement or extra contribution asset. Separate royalty currency
and conversion-wrapper support remains legitimate. Challenge design tradeoffs
without silently changing them.

## 4. Review every contract interaction and function class

For each callable: purpose, caller, inputs/units, output, state transition,
external calls, pre/post checks, events, revert/rollback, bounds and recovery.
Inspect inheritance, constructors/children, immutable parent bindings, sealing,
governance/guardian/keeper/holder separation, pause/preparation/canonical/exit
states, callback admission, ERC721 approvals and read-only reentrancy.
Review arithmetic, signed/narrow types, assembly, storage layouts, gas loops,
allowances, exact deltas, prefunds/donations, malformed tokens and codehash/proxy
limitations. Preserve exact accounting, callbacks and atomic rollback.

## 5. Shares, contributions and custody

Trace incumbent checkpoints, entrant-only funds, marginal physical MAIN LP,
post-swap incumbent NAV, net share issuance and historical contributions. Test
zero/tiny values, rounding, share inflation, max limits, price movement, callbacks
and concurrent serialized entries. Existing idle/compound/residual must not fund
the entrant's floor. Entry must not recenter, reset clocks or grow residual L.
Value raw amounts per physical range; never sum incompatible liquidity units.

## 6. Uniswap portfolio and execution

Inspect pinned core/periphery, PoolKey/PoolId, static hookless native admission,
packed ticks and exact downward-boundary behavior, full tick spacing, native
settlement, Permit2/exact approvals, debt signs, collect versus close proceeds,
refunds, fee accounting and price impact after our own withdrawal.

One logical bucket has one main plus at most ONE optional residual in the same
pool. Review both-leg identity/custody/NAV/fees, default main>=60% at replacement,
half-side residual placement/gap, filled/mixed/outside residuals, mode changes,
partial close, merge, park, resume and terminal close. Follow repeated volatile
market cycles and1→2→1 transitions; never create a third leg or erase backing.

Evaluate bounded venue comparison independent of LP destination, actual-core
quotes, deterministic sizing, one balancing swap, captured gross/additional
loss and idle/caller floors, active-main proofs and adverse/empty routes. Reject
unsafe fallbacks. Explain infeasibility, gas/economic limits and operational exits.

## 7. Price, manipulation and timing

Review independent dual USD sources, raw units, fresh rounds, decimals,
sequencer grace, confidence, code/proxy updates and fixed operation valuations.
Do not presume stable pegs or target-pool spot independence. Examine local and
market-wide pumps/dumps, sandwiches, liquidity removal, timing extraction and
compromised keepers under repeated individually permitted losses.

Trace85% actual centre-to-boundary ZZZ-price distance, physical/reference
same-side corroboration,600s sampled window/maxgap300,240s checks, durable fresh
60–300s jitter and initial hard12h cooldown. Distinguish raw need, sampled
readiness, service timing and explicit manual geometry/emergency exceptions.
Evaluate missing/delayed samples, restarts, resets, identity changes and faults;
do not describe sampling/jitter as uninterrupted history or strong MEV protection.

## 8. Day-to-day keeper and reserves

Follow pending-first receipt/nonce/spend recovery, bounded work, queue fairness,
deadline priority, retries, configuration changes, key separation and stop/restart.
Hourly harvest includes both legs, applies the split once and is independent
from conversion/compound/buyback/claims. Coalesce clocks only from authenticated
successful receipts. Distinguish unrelated metadata faults from invalid price
evidence; avoid introducing perpetual reset/gas loops.

Compound uses designated reserve/idle and its separate governed interval after
max(lastCompound,lastRebalance); service waits in-range/below adjustment threshold
with no geometry pending. Include stranded-but-attributed idle, economic thresholds,
buyback gas/depth/fixed ZZZ burn and full operator recovery.

## 9. Rewards, royalties and historical reporting

Prove received backing,80/10/5/5 integer/dust policy, owner-share and equal-active
indices/fractions, membership changes, transfers, dormant NFTs, rarity-only
royalties, optional-currency outages/deferred admission and batch conversions.
No principal/reserve/orphan/quarantine subsidy, retroactive dilution, double
claim or double income. Current owner inherits old unclaimed rights; claims,
conversion/import and principal return are not new earnings. Reconcile net
24h/all-time/claimable/claimed amounts through transfers, moves and replacements,
at today's reviewed prices, with unavailable data never guessed zero.

## 10. Recovery and lifetime boundaries

Review reversible parking, residual-only close, guarded same-pair movement,
manual paused emergency and pre-exit same-chain canonical replacement separately.
Emergency financial bypass is trusted governance and may lose nearly all
principal; it is never automated fallback. Canonical V6 needs no live residual,
exact ownership/traits/shares/ledgers/fractions/backing, funded abort and one
active successor. Compatible wire is not runtime compatibility.

Terminal governance exit freezes LP activity, closes both legs, returns actual
ETH/ZZZ and compound by immutable per-NFT shares, allocates/distributes in bounded
governance-only batches to current owners, isolates failed receivers and preserves
backed owner fallback/old rewards/transfers/future royalties. Include1000 holders,
mixed wallets, dormant NFTs, different shares/rarities/tiers, partial failures and
transfers between allocation/payout. No reopening or post-exit canonical handoff.
State chain disappearance, broken dependencies, dead owners and key loss limits.

## 11. NFT, randomness, marketplace and artwork

Audit ordered VRF requests/callbacks/finalization, quotas, modulo significance,
fair remaining draws, funding/gas/outage/provider rotation without rerolls or
retargeting. Existing ERC721/direct mint is not OpenSea primary-drop integration;
verify exact product, chain and gross price/platform fees before claiming support.
ERC2981 requests royalties; only actual receipts can be allocated.

Check fixed artwork/trait mappings,1000 inventory versus2784 rendered states,
immutable design versus dynamic evolution, known dormant rarity weight versus
economic eligibility, metadata URI/CID hashes, refresh and unavailable valuations.
Preserve accepted egg texture/assets and actual audio/image confirmation timing.

## 12. Backend, data, concurrency and frontend

Inspect same-block/hash reads, code/lifecycle/profile/ownership bindings, RPC
failover, malformed responses, budget/deadline cancellation, strict transaction
preparation, exact approvals, allowances, expiry and unsigned-only boundaries.
Review indexer anchors, confirmed depth, reorg proof, atomic transactions,
configuration identity, duplicate/omitted/contradictory logs, restart/restore,
historical lineage, SQLite/WAL contention, memory/CPU and years of history.
Provider responses and matched hashes do not prove complete honest history.

Check bounded HTTP admission, framing, proxy identity, timeouts, workers,
multi-user/cross-tab/account/network concurrency, stale/cancelled requests,
pending saved intents, rejection/replacement/nonce gaps and recovery without
resending. Preserve signer restrictions. UI must distinguish approval/submitted/
confirmed LP/reward refresh and unavailable/pending/dormant states, use current
net NFT rights, mapped evolution and accessible responsive reduced-motion behavior.

Separate popldemo, served current3 poplint and fresh source8. Update stale current
documentation without relabelling historic codecs, releases, fixtures or journals.
Keep demo values clearly illustrative and do not inject them into integration.

## 13. Operations, maintainability and verification

Review dependencies/toolchain/compiler bugs, size/initcode/constructor limits,
CI/publication provenance, storage/backup/restore, logs/secret redaction, alerts,
funding, rotations, outages, operator workload, supply-chain and succession.
Write exact procedures with authority/inputs/outputs, prerequisites, limits,
verification, pause/restart/reverse and irreversible boundaries. No generic
executor, unnecessary policy layer or unapproved complexity as a shortcut.

Build cross-feature scenarios: trending/reversing/spiky prices, low depth,
simultaneous serialized mint/activation/growth/claim/transfer, both LP modes,
different membership weights, outages at each external call, short/long downtime,
restart/reorg, independent job failure and terminal/aborted lifecycle transitions.

Prioritize reproducible impact. Improve a misleading harness before relying on
it, retain negative controls and use actual components where needed. Run useful
affected checks, not unchanged broad suites for documentation. Match any reused
Solidity/static/compiler result to exact source/dependency/settings pins; do not
call inventory/source checks execution or local models production acceptance.

## Completion

Implement justified in-scope corrections. Record findings, severity, evidence,
changes, retained tradeoffs, actual fresh/reused checks and residual risks.
Update the sole JSON task ledger/generated Todo, features/findings, operator,
roadmap/release/context and both READMEs where applicable. Preserve immutable
historical reports and unrelated dirty files. Check staged Python closure before
publication and exact local/remote main identity afterward. Final report must
distinguish scope reviewed from unchanged evidence reused, untested hypotheses,
external release blockers and independent audit. Never promise all bugs removed.
