# Atomic source activation

`ZZZActivationEntry` is the immutable PoolRegistry-created contribution entry,
paired with `ZZZActivationAssets`. The current undeployed profile is accounting
6 / fee-intake1 / routing2 / pricing2 / reviewed policy2 / ProtocolPolicy1, with direct
governance2, custody4 and local canonical adaptable-policy V6. It accepts **native ETH or the one fixed
ZZZ only**. USDC, USDG and WETH are not user contribution inputs.

Entry never owns the NFT or grants principal redemption. It authenticates one
owner-funded operation, optionally converts the source through a reviewed typed
route and calls the fixed Vault. [Preparation](ACTIVATION_PREPARATION.md) returns
an unsigned review; source support does not qualify a live deployment or service.

## Request and wallet call

The current owner calls `executeReviewed(Request,uint16 maximumLossBps,bytes32 expectedContributionPolicy)`.
The old `execute` selector is absent from the current Entry; historical deployments
keep their original ABI. The request has these nine fields, in ABI order:

| Field | Type and meaning |
| --- | --- |
| `nftId` | `uint256`: actual hashed NFT ID, not mint ordinal. |
| `poolId` | `bytes32`: current reviewed contribution pool; growth must use this NFT's existing bucket/pool. |
| `sourceAsset` | `address`: zero for native ETH, otherwise the fixed ZZZ. |
| `amountIn` | `uint256`: exact positive source amount in raw units. The preparer bounds it below `2**128`. |
| `routeId` | `bytes32`: zero for direct accounting-currency input; otherwise the reviewed route identity. |
| `minimumOut` | `uint256`: zero for direct input, positive raw output minimum for conversion. |
| `minimumLiquidity` | `uint128`: positive actual shared-LP liquidity-unit minimum, not USD or NFT shares. |
| `deadline` | `uint256`: Unix time, current and at most ten minutes ahead. Prepared reviews expire sooner. |
| `increase` | `bool`: false for first activation, true for growing an already active NFT. |

`expectedContributionPolicy` must equal the reviewed ProtocolPolicy.entryFingerprint,
covering action minima, idle ceiling and revision; stale/callback-mutated terms revert.
`maximumLossBps` is the caller's reviewed cap, at most 1000 bps. The captured
contribution policy must not exceed it. Governance can tighten future execution;
a widening beyond that signed review requires a new review. ERC20 allowance is
to Entry for exactly the chosen source amount; native input requires exactly
`msg.value == amountIn`, with no token approval. Gas is separate.

## One source value and one execution budget

Activation defaults to **$100 original source value** and growth **$5**;
ProtocolPolicy may set future USD18 minima, each>=1USD and growth<=activation, with any higher configured pool minimum also enforced. Entry freezes
two-source source/pair price bounds, policy identities and limits through
`ContributionPricing.beginEntryReviewed` before token pulls, approvals or
conversion. The selected source-agreement tolerance is 3%, distinct from the
contribution loss allowance. Source prices are not caller-supplied USD values.

After direct input or a typed route, Entry makes exactly one Vault `activate`
or `increase` call. A temporary context binds owner, NFT, pool, exact raw pair
amounts, original measured source USD and `keccak256` of the Vault calldata.
Vault and Registry authenticate this context. An active mismatch reverts rather
than falling back to the smaller post-conversion pair valuation.

Conversion plus balancing plus deployment consume one captured contribution
budget: default **2%**, governed up to **10%**, with stronger caller/venue minima
still binding. Both net new backing and marginal deployed LP must satisfy the
floor; at default the new LP must cover at least 98% of conservative upper input
value, valued at the frozen lower pair prices. Incumbent LP, idle, historical
compound, fees or donations cannot subsidize it. Idle is not deployed LP. See
[price security](PRICE_SECURITY.md) and [execution policy](EXECUTION_LOSS_POLICY.md).

Current ownership is checked before custody, after conversion and after the
complete Vault operation. Token/operator NFT approval is not authority to add
LP for another owner. Callback transfers or inconsistent context revert the
whole operation. Optional royalty-currency isolation remains a separate ledger
rule: a failed currency can defer its eligibility without undoing otherwise
valid activation or giving newcomers older royalties.

## Route policy

For the selected ETH/ZZZ pool, either original input is already an accounting
currency and can use route zero. Vault still performs guarded ratio balancing;
route zero does not promise a cost-free or swap-free contribution.

Optional pre-Vault routes are typed, single-hop v3 or static hookless v4. Output
must be one actual currency of the selected pool. They cannot add another input
identity, choose a payout recipient, call arbitrary code or perform a bridge.
Native v4 uses actual ETH; v3 requires ERC20 source and output. A reviewed future
ERC20 accounting pool does not make WETH an additional original source.

The Entry v3 `RoutePolicy` has twelve fields, in order:
`source`, `output`, `router`, `factory`, `pool`, `fee`, `routerCodeHash`,
`factoryCodeHash`, `poolCodeHash`, `sourceCodeHash`, `outputCodeHash`, `reviewHash`.
The first five are addresses, `fee` is `uint24`, and the remaining fields are
`bytes32`. Route identity is `keccak256(abi.encode(policy))`.

Entry validates runtime pins, factory pool mapping, token ordering, factory/fee
and router factory. It emits only SwapRouter02's typed seven-field
`exactInputSingle` call: recipient Entry, exact input and zero price limit.
Policies are append-only. Direct governance records or toggles them; disabling
requires no failing dependency read and re-enabling revalidates. See the separate
[v4 policy tuple and executor](TYPED_V4_ROUTES.md) and [routing guide](ACTIVATION_ROUTING.md).

## Custody and callbacks

Exact router/Vault approvals are cleared after use. Measured source/output
balance changes reject partial consumption, taxed transfers, invented output
and prefund subsidy. Native/token balances return to their pre-operation
baselines; donations are not a refund or operator surplus. There is no rescue
or arbitrary-call path.

Entry is nonreentrant. Vault approval occurs while contribution context is
inactive; ownership is rechecked immediately before arming the one fixed Vault
call. Context clears before final approval-reset callbacks. `validateOwner` is
restricted to the fixed Vault, `sourceValue` to the immutable Registry, and
`pricingContext` to the fixed pricing companion. Venue, approval, ownership,
price, balance or LP-check failure rolls back that transaction. A separately
confirmed allowance and spent network gas are not rolled back with it.

## Qualification boundaries

Use the [feature/evidence reference](IMPLEMENTATION_STATUS.md) for source-matched
checks. Earlier [atomic integration](../reports/activation-preparation/VERIFICATION.md),
[native-port](../reports/native-eth-port/VERIFICATION.md) and
[liquidity operations](../reports/liquidity-operations-20261025/VERIFICATION.md)
retain their own source, mocks and policy defaults. Old Pons/wrapped/99% examples
are not current route qualification or a reason to relabel an existing deployment.

Actual independent feeds, depth/routes, token/proxy behavior, wallet/API services,
VRF, authorities, OpenSea, target gas, operating recovery and independent audit
remain release work. Runtime hashes do not prove proxy administrators or source
reporters are honest. No deployment, public signing or transaction is authorized
by this guide. Production is NOT APPROVED.
