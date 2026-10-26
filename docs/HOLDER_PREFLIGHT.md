# NFT-holder preflight for collection replacement

Moving an NFT to a new collection address can strand it in an old escrow whose
withdrawal logic only recognizes the original collection. The handoff preserves
owners exactly; it does not call receiver hooks or rewrite owners. This procedure
inventories that risk before [whole-collection replacement](CANONICAL_HANDOFF.md).
It does not apply to ordinary LP rebalancing or moving LP between pools.

The current collection handoff is same-chain canonical V4 with a compatible
accounting 3 successor. An external custody exit can send assets for a later
token/chain migration, but does not automatically preserve canonical NFT owners
or reward ledgers on that new chain. This inventory does not add bridge or
post-halt recovery capability.

## Produce a pinned inventory

Use [the configuration template](../config/holder-preflight.example.json). Replace
every null source value with reviewed deployment information: chain ID, exact
confirmed block number/hash, chain-specific confirmation depth, controller/NFT
addresses and their Ethereum Keccak-256 runtime code hashes. Confirmations are an
operating policy, not proof of finality. The tool requires a sealed source in active
or frozen canonical state. Empty/unconfigured templates fail closed.

Optionally provide `destination` with the same four fields as `source`. That
checks a distinct sealed inert importer and bidirectional NFT/controller bindings.
It **does not validate the complete successor, its incoming-source commitment,
economic code, transport or backing**; those remain the handoff procedure's duties.

Provide the read-only RPC URL in `POPL_READ_RPC_URL`, outside Git. The tool never
uses a private key, signs or sends transactions. From the repository root:

```sh
python scripts/inventory-nft-holders.py scan --config holder-preflight.json --first 1 --limit 50 --output holders-001.json
python scripts/inventory-nft-holders.py scan --config holder-preflight.json --first 51 --limit 50 --output holders-051.json
python scripts/inventory-nft-holders.py summarize holders-001.json holders-051.json --output holder-review.json
```

Continue through the actual `minted_count`, up to 1,000. Use the **same explicit
block configuration for every page**. All calls/code reads use its canonical block
hash; the tool rechecks the header and confirmation depth after reading. Each page
is limited to 50 NFTs, 60 seconds and bounded RPC work. If a slow provider exhausts
the budget, reduce the page size and retry missing pages at the same block. Do not
mix observations from different blocks or select a new block without rescanning.

Pages group observations by owner. The summary rejects duplicate tokens/ordinals,
mixed snapshots, inconsistent owners and changed checksums, and lists every missing
ordinal. Missing coverage remains explicitly incomplete. A failed read writes no
successful page; output paths must be new so failed retries cannot overwrite older
observations. Scan exit 0 means a page was saved. Summary exit 2 means incomplete
inventory or unresolved code-bearing owners; exit 0 only means neither was found.
Exit 1 means the operation failed. **None is release approval.**

## Resolve each flagged owner

All contracts and code-bearing delegated accounts are unresolved by default.
There is no automatic exemption for a multisig, an ERC721Receiver implementation
or a marketplace name. Review each owner and exact old/new collection pair:

| Review | Required evidence / action |
| --- | --- |
| Ownership and authority | Identify the authorized escrow beneficiary or wallet operators and the current withdrawal/release permissions. No-code addresses still require ordinary custody/key review; absence of code does not prove access to keys. |
| Implementation and mutability | Inspect proxy implementation, beacon/admin, delegation targets and upgrade authority. Runtime hash alone does not bind these. Record addresses, storage/code observations, reviewer and block. |
| Exact replacement behavior | Rehearse receipt, NFT transfer/release and LP/royalty claims against the exact replacement address/code. Test collection allowlists, hardcoded addresses, callback expectations and any marketplace or custody adapters. ERC165/receiver support alone is insufficient. |
| Incompatible or unresolved escrow | Have its authorized user withdraw to an address they control **before freeze**, using the escrow's existing supported procedure. Cancel preparation if its workflow needs ordinary economic operations. Do not substitute an administrator-selected owner. |
| Listings and approvals | Cancel obsolete listings as needed, notify marketplaces, prepare new collection recognition and update indexing. ERC721 approvals are not imported; never grant replacement approvals automatically. |

Store rehearsal receipts/simulations and reviewer decisions in the release evidence,
linked to the owner, held token IDs and exact successor. The tool deliberately
does not accept an unchecked “compatible” flag that converts this into approval.
Page checksums detect accidental edits, not forged provider or local evidence.
Use independently trusted RPC/code review for high-value migrations.

## Freeze, final review and recovery

1. Run the initial complete inventory while owners can still move their NFTs.
   Resolve every code-bearing owner or postpone the operation.
2. Follow the complete handoff preparation/reveal/custody procedure. After ownership
   freezes, create a **fresh complete inventory at a confirmed frozen block**.
   Compare it with the reviewed holders: transfers and new mints before freeze can
   introduce new owners. A planning snapshot cannot stand in for this final scan.
3. Recheck canonicality, freeze/abort state, exact successor commitments, mutable
   escrow implementations and all review evidence immediately before committing.
   Inventory completion does not verify balances/backing or approve retirement.
4. If an incompatible holder is found after freeze, do not commit. Use the supported
   fully funded abort/return/`finishAbort` sequence, then let the authorized holder
   withdraw and restart review. A partial abort does not unlock ownership. A failed
   external dependency can block restoration; no universal recovery is promised.
5. After commit, the old source cannot be revived. Verify the new owner can claim
   and release the NFT, publish collection cutover notices, switch reviewed service
   bindings and verify late royalty forwarding. Keep both inventories and receipts.

The implementation and [local verification](../reports/holder-preflight/VERIFICATION.md)
do not qualify any actual escrow or marketplace. No deployed PoPL inventory was
available for a live rehearsal in this change. External custody/redeployment is
not qualified by this same-chain owner inventory.
