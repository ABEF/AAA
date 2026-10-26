# Adversarial market and input review

Internal review of the current accounting3/governance2/fee1 candidate, starting
from `25ac8d48e535fc0ad0e93b450f6fdd4fcd564a7b`. Production remains **NOT APPROVED**.
This scope adds to earlier reward/keeper reviews; it is not a whole-project audit
guarantee or live dependency qualification. [Verification](VERIFICATION.md).

## Findings and corrections

| Finding | Consequence | Correction |
| --- | --- | --- |
| Backend accepted individually bounded but contradictory v4 sqrt prices and ticks | A malformed/compromised RPC response or hand-authored inventory could become a misleading contribution/route review, range warning or release observation. This is not evidence of an on-chain loss-guard bypass. | Shared exact integer [TickMath/slot0 validator](../../zzz_ops/tick_math.py), used by contribution context, typed routes, production observer and both offline inventory state gates. |
| Slot0 fee fields lacked shared canonical/domain validation | Malformed directional protocol fees, invalid stored LP fees or a reviewed-static-fee mismatch could reach a review or gate. | Reject noncanonical ABI integers, each packed protocol-fee direction above1000, stored LP fees above1000000 and static-fee mismatches where the reviewed key is available. No default, float approximation or extra RPC call. |
| Existing composed fixture admitted the token as a pool currency but never configured its fixed ZZZ source identity | New ZZZ growth cases failed at admission; the older exact late-source callback method could not reach its intended path on this fixture. | Explicit test-only `configureZZZ` before sealing. The affected shared-fixture selection now executes all15composed cases, including the exact expected callback/revert assertion. No production guard was weakened. |

The validator preserves the actual stored tick. Uniswap's exact downward crossing
can retain `sqrtAtTick(tick+1)` with stored `tick`; this is a legitimate state,
not corruption. Replacing it with a reconstructed floor tick would give incorrect
range membership at an aligned boundary. Consistency is not RPC authentication:
a malicious provider can fabricate internally consistent data. Runtime, chain,
block-hash, independent observations and actual execution checks remain required.

## Additional adversarial market cases

- **LP entirely above or below its old range:** actual swaps move the installed
  local v4 market beyond the position; explicit fresh fixture feeds match the
  new market. New ETH activation and minimum-value ZZZ growth use the same old
  physical LP, preserve incumbent allocations/shares and exclude old fee receipts
  from the newcomer. Subsequent eligible rebalance centers a new range without
  changing NFT shares; funded claims and physical backing reconcile.
- **Funded pool donations before activation:** actual permissionless
  `PoolManager.donate` changes fee growth. Activation harvests incumbent income
  first; the newcomer receives none of that past donated income. Donation money
  remains physically backed and follows the fixed80/10/5/5 allocation. This is
  distinct from raw unsolicited Vault ETH/token prefunds, which remain
  unattributed and cannot buy shares or masquerade as earned receipts.
- **Hostile observations:** malformed signed tick words, impossible sqrt/tick
  pairs, uninitialized/extreme prices, both protocol-fee directions, stored LP
  fee flags and static-fee mismatch reject before approval/trace. Valid exact
  boundaries remain readable. Observer incompleteness and offline gate errors
  retain their existing schemas; no unavailable value becomes guessed zero.

Local governance/admission, token, provider independence, VRF and Permit2 are
explicit fixture substitutes. ETH is priced at a synthetic$1 for these composed
tests; `100 ether` is a fixture$100 budget, not a production quote or gas estimate.
No installed Anvil or live market was modified.

## Reviewed limits and residual risks

| Threat or unusual condition | Assessment / remaining action |
| --- | --- |
| Donation or wash-trading inflation of displayed earnings | Actual funded receipts are real money, not proof of organic volume or future yield. Do not infer APY or market demand from them. The protocol does not classify trader intent. |
| Thin depth, price shocks, fee changes and adversarial transaction order | Captured prices, marginal-LP measurement and caller/venue loss guards remain; infeasible operations revert and still cost network gas. Earlier thin-depth/callback/second-swap rollback evidence retains its exact source scope. Qualify actual depth, swap routes and target-chain costs. |
| MEV and repeated maintenance | Per-operation caps do not eliminate sandwich loss, IL, market loss or cumulative turnover costs. The user retained per-operation limits only; no new cumulative budget or economic restriction was added. |
| Out-of-range LP | Permission to contribute does not guarantee fee earning or execution feasibility. Pool state can move between a quote and transaction. Polling/cooldown is not a promised next rebalance time; display qualified state and schedule caveats. |
| Two agreeing but correlated or compromised price sources | Numerical agreement is insufficient to establish independence. Real reviewed feeds, source controls, freshness and RPC policy remain release blockers. |
| Transfers, claims and adversarial callbacks | Current owner retains unclaimed rights. Exact callback/revert and all affected shared-fixture cases pass; prior reward fraction/claim-order evidence is reused without claiming fresh global coverage. Marketplace ordering and lost/dead owner addresses remain existing limitations. |
| Privileged controls, custody or token failure | Immediate governance and approved external custody remain trusted. A malicious replacement/dependency or permanently broken asset is not repaired by slot0 validation. No hidden recovery, seizure or arbitrary sweep was added. |

No new production Solidity, ABI, storage, signing capability, schema, economic
split, cap, token, role or custody path is introduced. Existing local state,
journals, website/server and paused monitoring are untouched. The exact source
bindings, failed first fixture attempt and useful new evidence are retained;
external services, final release regression and independent audit remain open.
