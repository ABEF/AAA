# Main/residual lifecycle, market and recovery matrix

Fresh source6/portfolio2,6November2026. Production NOT APPROVED.
**S** = fresh source/path review; **R** = earlier source-scoped evidence, not a
rerun; **N** = new selected verification recorded in VERIFICATION.md; **Q** = actual
provider/token/market/gas/operating qualification remains open.

## What is owned and tracked

NFT shares cover aggregate attributed main+residual principal, idle and designated
compound. They do not represent an isolated60/40 portfolio or a normal right to
withdraw principal. Both Uniswap NFTs stay Vault-owned. Funded holder rewards,
buyback reserves and original-currency royalties remain separate.

The typed child records secondaryId(main), primaryOfSecondary(aux) and a global
activeSecondaryCount. That count means **registered residuals**, including filled
or out-of-range positions; it is not the number currently earning fees. Only one
residual may belong to a main, and the global bound is4 alongside at most4 logical
buckets. Moving through another pool alias of the same bucket does not consume a
new bucket slot. New physical IDs replace old IDs; old residuals never accumulate.
At the global count4, a whole replacement closes its old residual first(4→3)
before registering its replacement(3→4). This does not require a fifth slot.

## Creation and transition map

| Case | Actual behavior / important condition | Evidence |
| --- | --- | --- |
| First activation, desired OFF or ON | Initial mint is one main. ON is permission, not a promise to create a second position. | S/R |
| Growth in one/two positions | Increase main only; retain residual ID/ticks/L and rebalance clock. Repricing can still change both legs' token amounts. | S/R |
| Standalone compound | Reinvest idle/designated compound into existing main. No independently minted residual. Shares remain unchanged. | S/R |
| Enable residual mode | Governance setMode(pool,true,reviewHash) changes desired geometry, without moving funds. Eligible later replacement may create a useful residual. | S/R |
| Ordinary rebalance, destination OFF | Harvest and close both existing legs, balance attributed inventory, mint one main atomically. | S/R |
| Ordinary rebalance, destination ON | Same full close; mint active main plus at most one useful residual. Natural adequate main may need no swap;40% is a ceiling, not a mandatory target. | S/R |
| Move to another same-pair pool | Source both close. Destination's mode/geometry applies; ON can create a residual. Governance-only live execution retains financial guards, without ordinary keeper cooldown/sample/jitter. | S/N |
| Resume a parked bucket | Idle plus released designated compound redeploy under destination policy. ON may recreate two positions. Governance-only live execution retains financial guards, without ordinary keeper cooldown/sample/jitter. | S/N |
| Mode ON but residual absent | Valid applied state when no useful excess/representable liquidity exists. Tiny excess remains attributed idle under ordinary floors. | S/R |
| Disable mode with residual live | Desired OFF and pending geometry coexist with the old residual. Both remain valued/harvested until actual close/merge. | S/R |
| OFF→ON→OFF / ON→OFF→ON before execution | Monotonic geometry/control revisions prevent restoring old observations/reviews merely by restoring a bool. | S/R |
| Change width/allocation/residual gap | Setter does not change existing ticks. Pending configuration applies on a later eligible replacement; infeasible geometry can reject it. | S/R |
| Close only residual | Paused governance closeResidual harvests both then burns only aux. Principal returns to same-bucket idle; main/shares/clock/mode remain. | S/R |
| Close residual while desired ON | It stays absent until a later eligible whole replacement. To remain single, disable mode separately. Same-value residual-side review can request reapplication when appropriate. | S/R |
| Ordinary two→one merge | Disable mode, then eligible Vault.rebalance from a keeper-granted wallet. Old legs close, inventory is balanced and one active main opens. | S/R |
| Emergency consolidation | Paused governance exact manifest closes the portfolio and creates one explicit main. Does not silently disable hybrid mode or guarantee50/50USD. | S/R |
| Park both | Raw closure leaves bucket-attributed idle and no physical legs. Unpause alone does not redeploy. | S/R |
| Terminal holder return | Both legs close, designated compound follows shares, actual ETH/ZZZ is allocated/distributed to current holders. No reopening. Rewards/royalties/transfers survive. | S/R/Q |
| Canonical pre-exit replacement | Every registered residual must already be closed; exact backing/runtime/lifecycle admission remains. No integrated cross-chain move. | S/R/Q |
| Failed move/replacement/second mint/burn | Entire transaction reverts, including source burns, new associations, reservations and monetary effects. Earlier separately mined setters remain. | S/R/N |

