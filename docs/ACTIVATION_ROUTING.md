# Current ETH/ZZZ contribution routing

The current release accepts native ETH or the one fixed ZZZ only. Contributions
use the reviewed Entry, two-source prices and actual marginal LP verification;
the API prepares the complete unsigned operation with a caller loss maximum.
See [preparation](ACTIVATION_PREPARATION.md), [price security](PRICE_SECURITY.md)
and the [current profile](POSITION_V3.md). Network gas is separate.

USDC/USDG activation research and its conversion-only reader/tests are retired.
They are not a cheaper-route qualification or a supported activation option.
Committed sources and unpublished draft hashes are preserved in the
[retirement record](../reports/architecture-pruning-20261025/retired-tools/stable-research-retirement.json).
WETH and admitted stablecoin marketplace royalties are a separate settlement
requirement; this retirement does not discard their existing NFT entitlements.

## Historical routing research (superseded)

The text below is retained as historical context, not current commands or
production input support. The old standalone reader is no longer executable.

# Current and historical contribution routing

Current source inputs are native ETH and explicitly reviewed ZZZ only.
USDC/USDG/WETH are not contribution options. See [current scope](SIMPLIFIED_RELEASE.md)
and [Entry](ACTIVATION_ENTRY.md). The research and addresses below are historical
or optional internal/royalty-market observations, not admission of user currencies
or qualification of a production route.

## Reviewed Entry policy V1 - 2026-10-25

