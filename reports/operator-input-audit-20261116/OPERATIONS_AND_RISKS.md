# Operator input validity, guard coordination and economic review

Baseline: `72e519797659158eb48cfe5da582fb8c88b90bfa`. This is source review,
not new market execution, an independent audit or release approval. Source
locations below identify the implementation reviewed; exact hashes are retained
in the accompanying inventory/baseline. No existing chain was contacted.

## What changes while an operation is prepared

External swaps change current tick, sqrt price, inventory, fee growth and usable
depth. They do not change an existing position's lower/upper ticks. Another
transaction cannot interleave the atomic close/swap/mint sequence. Transactions
before inclusion and nested callbacks are separate threats. Pausing PoPL does
not pause Uniswap trading.

| Input/state | Authoritative source | What invalidates it; appropriate response |
| --- | --- | --- |
| NFT ID | `NFT.tokenAtOrdinal(ordinal)`; confirm `ownerOf(id)` | A transfer changes the authorized claimant/current payout owner, not the ID. Never substitute the ordinal for the full ID. |
| Bucket | `Vault.nftBucket(id)`, `poolBucket(poolId)`, `group(bucket)` | Confirm the current mapping/status; a movement/replacement changes the underlying position/pool. |
| Main/residual IDs and bounds | `Vault.group`, Manager's portfolio/ticks and actual position-manager custody | Swaps change current price, not bounds. Replacement changes IDs/geometry; contribution increases main L. Reread physical snapshot for an L-sensitive request. |
| Entry policy | `ProtocolPolicy.entryFingerprint()` | Entry revisions invalidate previous reviews, even if values are later restored. Never replace the captured fingerprint inside an existing wallet review. |
| Mint review | `Vault.mintPolicyFingerprint()` and mint2/SeaDrop configuration | Sale end/revision, payee/price/VRF or integration controls can change. Core sale-policy hash alone is insufficient. |
| Stable geometry hash | `Manager.portfolioFingerprint(mainId)` | Excludes L so an ordinary contribution does not restart stable geometry observations. Replacement/geometry changes invalidate it. It is not the emergency physical snapshot. |
| Physical custody hash | Operation-specific `Migration.emergencyCustodyHash(bucket)` / `consolidationCustodyHash(bucket)` and Manager's `executionPortfolioFingerprint(mainId)` | Physical IDs/ticks/L change physical hashes; consolidation additionally binds its nonce/epoch/control context. Use the selected operation's getter. These hashes are not price quotes or commitments to every policy. |
| Review hash | Source-bound review producer with exact notes/evidence digest | It identifies reviewed evidence. A nonzero arbitrary value is not a simulation or authorization. SHA256 artifact identity and Keccak on-chain fingerprints are different domains. |
| Swap amount/venue/output floor | Explicit reviewed choice for manual swap; ordinary bounded router sizing | Before inclusion, external depth, price or fee changes may make it fail. Reprepare or use a distinct reviewed operation; do not silently relax the floor. |
| Liquidity minimum | Actual simulation of the selected operation | It is raw uint128 L. For same-main consolidation it is added L; for replacement/resume it is new L. Never sum L from different ranges as value. |
| Deadline | Original absolute Unix-seconds choice within contract bounds | RPC/wallet/Safe delay can expire it. Reprepare a new review; never mutate a submitted intent or extend the original review during revalidation. |
| Distribution beneficiary | Current `NFT.ownerOf(id)` at payout | Not a frozen beneficiary list. Read paid truth/events after inclusion; simulated success count is not a successful prefix. |
| Allocation cursor | On-chain exit/canonical cursor | Permissionless or previously authorized progress may advance it. Inspect actual progress rather than replaying an assumed next row. |

## State transitions and safe next actions

These are reviewed function families, not a claim that their entire state space
was freshly executed. The complete ABI inventory separates direct management,
keeper, holder, permissionless, module/callback, constructors and views.

