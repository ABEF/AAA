# Bounded LP and royalty claim batching

`ZZZNFT` creates one immutable `ZZZClaimRouter` alongside its royalty ledger.
This optional helper lets the website request several NFT/asset claims, including
LP rewards and NFT-sale royalties, in one owner transaction. It does not activate
NFTs, harvest LP fees, redeem principal, bridge assets or
convert currencies. Only already allocated LP balances are claimable; royalty
claims retain the ledger's existing admitted-receipt synchronization behavior.

## API and limits

Read `ZZZNFT.claimRouter()`; independently verify the canonical NFT and controller
bindings, deployed bytecode and immutable endpoints before using it. The router's
`access()`, `nft()` and `royalties()` getters identify those fixed bindings. Its LP
ledger is resolved solely through the canonical controller's sealed `REWARDS`
module. There is no owner/admin-selected router replacement or arbitrary target.

```solidity
struct Claim {
    uint256 nftId;  // Actual token ID, not its mint ordinal/display label.
    address asset; // Native ETH is address(0) in both current reward ledgers.
    bool royalty;  // false = LP rewards; true = NFT-sale royalties.
}
function claimBatch(Claim[] calldata claims) external returns (uint256[] memory amounts);
```

- A batch contains **1 to 32 claim operations**, including both ledgers and all
  selected assets/NFTs. This is not 32 NFTs multiplied by every admitted asset.
  One NFT's three assets across two ledgers already uses six operations.
- The caller must currently own **every selected NFT**. ERC721 approval is not
  claim authority. Third parties cannot trigger another owner's claim or receipt
  synchronization through this router. The controller must be sealed and bind
  this exact NFT as its canonical `NFT` module.
- Duplicate `(nftId, asset, royalty)` entries are rejected. The same asset/NFT in
  the two distinct ledgers is valid. Empty or oversized arrays are rejected.
- Results follow input order in **raw asset units**. Never sum ETH, ZZZ, USDC or
  other token amounts without a separately labelled, verified valuation layer.
- A failure rolls back the **entire batch**, including previous payouts, index
  changes and NFT transfers made by payout callbacks. The frontend must simulate
  the exact batch, estimate gas, omit failing/unsupported entries and chunk larger
  portfolios. Partial success or automatic failure-skipping is not implemented.

For example, two NFTs each claiming ZZZ LP rewards, ZZZ royalties and native ETH
royalties require six entries and one transaction. The router itself takes no
value, approvals or payout-recipient parameter. Each ledger transfers directly
to the authenticated current owner and emits its original `Claimed` event;
the router adds `BatchClaimed(owner, operations)` for successful batches.

## Authority and callback safety

Existing owner-only direct `claim(id, asset)` functions remain available. Both
ledgers add `claimFor(id, asset, owner)`, callable only by the exact immutable
router returned by their NFT. Each repeats the current-owner check and pays that
owner directly. The router also checks ownership before any payout and again
immediately before every operation, since a prior native/token callback may
transfer a later NFT.

The router and both ledgers have independent reentrancy guards. A rejecting native
recipient or nonconventional token can fail its batch; the owner can still select
other working assets in a separate transaction or use the direct claims. Claims
do not depend on strategy pause, LP valuation, current venue availability or
migration execution. They still depend on ownership/share/membership accounting,
the selected ledger, the selected asset and its backing being available.

No ETH receiver, token/NFT custody interface, arbitrary call, delegate call,
withdrawal, administrator rescue or approval path is provided. Forced ETH or
direct unsolicited token transfers cannot be recovered; they are never counted
as funded claim rewards. Do not send assets to the router.

## Website and production boundaries

“Claim all” means the connected owner's chosen, funded operations within these
bounds, possibly split into multiple transactions. An indexer must retain LP and
royalty `Claimed` events separately, including transfers and reorgs, to calculate
cumulative previously claimed totals. This helper does not store lifetime dollar
totals or infer historical token prices. The website remains a simulation until
the reviewed deployment, verified addresses, live reads and wallet transaction
flow are integrated.

The contract repository now includes opt-in [unsigned claim preparation](FRONTEND_TRANSACTIONS.md).
It validates a selected batch and simulates exact router calldata at one confirmed
canonical block. It neither requests approval nor signs/broadcasts. Fresh wallet
account/chain/calldata validation, gas estimation, user confirmation and receipt
handling remain frontend integration work.

The local regression suite uses the real NFT, router and reward ledgers with a
mock share vault, mock exact-transfer assets and mock VRF. It covers authorization,
mixed assets/NFTs, transfer ownership, atomic failures, native callbacks, refunds,
duplicate/size bounds, direct claim compatibility, funded conservation and a
32-operation gas workload. These checks do not establish production token safety,
target-chain gas headroom, real VRF support or independent audit approval. Record
fresh compilation/size, full regression, source-bound static analysis and staged
operating evidence under the [transaction integration task](../TODO.md#task-transaction-ui) before deployment approval.

Historical router test/size measurements are recorded in [the original feature evidence](https://github.com/ABEF/AAA/blob/a5fad3e744da3d2ecbde01611c3f0b5371736784/docs/CLAIM_ROUTER.md); they are not current target-chain gas qualification. Use actual current compilation/constructor inputs and simulation.
