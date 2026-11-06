# Operator lifecycle and recovery coverage

This matrix supplements the single [operator manual](../../docs/OPERATOR_MANUAL.md#same-main-residual-consolidation).
It records source behavior and focused evidence; it does not qualify deployed
services, real funds or all market inputs. Main/residual are two positions in
one native ETH/fixed-ZZZ pool, not separately pausable pools.

| Intent/state | Operator action | Result / retained boundary | Recovery/reverse |
| --- | --- | --- | --- |
| One main, enable optional strategy | Governance `PortfolioPolicy.setMode(pool,true,reviewHash)` | Desired ON; no immediate LP creation or promised40%. Later whole adjustment may create one useful residual. | Set OFF again; monotonic controls invalidate stale reviews. |
| Need optional geometry applied ordinarily | Permitted keeper `Vault.rebalance(bucket,minL,deadline)` when due | Close/redeploy old portfolio under current policy, initial12h minimum and applicable on-chain readiness/execution rules. Service scheduling is separate. | Failure preserves old portfolio; fix cause/review fresh. |
| Need governed whole deployment without keeper scheduling | Pause/park, inspect, explicitly unpause, `Migration.resume(bucket,pool,minL,deadline)` | Current or reviewed same-pair destination policy applies, ON may create useful residual. Financial/deployment guards remain; this is not automatic keeper fallback. | Park again or deliberate full emergency replacement if ordinary prices/routes fail. |
| Two positions, keep main ID/range and stop residual | Pause; governance **consolidateResidual(request,false)** | Harvest both; close only residual; auto-route attributed idle into same main. Atomically OFF/applied; independent main-width mismatch remains. | Inspect then explicitly unpause; later ON requests a future whole adjustment. |
| Mode already OFF but residual remains/pending | Same consolidation call; no duplicate setMode needed | Clears actual residual and pending residual mode only after positive main L growth. | Revert preserves both old legs and original pending state. |
| Residual mixed or fully converted | Same guarded call with actual current main ticks and custody hash | Actual ETH+ZZZ receipts, not the historical one-sided label, fund reinvestment. | If guarded economics fail, review explicit route/mask or raw close. |
| Old raw close left idle/no residual | Same consolidation with positive attributed idle | Main remains same; no empty auxiliary burn; no FeeController compound reserve release. | Tiny/zero-L work stays attributed; wait/review larger usable idle or full recovery. |
| Same-main reinvest despite failed prices/operation flags | Paused governance consolidateResidual(request,true), exact explicit swap/mask | Mask0 can bypass optional price/value/idle/timing/operation policies. Fixed pair/admitted core, exact balances/custody, positive caller floors and lifecycle remain. | Deliberately inspect fees/value/idle; repair ordinary policy before unpause. |
| Want selected timing/sample protections retained | Forced request with explicit bits1/16 and other desired bits | Each retained predicate must pass. Bit16 authenticates Budget directly and preserves the existing explicit-geometry exception; bit1 separately retains raw cooldown/need. | Missing/expired ordinary evidence blocks unless the documented geometry exception applies. Prepare a consciously reviewed request rather than silently dropping a bit. |
| Main outside range, preserve its ticks | Explicit force can increase it | May remain one-sided/inactive. Same-main increase cannot make unchanged unsuitable geometry active. | Full replacement to reviewed suitable ticks, or park/terminal return. |
| Change main range or recenter | Normal guarded rebalance or paused `Migration.emergencyRebalance(request)` | Full replacement closes both, releases designated compound and mints one emergency main when forced. It is separate from same-main reinvest. | Main/timer identity changes; inspect actual ticks/activity and resume only deliberately. |
| Pending width plus residual stop | Same-main consolidation can stop residual without changing main ticks | Portfolio OFF is applied; Strategy's actual-versus-configured main geometry test still reports pending width. | Later whole replacement applies width; do not falsely clear that request. |
| Temporarily close residual with no reinvestment | Paused `Migration.closeResidual(ParkingRequest)` | Main L/ticks/shares/clock/mode preserved; proceeds become attributed idle. Both-leg fees separately harvested. | New consolidation recovers idle; unpause alone does not deploy it. |
| ModeON → consolidateOFF → enableON → later adjust → consolidateOFF | Existing setter plus new/manual or ordinary calls | No unbounded auxiliary accumulation. Repeated operations consume fresh hash/nonces and preserve shares/reward liabilities. | Each successful manual reinvest changes controls, including alreadyOFF/idle-only, invalidating old samples/jitter. |
| Ordinary compound or idle worker | Existing `Compounder.compound`; keeper idle scheduling explicitly configured | Existing interval/healthy in-range below-threshold/no-pending policy remains. Designated compound may be released here; new consolidation leaves it separate. | Wait or use explicit whole emergency if that separate operation must bypass policies. Never guess a governance-only keeper action. |
| Harvest/claims during management | Harvest inside atomic calls; owner claims retain separate path | Fees collected before closure and after balancing are allocated80/10/5/5 once. Reinvested principal is not income. No claimant registry/share rewrite. | Fault reverts complete management; earned claims/backing are not erased. |
| Contributions/transfer before or after management | User's confirmed operation executes serially on-chain | Current ownership/share/NAV/physical review must still match. A stale unsigned review fails; entrant-only funding and main growth rules remain. | Refresh confirmed state and reuse/resolve known pending transaction hashes; no blind duplicate approval/action. |
| Stop new contributions but preserve custody | Existing pool/deposit stop flags | Does not close LP or stop external Uniswap trading. A disabled operations flag can block guarded maintenance. | Re-enable with validated configuration; an enabled getter is not qualification. |
| Stop both physical positions temporarily | Paused `Migration.park` | Both close into attributed idle; retains shares/rewards, no holder/governance payout. | Resume requires an explicit reviewed call and destination-mode check. |
| Switch pool/fee tier | Governance `Migration.moveFunds` to reviewed same-pair destination | Both source legs close; reservations/aliases/capacity and destination financial guards remain. One contribution destination at a time. | Guarded parking/resume or explicit current-pool emergency; no arbitrary new venue/asset/bridge. |
| Permanent principal shutdown | Paused collective exit, close funded buckets, allocate/distribute bounded batches | Terminal; current NFT holders receive actual principal. Both legs/compound counted, rewards/buyback/royalties remain separate. No reopening. | Failed receiver payments stay backed for authorized retry/owner fallback; broken token/core cannot be universally repaired. |
| Pause then change mind | Governance `Access.setPaused(false)` after review | Re-enables only the global pause gate. No deployment, mode, pool flag, preparation or terminal state is implicitly reversed. | Use the specific operation/flag's documented reverse. |
| Swap/mint/minL/transfer/control callback failure | Any affected operation reverts | No partial residual burn or acknowledged OFF state survives that same failed call. Previously mined pause/setters survive. Gas is spent. | Read exact receipt/revert; repair/re-simulate with a NEW current hash/deadline. |
| RPC/host/website outage or lost local history | Preserve journals, stop conflicting scheduling, recover confirmed receipts and actual state | Contract rights survive; stale/missing data is unavailable, not zero or permission to force. No governance key on keeper host. | Reviewed backup/restore/new-host procedure and matching runtime profile; no old-journal relabel/reset. |
| Wrong/mixed deployment generations | Fresh inventory15 requires cap1 on all five new participants and rawExit1 closure graph | Same accounting6/tuple shape is insufficient. Current seal does not prove every extension/runtime; exact preflight is required. | Correct before seal; no silent upgrade or source-publication adoption. |

## Evidence and exclusions

The new selected actual-v4 methods cover same-main ID/ticks/owner/centre/clock,
positive added L, exact idle and fee/reserve splits, already-closed recovery,
mixed/converted inventory, width pending, explicit forced failures and recovery,
nonce/control/callback rollback, positive retained samples and repeated mode
cycles. Existing targeted controls cover raw close, full emergency, six-day
entry/growth/compound/claims, parking/reentry, terminal payout/royalties and real
fixed-token bootstrap/seal identity. See [verification](VERIFICATION.md).

At global capacity4, source operations can remove their one old registered
residual before any whole replacement creates a new one; consolidation creates
none. Never add raw L across ranges for value. A residual is contained in main;
some two-leg market combinations are therefore unreachable in ordinary geometry.
The earlier [lifecycle matrix](../residual-lifecycle-20261106/LIFECYCLE.md) retains
its original source scope and geometry reasoning; its former missing same-main
management path is addressed here.

No new partial LP-withdrawal right, arbitrary recipient, universal dust sweep,
continuous60/40 target, passive-order algorithm or cross-chain transport is added.
Forced hybrid placement without normal financial qualification is not invented:
use the existing governed park/resume deployment when guards pass, or deliberate
single-main full emergency recovery when they do not. Optional mode need not
produce a residual when no useful excess exists. These are intentional distinct
operations, not a guarantee that every requested LP shape is feasible.