The current undeployed pricing-V2 candidate uses
`executeReviewed(Request,uint16 maximumLossBps)` with explicit
`review_policy_version: 1` in activation/release profiles and matching Entry/Pricing
getters. It rejects a captured governed cap above the caller maximum before
funds move, retaining all final price/LP/policy checks. Legacy execute is disabled
on the new code; historical pricing-V1/local deployments retain original ABI.
Read [policy and exact compatibility boundaries](EXECUTION_LOSS_POLICY.md#review-time-policy-binding)
and [scoped evidence](../reports/comprehensive-improvement-20261025/VERIFICATION.md).
The native-V2 read/unsigned browser profile is implemented; actual provider/wallet qualification remains open;
no existing chain, website build, journal or public signer was upgraded.

## Current dual-price route boundary - 2026-10-24

Every admitted source and LP currency needs [two qualified USD sources](PRICE_SECURITY.md).
The selected agreement tolerance is3%; conservative bounds still must prove the
separate current contribution execution floor (2% by default). No route can replace original
source value with a post-swap quote, pool spot, one source or a stable peg.
Pricing2 preparation verifies the complete Entry/LP trace and all source rounds.
Live market/provider qualification stays open; historical observations below keep
their original scope. [Evidence](../reports/price-security/VERIFICATION.md).

**Current policy, 2026-10-24:** [Typed v4 conversions](TYPED_V4_ROUTES.md) and
[governed execution-loss limits](EXECUTION_LOSS_POLICY.md) are implemented in the
undeployed candidate. Defaults are 2% contribution, 1% conversion and 3% maintenance;
immediate governance may set each category up to a hard 10%. Existing stricter
venue/caller minima remain. Pending normal custody approvals retain their original
absolute floor. Earlier fixed-cap or v3-only descriptions below retain their
historical/default scope. Actual routes, services and independent audit remain open.

# Activation inputs, routes and source provenance

**Current target (2026-10-24):** [Selected hookless ETH/ZZZ](POOL_SELECTION.md) replaces Pons. Earlier on-chain route observations below remain historical; qualify the complete selected-pool operation. Current conversion supports typed single-hop v3 and static hookless v4; qualify actual routes under explicit profiles. The user retained the1% reward-conversion cap and requires a cheaper route.

The accepted input choices are **USDC, USDG, ETH and ZZZ**. An activation starts
from at least **$100 of source input value**, with at most **2% total contribution execution
loss** and network gas paid separately. A $100 source input therefore requires
at least $99 actually deployed LP. The bound covers the whole conversion and LP
execution, not a fresh 2% allowance at each step. Inputs and final LP must use
reviewed prices; neither a stablecoin ticker nor an assumed dollar peg proves
its value.

## Verified addresses and outstanding authority review

Read-only observations on Robinhood mainnet **4663**, block **89,527,712**,
hash `0xb0e0ef3bbe955794a5d562bd2a68c0453b6b6165074c973cc7bba53d8d2e0256`:

| Asset | Exact address | Decimals | Provenance |
| --- | --- | --- | --- |
| USDC | `0x80e0e24718dbfcad49ecaa6f1e6c89a190586ca8` | 6 | Canonical Ethereum bridge representation |
| USDG | `0x5fc5360d0400a0fd4f2af552add042d716f1d168` | 6 | Paxos/Robinhood official native USDG |
| WETH | `0x0bd7d308f8e1639fab988df18a8011f41eacad73` | 18 | Official Robinhood wrapped native ETH |
| ZZZ | `0x7dbf38976f6d3b9c529e7d9484a71898b409ee6a` | 18 | User-selected token; see ROBINHOOD_POOL.md |

[Circle's supported USDC contracts](https://developers.circle.com/stablecoins/usdc-contract-addresses)
do not list Robinhood as a native issuance network at this verification.
[Robinhood's bridge directory](https://docs.robinhood.com/chain/protocol-contracts/)
identifies L2 Gateway Router `0x1e324b9316138ca9a73f960213621ad1aaf01b89`.
Its `calculateL2TokenAddress` maps Circle's Ethereum USDC
`0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48` to the USDC address above. Both
the token's `l1Address()` and `l2Gateway()` agree, and `getGateway` returns the
official standard L2 gateway `0xfd9b17206278c16ddaacf6ac8f05dbf97edcb31e`.
This is bridged collateral exposure, not Circle-native Robinhood issuance.

The USDC token is a beacon proxy. Its beacon
`0x883d9f54f50c9d096b6b3823532fdc8fd8dfa293` points to implementation
`0xef3b461697c6bd38c5458afa31e1250c98fd0f5f`; beacon `owner()` is
`0x2a153c6a1b66dbc930a8d7017230ab0253005c09`, also the observed owner of the
official L2 ProxyAdmin. The standard gateway is itself upgradeable. L1 Circle
issuer/asset controls and Robinhood bridge/beacon controls require dependency
review; these representations are not immutable assets just because a proxy's
runtime hash stays constant.

[Paxos's USDG directory](https://docs.sandbox.paxos.com/guides/stablecoin/usdg/mainnet)
and [Robinhood's token directory](https://docs.robinhood.com/chain/contracts/)
identify the same USDG address. Its ERC1967 implementation slot contains
`0x68184c449e1a8f34fa18d289737129fd27b66f8f`; `owner()` and `defaultAdmin()`
both return `0xcfa0388f5ddf905fdc08c45c716c15dc10a14c6f`. `paused()` was false.
These observations do not complete the issuer's upgrade, mint, pause and asset
protection role audit. The quote helper pins both proxy and implementation code,
implementation address and observed administration; changes fail closed.

The WETH proxy implementation is
`0xc6b81b429797e0f555440b70cd99e032d7ae947e`. Its `l1Address()` is Ethereum
WETH `0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2`, and `l2Gateway()` is the
official WETH gateway `0x1d187c3e2da52d72bc9c41e3aba0fdfa6a7bf055`. This
implementation is also pinned before constructing an unsigned native wrap step.

## Actual route findings

[Uniswap's official deployment feed](https://developers.uniswap.org/deployments.json)
lists the Robinhood V3 factory `0x1f7d7550b1b028f7571e69a784071f0205fd2efa`,
QuoterV2 `0x33e885ed0ec9bf04ecfb19341582aadcb4c8a9e7` and SwapRouter02
`0xcaf681a66d020601342297493863e78c959e5cb2`. On-chain factory and WETH
bindings agree with these reviewed addresses.

USDG/WETH pools exist at fees 100, 500, 3000 and 10000. The best of the four
read-only exact-input quotes for **100 USDG** at the pinned block was the
500-fee pool `0x69bfaf19c9f377bb306a89aed9f6b07e2c1a8d9a`, returning
`40,816,277,314,820,045` raw WETH units. This is a conversion quote at one block,
not a promise of future execution or sufficient final LP after its Pons swap.
Pool identity, active liquidity, funded output balance, fee and quote are checked
before returning a result. The helper chooses the best actual output, rather
than assuming the lowest fee pool is best.

The independent USDG/USD round was **0.99999**, so exactly 100 USDG had only
$99.999 of source value. The actual $100 input minimum at that price rounds up
to **100.001001 USDG**. The helper's `minimum_input_amount('USDG')` calculates
this ceiling in integer token units; it does not silently treat 100 tokens as
100 dollars or waive the source minimum.

The canonical USDC supply was only **340.536993 USDC** at this snapshot. No V3
USDC/WETH or USDC/USDG pools existed at those four factory fee tiers. This bounded
search does not establish the absence of every possible venue or representation.
**USDC routing stays disabled** until a reviewed, funded route is supplied and
tested. A differently addressed token named USDC is not substituted automatically.

## Read-only implementation

`zzz_ops/activation_route.py` adds a fail-closed reader with pinned block identity,
reviewed runtime/implementation checks, token provenance, V3 binding/quote checks,
and independent feed-round validation. It never signs or broadcasts. The existing
RPC allowlist adds only the read method `eth_getStorageAt` for proxy checks.

[Chainlink's Robinhood directory](https://reference-data-directory.vercel.app/feeds-robinhood-mainnet.json)
identifies ETH/USD `0x78f3556b67e17df817d51ef5a990cdaf09e8d3a9`, USDG/USD
`0x61b7e5650328764b076a108eff5fa7282a1b9ad2` and USDC/USD
`0x9e6f4605992a899ee2999999f3ec80c41f452546`, all eight decimals with 86,400
second heartbeats. Positive, complete, nonfuture rounds within that heartbeat
are required. Actual prices replace any assumed peg. There is no independently
reviewed ZZZ feed in this helper; production outage policy and feed controls still
require review.

`quote_usdg_to_weth(amount_in, slippage_bps)` returns raw output and its conservative
minimum, source USD value, the original-source 99% final LP floor, and the
remaining loss allowance for the LP leg. A conversion floor below that total
floor is rejected. Gas is explicitly separate. **Every quote returns
`activation_ready: false`**, because final LP valuation and original source
accounting are not established by a V3 quote. Do not turn it into a live activation
button or call it an end-to-end simulated success.

`eth_wrap_step(owner, amount)` returns only an unsigned WETH `deposit()` call from
that same owner. It does not approve, swap or activate. `usdc_route_status()`
verifies canonical provenance but reports routing disabled. ZZZ token identity is
checked, while ZZZ price/route completion remains gated. Existing quotes and
unsigned steps must be refreshed and simulated against current state before any
future user signature; the saved historical research snapshot is not a live quote.

Set `ACTIVATION_RPC_URL` in the process environment to a reliable HTTPS RPC on
chain 4663, then run from the repository root:

```text
python -m zzz_ops.activation_route --symbol USDG
python -m zzz_ops.activation_route --symbol USDC
python -m zzz_ops.activation_route --symbol ETH --owner 0xYourCurrentOwnerAddress
```

The last line uses an address placeholder; replace it with the actual public
owner address. `--amount` accepts raw integer units, not a dollar string. Without
it, supported inputs calculate the current $100 minimum. `--output` can save the
read-only JSON evidence. Do not place RPC credentials in a command, source file or
committed configuration. Public RPC 403/429 responses fail closed; a successful
offline test is not proof that a public endpoint can sustain this workload.

## Atomic entry candidate and remaining qualification

An external USDG-to-WETH swap followed by ordinary pair-token entry still does
not authenticate the original USDG input or the loss spent before Vault entry.
Caller-supplied dollar values, ERC721 approvals and smart-wallet batching cannot
supply that missing provenance. The read-only quote helper therefore continues
to return `activation_ready: false`; its historical quotes do not simulate final
LP deployment or authorize a wallet transaction.

The contract candidate now implements [atomic source activation](ACTIVATION_ENTRY.md)
through `ZZZActivationEntry`, an immutable child created by the existing Pool
Registry. It does not add a replaceable seventeenth module or take NFT custody.
The current NFT owner can supply an admitted pair asset, exact native ETH wrapping,
or an admitted source with a governance-reviewed single-hop V3 route. Route records
pin router, factory, pool, ordered tokens, fee and runtime hashes; governance
appends policies and controls their enabled flag through the existing governance controller.

Entry measures exact original input and values it through the governed asset
helper before conversion. Its temporary context is armed only immediately before
one fixed Vault call, binding the owner, NFT, exact calldata, pool and pair amounts
to that original source value. Vault authenticates the context, and Registry uses
the proven source value in contribution checks. An active context mismatch reverts;
it cannot fall back to valuing only the smaller post-conversion output. The existing
Vault enforces one combined captured contribution budget (2% at current default) across conversion and final
LP deployment, for activation and later additions. Fixed recipients, exact transfers,
bounded approvals, donation isolation and nonreentrancy remain mandatory.

This implemented source path does not make the historical USDG quote a production
route admission. The real V3-to-selected-Pons execution still needs a fresh complete
fork rehearsal, actual source and ZZZ valuation review, realistic gas/strategy
tests, Robinhood Testnet wallet rehearsals and independent audit/remediation.
**USDC conversion remains unavailable** until a reviewed funded route is found,
admitted and qualified. No ticker substitution or assumed stable peg is authorized.

Reader regressions use explicit mocks; Entry unit tests and real Registry/Vault
integration tests have separate scope. The actual native/Pons custody fork suite
does not by itself prove V3 source conversion. Keep these evidence boundaries
separate in the [activation tasks](../TODO.md#task-activation-assets). This documentation
authorizes no deployment, signature or real transaction.