| Action | Caller/input commitment | Price and concurrent activity | Success, stop and recovery |
| --- | --- | --- | --- |
| `Access.bind`, `bindProtocolPolicy`, `seal` | Actual bootstrap; exact IDs, parent bindings, runtime/build and fixed token graph | Trading is irrelevant; a wrong/unconfigured dependency can make sealing irreversible. `seal` does not validate all release configuration. | Verify the complete graph and current bootstrap before execution. No unseal or automatic repair of a bad fixed graph. |
| `proposeGovernance`, `acceptGovernance` | Current and nominated wallets respectively | Pending proposal does not itself transfer authority. Review pending keeper/manual work independently. | Verify accepted governance; zero proposal cancels. Governance is not implicitly a keeper. |
| `setKeeper`, `setGuardian` | Bootstrap/configuring governance; address and boolean | Revocation can invalidate pending ordinary work. | New key must be verified; revoke compromised keeper and reconcile saved intent. No holder-claim authority is granted. |
| `setPaused`, `NFT.setMintPaused` | Governance; guardian can only set global pause true | External trading continues. Global pause, mint pause and pool flags are separate. | Unpause does not restore a pool flag, resume Parked LP, cancel preparation or reopen terminal exit. |
| Asset/source/route setters | Current configuration authority, exact identities/code/control/review data | Source age, decimals, prices, upstreams and venue depth are not frozen by an address/code hash. | Validate live controls and independent sources; absence is unavailable, not a spot/peg fallback. |
| `PoolRegistry.configureNative`/disable and contribution cutover | Exact native ETH/fixed-ZZZ PoolKey, human orientation and current pool controls | External trades change prices; admitted historical buckets retain backing. | One contribution pool only; disable without external price calls, re-enable through complete validation. |
| Portfolio/range/policy setters | Governance; reviewed values/revisions; some typed Strategy module calls | A mode/width update records desired state and can invalidate observations/reviews. It does not move LP by itself. | Apply at the source-defined eligible operation. Keep intentional mode state and physical residual existence separate. |
| `Vault.collectFees(bucket,deadline)` | Permissionless, sealed/live/canonical checks; raw bucket and deadline | Neither USD nor ordinary range eligibility is needed. Public harvest can change fee books before a later operation. | Both legs' actual receipts allocate once. No compound, burn or principal payment is implied. Global pause still applies. |
| `Vault.rebalance(bucket,minL,deadline)` | Authorized keeper; current trigger, cooldown, confirmation, prices, routes and budgets | Check destination/reference same-side 85% condition, sampled 600s/gap300, hard12h, service240s checks and durable60–300s jitter. A late state change may safely revert. | Atomic full one/two-leg replacement. Recover the same submitted hash; no forced fallback or guessed success. |
| `Compounder.compound(bucket,minL,deadline)` | Keeper; separate compound readiness, actual thresholds/budgets | Service additionally waits below threshold/in range/no pending geometry; an alternate keeper can ignore this extra service rule. | Harvest/reinvest existing main, preserve residual/shares/centre/rebalance clock. Service restriction is not an on-chain guarantee. |
| `Migration.moveFunds` / `resume` | Governance; destination/minL/deadline, inclusion-time attributed state | ABI has no off-chain custody-hash argument. Guarded sizing occurs at execution. Destination mode ON can create a residual. | Move closes both; resume starts Parked/unpaused. Normal financial guards remain; these are not keeper cooldown/observation paths. |
| `park` | Paused governance, exact ParkingRequest/custody state and raw close minima | Raw closure needs no USD; price movement changes returned mix, not fixed geometry. A contribution before pause changes physical L and can stale a request. | Both legs become attributed idle. Remains paused; guarded resume is separate and unpaused. |
| `closeResidual` | Paused governance, exact ParkingRequest/minima | Main remains; fees may be harvested from both legs. | Residual principal becomes attributed idle. Desired mode is unchanged. No implicit reinvestment. |
| `consolidateResidual(request,false)` | Paused governance; current main bounds, exact custody, checks14, no explicit swap | Main must remain active; current price can change the needed mix. Old bounds do not move with traders. | Close residual/reinvest idle into SAME main; atomically mode OFF, shares/centre/rebalance clock unchanged. Reprepare or full replace if geometry is unsuitable. |
| `consolidateResidual(request,true)` | Paused governance; explicit swap/no-swap and retained mask | A bypass can accept poor execution or inactive geometry. It cannot invent missing inventory or bypass hard identity/custody rules. | Same main retained and mode OFF. Review residual idle/deployed values, then deliberate unpause. |
| `emergencyRebalance(request)` | Paused governance; exact Active/Parked profile, explicit new ticks, swap/floors/mask | Full replacement; masks1/16 need their applicable Active evidence. Financial bypass is an emergency trust decision. | Both legs/attributed state redeploy into one main; desired mode does NOT automatically turn OFF. Remains paused. |
| `Buyback.execute` / LP conversion | Keeper; actual reserve or per-NFT balance, route, amounts, deadline and limits | Swap source/reference coupling, directional fees, thin reverse depth and price changes can block. | Only actual ZZZ is burned; LP conversion credits same NFT. Neither operation creates income a second time or sweeps principal. |
| Collective begin/close/allocate/distribute | Governance; terminal confirmation, raw floors, count/explicit IDs | Transfers before distribution change current owner; rejects/reentrant recipients must remain isolated. | Terminal closure; allocate exact units and verify individual paid truth. Future royalties/old claims survive; unpause never reopens LP. |
| Royalty admission/capacity/end/unallocated recovery | NFT governance wrappers; ledger recovery checks current authority/window/review | Newly admitted balance is unallocated, not automatically retroactive earnings. Currency outages defer eligible entry; opening cutoff must survive late calls. | Original currencies, exact units and previous cohort rights retained. No automatic swap. Capacity review is not a gas proof. |
| SeaDrop helper configure/NFT forwarding | Configuring governance, immutable helper/SeaDrop, exact staged config/root/payers/fee recipient/price | Upstream drop drift or phase change can invalidate mint. A new root must have the intended leaf terms and supply reservations. | Typed setters only; team/allowlist/public counts never reset by transfers or reconfiguration. Real onboarding remains unqualified. |
| VRF configure/settings/rotate, trait finalization | Configuring governance or authenticated coordinator; public ordered finalization | Pending requests cannot be retargeted/rerolled; original coordinator may drain after runtime change. | Rotation waits for finalized old draws. Permanent provider failure remains an external recovery limitation, not permission to choose traits. |
| Metadata changes/notifications | Source-specific governance/module/public interfaces | Valuation outages must not falsify ownership, royalties or lifecycle. | LP Exited differs from Dormant. Public refresh is notification, not price synchronization or a new draw. |
| Canonical prepare/freeze/progress/fund/commit/abort | Bootstrap/governance decisions; exact peer/root/row/backing; specified progress is permissionless | Frozen ownership prevents competing transfer/claim accounting. Late funds are outside original cutoff. Caller races can advance cursor but not choose another beneficiary. | Pre-exit only, no live residual at capture; exact backing and atomic retirement/activation. Abort requires full restoration; no post-exit or cross-chain reopening. |

