# Direct ETH/ZZZ activation Entry

Fresh **Entry-routing3 / pricing2 / reviewed-policy2**, over unchanged accounting6,
ProtocolPolicy1, Portfolio2 and canonical V6. The release inventory is schema9
with20 helpers. This is undeployed source; historical routed Entry2 deployments,
API configurations and signed/pending records retain their original ABI.

`ZZZActivationEntry` accepts native ETH or the one fixed ZZZ, already one of the
selected pool's currencies. It forwards that exact input to the fixed Vault.
**There is no pre-Vault conversion, route catalogue, route toggle or Entry-owned
v4 executor.** The Vault still performs reviewed ratio balancing and actual LP
placement. Separate earned-LP and royalty converters remain.

## Exact owner transaction

Call `executeReviewed(Request,uint16 maximumLossBps,bytes32 expectedContributionPolicy)`
from the NFT's current owner, with this seven-field static tuple:

| Field | Type and meaning |
| --- | --- |
| `nftId` | `uint256`: canonical hashed NFT ID, not its ordinal. |
| `poolId` | `bytes32`: exact selected contribution pool; growth uses the NFT's existing pool. |
| `sourceAsset` | `address`: zero for native ETH, otherwise the fixed ZZZ. Must already be a pool currency. |
| `amountIn` | `uint256`: exact positive raw source units/wei. Preparation bounds it below2**128. |
| `minimumLiquidity` | `uint128`: positive marginal LP-unit minimum, not USD or NFT shares. |
| `deadline` | `uint256`: Unix seconds, now through now+600. Reviews expire sooner. |
| `increase` | `bool`: false activation, true growth of an activated NFT. |

There is no `routeId` or `minimumOut`. The selector differs from the old
nine-field tuple. `ENTRY_ROUTING_VERSION()` returns3; `REVIEW_POLICY_VERSION()`
and Pricing's `ENTRY_REVIEW_VERSION()` remain2 because captured review semantics
are unchanged. Old selectors/getters do not have a compatibility fallback.

`maximumLossBps` captures the caller's allowed contribution budget,0..1000.
The governed policy may tighten before execution but cannot widen beyond that
review. `expectedContributionPolicy` is the nonzero exact
`ProtocolPolicy.entryFingerprint()` at the reviewed snapshot; revisions before
or during callbacks reject. It is not an arbitrary operator reviewHash.

Native ETH requires exactly `msg.value=amountIn`, with no approval. ZZZ requires
`msg.value=0` and only the chosen amount approved to Entry. Entry approves the
fixed Vault for exactly that amount, clears approval afterward and preserves
pre-existing balances. Unsolicited plain ETH transfers are rejected; forced ETH
is not caller input or spendable surplus. No sweep, rescue or arbitrary recipient.

## Preserved economic and callback checks

Default source-value minima remain100USD activation/5USD growth, future-governed
within policy bounds and subject to stronger pool minima. Dual-source agreement
defaults3%. Source/pair USD bounds and operation limits freeze before token pulls
or approvals can call external code. Original source value is never supplied by
the caller or inferred from an intermediate conversion.

Vault checkpoints incumbents, balances only entrant funds, harvests fees generated
by that swap, increases MAIN only, verifies marginal physical deployed LP/net
NAV and issues shares. It neither changes residual liquidity nor recentres or
resets the rebalance clock. Default contribution loss2%, ceiling10%, gas separate;
idle, known fees, additional loss and stronger caller/venue minima remain distinct.
Direct input can still require a guarded balancing swap and can still fail.

Entry's temporary context binds owner/NFT/pool, exact pair amounts, original USD
and exact Vault calldata. It is inactive during initial approval and cleared
before reset callbacks. Current-owner, captured policy/price and exact baseline
checks survive the complete operation. Failure reverts the input transfer,
balancing and LP changes together; network gas is still spent. A prior separately
confirmed wallet approval remains an approval, not activation.

`SourceContributed` retains its event wire for history: output equals sourceAsset
and outputAmount equals amountIn in routing3. These fields no longer imply an
Entry conversion. [Preparation](ACTIVATION_PREPARATION.md), [routing boundaries](ACTIVATION_ROUTING.md),
[current change/evidence](../reports/direct-entry-v3-20261103/REVIEW.md).

New runtimes/configuration require review and an authorized deployment/rollout;
no existing contract, journal, service, site or public signer is upgraded here.
