# Atomic source activation

**Selected integration (2026-10-24):** [Hookless ETH/ZZZ](POOL_SELECTION.md) supersedes Pons; historical Pons examples below keep their scope. Current Entry remains WETH-accounted and typed single-hop v3 for converted inputs. [Native ETH](NATIVE_ETH_ARCHITECTURE.md) and [future v4 routing](POST_SEAL_POLICY.md) are pre-seal work, not implemented by pool selection.

`ZZZActivationEntry` is an immutable child created by the canonical Pool Registry,
alongside `ZZZActivationAssets`. It converts a current NFT owner's admitted source
asset into one accounting currency and calls the existing permanent-liquidity
Vault in the same transaction. It creates no redemption right and never takes
custody of the NFT. This source implementation is not a deployed service.

## One source value and one execution budget

The owner calls `execute(Request)` directly. ERC20 owners approve only their chosen
amount to the Entry. Native ETH uses the exact `msg.value`, wrapped into the native
pool's Registry-verified accounting-slot-zero wrapper. Gas is separate.

Entry measures exact token ingress and asks the governed activation-asset helper
to value the actual source amount. A stablecoin name is not an assumed dollar peg.
Activation requires at least $100 gross source value. Later additions retain their
configured pool minimum. The caller supplies neither a USD valuation nor a custom
executor, recipient, signature or arbitrary transaction payload.

After a direct pair input, exact native wrapping or an admitted single-hop V3
conversion, Entry calls exactly one `activate` or `increase` operation. A temporary
context binds the owner, NFT, pool, pair amounts and hash of the exact Vault calldata
to the proven original source USD value. Vault authenticates that context, and
Registry contribution valuation uses that original value. The existing Vault
checks therefore enforce one aggregate floor of at least 99% marginal actually
deployed LP, including conversion and LP execution. Two separate allowances of 1%
are not created. For example, 0.8% conversion loss plus 0.3% LP loss fails the total
budget even though each leg individually loses less than 1%.

The Registry must call `sourceValue` only while evaluating a contribution from its
canonical Vault. An inactive context returns zero, permitting normal owner-only
pair entry. An **active** context with different pool or amounts reverts; it cannot
fall back to the cheaper post-conversion pair valuation. Vault's helper-authorized
owner branch must call `validateOwner(id, keccak256(msg.data))` and reject every
other nonowner caller. Entry also checks current ownership before custody, after
conversion and after the complete Vault operation. Token/operator NFT approvals
are not contribution authority. NFT transfers during callbacks revert the entire
transaction and restore the source funds and NFT ownership.

## Route policy

`RoutePolicy` fixes the source/output assets, SwapRouter02, V3 factory, V3 pool,
fee, exact runtime hashes and a nonzero review reference. The factory's pool
mapping, pool token ordering, pool factory/fee and router factory must all agree.
Every execution rechecks those observations. Only the controller's governance can
record a route or change its enabled flag; after sealing, that means the zero-delay
governance controller. Policy identity and contents are append-only. Disabling does not call a
potentially broken dependency. Re-enabling validates it again.

Only SwapRouter02's typed seven-field `exactInputSingle` tuple is emitted: the
output recipient is Entry, the input amount is exact, and the price-limit argument
is fixed to zero. Entry independently enforces a deadline no more than ten minutes
ahead. User `minimumOut` and `minimumLiquidity` may tighten execution but cannot
relax the Vault's original-source 99% bound. Routes cannot emit arbitrary calldata,
use a user-selected receiver, change custody, bridge or invoke unrelated contracts.
The output must be exactly one of the requested pool's accounting currencies.

Source admission is independent of intermediate currency admission. For example,
disabling WETH as an original source does not itself disable an admitted USDG input
that converts into WETH. Pool admission, operations, fresh valuation, dependency
pins and the final LP budget still apply. Native ETH is normalized to WETH source
admission. Unsupported USDC conversion remains unavailable until a reviewed,
funded route exists; this helper does not invent one.

## Custody and callbacks

Approvals grant the fixed router only the exact source amount and the canonical
Vault only the exact newly obtained output. Both are reset. Exact source and output
balance deltas reject partial consumption, fabricated router outputs and taxed
transfers. Native and token balances return to their pre-operation baselines;
preexisting donations cannot subsidize the input, become a refund or be swept.
Unsupported donations remain quarantined. There is no administrator token rescue.

The Entry is nonreentrant. Its exact Vault approval runs while context is still
inactive, then ownership is rechecked before context is armed immediately for the
one fixed Vault call. An approval callback cannot lend source-value provenance to
an unrelated contribution. Context is cleared before final allowance-reset
callbacks. Read access is restricted:
`validateOwner` to the canonical Vault, `sourceValue` to the immutable Registry.
The Vault independently guards its own mutation paths. Any route, approval,
ownership, balance, price or LP-budget failure rolls back the whole transaction.

## Qualification boundaries

The 28 focused offline tests use a deterministic V3 fixture and a minimal Vault
enforcing the original-source 99% rule. They cover context, aggregate loss,
unauthorized callers, exact custody, callback transfer/reentry and failing route
dependencies. The separate nine-case `AtomicActivationIntegration.t.sol` suite
uses the real Registry-created Entry/Assets, Oracle, Vault, NFT, Membership and
reward ledgers. It tests $100 original input becoming $99 LP, rejects a 1% loss
at each of two legs, checks direct-pair and top-up budgets, actual owner events,
depegged source pricing, callback ownership/context and funded transfer claims.
Its router and LP venue remain explicitly mocked. Neither suite establishes
actual stable-route liquidity, combined USDG-to-Pons execution or supported
production services. Preserve separate pinned-pool fork evidence and complete
Robinhood Testnet rehearsal before release.

Runtime hashes cannot prove the future honesty of upgradeable assets, oracle
administrators, blacklisting issuers or external venues. Their implementation and
authority review remains required. Production feeds, routes, wrappers, strategy
parameters, gas budgets, wallet flows and independent audit/remediation must be
qualified. No deployment or real transaction is authorized by this implementation.
