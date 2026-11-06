# Changing-input and execution matrix

Read with [scope](PROMPT.md), [blockers/recovery](BLOCKERS.md) and
[verification](VERIFICATION.md). This is a finite source/test audit, not a claim
to have executed every possible state. Units and different capture points matter.

## Four distinct operations

| Path | Inputs / authority | Geometry and principal | Timing / financial boundary |
| --- | --- | --- | --- |
| A: ordinary keeper replacement, including OFF merge | `Vault.rebalance(bucket,minL,deadline)`; actual keeper grant | Close main AND residual; harvest once, release designated compound, use current shares/NAV; new approved reference-based range and live routing; OFF produces one main | Hard cooldown and applicable sampled readiness; current operation/price/value/idle/output/utilization/caller checks; service adds jitter/scheduling |
| B: guarded manual same-main reinvestment | `Migration.consolidateResidual(request,false)`; paused governance | Close residual only, or use already-attributed idle. Same main ID/bounds/centre/rebalance clock/shares. No designated compound release. New active-aware quote filtering; positive added L; atomic OFF acknowledgment | No keeper timing/sample/compound-interval prerequisite. Main active before/after; checks14/current financial policies. Remains paused |
| C: explicit forced same-main | Same facade with `forced=true` | Same mandatory main identity and exact accounting; explicit reviewed swap, not automatic quote. Can increase one-sided inactive main | Retained mask0..31 is explicit governance risk. Optional financial/timing checks do not change fixed assets/custody/positive caller floor/deadline/lifecycle |
| D: explicit full emergency replacement | `Migration.emergencyRebalance(request)`; paused governance | Close both and release designated compound; reviewed NEW fixed ticks/explicit swap; one new main | Optional retained financial/timing checks. Even checks14 is NOT an automatic active-placement guarantee; it is not A's dynamic normal target or an automatic fallback from B |

Manual use of ordinary `Vault.rebalance` still requires an actual keeper grant
and preserves A's on-chain guards. Governance status alone does not bypass them.
Pre-seal bootstrap access does not make unsealed principal operations valid.

## Identity, market, money and governance inputs