Default replacement targets require main>=60% and complementary residual<=40%
at captured post-cost valuation. They are not continuously enforced; valid later
market moves or main-only contributions need not preserve the original ratio.
A single main uses its current range-required asset ratio, not necessarily50/50.

## Market classes and geometry

| Price/inventory class | Expected behavior / adversarial boundary | Evidence |
| --- | --- | --- |
| Flat or modestly oscillating price | No recenter merely to perfect the centre. Existing policy/cooldown/trigger rules decide ordinary work. | S/R |
| Persistent rise or fall toward trigger | Main geometry determines the85% centre-to-boundary condition; independent reference corroborates same side. Residual status does not replace confirmation. | S/R/Q |
| Residual unfilled/inactive, main active | Keep excess asset in that range; may earn no residual fees. Do not omit its value. | S/R |
| Price inside residual | It becomes mixed; both main and residual may earn fees. Same IDs/L remain. | S/R |
| Price crosses entire residual | It may become one-sided in the opposite asset. No automatic extra leg or independent close occurs. | S/R |
| Reversal through residual again | Composition may reverse again. Both remain accounted until whole replacement or explicit residual-only close. | S/R |
| Price leaves main | Contained residual is also outside on the same asset side. Hard cooldown can intentionally delay maintenance. | S/R/Q |
| Main inactive but residual active | Unreachable normal geometry if residual containment holds. Contradictory observed bounds must fail fresh reader admission. | S/N |
| Both outside on opposite sides | Unreachable for the legitimate nested ranges at one pool price; do not simulate it as an ordinary valid state. | S |
| Local pump/dump, reference remains inside/opposite | Ordinary market trigger does not gain independent corroboration. Harvest/claims retain separate rules; no automatic emergency fallback. | S/R/Q |
| Cross back during samples/jitter | Reset sampled evidence/jitter according to source rules; a timer is not uninterrupted market-history proof. | S/R/Q |
| Exact tick boundary/downward crossing | Use actual stored tick for fee activity. Identical sqrt values alone need not imply identical activity at a boundary. Physical principal still follows exact amount math. | S/R/N |
| Narrow side/excessive spacing gap/minimum liquidity | Configuration may be admitted yet unplaceable. Replacement rejects atomically; disable optional mode or explicitly review viable geometry/recovery. | S/R/N |
| Tiny residual or zero representable L | Deliberately omit it; retained amounts stay attributed idle. Positive but infeasible geometry instead rejects. This is not a missing NFT or a forced40% allocation. | S/R |
| Price/feed outage | Physical holdings and funded raw claims can remain readable independently of USD valuation. Missing data is unavailable, not zero. | S/R/N/Q |

For a human-price main50→150 around100, default half-side residual is approximately
75→100 or100→125 before the required spacing gap/rounding. Excess ETH is a bid
below human spot: moving down through it buys ZZZ. Excess ZZZ above human spot
sells into ETH as price rises. Moving away leaves that side inactive. This changes
inventory/execution exposure; it is not proof of improved returns, no IL or no MEV.

## Contribution, money and failure interactions

