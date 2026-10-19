## Royalty conversion history extension - 2026-10-19

Raw replay now recognizes the exact `RoyaltyConverted` event from the pinned
royalty ledger. The API exposes lifetime source amounts converted and ETH credited
as `royalty_conversions`; only actual `Claimed` events affect `previously_claimed`.
Complete configured same-chain predecessor replay carries both histories through
retirement cutoffs, preserving historical currencies and all past owners.
Missing history/lineage remains unavailable; invalid coverage never yields a
partial lifetime total. Existing raw logs need no reset solely because an older
decoder labelled an event unknown.

Read [the integration and recovery guide](ROYALTY_REPORTING.md) and
[scoped verification](../reports/royalty-reporting/VERIFICATION.md). Conversion is
not new earned revenue; verified gross 24h/all-time fees and USD pricing remain
separate unfinished work. Native claimable balances already include remaining
conversion credits, so consumers must not add lifetime credited ETH to them.

# Confirmed wallet inventory and lifetime claims

Updated 2026-10-15. `frontend_api/history.py` extends the unhosted
[confirmed read API](FRONTEND_API.md) using the existing event indexer's SQLite
database. It implements complete current wallet NFT inventory and cumulative
**Previously claimed** amounts per NFT/asset, including every past LP and royalty
claim paid to previous owners. It neither deploys/hosts a backend nor changes the
website's simulated actions.

## API behavior

```text
GET /v1/wallets/{nonzero-Ethereum-address}/nfts
GET /v1/nfts/{actual-decimal-uint256-token-id}
```

The wallet endpoint returns exact string `token_ids`, count, canonical NFT
address and confirmed block/hash provenance. It cross-checks the replayed count
against `NFT.balanceOf(wallet)` and every returned token against `ownerOf` at
the same EIP-1898 canonical block. Combined, those checks detect stale/omitted
wallet transfers without querying all 1,000 owners for every wallet. A genuine
empty wallet is returned only after confirmed history and `balanceOf == 0`
agree. Address zero is invalid. Callers cannot select another database,
contract, RPC, chain or arbitrary query.

The NFT endpoint adds:

```json
{
  "previously_claimed": {
    "available": true,
    "assets": [
      {"asset": "0x<address>", "symbol": "ZZZ", "decimals": 18,
       "lp_raw": "30", "royalties_raw": "7", "total_raw": "37"}
    ],
    "scope": "All-time NFT claims, including LP and royalties paid to every past/current owner.",
    "provenance": {"through_block": 123, "block_hash": "0x<hash>"}
  }
}
```

Amounts above are **raw token units**, not example dollars. The total is
`all LP Claimed amounts + all royalty Claimed amounts` for that NFT in that
**same asset**; the last claim never overwrites an earlier amount. Different
assets remain separate, including native ETH versus WETH. The totals are
associated with the NFT throughout ownership changes, not just the connected
wallet's personal earnings. Current claimable balances remain separate.

Each NFT response checks replayed owner against canonical `ownerOf`; all history
responses check replayed mint inventory against `mintedCount`, bounded to 1,000.
Underlying ledger events emitted during claim batches are counted exactly once;
`BatchClaimed` is not added as another financial amount.

The wallet list and subsequent NFT reads can select different confirmed blocks
as the chain advances. Compare their explicit provenance before combining them
into a portfolio snapshot. This change does not provide a caller-selected
historical-block endpoint or a complete multi-NFT valuation response.

Without history configuration, NFT responses explicitly return
`previously_claimed.available=false`, `assets=null` and a reason; they do not
invent zero past claims. The wallet endpoint returns 503. With history configured
but stale, incomplete, orphaned or malformed, the complete request fails 503;
no partial inventory or fallback demo totals are served. Existing no-store,
loopback Host, read-only GET and sanitized-error rules apply.

## Configuration and genuine coverage

Add this optional object to the reviewed API configuration:

```json
{
  "history": {
    "database": "/operator-owned-path/indexer.sqlite",
    "start_block": 123,
    "start_parent_hash": "0x<64 lowercase hex digits>",
    "contracts": ["0x<NFT>", "0x<LP Rewards>", "0x<Royalty Rewards>"],
    "max_events": 100000
  }
}
```