| Input / source | What can change after reading? | Execution / recovery rule |
| --- | --- | --- |
| Chain ID, controller, module/helper/parent/runtime bindings | Wrong RPC, fork, incompatible deployment, upstream proxy behavior | Authenticate exact selected profile/runtime graph. Same tuple/version alone is insufficient. New Manager runtime requires fresh pins; no old service/journal relabel |
| Caller and keeper/governance grants | Revocation, governance transfer, pause/preparation/retirement | On-chain authorization/lifecycle checked before and after sensitive calls. Keeper pre-sign rechecks; emergency never becomes a keeper method |
| Bucket ID | Wrong NFT/array index, wrong pool alias, earlier terminal/canonical state | Discover current shared account. Zero/unfunded/wrong status fails; do not substitute a PoPL NFT ID or physical LP NFT ID |
| Main ID | Whole rebalance/move/recovery replaces it | A discovers current state at inclusion. B/C bind current physical identity with exact custody hash. Old burned metadata may return0,0; authenticate current Vault owner/key/L |
| Residual ID / association / global count | Creation, mixed fill, close, whole replacement | Both physical NFTs remain Vault-owned. At most one residual per logical bucket; close/count/association verified. No third leg or raw-L summation |
| Main/residual lower and upper ticks | Fixed per physical ID; replacement creates new ID | Trading does NOT move these bounds. B/C require current main's exact ticks. A derives a new approved range; D explicitly supplies reviewed new ticks |
| Current stored tick / sqrt | Any external swap before inclusion; our own swap/callback inside | Read live state. Use actual stored tick `lower<=tick<upper`, including downward exact lower boundary. External transactions cannot interleave inside one atomic call |
| Main/residual liquidity L | New activation/growth or maintenance, not ordinary swaps | A captures latest principal/shares at execution. Manual custody identity includes actual L. Same-main final L must increase by caller floor; other identities remain unchanged |
| ETH/ZZZ composition | Trading changes each position's token amounts without changing L | Read live per-leg token amounts; retention uses the captured USD vector. Aggregate token amounts/NAV, never sum raw L across ranges. Close actual inventory, not its historic one-sided label |
| Uncollected fees / donations to pool | Trading and core donations while PoPL is paused | Harvest actual receipts into80/10/5/5. A releases classified compound; B/C do not. Reinvestment/claim/telemetry is not new income |
| Raw Vault/Manager/PosM prefunds | Forced ETH or token transfers | Exact before/after balances and classified idle keep donations from subsidizing or being swept by a participant/operation |
| Bucket shares / per-NFT shares | Activation/growth before execution | A uses current supply/NAV; stable sampled geometry deliberately excludes L. B/C reject changed custody/share identity. Confirm pause before manual capture |
| Contribution USD / caps | Another contribution; governance changes future minimum/maximum | Historical contributionUSD is not current NAV. Per-NFT admitted cap, action minimum and actual marginal deployed-LP floor remain; no shared principal subsidy |
| Attributed idle | Placement leftovers, raw close, released designated compound, maintenance | Included in the correct owner's NAV and accounting. B supports positive idle-only recovery; empty work fails. Whole-operation idle ceiling is independent of loss floor |
| Designated compound reserve | Each real fee harvest and successful release | A includes released compound BEFORE final retention proof. B/C leave it separate. No double-counting residual closure proceeds as released compound |
| Holder/collective rewards, royalty liabilities, buyback reserve | Harvests, current-owner claims, transfers | Keep funded liabilities separate from principal. Current owner retains unpaid rights; dormant NFTs do not dilute active collective share; royalty currency outages retain their separate rules |
| Width / orientation / residual mode / half-side / gap / main floor | Reviewed governance updates; pending desired geometry | Existing bounds never reinterpret. A uses current admitted policy; OFF closes both and creates one. B applies residual OFF only after physical success and leaves independent width pending |
| Pool key / fixed currencies / fee / tick spacing / admission | Governed same-pair destination and route changes; actual directional protocol fee may change | Native ETH/fixed ZZZ only. Static hookless reviewed pools; fresh directional fees/quotes. A/B cannot invent a new asset/venue or external recipient |
| Contribution pool / pool occupancy / capacity | Governance cutover, reservations, historic buckets | One contribution destination, bounded historical buckets. A/B preserve bucket identity. Same-pair movement and terminal exit have separate explicit procedures |
| Execution venues / solver iterations / quote gas | Reviewed catalogue changes, disabled/unavailable route, thin remaining depth | B now filters active candidates like A. Quote actual core after recovered inventory is available; bounded search, zero/one actual swap, no unsafe fallback. Empty catalogue disables swaps |
| Dual feed values / rounds / ages / decimals / identities | New rounds, stale/down feeds, configuration or proxy changes | Two reviewed sources with3% agreement and no spot/peg fallback. Actual independent provider/market quality still needs qualification; code hashes do not freeze proxies |
| Independent reference / pool deviation / sequencer | Market divergence, sequencer outage/recovery | Normal physical/reference and freshness controls remain. A new range uses reference and live checks, not a caller's old chart centre. Known raw recovery can omit prices explicitly |
| Known fee / additional execution loss / gross budgets | Actual venue fee, admitted controls, new price vector | Defaults contribution2%, conversion1%, maintenance3%, additional1% after actual directional fees. Different denominators/rounding; do not remove as duplicates |
| Idle ceiling / main allocation / caller minimum L | Governed thresholds, rounding, range change | Separate constraints: retained value is not necessarily deployed LP. A new L is not comparable to old L across changed ranges. B minL is ADDED delta. Caller floors never auto-relax |
| Main centre / lastRebalance / lastCompound | Successful replacement versus same-main reinvestment | A changes rebalance clock/centre; B preserves them and advances compound clock. Contributions never recenter/reset rebalance clock |
| Sample identity / 85% side / cooldown / gap / jitter | Returns, side reversal, faults, new geometry/settings or expiry | Preserve12-hour hard minimum and600/240/300 sampled semantics. Geometry exception is explicit. Recheck before submission and on-chain; monotonic estimate only wakes scheduling |
| NFT owner / approvals / funded claims | Transfer or claim during pause | LP management never redirects holder rewards or principal to operator. Owner/claim permissions remain separate. Transfer approval is not claim authority |

