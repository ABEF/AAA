# Confirmed earnings and current-price USD values

This optional read-only backend reports processed earnings across the collection
and for each NFT. It does not harvest, synchronize, convert, claim or sign a
transaction. The website still uses example data. See the owning
[financial-history task](../TODO.md#task-financial-history) and
[scoped verification](../reports/earnings-history/VERIFICATION.md).

## Endpoints and definitions

| GET endpoint | Result |
| --- | --- |
| `/v1/earnings` | Collection processed LP revenue, allocations, processed royalties and quarantine, by asset |
| `/v1/nfts/<decimal-token-id>/earnings` | That NFT's individual LP, collective LP and royalty earnings, including earnings already claimed by previous owners |

Each response contains `all_time` and `last_24h` asset rows, raw integer amounts,
current-price USD values, the confirmed block and the complete verified epoch
list. All financial integers are decimal strings. USD fields ending in `_18`
use 18 decimals. For example, `1000000000000000000` is $1. Token amounts instead
use that asset's configured and verified decimals.

**Earnings are not the remaining claimable balance.** Keep these endpoints
separate from current ledger `claimable` and actual `previously_claimed` payouts.
Transfers preserve the NFT's lifetime history; they do not reset it for the buyer.

| Metric | Meaning |
| --- | --- |
| `lp_processed_raw` | New receipts processed by the pinned canonical FeeController, including carried allocation dust once on receipt; never pool trading volume |
| `lp_owner_allocated_raw`, `lp_collective_allocated_raw` | Amounts credited to the holder ledgers; integer index dust can make their sum exceed the sum of immediately claimable whole units |
| `lp_compounding_allocated_raw`, `lp_buyback_allocated_raw` | Amounts allocated to those reserves, not proof that compounding or a burn has executed |
| `lp_collective_quarantined_raw` | Collective credits with no eligible membership |
| `royalties_received_raw`, `royalties_allocated_raw`, `royalties_quarantined_raw` | Actual processed royalty receipts, separated by eligibility; admission/constructor prefunds are excluded |
| NFT `lp_individual_raw`, `lp_collective_raw`, `royalties_raw` | Exact whole-unit earnings reconstructed from the ledger's 1e36 indexes and carried fractions |

Do not sum gross receipts and their allocations as additional income. Remote
holder credits are included when the home ledger processes them, but the API
does not invent the remote gross revenue or remote reserve allocations from a
90% credit. Complete satellite gross reporting needs separately reviewed history.

The clock is **on-chain processing/allocation time**. The 24-hour window is
`(confirmed timestamp - 86400, confirmed timestamp]`. An unsynchronized royalty
deposit, unharvested venue fee or unpaid creator obligation is not yet processed
earnings. A late creator payment enters the period when processed, not when the
creator's underlying trades happened. A fractional token unit enters an NFT's
period when carried fractions first become a whole raw unit. This distinction
matters for very small amounts and is returned in the response.

## USD valuation decision

The user selected **today's price**, on 2026-10-19. Both all-time and 24-hour earned
token amounts use prices at the same current confirmed snapshot. They are not
historical USD revenue, realized sale proceeds, or the current value of unclaimed
funds. Display a label such as **“Earnings at current prices”** and the snapshot
time. The amounts can rise or fall without new earnings when prices change.

Royalties converted from a stablecoin into ETH remain earnings in the original
source currency. The conversion is a separate denomination record; its ETH credit
must not be added as new income. Current ETH claimable already includes unclaimed
conversion credits. Use [conversion reporting](ROYALTY_REPORTING.md) for actual
source/output amounts and lifetime claims for payouts.

Missing, stale, invalid or changed price policies return `null` USD values and a
reason. Raw earnings remain available when only pricing fails. An aggregate is
`null` if any nonzero component lacks a price. No stablecoin is assumed to equal
$1; zero raw earnings can be valued at zero without a feed.

Use the [read-only independent-provider audit](HISTORY_AUDIT.md) to compare indexed raw logs and block ancestry before enabling live reports. It produces bounded window evidence and detects omissions/conflicts; it does not replace the accounting/lineage checks below or prove full history by itself.

## Configuration and operating procedure

Use a reviewed [schema-2 API configuration](FRONTEND_API.md). The opt-in block is:

```json
{
  "earnings_history": {
    "schema": 1,
    "deployments": [
      {
        "controller": "<reviewed controller address>",
        "fees": {"address": "<FeeController address>", "code_hash": "<runtime hash>"},
        "membership": {"address": "<Membership address>", "code_hash": "<runtime hash>"}
      }
    ],
    "prices": null
  }
}
```

These are placeholders, not usable deployment addresses. `deployments` must
cover every configured same-chain predecessor in order, then the current
deployment. FeeController and Membership must be the sealed controller bindings.
The already pinned NFT, Vault, Rewards, RoyaltyRewards and CanonicalHandoff
complete the seven emitters. Both reward ledgers must use the reviewed 1e36 scale.
An arbitrary replacement with different event/accounting semantics is unsupported
until reviewed and implemented; the profile is not a general successor decoder.

1. **Review configuration:** an API operator selects exact addresses, code hashes,
   creation blocks/parents, asset decimals and complete predecessor cutoffs. No
   governance call or new transaction is needed to enable these reads.
2. **Backfill all seven emitters:** NFT, Vault, Rewards, RoyaltyRewards,
   CanonicalHandoff, FeeController and Membership must be in each indexer's
   `contracts` list from creation. Adding addresses to an existing cursor without
   backfill is invalid. Build a new database with the reviewed configuration;
   preserve the old database, WAL-consistent backups and retirement records.
3. **Reconcile:** compare the pinned block, minted count, total shares, reward
   indexes, membership, royalty cohorts and a known NFT's earnings/claims.
   Do not switch service traffic to incomplete history.
4. **Enable prices only after review:** use the policy below and independently
   qualify actual feed, proxy/admin, wrapper equivalence and sequencer behavior.
5. **Serve through the existing supervised read server:** the routes retain
   request deadlines, RPC budgets, bounded SQLite reads, serial worker execution,
   final canonicality/confirmation checks and no-store responses. Never replace
   rejected history with a zero balance. Validate latency on the actual workload
   before public hosting.
6. **Stop/recover:** remove the optional earnings profile and restart the read
   service to disable these endpoints. Claims and keeper operation are unaffected.
   Restore/backfill history separately, review changed dependency pins and verify
   both endpoints before re-enabling. Preserve the original evidence on mismatch;
   do not edit raw logs to force reconciliation.

### Optional price policy

Replace `prices: null` with:

```json
{
  "oracle": {"address": "<bound ZZZOracle>", "code_hash": "<runtime hash>"},
  "sequencer": null,
  "feeds": [
    {
      "asset": "<earned asset address>",
      "priced_token": "<same token, or reviewed wrapper for native ETH>",
      "token_code_hash": "<runtime hash>",
      "source": "<reviewed USD feed>",
      "source_code_hash": "<runtime hash>",
      "max_age": 60,
      "feed_decimals": 8
    }
  ]
}
```

Use `sequencer: null` only when the reviewed Oracle actually has no sequencer
feed; otherwise provide its exact `address` and `code_hash`. Native ETH's asset
identity is the zero address and requires an explicit reviewed equivalent-token
price mapping. Other assets cannot alias another token. `max_age` and decimals
must match Oracle storage exactly; this example does not choose a production
feed age. Oracle.price supplies the existing freshness/round/uptime guards.
Proxy runtime pins do not independently authenticate their upstream economics;
actual provider and upgrade monitoring remain release requirements.

## Accounting and recovery boundaries

Replay excludes mint payments, principal contributions, NFT transfers, imported
balances, payouts and denomination conversions from income. Top-ups affect only
later LP allocations. Collective earnings use equal active membership; royalties
use rarity weights and the actual per-currency eligibility cohort. Recovery gives
old receipts to the older cohort before new members join. The different event
order during frozen canonical settlement is handled explicitly.

Complete same-chain lineage uses the existing verified retirement/activation
receipt pair, state root and immutable original identity. Indexes and fractions
continue across the boundary; successor constructor/import events are skipped.
Late forwarded money counts when the active successor actually processes it.
Missing origins, mismatched receipts, unsupported profiles or incomplete events
reject the history. This is not cross-chain consensus verification.

Per-NFT reconciliation also compares earned amounts with current entitlement,
actual lifetime payouts and source/native conversion amounts. Pending royalty
funds are reconciled separately and are not silently included as processed income.
A failed ledger/pending-balance read can make this strict earnings endpoint
unavailable. The separate [currency-isolated balance view](ROYALTY_REPORTING.md)
can still expose healthy current balances; no availability claim is made for the
entire history endpoint during a token outage.

History is operator-maintained evidence plus pinned RPC reconciliation, not a
cryptographic proof that every log was ingested. Whole-history reads are bounded;
large histories or many predecessor/assets can exceed the request budget and
must fail without truncation. Production backfill, reorg/load rehearsals, archive
providers, current feed policies and frontend display remain qualification work.
