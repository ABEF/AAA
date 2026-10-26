# Local Position and direct governance profile

The undeployed candidate uses `ACCOUNTING_VERSION() == 3`,
`GOVERNANCE_VERSION() == 2` and canonical schema
`ZZZ_CANONICAL_SAME_CHAIN_NATIVE_LP_ONLY_V4`. Routing/pricing remain 2,
review-policy 1 and fee-intake 1. HTTP read schema 2 retains decimal-string amounts
and named statuses; its deployment configuration explicitly selects accounting 3.
These are source changes for a **fresh deployment**, not an upgrade to Anvil or
any existing contract, journal, database or website configuration.

## Eight actual Position fields

| ABI word | Meaning |
| --- | --- |
|0 `poolId`|Admitted current pool identity; its immutable key supplies currencies.|
|1 `lpTokenId`|Actual shared Uniswap position, or zero when none is deployed.|
|2 `idle0`|Attributed first-currency principal held by the Vault.|
|3 `idle1`|Attributed second-currency principal held by the Vault.|
|4 `depositUSD`|Historical contribution mark, not a guaranteed current USD floor.|
|5 `centerX96`|Recorded range reference used by maintenance.|
|6 `lastRebalance`|Last rebalance timestamp.|
|7 `status`|0 None,1 Active,2 Outbound external custody,3 Dormant,4 Parked.|

There are no per-position home-chain, home-Vault, receiver, home-currency or
location fields. A pinned current Vault operates locally; module authorization,
actual venue ownership/key/ticks/liquidity, balances and chain/deployment binding
still establish custody. Removing duplicate provenance does not remove those
guards. `canonicalChainId` and canonical predecessor identity remain deployment
domain checks, not satellite or cross-chain liquidity features.

The pure [codec](../zzz_ops/position.py) selects the exact row length/status map
from the declared profile; it never guesses from return length. Keeper and API
retain separate 15-word historical codecs for accounting1/2. New rows cannot be
labelled as old ones, old rows cannot be imported into V4, and a version change
cannot repair or upgrade a saved journal. Canonical group rows are 384 bytes;
legacy/trailing rows reject before import writes. Complete record ordering,
source authentication, backing and funded-abort rules remain.

## Direct governance

The selected multisig calls the actual module with exact calldata/value. Access
has no scheduler, operation timestamps, proposer/executor/canceller roles,
generic call executor or ETH-receiving hook. The wallet's own signatures and
nonce policy authorize execution. `canConfigure` permits temporary bootstrap
before seal and the selected governance wallet afterward, only in the allowed
operating lifecycle. Guardian remains pause-only; keeper remains bounded
maintenance. Neither gains principal custody by its role alone.

Governance changes use `proposeGovernance(candidate)` and the candidate's
`acceptGovernance()`. There is no delay; acceptance protects against losing
authority through a mistyped address. A zero proposal cancels. Preparation and
frozen/terminal handoff states block handover. Keeper, guardian and immutable
mint recipient do not rotate automatically. Review the new wallet's actual
signers/threshold and configure separate roles deliberately.

The [operator manual](OPERATOR_MANUAL.md) owns exact procedures. Old schedule/
execute recipes apply only to old controllers and must not be used for profile3.
Only 16 supported core modules may be bound; unknown and retired identities
reject. Sealing permanently clears bootstrap and prevents module rebinding.

## Retained rights and boundaries

Activation/growth accept native ETH or the single fixed ZZZ, with $100 / $5 minima,
two-source USD checks, actual added LP and caller-bound execution limits. Every
admitted contribution/maintenance pool must contain that same ZZZ. Native ETH
and WETH are distinct; WETH/ZZZ remains a possible reviewed future ERC20 pool,
not another permitted user input. The selected market remains native ETH/ZZZ.

80/10/5/5 LP allocation, equal active membership, separate rarity-weighted
royalties, funded claims, transfer-carried unclaimed rights, range/idle controls,
same-pair moves and explicit normal/raw external custody remain. No holder
redemption or arbitrary sweep is added. Zero-asset Membership/NFT codecs retain
record migration but expose no asset-transfer/backing hooks.

There is no integrated bridge or cross-chain NFT/ledger transport. An external
custodian can exchange/bridge outside the protocol, with accepted counterparty
risk. Normal recovery requires the original actually sent currencies. **Do not
irreversibly exchange/burn the old token assuming fresh deployment automatically
relocates existing NFTs or accounting.** An issuer/chain cutover needs a separately
reviewed continuity plan before exit; no such universal cutover is qualified.

Stablecoin/WETH royalty receipts and cheaper approved conversion routes remain
separate from activation support. Removing those settlement paths would discard
required currency handling, not simplify obsolete activation code. Historical
event readers retain old layouts without re-enabling old contracts.

The public website remains a simulation, its deployment null and signer
Anvil-only. Its previously published native2 integration is not silently relabelled
as profile3; real native3 wallet integration and service/marketplace qualification
remain release work. See [review](../reports/architecture-pruning-20261025/REVIEW.md),
[verification](../reports/architecture-pruning-20261025/VERIFICATION.md) and
[Project Todo](../TODO.md). Production is NOT APPROVED.
