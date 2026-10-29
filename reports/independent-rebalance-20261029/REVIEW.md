# Independent rebalance confirmation and manual emergency recovery

Baseline `2feee92f6bc13b09bae1d43f36bfb7cf6c8faac9`, main only. Fresh local
candidate; **production NOT APPROVED**. No deployment, public transaction,
signer-policy, service, journal, website or existing Anvil change occurred.
[Verification](VERIFICATION.md) distinguishes executed evidence and limits.

## Requirements and authority

The user accepted ordinary protection against a local pump/dump: actual managed
LP and configured independent reference must be outside identical physical bounds
on the same side through the sampled window, with final execution checks. A
reference-only exit, target-only exit or opposite sides cannot authorize ordinary
rebalance. Governance must be able to change policy without permanently stranding
LP. The user separately authorized **manual emergency-only governance bypass**
of optional safeguards, explicitly unrelated to day-to-day keeper work.

The implementation therefore separates ordinary confirmation2 from a globally
paused governance-only emergency1 entry. It does not add a generic executor,
external custodian, new operator identity, automatic retry fallback, unqualified
pool oracle or transaction service. Existing two-source USD pricing, fixed ETH/
ZZZ, economics and terminal collective holder return remain.

**Accepted trust expansion:** with independent-price/financial checks disabled,
governance can deliberately accept an unfavorable swap and lose nearly all LP
principal, including trading against a related party. Approved venues, accurate
bookkeeping, manual invocation and global pause do not make that economically
safe or prevent ordering attacks. Ordinary loss ceilings are no longer an
unconditional protection against governance itself. This was explicitly requested;
it is not classified as an accidental backdoor or protection from malicious
governance. Actual key custody, operation simulation and independent audit remain
release requirements. No timelock or extra approval committee was introduced.

## Concrete improvements and review findings

| Area | Change and consequence |
| --- | --- |
| Independent trigger | Confirmation2 compares existing `Oracle.referenceX96` against the actual physical TickMath bounds in raw pool-key order, never inverted display percentages or desired target ticks. Manual governed width changes retain their established exception. |
| Mutable policy | `setRequireReferenceExit(bool,reviewHash)` defaults true, requires a nonzero commitment for changes and advances a monotonic revision. Changed-and-restored settings cannot reuse prior samples. It changes no execution-loss cap. |
| Indirect width bypass | Optional automatic keeper widths could otherwise use the deliberate-width exception. They cannot be enabled while reference protection is true; restoration requires their exact enabled count to be zero. Disable/orientation invalidation decrements; reconfiguration cannot double-count. |
| Negative observation race | An off-chain observed disagreement could become healthy before `observe` inclusion and extend the old window. The worker persists and confirms `resetObservation` first when an old window exists, rather than trusting renewed observation to clear it. Empty negative state submits no redundant clear. |
| Isolated emergency authority | `Migration.emergencyRebalance(request)` requires sealed/paused current governance and an operating, pre-terminal canonical lifecycle. Immutable-parent Budget/Manager context is limited to that atomic Vault operation and cleared on success or reverted on failure. Other callers and ordinary keeper work cannot adopt it. |
| Exact request | Chain/Vault/Position/share custody hash, explicit physical ticks, optional exact reviewed-venue swap, positive raw output/LP minima, bounded deadline and nonzero review commitment. No automatic USD sizing when its price protection is explicitly bypassed. |
| Optional versus structural | Retained bits cover raw trigger/cooldown, independent price agreement, value/quality/idle limits, operations flags and existing sampled confirmation. Fixed assets and typed admitted venue identity, exact budgets/received deltas, approvals, LP ownership, NFT shares, reward reserves and terminal/canonical locks are never optional. |
| Callback integrity | Governance/pause/lifecycle and reviewed control identity are checked through completion. If sample bit16 is retained, policy/raw observations are pinned across callbacks even with financial bit4 off. Compare stable evidence, not readiness against the deliberately replaced LP. |
| Parked recovery | Manual emergency can redeploy parked attributed custody; normal guards can be retained when available. It cannot revive terminal holder exit. Native ETH and fixed ZZZ stay inside Vault-managed custody. |
| Accounting | Unwind harvests actual fees and releases attributed compound; original NFT shares/contributions and earned claim/buyback reserves are preserved. Failed swap/mint rolls everything back, while network gas is spent. No recipient or reserve sweep was added. |
| Readers/configuration | Explicit historical confirmation1 remains separate. Fresh keeper/API/helper/Budget reads support version2, report coherent `reference_disagreement` and never guess zero or readiness. Schema6 inventory requires fresh confirmation2/emergency1 capability/runtime fields and inactive emergency context. Examples remain unconfigured. |
| Code size | Shared exact v4 math moves to the existing immutable Balancer; stateless maintenance valuation/compound readiness to existing Pricing; raw evidence hashing to Confirmation. Normal object gates are preserved. Added external calls have overhead; size compliance is not proof of lower gas. |

## Safety properties traced

The fixed call chain is governance -> Migration manifest -> Budget context ->
Vault nonreentrant wrapper -> Manager context -> typed core close/swap/mint ->
postconditions -> clear contexts. Manager recognizes emergency state only for
actual Vault calls; the other module/user swap path does not inherit bypasses.
Budget public third-party valuation does not use the internal no-value sentinel.
Read-only math helpers create no custody, approval or generic call authority.

Optional price checks are distinct from optional value checks: retaining value
floors still needs fresh USD pricing even when price-agreement bit2 is disabled.
Retaining raw eligibility or sampled evidence also retains that read's actual
dependencies. Masks are not promises that arbitrary combinations can succeed.
Existing samples can expire during pause. A positive raw liquidity result can be
outside the market and earn no fees; the operator must inspect the actual result.

The reference trigger uses the configured dual USD sources. It does **not**
install or qualify a deeper-market TWAP, prove source independence, observe during
cooldown or establish continuous price history between samples. Ordinary policy
remains initial12hours, selected900-second duration/300-second maximum gap,
240-second source checks and durable60-600second post-ready service jitter.
Hourly harvest and separate compounding remain independent; no passive/40% or
cumulative-loss strategy was introduced.

## Engineering guidance and unresolved qualification

Review followed the actual Solidity/Uniswap dependency implementations and
[Solidity security guidance](https://docs.soliditylang.org/en/latest/security-considerations.html)
on external callbacks, cross-contract reentrancy, limited proxies and fail-safe
modes. [OpenZeppelin access-control guidance](https://docs.openzeppelin.com/contracts/5.x/access-control)
highlights privileged-role risk. Neither source endorses this particular economic
bypass or certifies the code. Source review and local fixtures cannot prove
absence of vulnerabilities or an attacker-profit bound.

Real source/market/route independence, post-withdrawal depth, output/raw-floor
selection, cold/maximal catalog gas, target-chain ordering, key/nonce/recovery
operations and independent review/remediation remain open. Existing runtime and
constructor margins are small and must be checked again on any source change.
The [emergency runbook](../../docs/EMERGENCY_REBALANCE.md) and
[sole Todo](../../TODO.md) record these limits. No installed service was upgraded.

The wider whole-project audit remains unfinished. Static body review continued
through contracts/ledgers/canonical handoff, but navigation maps and historical
scenario inventories are not individually executed coverage. Remaining backend/
secondary-script depth is not closed by this feature's focused verification.