These are unusable placeholders, not deployed addresses. `contracts` must be the
**exact complete tracked list** in the indexer's cursor identity, without
duplicates, including the three pinned NFT/LP/royalty emitters. Additional
operator-reviewed tracked addresses are allowed in that exact list; their logs
are not treated as NFT claims. Addresses and parent hashes should be normalized
to lowercase before the indexer creates its cursor.

`start_block` must be the actual canonical NFT creation block, not a later
convenient checkpoint, and no later than the API deployment anchor. The service
checks its parent against RPC, requires NFT code to be absent at `start - 1`,
and verifies the pinned NFT runtime at `start`. It checks that SQLite's starting
hash is that same canonical creation block. The NFT-created royalty helper
exists in the same constructor transaction; no legitimate NFT claim or transfer
can predate NFT creation. Genesis-installed NFT contracts are not covered by
this creation-block proof.

The indexer must have processed every block through the API's exact confirmed
target. A later indexer tip is allowed, but events after the target are excluded.
The reader verifies the cursor chain/start/parent/contracts identity, complete
contiguous stored block coverage, stored parent links and target hash/timestamp.
Canonical RPC block checks run again before a successful response is released.
A reorg or provider failover onto a different chain view fails closed. The API
still reports confirmation depth only, not rollup/L1 finality.

## Replay and consistency

Every request opens SQLite with `mode=ro`, enables `query_only`, disables trusted
schema behavior and reads within **one transaction snapshot**. It neither
advances cursors nor updates/rebuilds/checkpoints the indexer. Do not use
SQLite `immutable=1` for a live WAL database: normal read locks and the writer's
WAL/shm files are necessary for consistent concurrent operation.

The reader ignores optional `event` labels and `decoded` JSON. It uses only
raw logs emitted by the exact pinned NFT or the two exact pinned reward ledgers:

- NFT `Transfer(address,address,uint256)`: exactly four topics and empty data,
  canonical address padding, a zero-address mint followed by consistent previous
  owners, no duplicate mint and no burn (the pinned NFT has no burn entrypoint).
- Both ledgers `Claimed(uint256,address,address,uint256)`: exactly four topics
  and one uint256 data word. Each claim must name a minted NFT, a nonzero payout
  recipient and an asset admitted by that particular ledger. Native address zero
  is permitted for royalties only.

Each raw log must match its stored block/transaction/log-index/emitter identity
and confirmed header; removed logs, duplicate block/log indices and transactions
assigned to multiple blocks are rejected. A royalty payout callback can
legitimately transfer the NFT **before** its `Claimed` event is emitted. The
recorded recipient therefore must not be compared to the owner at emitted-log
time; canonical contract authorization and direct payout determine entitlement.

`max_events` bounds all examined logs from those three emitters, including
unrelated metadata events, to at most 1,000,000. Exceeding it fails rather than
truncating lifetime history. Asset and collection bounds remain 32 LP assets,
17 royalty assets and 1,000 NFTs. This implementation replays history per request;
production load/cold-backfill testing and a separately reviewed incremental
checkpoint design may be needed as history grows. No history cache or supplied
aggregate is trusted as the authoritative answer.

**Trust boundary:** a complete cursor and SQLite file are not a cryptographic
proof that the RPC/indexer omitted no claim logs. Ownership receives additional
on-chain count/owner checks; historical financial totals still depend on genuine,
complete operator-maintained event ingestion. Preserve raw receipt evidence,
independently compare backfills/providers and monitor indexer identity/reorg
health. Do not use a displayed history total as claim authority: the funded
on-chain ledger remains authoritative.

## Verification and remaining scope

```sh
python -m unittest tests_python.test_frontend_history tests_python.test_frontend_api -v
```

Tests build a real SQLite database through the existing `Indexer`, then verify
past/current owners, repeated claims, separate assets/ledgers, callback transfers,
an indexer ahead of the API snapshot, ignored decoded caches, consistent reads
during a concurrent WAL commit, creation coverage, missing/orphaned blocks,
malformed/duplicate logs, bounded replay, actual loopback wallet HTTP and
post-history RPC reorg rejection. These are offline tests, not a live deployment
or independently audited history pipeline.

All-time/last-24h **gross generated fee attribution**, reward USD conversions,
production hosting/proxy/load/finality/recovery rehearsals and live website
transactions remain open. Past claim totals are not gross revenue or a yield
forecast. No public service, contract, signature or real transaction is created
by this implementation.
