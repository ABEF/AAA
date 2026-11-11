# Reference-pool swaps with captured valuation

User decision11November2026: the highest qualifying external ETH/ZZZ price
reference must remain eligible for best execution, with existing safeguards.
This source candidate separates an authenticated own-swap market transition from
unexpected observation/control changes. It does not select or qualify a real pool.

## Plan and implementation boundary

The [full design and operator procedure](../../docs/REFERENCE_SWAP_EXECUTION.md)
records the model: start before callbacks, retain one original two-source vector,
quote actual core depth, prove the selected exact full state before settlement,
revalidate through final callbacks, and clear the transaction-only scope.

New explicit execution-price1/LP-routing3 retains public pricing2, direct Entry3,
accounting7, canonicalV10 and custody5. The nine original Plan words are followed
by five market-state words. Older LP2/trace/profile/journal consumers remain
explicitly historical; they are not relabeled or silently upgraded.

No global cached public Oracle mode, keeper-selected prices, guessed post-state,
new swap/loss ceiling, fund recipient or arbitrary executor is added. The chosen
reference may be a swap venue, but not the same-core owned LP destination. This
keeps external-depth qualification and avoids pretending own LP changes are
external market evidence. No automatic highest-TVL rotation is introduced.

## Material changes

- Oracle owns bounded transient commitments and verifies original source/policy,
  current freshness/agreement and allowed own-state transitions. Composite proof
  admission is explicit governance with a monotonic revision and runtime binding.
- Captured data getters are separated from full validation at mutable boundaries.
  An initial prototype repeated full proofs inside every read-only calculation
  and exceeded the unchanged12M/full20%-headroom cold Entry budget. Its failure
  and gas attribution are retained. The correction coalesces readonly work and
  combines original/live round proof reads; it does not raise the budget.
- Manager proves exact actual-core output/full state before token settlement;
  later callbacks cannot silently move the expected reference. Standalone swaps
  own a scope; only the expected Vault branch borrows a Pricing-owned scope.
- Contribution/maintenance/share/idle/utilization calculations retain their
  starting valuation. Actual main deployment still uses physical post-swap spot
  and amounts; source movement cannot reprice away loss or subsidize entrants.
- Existing fixed read-only Math now shares execution geometry, admission and
  maintenance calculations. Authority/masks and scope control remain in their
  original typed callers. No new deployed helper or constructor change is needed.
- The old balance-only output/sqrt comparison is implied at the same boundary
  by strict positive quote output plus full state proof inside `_swapExact`.
  Zero quote output remains reserved for the explicit emergency path; it is not
  an ordinary fallback. Exact later physical LP/receipt proofs remain.
- Backend, keeper and unsigned operator consumers select fresh semantics only
  under the explicit capability. A stale trace assumption about removed foreign
  compound epoch calls is corrected only for the fresh graph; historical traces
  retain their original requirements.

## Verification status

The [verification record](VERIFICATION.md) separates normal production size gates,
actual-core/Entry tests, synthetic consumer checks and source reuse. Initial size
failures are preserved and resolved through typed factoring, not higher limits.
No successful test is evidence of qualified live markets or independent approval.

## Remaining risks and decisions

- Cold Entry uses15.32M ETH/15.64M ZZZ in the final controlled fixture, requiring
 18.38M/18.77M with20% headroom. The unchanged12M default rejects it. Qualify the
 existing optional activation policy2 separately; no default/running budget is
 raised and these measurements are not target-chain fees or a universal ceiling.
- Initial source honesty, true independence, external depth, sequencer/liveness,
  source publication and actual target-chain operation remain unqualified.
- A valid exact quote may still fail if its own impact exceeds live source
  agreement, spot, per-swap/additional, contribution or maintenance limits.
- Snapshotting does not remove pre/post-transaction MEV or repeated permitted
  loss. A large pool is harder to manipulate, not intrinsically independent.
- References used as owned LP destinations remain unsupported by this normal
  capability; that requires a separate independence/LP-transition design.
- Runtime/initcode headroom remains tight; exact normal source/configuration and
  constructor arguments must match the release. No limit was raised.
- Existing sealed deployments and installed consumers need reviewed replacement
  or source adoption. Publication changes no service, public signing, site,
  wallet, existing Anvil/journal or user-paused heartbeat.
