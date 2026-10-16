# Feature and evidence reference

Reviewed 2026-10-16 against published source `e35663c7edaef4bf66efa43d0c7e15d45ca2751b`.
The contracts remain undeployed and the website remains a simulation.
Implemented means the behavior exists in source; it does not mean production
services, deployment or independent audit are approved.

**All task status, remaining work and acceptance criteria live in the
[central Todo](../TODO.md).** This page describes published capabilities and their
evidence. The [release approval record](RELEASE_CHECKLIST.md) records the final
decision for an exact release, not development progress.

## Published capabilities

| Area | Behavior available in published source | Reference |
|---|---|---|
| Mint and identity | Dormant mint costs exactly 0.05 ETH and adds no LP. The fixed 1,000 supply uses canonical hashed token IDs, separate mint ordinals and exact eventual 600 Commun / 300 Rare / 100 Legendary quotas. Ordered VRF draws select existing artwork without replacement; no administrator reroll exists. | [NFT metadata](NFT_METADATA.md), [Vault](../src/ZZZVault.sol) |
| Activation and additions | Immutable Registry-created Entry binds the original source value, current owner and exact Vault call. Activation starts at $100 gross value; conversion and marginal LP deployment share a 1% execution/undeployed budget, with network gas separate. Governed asset and route admission does not itself qualify a live route or price feed. | [Activation Entry](ACTIVATION_ENTRY.md), [asset policies](../src/ZZZActivationAssets.sol) |
| Shared LP custody | Many NFTs own nonredeemable shares of one physical LP per pool/strategy. Maintenance acts on the shared bucket. The cap is four historical local buckets, including imports; all 1,000 NFTs can share the initial pool. | [Architecture](ARCHITECTURE.md), [scale/capacity verification](../reports/nft-rights-audit/VERIFICATION.md#execution-gas-and-capacity) |
| LP revenue | Actual admitted receipts allocate 80% by LP shares, 10% equally among activated NFTs, 5% to the earning bucket's compounding reserve and 5% to buyback/burn. Rarity does not affect LP rewards. Documented raw-unit dust and receipt-time membership rules apply. Creator inboxes receive funds; they cannot enforce a creator's payment obligation. | [Economics](ECONOMICS.md), [external funding](EXTERNAL_REWARDS.md) |
| Royalties and claims | ERC-2981 requests 5%; actual eligible receipts use a separate immutable ledger at activated rarity weights x1/x2/x3. Current owners claim; unpaid balances follow the NFT. Direct ledger claims and an immutable 1-32-operation mixed claim router exist. Marketplace payment is not enforced. | [Claim router](CLAIM_ROUTER.md), [ownership review](../reports/nft-rights-audit/REVIEW.md#identity-and-ownership) |
| Artwork and metadata | Eight colors, 58 palettes and four patterns produce 2,784 evolution states for the fixed inventory. Current marked LP value selects the stage; a market decline can lower it without removing activation rights. Bounded ERC-4906 notifications and an optional keeper watcher exist. The prepared artwork bundle is not a published immutable CID. | [Metadata](NFT_METADATA.md), [artwork publication](ARTWORK_PUBLICATION.md) |
| Venue and recovery boundaries | The selected native-ETH/Pons adapter separates venue keys from WETH accounting and rejects unrelated native/hooks. Pause, timelocked asset/wrapper/sequencer policies, close-only custody parking and guarded resumption exist. They do not guarantee recovery from every external dependency failure. | [Selected market](ROBINHOOD_POOL.md), [parking](CUSTODY_PARKING.md), [recovery model](CHANGE_AND_RECOVERY.md) |
| Read services and measurements | The confirmed read API exposes NFT ownership and funded LP/royalty balances. Optional complete indexed history supplies wallet inventory and cumulative raw claims. Route/revenue measurement tools exist. Gross generated-fee/USD history and hosted live website transactions are not supplied by those balances. | [Read API](FRONTEND_API.md), [history](FRONTEND_HISTORY.md), [revenue measurement](REVENUE_SHARE.md) |
| Keeper and operating tools | Bucket discovery, guarded maintenance, serial budgets, durable pending recovery, confirmed receipt/nonce checks, metadata watching, health checks and exclusive recovery snapshots exist. Isolated Anvil/systemd rehearsals are recorded; production signing and target-chain qualification are separate. | [Recovery runbook](KEEPER_RECOVERY.md), [rehearsals](KEEPER_REHEARSALS.md) |
| Future migration | Timelocked routes and whole-bucket migration/parking preserve canonical NFT rights and funded-liability barriers. Identity reservation does not reserve destination capacity. Canonical NFTs and claim ledgers do not automatically migrate with LP custody. | [Migration source](../src/ZZZMigration.sol), [recovery model](CHANGE_AND_RECOVERY.md) |

The [component assessment](../reports/nft-rights-audit/IMPLEMENTATION.md) gives
module-level boundaries. All remaining qualification, implementation and decision
requirements are maintained once in the [Todo](../TODO.md), including the
[migration gate](../TODO.md#task-destination-slots) and
[canonical-chain recovery decision](../TODO.md#task-security-chain-recovery).

## Evidence and its limits

- The [NFT-rights verification](../reports/nft-rights-audit/VERIFICATION.md)
  records 531 offline Solidity passes, zero failures and two intentional fork
  setup skips, plus 23 normal object-size gates and 29 production source
  bindings. The 1,000-NFT scenario and extended dual-ledger invariant use explicit
  local venue, authority, price and VRF fixtures.
- The same report identifies reused source-bound evidence: 33 prior fork cases
  (24 selected native/Pons and nine hookless) and 220 internally reviewed Slither
  findings. Those were not fresh runs in the NFT-rights review and are not an
  independent audit.
- [Keeper operating evidence](../reports/keeper-rehearsal/README.md) records
  runtime revision `089d391`, 209 Ubuntu tests and 14 local process rehearsals,
  plus isolated server crash/restart and snapshot restoration. It does not prove
  a multi-day soak, production RPC/fees or physical host-loss/key rotation.
- The 628-pass portable Python receipt in the NFT-rights report covered a broader
  local working tree, including unpublished work. It is not evidence that those
  unpublished features exist in this GitHub revision. Exact-release CI and
  production approval belong to the [release record](RELEASE_CHECKLIST.md).

Historical reports retain their original revisions and assumptions; they are not
maintained as additional task lists.

## Local unpublished candidates

The local working tree also contains unsigned mint/mixed-claim preparation and
HTTP handling, final read freshness/depth checks, canonical-hash activation quote
hardening, and bounded fork-runner process/timeout cleanup. These are distinct
from the published read API and contract claim router. This page does not link
to their unpublished files or describe them as shipped features.

Publication/review and integration are tracked under
[unsigned actions](../TODO.md#task-unsigned-actions),
[activation quotes](../TODO.md#task-activation-quotes),
[read API](../TODO.md#task-read-api) and
[mainnet-fork qualification](../TODO.md#task-mainnet-fork).
No candidate signs, broadcasts or makes the simulated website live merely by
being saved locally.

## Moved task links

<a id="todo-to-turn-the-website-flows-into-real-transactions"></a>
Website transaction work is now maintained in the central
[wallet task](../TODO.md#task-wallet),
[unsigned-action task](../TODO.md#task-unsigned-actions) and
[activation-quote task](../TODO.md#task-activation-quotes).

<a id="todo-before-enabling-real-bridging"></a>
Future bridge work is now maintained in
[destination capacity](../TODO.md#task-destination-slots) and
[bridge operation](../TODO.md#task-bridge-operation).

<a id="todo-before-a-funded-initial-launch"></a>
Initial-launch acceptance and final approval are tracked in
[audit and release](../TODO.md#task-audit-release).