## Units and worked non-executable examples

| Domain | Correct interpretation | Invalid substitution |
| --- | --- | --- |
| ETH | `0.01 ETH = 10000000000000000 wei` | ETH decimal entered directly into uint argument |
| USD18 | `$100 = 100000000000000000000`; `$1m = 10^24` | Token units or current position L |
| Token raw units | In a declared six-decimal test currency, `1.25 = 1250000` | Assuming that illustration is actual ZZZ decimals |
| Contribution limit | `300 bps = 3%`, at least97% captured marginal deployed LP under that floor | Permission to ignore stricter venue/idle/user/price guards |
| Uniswap fee | `10020 pips = 1.002%` LP fee; actual protocol directional fee is separate | `10020 bps`, a universal0.3%, or known fee counted twice |
| Range/trigger | Declared human centre100, actual bounds50/150: 85% distance thresholds57.5/142.5 before tick rounding | An85% absolute move, or pool raw ratio without orientation/decimal correction |
| Position cap | `maxPositionUSD` limits cumulative admitted inputUSD per NFT | Current market NAV, total bucket or collection cap |
| Exact LP split | Declared fresh receipt20 raw units:16individual,2collective,1compound,1buyback |20 wei from every asset summed as money |
| Sub20 split dust | Carried until another receipt or authenticated incumbent settlement | A public sweepable balance; `flushDust` is Vault/Membership restricted |

For a manual same-main review, first prove pause and read `group`, physical
portfolio and `ticks(mainId)` at one canonical anchor. The selected lower/upper
are those stored bounds, not the moving current tick. Choose added-L/output/raw
floors from that exact isolated simulation. If price then makes the main
unsuitable, guarded rejection is protective: refresh the review or use a
separately reviewed full replacement. Do not copy a historical hash, shorten
the request to omit its controls, or call a second reinvest after a successful
consolidation; reinvestment is already part of that atomic call.

Manual preparation now proves both snapshots using the SAME `transaction.gas`.
Each anchor must still fit full25% estimated headroom. A lower later estimate
does not lower the frozen gas; a higher requirement rejects. A cap-sized call
does not prove the returned lower-gas transaction succeeds. See the fix evidence.

## Guard coordination and failure classification

