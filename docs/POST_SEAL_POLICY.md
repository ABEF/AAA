# Post-seal configuration and public-chain rehearsals

Decision recorded 2026-10-24. Routine operating settings should remain configurable
after sealing. This is a pre-seal design requirement, not a claim that all of the
controls below are implemented. The [central Todo](../TODO.md#task-post-seal-configuration)
owns completion status. No public deployment, transaction or signer extension is
authorized by this document.

## Configuration boundary

**Current policy, 2026-10-24:** [Typed v4 conversions](TYPED_V4_ROUTES.md) and
[governed execution-loss limits](EXECUTION_LOSS_POLICY.md) are implemented in the
undeployed candidate. Defaults are 2% contribution, 1% conversion and 3% maintenance;
immediate governance may set each category up to a hard 10%. Existing stricter
venue/caller minima remain. Pending normal custody approvals retain their original
absolute floor. Earlier fixed-cap or v3-only descriptions below retain their
historical/default scope. Actual routes, services and independent audit remain open.



| Category | Requirement | Current boundary |
| --- | --- | --- |
| Routine operations | Change keepers/guardians, pause/reopen activity, tune supported LP ranges, explicit price orientation, approved two-width keeper selection, triggers, cooldowns and operational limits within reviewed bounds. | Role, pause and pool configuration controls exist. `Buyback.setOperatingTradeUSD` sets a USD18 execution ceiling from zero through immutable `maxTradeUSD`; zero stops buybacks before prices or reserves are queried. |
| Assets and conversions | Enable/disable/re-enable native ETH and the fixed pre-seal ZZZ input; rotate reviewed routes when liquidity changes. Marketplace royalty admission is separate. | No third contribution currency or post-seal ZZZ replacement is supported. Bind matching contribution/normal-exit ZZZ identities before sealing; issuer migration uses custody exit and a fresh reviewed deployment. Entry and LP/royalty converters retain pinned append-only typed v3/v4 route controls. Native v4 output needs no wrapper; v3 converters keep their own wrapper checks. Real qualification remains open; routes do not add a new input identity or algorithm. |
| Pools and pricing | Change the sole contribution pool, reviewed two-source USD policies and supported strategy settings through existing immediate governance. | `Oracle.setDualFeed` appends a policy with two distinct source/independence identities, runtime pins, per-source ages and 0-500 bps disagreement. Both sources must pass; old `setFeed` is not a current callable function. No missing-source/spot/peg fallback. Entry freezes prices and operating limits before transfers/conversion; new settings cannot replace that captured basis. Live source independence/proxy/depeg/gas qualification remains open. |
| Randomness operation | Tune future callback gas and confirmations within contract and actual provider bounds; preserve pending requests and ordered draws. | After initial configuration, `NFT.setRandomnessRequestSettings` changes only future confirmations (3-200) and callback gas (200,000-10,000,000). Coordinator, key/gas lane, subscription and payment mode stay fixed. It cannot repair or reroll an old request. |
| Services | Rotate qualified RPCs, hosting and compatible API/keeper settings without resetting transaction journals or changing deployment identity. | Off-chain configuration does not alter sealed bytecode. Keep the shared signer Anvil-only and public `DEPLOYMENT` null until separately authorized and qualified. |
| Economic rights and safety | Preserve supply/rarity inventory, revealed traits, ownership, earned rewards, backing, the 80/10/5/5 allocation and approved execution-loss limits. | No reset, confiscation, arbitrary sweep, generic executor or unbounded upgrade is introduced. A reviewed replacement uses the explicit handoff and preserves rights; it is not a way to erase them. |

Adding a route or feed is security-sensitive even when it is configurable.
Governance retains immediate authorization with no new waiting period. Every
control still needs an explicit caller, bounds, events, dependency checks,
stop/reopen behavior and old-transaction/pending-state handling. A global pause
does not bypass preparation or terminal canonical locks.

The [bounded operating-control candidate](../reports/post-seal-controls/VERIFICATION.md)
adds these two setters with previous/new-value events and immediate governance.
They work during an ordinary pause, but reject preparation, canonical lifecycle
locks and reentry. A successor reviews its own operating settings; these are not
imported NFT economic entitlements. Actual provider acceptance can be narrower
than the contract bounds and still needs independent qualification.

For randomness observations, the blocked production template now distinguishes
`immutable_provider_configuration: true` from the exact mutable field list
`["requestConfirmations","callbackGasLimit"]`. The old ambiguous
`immutable_configuration` flag is rejected in that NFT record. Capture current
getters and retain original request transactions when reviewing pending draws.

Defaults remain **2% contribution / 1% conversion / 3% maintenance**, gas separate. Governance may now change each category through the [bounded execution policy](EXECUTION_LOSS_POLICY.md), maximum 10%. The earlier fixed-cap requirement is superseded.
The selected pool's observed approximately 1.101% swap fee means it is not a
qualified full-balance conversion route at reference prices. Require a cheaper,
independently reviewed route; until then keep earned source balances backed and
report conversion unavailable. Do not silently increase the limit or substitute
pool spot prices for independent valuation.

## Pricing implementation and source qualification

[Dual-source pricing and factual LP checks](PRICE_SECURITY.md) are implemented as
an undeployed pricing-V2 candidate. Governance can replace the reviewed source
pair, ages and disagreement within explicit bounds after sealing; the Oracle-created
pricing companion remains fixed and holds no funds. Versioned inventories and
backend configurations require explicit pricing V2 and all 15 helper bindings.
A new source policy is an operational change requiring fresh review/observations,
not a rewrite of NFT rights or historical price profiles. No actual ETH/ZZZ source pair or optional admitted royalty/conversion-asset
source pair is qualified. Failure of either source stops affected price-dependent
work; raw funded claims and explicit raw custody paths retain their own rules.

## Native implementation versus configurable policy

The native V2 candidate implements actual ETH custody, fee indices, principal
return and same-chain canonical funding. Its schema rejects old V1 handoff codecs;
existing WETH deployments/journals are not upgraded by changing configuration.
Record exact version 2 Vault/runtime pins in fresh API/keeper profiles and retain
per-deployment historical currency semantics. The existing 8902 fixture and saved
transactions remain unchanged; the public website deployment stays null and its
V2 profile remains to be qualified.

Atomic pool moves currently require identical actual ordered currencies. ETH and
WETH are distinct: moving between those pools needs an explicit reviewed boundary
that is not implemented. Admitting a WETH destination or changing a route cannot
supply missing code. A separately approved external custody exit/manual conversion
and actual funded local completion is a different, governed path. Typed v4
conversion is implemented with [scoped qualification limits](TYPED_V4_ROUTES.md). The two bounded controls are implemented as a
candidate; they do not qualify actual VRF, routes, inventory or services.

See [native verification scope](../reports/native-eth-port/VERIFICATION.md) for the
candidate and remaining gates; this policy is not a live release approval.

## Testing with real funds on Robinhood

Use a **separate, clearly named mainnet rehearsal deployment**, dedicated disposable
funds and reviewed per-operation/campaign limits. Preserve production economics
and guards when qualifying production behavior. A reduced-minimum test build is
a different candidate and does not verify the unchanged $100 activation rule.
The current $1 rehearsal is local-only. Production mint is intended for OpenSea;
direct local mint evidence does not qualify an OpenSea primary mint.

Before any operator-run public transaction, record exact source/runtime/configuration,
chain, asset/venue/feed/provider identities, roles, funding and actual signer
permissions. Simulate exact calldata and retain receipts and balance/liability
assertions. Real swaps create fees only according to actual venue execution;
funded royalty distribution tests and genuine marketplace royalty receipt tests
must be identified separately. This design discussion does not approve public
signing, deployment, sealing or use of real funds.

After the campaign:

1. Stop new mints with `NFT.setMintPaused(true)`, disable affected contributions
   and pause economic work as appropriate. Reconcile every submitted transaction.
2. Use the approved paused custody exit to close attributed LP principal if the
   venue and assets remain usable. Normal all-ZZZ and explicit raw exits have
   different guarantees; a failed normal exit never selects raw mode automatically.
   The native-accounting V2 candidate sends actual ETH/ZZZ in a raw exit without
   calling WETH. Core/token runtime bindings, usable settlement and a recipient
   that accepts ETH remain required; wrapper independence is not a guarantee
   against every external failure. See [native scope](NATIVE_ETH_ARCHITECTURE.md).
3. Claim funded rewards as their current NFT owners. Account separately for
   compounding/buyback reserves, royalties, rounding dust, mint payments and gas.
   A principal exit does not empty every contract or erase any liability.
   `RoyaltyRewards.exitCustody` preserves liabilities and is not a settlement/reset.
4. Archive manifests, journals, receipts, final balances and remaining obligations;
   remove rehearsal addresses from active service/UI configuration. Public-chain
   and marketplace history remains. No public burn/reset or standalone deployment
   retirement function exists; canonical retirement requires an actual checked,
   funded successor handoff and preserves economic rights.
5. Use a fresh, separately reviewed deployment for the final collection. It has a
   different address/collection identity. Rehearsal NFTs do not become final NFTs
   automatically, and already spent gas, swap fees, losses or burned assets cannot
   be refunded by a reset.

Do not admit unrelated public holders to a disposable rehearsal. If outside holders
or unresolved liabilities exist, stopping services does not remove their rights.
There is no guarantee that a failed token, pool or external custody recipient
will permit full recovery. Do not add a production deletion/sweep backdoor to make
test cleanup easier.

## Review scope

This policy distinguishes implemented candidate behavior from unimplemented
operating controls and external qualification. Source-bound native evidence is
recorded separately; earlier WETH reports retain their original scope. Current controls were
read in `ZZZAccessController`, `ZZZNFT`, `ZZZActivationEntry`, `ZZZRoyaltyConverter`,
`ZZZLPRewardConverter`, `ZZZBuyback`, `ZZZMigration`, `ZZZVault` and
`ZZZCanonicalHandoff`. Updating this policy performs no public transaction,
service action or change to existing chain state. Any later setter/executor requires focused tests for its
changed behavior, code-size checks and refreshed operator/inventory guidance.
