# Future activation asset admission

`ZZZActivationAssets` is an immutable helper created by the canonical pool
registry. It separates **permission to contribute a currency now** from the
accounting and custody of assets already attached to NFTs. Governance can append
a reviewed policy for a future token or disable an existing contribution source
without replacing the NFT, Vault or helper.

This helper is an admission gate, not a swap router or asset-custody contract.
Admitting USDC, USDG or a future token does not create a route into the selected
LP pair. The separate immutable [Entry](ACTIVATION_ENTRY.md) now implements
original-source valuation, owner authentication and the complete 1% execution
budget through typed conversion. Actual route funding, dependency/price review
and operating qualification remain described in [routing](ACTIVATION_ROUTING.md).

## Authority and interfaces

```solidity
constructor(address controller, address poolRegistry);
function setAsset(address token, bool enabled, bytes32 expectedCodeHash, bytes32 reviewHash)
    external returns (bytes32 policyId);
function admitPoolAsset(address token) external returns (bytes32 policyId);
function value(address token, uint256 amount) external view returns (uint256 usd18);
```

The constructor requires its caller to be `poolRegistry`, including when the
registry creates the helper from its own constructor. The registry address and
access controller are immutable. No extra replaceable sealed module is added.

`setAsset` uses the existing `onlyGovernance` boundary. Bootstrap governance can
configure before sealing; after sealing the controller's zero-delay controller must
execute the exact operation. A production governance multisig, guardian, keeper,
NFT operator or holder cannot bypass authorization by calling the helper directly.
Authorized controller operations execute immediately. Guardian pause does
not grant asset configuration powers.

`admitPoolAsset` is callable only by the immutable registry. The registry's
governed pool-configuration path initially admits an unknown normalized currency.
This records the observed code hash and a deterministic pool-admission reference,
with `poolAdmission=true`. That reference identifies the authenticated configuration
action; **it is not an independent audit or a claim that one occurred**.

For every known token, automatic admission returns its existing active policy
unchanged. Pool reconfiguration cannot silently re-enable a disabled token,
replace its code pin, refresh its decimals or erase a previous review. A future
explicit change goes through `setAsset` and the governance boundary.

## Enabling and policy history

Enabling requires all of the following:

- A nonzero ERC20 token address with deployed code matching the nonzero supplied
  runtime code hash; native ETH is normalized to the reviewed WETH address.
- A nonzero review reference supplied by governance. This is an accountable
  reference to its review materials, not an on-chain proof of audit quality.
- Successful ERC20 `decimals()` with at most 18 decimals, matching the oracle's
  configured token decimals.
- A configured, positive, currently valid oracle price, including that oracle's
  freshness, round and sequencer checks.

Code and metadata inspection cannot prove that a token remains untaxed,
nonrebasing, unfreezable or safe after an issuer/proxy upgrade. Governance must
review those dependencies and control powers before admission. Actual execution
retains the existing `ExactToken` debit/credit checks; an admitted taxed token
still fails its attempted transfer atomically. A proxy's stable runtime hash
alone does not pin its implementation or administrators. The selected native
wrapper's separate upgrade-policy checks remain relevant, and future proxy assets
need their own complete dependency review.

Every explicit policy appends a fresh immutable record, even if its parameters
repeat a historical configuration. `policyCount()` / `policyAt(index)` enumerate
history; `policies(id)` returns its token, enabled flag, expected code hash, review
hash, decimals and admission origin. `activePolicy(token)` identifies the current
record. Events report both the new record and the old-to-new active transition.
There is no history deletion, mutation of an old record or broad iteration over
the complete history during contributions.

## Disabling without locking existing positions

Disabling records a new policy without reading the token, its decimals, its
implementation or its oracle. It remains possible when code has changed, the
token reverts, a feed is stale or the oracle is unavailable. The last known
decimals are copied from recorded history. Governance can also record a disabled
future address, with a zero expected code hash, to prevent automatic admission
until an explicit later review. No token contract must exist to disable that
address.

`value(token, 0)` returns zero before every policy or dependency read. This permits
the other side of a one-sided contribution to pass its own source-admission
check, including when the zero side is disabled. Positive amounts require the
current enabled policy, unchanged runtime pin, matching configured decimals and
the existing oracle valuation. Missing, disabled, changed-code or misconfigured
sources fail closed.

Only the new-contribution valuation path should call this helper. It must not be
used as a prerequisite to claim rewards, value old LP, collect fees, rebalance,
close LP or execute an approved migration. Disabling a source does not remove a
pool, change its assets, cancel NFT shares, alter funded rewards or withdraw
principal. Existing LP strategy execution can still involve that asset. Other
dependencies, outages and migration checks retain their own safety limits;
admission separation does not guarantee that every operation works during every
possible token, oracle, venue or bridge failure.

The helper never receives approved spending authority, pulls assets, approves
spenders or executes arbitrary calls. Its external dependency calls are read-only
token metadata/oracle queries. It has no receiver, sweep, rescue or withdrawal
method. Do not send funds to it; unsolicited or forced assets are not protocol LP
and cannot be recovered through policy updates.

## Verification scope

The helper's unit suite uses the real access controller with zero delay and the real
oracle with explicit test tokens/feeds and a test-only registry factory. Tests
cover initial admission, wrong callers, immutable history, code/decimal/feed
changes, failed-token/feed disabling, zero-side contributions, immediate enable and
disable operations, guardian limits, no custody and preservation of the existing
exact-transfer execution guard. These tests do not substitute for the canonical
registry/Vault integration, actual token routing, target-chain operating tests or
an independent audit. Production addresses and release approval remain unset.

The scoped local run on 2026-10-15 passed **19 tests, zero failures and zero
skips** with pinned Solidity 0.8.26 and the repository's existing optimizer
profile. The helper's runtime/initcode objects measured **4,810 / 5,305 bytes**.
The registry's complete embedded creation code and actual deployment arguments
still require their own final size gate after integration.
