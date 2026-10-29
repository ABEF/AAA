# Confirmed collection positions and attached LP

The backend supports explicit fresh accounting4/custody3/canonical holder-exit V5
and reviewed historical codecs. The separately served poplint website remains
accounting3/canonical V4; native2 and other local profiles remain historical.
Backend support does not upgrade a browser reader or its deployment manifest.
Public configuration stays disabled until matching readers/services are reviewed.

The read API and opt-in website deployment profile list the complete canonical
collection, up to 1,000 minted NFTs. They read ownership, immutable traits,
activation and current attached LP from the reviewed contracts. This is separate
from the public website's simulated collection and OpenSea primary minting.

## Operator setup

Use the existing [API configuration](FRONTEND_API.md), complete ownership indexer,
canonical deployment/runtime pins and [website profile](DEPLOYMENT_WEBSITE.md).
Deploy the matching API worker, website and reviewed Nginx allowlist together;
older workers or proxy rules will not support the collection endpoint. There is
no new contract address, signer, permission or financial configuration.

`GET /v1/collection/<confirmed-block>/<offset>` reads at most 16 positions.
Obtain the block from `/v1/protocol` and start at offset `0`. Follow the exact
`next_offset` until null, retaining the same confirmed block throughout. Offset
must be a multiple of 16 below 1,000. An empty, verified collection accepts offset
zero and returns zero LP. Unminted supply is excluded from both counts and LP.

The first chunk supplies the complete sorted `inventory_token_ids` and its
SHA-256 digest; later chunks supply the same digest/count and no repeated full
inventory. Each row verifies mint ordinal, reverse token identity and indexed
owner against canonical contract reads. Missing ownership history, inconsistent
identity, locked lifecycle, stale blocks, reorgs and exceeded budgets fail the read.

Clients must verify exact row coverage, unique ordinals, deployment and common
block/hash/timestamp, cursors and inventory digest. Only then display a total.
`chunk_lp_usd_18` and `chunk_activated` are chunk values, never collection totals.
The website independently reconciles both against each row before aggregation.

## Financial meaning and failure behavior

Attached LP is the sum of each NFT's `currentLPValue` quote, using the current
on-chain LP mark, attributed idle and compound reserves. It is neither lifetime
contributions nor claimable rewards. Per-NFT integer rounding is preserved; the
sum can differ from unrounded bucket NAV by rounding dust. No token-market or USD
price is invented by the API or browser.

Activated count means reward eligibility, including parked and terminal Exited
NFTs in accounting4; historical custody-outbound/remote states retain their old meaning. It
does not assert that every position is currently in range or earning fees. A
non-local or failed LP valuation makes the total unavailable while verified
positions and eligibility counts can remain visible. An unreadable dormant LP
view is not inferred to be zero. Broken identity, malformed data or a missing
page invalidates the complete collection rather than publishing a partial total.

The website shows 16 rows per page, ordinal/full-ID search, eligibility, rarity,
color/style filters and current-LP/newest sorting. Lifetime-fee sorting is disabled
because this endpoint does not supply per-NFT earnings. Position details reread
the NFT's current confirmed owner and balances; a changed owner requires refresh.
Collection allocations use the existing, separately validated earnings endpoint.
An earnings outage cannot hide healthy LP inventory; an LP outage cannot invent
an earnings value. Each metric identifies its own confirmed block.

## Stop, refresh and recovery

Navigation/refresh cancels the old collection read and clears its presentation.
Late responses cannot restore a cancelled inventory or partial totals. Search,
filters and pagination operate on the verified snapshot without new transactions.
Refresh to observe transfers, contributions or new mints; existing displayed
amounts are explicitly a block snapshot, not a promise about execution-time rights.

On stale/incomplete reads, inspect sanitized API/indexer outcomes, contiguous
history coverage, RPC chain/archive access, configured freshness and work budgets.
Refresh using a new `/v1/protocol` block after repair. Do not combine chunks from
different attempts or relax identity/freshness checks to obtain a number.
Disable the reviewed website profile or remove the collection proxy route to
stop serving these reads. Restore matching reviewed versions/configuration, then
verify a fresh complete snapshot before reopening. This has no custody effect.

Worst-case archive/history latency, real providers, Linux/TLS hosting and
production capacity remain qualification tasks. A 63-chunk functional fixture
does not establish 1,000-user capacity or 1,000-NFT live-market latency.
