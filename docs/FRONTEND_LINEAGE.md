# Lifetime claims across same-chain handoffs

The confirmed NFT endpoint returns lifetime LP and royalty claim totals
across the complete configured lineage of replacement deployments. These include
claims by every past/current NFT owner. Current funded balances still come only
from the active deployment; replay never changes or increases claimable rewards.

This implements the [read API task](../TODO.md#task-read-api) for the supported
same-chain handoff. It does not implement cross-chain consensus verification,
marketplace cutover or a hosted production indexer.

For the current accounting 3/canonical V4 candidate, every configured predecessor
must explicitly use accounting 3 too. Older accounting 1/2 readers remain for
compatible historical lineages; they are not an automatic import path into V4.
Custody exit to an operator-controlled address does not itself move NFT identities
or reward ledgers. See [custody exit](GOVERNED_CUSTODY_HANDOFF.md).

## Operator configuration

Schema 2 accepts an optional `predecessors` array. Omit it for the original
deployment. Configure it for a successor in oldest-to-newest order, ending with
the current deployment's immediate predecessor. The first entry must have no
predecessor on-chain. Configuration is explicit: no unreviewed peer or RPC is
automatically discovered.

Every entry contains exactly these fields:

| Field | Required meaning |
| --- | --- |
| `accounting_version` | Required for native/current lineage; current V4 requires 3 for every predecessor. Historical configurations retain their explicit supported codec. |
| `deployment_block`, `deployment_block_hash` | Reviewed sealed-deployment anchor, at or before its outgoing retirement; the destination anchor must also precede that handoff |
| `contracts` | All eight independently reviewed address/runtime pins, using the [API configuration format](FRONTEND_API.md#deployment-configuration) |
| `assets` | Exact historical LP/royalty asset union and descriptors at retirement, using the same API format |
| `history` | Separate complete creation-to-retirement indexer history, using the [history configuration](FRONTEND_HISTORY.md#configuration-and-genuine-coverage) |
| `retirement_transaction_hash` | Successful source-retirement transaction containing the matching successor activation |

The current deployment must also have its own complete `history` configuration.
Predecessors inherit its chain, RPC endpoints, confirmation depth, freshness
policy, fee-intake version and configuration schema. Their accounting version is
explicit; they do not inherit the current optional royalty/earnings reporting
configuration. They cannot override inherited fields or contain nested predecessor
lists. Every protocol contract address must be distinct across deployments;
repeated identities, cycles and asset/module collisions are rejected.

The API supports **up to eight predecessors** and **one million configured maximum
events in total**, including the current history. These are backend request-work
bounds, not protocol migration limits. Allocate each history's `max_events`
within that total. A longer chain or oversized history fails closed and requires
a reviewed backend scaling change; it is never silently truncated.

## How the response is established

1. Verify all pinned predecessor code, bindings and lifecycle at the same
   confirmed hash as current balances. Each source must be retired and retain
   the same original identity as the current NFT. Both directions of every
   source/successor link must match the configured order.
2. Fetch the configured retirement receipts. Require successful execution,
   canonical blocks no later than the current snapshot, exact transaction/log
   identities and bounded ordered logs. The source's `Retired` and destination's
   `Activated` events must commit the same nonzero handoff ID/state root and the
   expected peer controllers. The source's terminal stored commitment must agree.
3. Check controller/coordinator runtime pins at the historical transition too.
   A destination that later retires has a new outgoing root, so its old activation
   is authenticated from the receipt instead of comparing that new root.
4. Replay each predecessor's actual raw ownership/claim logs through its retirement
   block. Its index may stop there permanently. Verify creation anchors, coverage,
   admitted historical assets and the NFT's stable mint ordinal. A later-minted
   NFT has no fabricated pre-mint claims. Import transfers reconstruct ownership;
   they do not create claim revenue or paid marketplace sales.
5. Add current and historical raw LP/royalty amounts per NFT and asset. Retain
   old assets even if the current deployment no longer admits them. Conflicting
   decimal units are rejected; different currencies are never summed into USD.
6. Recheck the historical anchors and then the current snapshot's canonicality,
   confirmation depth and age before returning any success.

The existing `previously_claimed` object returns `available: true`, per-asset
`lp_raw`, `royalties_raw` and `total_raw`, plus provenance for every retirement and
index. `lineage_complete` describes this complete pinned same-chain replay; it
does not prove consensus finality. Current `claimable` amounts are unchanged.

Without configured predecessors, an imported successor still returns explicitly
unavailable lifetime totals. With a configuration that fails verification, the
request fails with the existing sanitized HTTP 503 rather than returning a partial
sum. The protocol status endpoint does not perform this potentially larger replay
and still treats its peer addresses as source commitments.

## Trust and release boundary

RPC observations and operator-maintained complete indexer ingestion remain the
data trust model. Stored SQLite rows and matching event receipts are not a
cryptographic proof of log completeness or L1 finality. Reviewed replacement code
may differ, but it must implement the documented lifecycle/claim ABI and semantics;
hash equality does not replace that review. The service never signs or broadcasts.

Actual archive-RPC availability, latency at the configured history bounds,
retention/backups and browser integration need operating qualification under
[hosted services](../TODO.md#task-host-services) and [live history UI](../TODO.md#task-live-history-ui).
There is no integrated bridge or cross-chain ledger-import procedure in this
release. External chain/token migration uses reviewed custody exit and redeployment;
it does not acquire same-chain lineage guarantees merely by copying configuration.
See the [scoped verification](../reports/frontend-lineage/VERIFICATION.md).