## Every field of the manual request

| Field | B: guarded same-main | C / D: explicit force |
| --- | --- | --- |
| `bucket` | Current nonzero shared bucket | Same authenticated source account; Parked full recovery has its separate allowed state |
| `custodyHash` | Fresh `consolidationCustodyHash` after confirmed pause | C uses consolidation hash; D uses full `emergencyCustodyHash`. Never substitute reviewHash |
| `checks` | Exactly14 | Explicit0..31;1raw trigger/cooldown,2price agreement,4value/quality/idle,8operation flags,16sample. Retaining one may require data/conditions of another |
| `lower` | Exact current main lower bound | C same; D reviewed NEW lower bound, not a moving spot tick |
| `upper` | Exact current main upper bound | C same; D reviewed NEW upper bound. Valid ordering/spacing/range still mandatory |
| `swapPool` | Zero bytes32; current active-aware automatic route selection | Exact admitted venue for positive input, or zero for no swap |
| `zeroForOne` | false | Exact reviewed direction in the venue's actual currency order |
| `amountIn` |0 | Raw fixed-asset units; bounded by available operation principal, not a percentage or operator funds |
| `minimumOut` |0; router enforces current output floor | Positive raw floor with a swap,0 without. Not USD, not old quote without review |
| `minimumLiquidity` | Positive minimum ADDED main L | C added L; D positive NEW-position L. Not a token amount, USD or old-main L |
| `deadline` | Current inclusion time through+600seconds | Same mandatory upper bound even with checks0. Never auto-extended or ignored |
| `reviewHash` | Nonzero reviewed source-bound commitment | Same public review evidence; grants no authority and proves no live simulation |
| Outer `forced` | false | C true; D is its separately named force operation. Never toggled by a failed quote/retry |

Custody hashes deliberately exclude market spot and are not commitments to every
Registry/router/oracle/Budget setting. Prepare a fresh explicit review after any
configuration change even if the hash is unchanged. Current policies are captured
and rechecked during execution. The offline review helper is not a live reader,
simulation engine, floor chooser or signer.

## Keeper submission and recovery fields

| Input / boundary | Current behavior and improvement |
| --- | --- |
| Function/bucket/minL/deadline | Exact known ordinary rebalance/compound calldata; no old ticks or swap quote in keeper transaction. Caller floor/deadline remain unchanged through signing |
| Read-only simulation / gas envelope | First complete simulation and estimate remain; new ONE late complete simulation uses captured gas/gasPrice and requires exact void0x result. No unbounded simulation or estimate loop |
| Service readiness | Recheck after late simulation; compound must still satisfy stricter service in-range/below-threshold/no-pending policy; never infer readiness from gas success |
| Code/route/runtime/lifecycle/stop | Existing authentication and final service/lifecycle gates retained. Wrong/missing evidence defers, never broadens authority |
| Nonce and funding | Recheck actual expected-next/pending/latest nonce and bounded funding before intent. Out-of-band same-key actions require explicit reconciliation |
| Fresh final head / deadline / UTC day / retry | Check after the final potentially slow policy/nonce/funding reads. Reject retreat/invalid date/expired original deadline/new-day cap/retry; no silent deadline extension |
| Fees | Original reviewed gas/price/L1/per-transaction/day ceilings remain. No pending/spend/sign on a failed late review. Actual canonical receipt fees are charged on inclusion day |
| Pending intent | Save durably BEFORE signer; once pending or ambiguous, recover existing hash/nonce only. New review dependencies cannot bypass recovery |
| Receipt / reorg / process crash | Confirm transaction identity/depth/canonical header/fees before clocks/spend. Reverts consume actual gas but do not credit harvest/compound/rebalance success |
| Local I/O and post-check market change | RPC/filesystem/signing/network latency cannot be made atomic with a public chain. Host/recovery qualification remains; inclusion-time contract checks are the final backstop |

No new on-chain authority, economic split, journal schema, public wallet signer,
deployment or running service change accompanies these source improvements.
