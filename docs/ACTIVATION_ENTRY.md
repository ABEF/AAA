# Atomic source activation

## Reviewed Entry policy V1 - 2026-10-25

The current undeployed pricing-V2 candidate uses
`executeReviewed(Request,uint16 maximumLossBps)` with explicit
`review_policy_version: 1` in activation/release profiles and matching Entry/Pricing
getters. It rejects a captured governed cap above the caller maximum before
funds move, retaining all final price/LP/policy checks. Legacy execute is disabled
on the new code; historical pricing-V1/local deployments retain original ABI.
Read [policy and exact compatibility boundaries](EXECUTION_LOSS_POLICY.md#review-time-policy-binding)
and [scoped evidence](../reports/comprehensive-improvement-20261025/VERIFICATION.md).
Native-V2 browser integration and actual provider/wallet qualification remain open;
no existing chain, website build, journal or public signer was upgraded.

## Pricing-V2 contribution security - 2026-10-24

The [current price-security guide](PRICE_SECURITY.md) supersedes older single-feed
descriptions below. Two sources per asset, a user-selected3% agreement tolerance,
frozen pre-pull prices/limits and actual marginal LP checks are implemented.
Agreement tolerance is separate from the default2% contribution execution-loss floor; gas is
separate. Actual feeds/ages/routes remain unqualified. Use explicit pricing2,
native accounting2/routing2 and the fixed Oracle-created helper, not a relabeled
legacy deployment. [Scoped evidence](../reports/price-security/VERIFICATION.md).

**Current policy, 2026-10-24:** [Typed v4 conversions](TYPED_V4_ROUTES.md) and
[governed execution-loss limits](EXECUTION_LOSS_POLICY.md) are implemented in the
undeployed candidate. Defaults are 2% contribution, 1% conversion and 3% maintenance;
immediate governance may set each category up to a hard 10%. Existing stricter
venue/caller minima remain. Pending normal custody approvals retain their original
absolute floor. Earlier fixed-cap or v3-only descriptions below retain their
historical/default scope. Actual routes, services and independent audit remain open.

## Activation native V2 boundary - 2026-10-24

Actual ETH funding/accounting is implemented in the undeployed [native V2 candidate](../reports/native-eth-port/VERIFICATION.md). Use explicit version2 API/keeper profiles and fresh runtime pins; preserve old WETH deployments and journals. Exact payable values, separate backing and current-owner claims remain mandatory. Atomic ETH/WETH conversion, V1 schema import, actual native services/market qualification and independent approval remain open. The website source/build/server, Anvil state and shared Anvil-only signer are unchanged. Earlier dated entries retain their original source scope.


**Selected integration (2026-10-24):** [Hookless ETH/ZZZ](POOL_SELECTION.md) supersedes Pons; historical Pons examples below keep their scope. Current Entry uses actual native ETH accounting V2 and typed single-hop v3 or hookless static-fee v4 conversion. [Native scope](NATIVE_ETH_ARCHITECTURE.md) and [typed routes](TYPED_V4_ROUTES.md) describe exact profiles and remaining qualification. Historical Pons/V3 tests below retain their original contracts and 1% fixtures.

`ZZZActivationEntry` is an immutable child created by the canonical Pool Registry,
alongside `ZZZActivationAssets`. It converts a current NFT owner's admitted source
asset into one accounting currency and calls the existing permanent-liquidity
Vault in the same transaction. It creates no redemption right and never takes
custody of the NFT. This source implementation is not a deployed service.

## One source value and one execution budget

For current reviewed EntryV1 the owner calls
`executeReviewed(Request,uint16 maximumLossBps)` directly; legacy `execute`
reverts on this code. ERC20 owners approve only their chosen
amount to the Entry. Native V2 uses exact `msg.value` and the real zero-address
ETH currency without wrapping for a compatible native pool. Gas is separate.

Entry measures exact token ingress and asks the governed activation-asset helper
to value the actual source amount. A stablecoin name is not an assumed dollar peg.
Activation requires at least $100 gross source value. Later additions retain their
configured pool minimum. The caller supplies neither a USD valuation nor a custom
executor, recipient, signature or arbitrary transaction payload.

After a direct pair input or an admitted typed single-hop V3/V4 conversion, Entry calls exactly one `activate` or `increase` operation. A temporary
context binds the owner, NFT, pool, pair amounts and hash of the exact Vault calldata
to the proven original source USD value. Vault authenticates that context, and
Registry contribution valuation uses that original value. The existing Vault
checks enforce one captured aggregate marginal-deployed LP floor, including
conversion and placement: 98% at the current 2% default. This is one budget
across all legs, not a fresh allowance per swap. Conservative input/output price
bounds and stricter venue/caller guards also apply; idle is not deployed LP.

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

[Typed V4 routing](TYPED_V4_ROUTES.md) is the current additional route family.
The following V3 policy is still supported under its explicit profile; it is
not the only route kind. No arbitrary router/call or hook is added.

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
relax the Vault's captured original-source marginal-LP bound. Routes cannot emit arbitrary calldata,
use a user-selected receiver, change custody, bridge or invoke unrelated contracts.
The output must be exactly one of the requested pool's accounting currencies.

Source admission is independent of intermediate currency admission. For example,
disabling WETH as an original source does not itself disable an admitted USDG input
that converts into WETH. Pool admission, operations, fresh valuation, dependency
pins and the final LP budget still apply. Actual native ETH and WETH have distinct typed source
admission; native V2 does not normalize ETH into WETH. Unsupported USDC conversion remains unavailable until a reviewed,
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

The following test counts and 99% examples are historical fixed-1% evidence,
not proof of current default policy or the newest source. Use the current
[liquidity operations verification](../reports/liquidity-operations-20261025/VERIFICATION.md)
for this delta and exact remaining limits.

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