| Guard | Enforced where | Important interaction / recovery |
| --- | --- | --- |
| Roles and immutable module/callback parents | Contracts, with path-specific post-call checks | Cannot be bypassed by emergency financial mask or paying gas. Rotate/revoke keys through actual authority. |
| Sealed/operating/preparation/terminal state | Contracts | Pause, canonical freeze and terminal exit are not interchangeable. Complete/cancel/abort the corresponding state, not a generic unpause. |
| Physical pool/portfolio identity and classified backing | Contracts plus pinned readers | Hash invalidation after a real custody change is safe. Reprepare; never relabel old state. |
| Trigger/cooldown/sampled confirmation | Ordinary contracts; scheduling/jitter additionally in service | Geometry exception and emergency masks have distinct semantics. Recorded observations are sampled, not uninterrupted history; writes still require actual keeper permission. |
| In-range/below-threshold compound wait | Extra keeper service policy | A compromised authorized keeper can ignore it before contract eligibility blocks. On-chain strengthening needs a separately reviewed behavior decision. |
| Source validity/agreement/control and own-swap proof | Priced contracts | Actual independent sources remain a release prerequisite. Same actual principal core as reference is excluded; no keeper price fallback. |
| Swap floors, directional known fees/additional1%, aggregate loss, caller minima, idle/main floor | Contract at distinct execution boundaries | These are different protections, not one interchangeable slippage value. A smaller limit may deliberately bind; inspect stage rather than auto-raising it. |
| Gas/headroom/funding/complete fee policy | Off-chain review, wallet and chain limits | Configurable budget is not provider qualification. Reprepare fresh caps/funding; no automatic increase, resend or journal edit. |
| Batch/array/currency bounds and recipient isolation | Contracts and tools | A count maximum is not worst-case gas acceptance. Replan unpaid IDs using receipts and ledger truth. |

Classify errors as not needed, not due, deliberately stopped, unconfigured,
known protective blocker, unavailable dependency, opaque unknown, submitted
unresolved, confirmed partial success, or confirmed revert. Do not describe an
opaque simulation revert as a known slippage, token or price error.

## Adversarial and long-term obligations

These are source-assessed threats and retained qualifications, not newly executed
market simulations. The inventory applies the relevant state/freshness families
to every ABI row; applicability is not proof of all possible interleavings.

* **Price manipulation and ordering:** local-only displacement cannot satisfy
  independent corroboration by itself; correlated reference manipulation still
  can. Sample gaps hide intermediate trading. Jitter and source code publication
  do not prevent sandwich/backrun/collusion. A same-block callback must not borrow
  an execution capture or settle an unproved swap transition.
* **Execution depth:** quote after our withdrawal, with external L removal/JIT and
  directional fees. A large TVL number or a small successful quote does not prove
  a complete contribution/maintenance route. Real independent markets are open.
* **Repeated losses:** a3% cap is per operation. Pure arithmetic `0.97^10` is
  about73.74% retained after ten worst-permitted reductions; this is a warning
  bound, not proof that an attacker can realize it or an executable market path.
  The user declined a cumulative cap. Monitor actual realized cost and turnover.
* **Attacker profit:** distinguish holder mark-to-market change from extraction.
  A net-profit conclusion requires actual depth/order/fees/gas/borrow/unwind
  evidence and a passive/no-attack counterfactual. This review does not invent
  current-market profitability numbers or assert a profitable exploit.
* **Equal collective incentive:** distributing10% equally per active NFT makes
  multiple adequately funded activations economically different from one larger
  NFT. That is the approved economics, not automatically a bug. Rarity changes
  royalties only; cosmetic tiers cannot change these weights.
* **Cohorts and rounding:** transfer/claim slicing/activation/funding/harvest order
  must preserve checkpoint and rotating exact-unit rights. Pre-admission or zero
  cohort royalties remain an explicit reviewed allocation decision; do not
  conflate them with already earned balances or promise universal payout.
* **Tokens/dependencies:** taxed, rebasing, blacklisting, unavailable or upgraded
  dependencies can prevent movement. Codehash pins do not freeze proxy upstreams.
  Original-currency royalties deliberately isolate optional outages but cannot
  guarantee transferability of every imaginable asset.
* **Recipients and keys:** contract recipients can reject payment; loss of the
  sole governance key has no inferred multisig override. Keep isolated payout
  retries and owner fallback separate from normal automatic payout expectations.
* **Operations:** one nonce lane, pending-first recovery, source-bound journals,
  off-host backups, recent canonical state, disk failure and fee budgets remain
  operating requirements. A restored old backup cannot be silently adopted.
* **No source rollout:** current tests/preparers do not qualify actual Safe
  envelopes, maximum-state gas, production RPCs, OpenSea, VRF or live services.
  Existing deployment/runtime/consumer profiles remain unchanged.

## Primary research and interpretation

The [Solidity0.8.26 ABI](https://docs.soliditylang.org/en/v0.8.26/abi-spec.html)
supports the exact tuple/order/signed-unit review; the
[security guidance](https://docs.soliditylang.org/en/v0.8.26/security-considerations.html)
supports checking external-call reentrancy and bounded progress. Uniswap's
[PoolManager description](https://developers.uniswap.org/docs/protocols/v4/concepts/poolmanager)
distinguishes pool state and deferred settlement. Actual behavior is traced
against this repository's pinned dependency code, not inferred from a new
documentation version. No documentation source establishes deployment safety.