| Interaction | Required invariant / consequence | Evidence |
| --- | --- | --- |
| Activate/grow before or after replacement | Resolve the current logical bucket/main, checkpoint incumbents and buy shares from aggregate repriced NAV. Stale caller reviews can reject. | S/R/N |
| Add ETH/ZZZ with live or pending-disabled residual | Only entrant funds meet entrant swap/marginal LP floors; no old idle/compound/residual subsidy. Residual L stays fixed, though its composition may change. | S/R/N |
| Hourly or internal harvest | Collect both actual IDs; allocate actual funded ETH/ZZZ receipts80/10/5/5 once. Claiming is not compounding or buyback. | S/R/N |
| Claim/transfer among maintenance calls | Current owner receives existing funded rights; no duplicated membership or reduction of other holders' liabilities. | S/R/N |
| Residual-only close | Separate harvested fees from raw principal. Do not release compound implicitly or pay governance. Large idle is a legitimate recovery state. | S/R |
| New contribution after large idle close | Existing ordinary idle/deployed-LP floors may block it. Do not let the newcomer repair incumbent deployment economics. | S/R |
| Swap/mint/refund callback | Captured owner/control/valuation/physical checks must hold after external calls. Failure rolls back complete operation. | S/R/Q |
| Wrong but self-consistent reported principal | Fresh6 reader must recompute both legs from captured sqrt/ticks/actual L, not merely compare two reported totals. | N |
| Wrong nonzero physical fingerprint | Derive stable identity and L-sensitive manifest exactly; reject mismatched source data without price feeds. | N |
| Donation/unregistered NFT | It cannot become a tracked leg merely because Vault owns it or token IDs are adjacent. Raw unclassified balances cannot pay entrant floors. | S/R/Q |
| Token/upstream compromise | Runtime pins do not freeze proxy implementations or arbitrary malicious token behavior. Qualify actual dependency semantics; no universal monetary recovery is proved. | S/Q |

## Recoverability and operator sequencing

| Situation | Existing response | Dependency / limit |
| --- | --- | --- |
| Residual no longer wanted; main should remain | Disable desired mode if long-term single is intended; pause; exact closeResidual request; inspect actual idle and main; separately unpause. | Exact snapshot/nonce/custody/positive caller floors and working core/token remain. |
| Want idle reinvested into one main normally | Mode OFF; eligible Vault.rebalance or eligible main-only compound. Governance same-pair move/resume are separate intended custody operations. | Ordinary rebalance has its configured cooldown/samples(service jitter separately); governance move/resume do not. Financial/deployment guards remain. |
| Need urgent single consolidation | Mode OFF before reviewing manifest; paused governance emergency with explicitly selected retained financial guards. | Structural custody/identity/settlement checks remain. Bypassing financial guards can lose nearly all principal. |
| USD/route failure but core/token usable | Raw residual close or both-leg parking can avoid ordinary USD/swap dependencies. Funded raw claims remain separate. | Neither fixes a broken asset or malicious venue. |
| Parked funds awaiting deployment | Guarded resume to reviewed same-pair destination, or separately reviewed current-pool emergency path. | Unpause is not resume; desired destination mode can recreate a residual. |
| Ordinary placement economically impossible | Preserve current backing; review configuration/venue/geometry, wait, park or use deliberate governance recovery. | No unsafe auto-fallback or promise that every target can be funded. |
| Keeper/RPC/host failure | Preserve journals; recover pending receipt/nonces first; re-read confirmed actual legs/controls before new work. | Source/profile/config changes require reviewed rollout, not relabelling old records. |
| Permanent shutdown required | Governance terminal closure and bounded holder distribution, with failed-receiver recovery. | Broken tokens/core/chain and actual batch-gas/recipient behavior remain qualification limits. |

No arbitrary sweep, custody recipient, bridge, continuous target rebalance or new
principal-withdrawal right is introduced by this audit. Detailed existing input
tables remain in the single [Operator manual](../../docs/OPERATOR_MANUAL.md#portfolio-management-controls).

The fee/principal statements above assume the conventional exact-transfer fixed
token and reviewed periphery model. If a compromised token/upstream callback
creates new fees between pre-close collection and either burn, current close
receipts do not separately reclassify those late fees: they can join principal.
An ordinary trader cannot interleave independent transactions inside the atomic
close. Actual ZZZ callback/proxy/admin and periphery qualification remains open;
this boundary is not fixed by documentation or covered by an invented malicious-
dependency success. See REVIEW.md and the owning dependency Todo.
