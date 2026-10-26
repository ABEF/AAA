# Confirmed earnings and current-price USD values

This optional read-only backend reports processed collection and per-NFT
earnings. It never harvests, synchronizes, converts, claims or signs. The current
candidate uses accounting 3, fee intake 1 and same-chain canonical V4. The public
website remains a simulation; current-profile service, website and provider
qualification remain open. See the [financial-history task](../TODO.md#task-financial-history).

## Fee allocation integrity

For explicit `fee_intake_version: 1`, the pinned actual FeeController must return
`FEE_INTAKE_VERSION() == 1`. Replay pairs each allocation with its exact preceding
funded LP credit in the same transaction, bucket and currency. Distributed 20*n
must fund 16*n individual and 2*n collective; each remaining n goes to compound
and buyback. A carried-only receipt has no reward credit. Membership dust
settlement has its exact individual-only credit. Unrelated logs may interleave;
missing, conflicting or unmatched entries reject the report.

At every epoch cutoff, observed fee keys also reconcile `dust(bucket,asset)`
against the actual pinned FeeController, including zero. Historical profile 0
retains its reviewed semantics. This adds no transaction or policy setter.
See [review and limitations](../reports/backend-remediation-20261026/HISTORY.md)
and [final affected verification](../reports/backend-remediation-20261026/VERIFICATION.md).

**Use the correct total:** NFT earnings = individual LP + collective LP + eligible
royalties. Reserves and gross pool fees are not extra NFT income. Earned 24h/all
time includes paid income; current claimable subtracts actual claims and includes
the ledger's presently claimable receipts. Pending royalty receipts can be
claimable before synchronization enters processed earnings. Claims/conversions
never create a second earnings event. Original earned currencies use today's
confirmed prices; a conversion is not a historical USD valuation.

Head-state reconciliation is not proof of raw-log completeness or every historic
timestamp: deleting an isolated unobserved dust-only receipt, or tampering with
intermediate dust while restoring the true final remainder, may leave no head
signal. Require authentic complete logs and the bounded independent-provider
history audit. Never repair raw logs, assume zero or weaken the profile to force
a report. Preserve the original database and diagnose using a separate replay
copy with the same seven emitter bindings and confirmed cutoff.

## Native royalty custody boundary

Current replay accepts native deferral only within an authenticated custody
exit/full-return interval. Returned backing is not royalty revenue. Ordinary
post-return synchronization credits earlier unseen receipts to the earlier
cohort before waiting NFTs join; conversions and claims still do not create
income. Missing/mismatched events and full earnings reconciliation while backing
is external remain unavailable, never zero. See [reporting and safe replay](ROYALTY_REPORTING.md#native-custody-history-and-recovery)
and the [source-scoped correction](../reports/day-readiness-20261025/royalty-matrix.md).
This is reader compatibility, not a running-service upgrade. Earlier
[earnings verification](../reports/earnings-history/VERIFICATION.md) retains its
original source/profile scope; current integrity evidence is linked above.

## Endpoints and definitions

| GET endpoint | Result |
| --- | --- |
| `/v1/earnings` | Collection processed LP revenue, allocations, processed royalties and quarantine, by asset |
| `/v1/nfts/<decimal-token-id>/earnings` | That NFT's individual LP, collective LP and royalty earnings, including earnings already claimed by previous owners |
| `/v1/wallets/<address>/earnings/<confirmed-block>/<offset>` | Up to 16 currently owned NFTs; sum every verified chunk for a wallet total |

Each response contains `all_time` and `last_24h` asset rows, raw integer amounts,
current-price USD values, the confirmed block and the complete verified epoch
list. All financial integers are decimal strings. USD fields ending in `_18`
use 18 decimals. For example, `1000000000000000000` is $1. Token amounts instead
use that asset's configured and verified decimals.

**Earnings are not the remaining claimable balance.** Keep these endpoints
separate from current ledger `claimable` and actual `previously_claimed` payouts.
Transfers preserve the NFT's lifetime history; they do not reset it for the buyer.

## Current-holdings totals

Read `/v1/wallets/<address>/nfts` first. Request earnings at that inventory's
confirmed block with offset 0, following `next_offset` until null. Each chunk
binds the wallet, NFT contract, ordered IDs, full count, inventory SHA-256, block
hash and API configuration. Offsets are multiples of 16, at most 992. Missing,
expired, reorged or mismatched chunks invalidate the entire total.

One replay per epoch handles the selected NFTs together, preserving each NFT's
fractions before summing whole units. Shares, weights, current entitlements,
actual claims and conversions reconcile against the chain. Existing same-chain
retirement/identity checks cover predecessors. Request deadlines, RPC budgets and
isolated workers still apply; large histories/assets/lineages can exceed them.
This is not production capacity qualification.

The website sums original earned currencies across chunks before USD rounding
at the same confirmed prices. Missing prices for nonzero earnings produce
unavailable USD, independently of healthy current LP/ETH balances. Account changes
discard old totals. These are **lifetime earnings of currently held NFTs**, including
earlier owners, not personal wallet income or remaining claimable rewards.

Per-asset collection holder allocations sum individual LP + collective LP +
allocated royalties. They exclude gross-receipt duplication, compound/buyback
and quarantine,
but include ledger rounding dust. They need not equal per-NFT whole-unit sums.
Full collection inventory/LP aggregation remains separate.

Enable through the reviewed `earnings_history` profile; no new role or
state-changing contract call is needed. Release matching read API/frontend
versions, verify known inventory/cutoffs, and qualify actual feeds/coverage/latency
before public use.
To stop reports, disable the optional profile and restart only the read service
under its runbook, or roll back matching releases. Never reset the chain/index
or substitute examples/zeros on failure. See [scoped evidence](../reports/wallet-earnings/VERIFICATION.md).

| Metric | Meaning |
| --- | --- |
| `lp_processed_raw` | New receipts processed by the pinned canonical FeeController, including carried allocation dust once on receipt; never pool trading volume |
| `lp_owner_allocated_raw`, `lp_collective_allocated_raw` | Amounts credited to the holder ledgers; integer index dust can make their sum exceed the sum of immediately claimable whole units |
| `lp_compounding_allocated_raw`, `lp_buyback_allocated_raw` | Amounts allocated to those reserves, not proof that compounding or a burn has executed |
| `lp_collective_quarantined_raw` | Collective credits with no eligible membership |
| `royalties_received_raw`, `royalties_allocated_raw`, `royalties_quarantined_raw` | Actual processed royalty receipts, separated by eligibility; admission/constructor prefunds are excluded |
| NFT `lp_individual_raw`, `lp_collective_raw`, `royalties_raw` | Exact whole-unit earnings reconstructed from the ledger's 1e36 indexes and carried fractions |

Do not sum gross receipts and their allocations as additional income. Current
fee-intake 1 accepts local LP receipts; no creator-payment inbox, satellite or
remote fee-intake configuration belongs in this release. Explicit historical
fee-intake 0 replay retains its earlier semantics and cannot establish remote
gross/reserve totals from a holder-only credit.

The clock is **on-chain processing/allocation time**. The 24-hour window is
`(confirmed timestamp - 86400, confirmed timestamp]`. An unsynchronized royalty
deposit or unharvested venue fee is not yet processed earnings. A fractional token
unit enters an NFT's period when carried fractions first become a whole raw unit. This distinction
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
   indexes, membership, royalty cohorts and a known NFT's earnings/claims. For
   fee-intake 1, verify actual version 1, complete matching fee/credit logs and
   each observed fee key's pinned final dust.
   Do not switch service traffic to incomplete history.
4. **Enable prices only after review:** use the policy below and independently
   qualify actual feed, proxy/admin and sequencer behavior.
5. **Serve through the existing supervised read server:** the routes retain
   request deadlines, RPC budgets, bounded SQLite reads, isolated request workers,
   final canonicality/confirmation checks and no-store responses. Never replace
   rejected history with a zero balance. Validate latency on the actual workload
   before public hosting.
6. **Stop/recover:** remove the optional earnings profile and restart the read
   service to disable these endpoints. Claims and keeper operation are unaffected.
   Restore/backfill history separately, review changed dependency pins and verify
   both endpoints before re-enabling. Preserve the original evidence on mismatch;
   do not edit raw logs to force reconciliation.

### Optional price policy

Leave `prices: null` until actual sources and policies are reviewed. Raw history
can remain available while nonzero USD totals are unavailable. For the current
accounting-3 candidate, a configured price block must use **pricing version 2**:

```json
{
  "pricing_version": 2,
  "oracle": {"address": "<bound ZZZOracle>", "code_hash": "<runtime hash>"},
  "sequencer": null,
  "feeds": [
    {
      "asset": "0x0000000000000000000000000000000000000000",
      "priced_token": "0x0000000000000000000000000000000000000000",
      "token_code_hash": null,
      "price_policy": {
        "policy_id": "<reviewed append-only policy identity>",
        "ordinal": 0,
        "policy": {
          "token": "0x0000000000000000000000000000000000000000",
          "primary": {
            "source": "<first independently reviewed source>",
            "expectedCodeHash": "<runtime hash>",
            "independenceId": "<nonzero independence identity>",
            "maxAge": 60,
            "feedDecimals": 8
          },
          "secondary": {
            "source": "<different independently reviewed source>",
            "expectedCodeHash": "<runtime hash>",
            "independenceId": "<different nonzero independence identity>",
            "maxAge": 60,
            "feedDecimals": 8
          },
          "maxDeviationBps": 300,
          "assetDecimals": 18,
          "reviewHash": "<nonzero reviewed-policy hash>"
        }
      }
    }
  ]
}
```

This illustrates native ETH; each ERC20 entry instead uses its own address,
runtime hash and verified decimals. Replace every placeholder. These illustrative
ordinals, ages and decimals are not production settings. Copy the exact reviewed
immutable record, including its Oracle-derived policy identity and ordinal; do not invent or hand-edit identities.
The user-selected disagreement policy is 300 bps (3%), measured against the
lower source; actual active records still require review. The contract permits
reviewed values up to 500 bps.

Native ETH uses address zero, 18 decimals, `priced_token: zero` and
`token_code_hash: null`; it never aliases WETH in this profile. Every ERC20 prices
itself with its exact runtime/decimals. Both independently reviewed source records,
active policy, round data and observation fingerprint must agree with the pinned
Oracle at the same block. The USD mark uses the conservative lower bound and
returns the upper bound/fingerprint too. Missing, stale or divergent sources make
that asset's USD unavailable; there is no single-source fallback or stablecoin peg
assumption. See [pricing controls and limits](PRICE_SECURITY.md).

Use `sequencer: null` only when the actual reviewed Oracle has no sequencer feed;
otherwise supply its exact address/runtime pin. Proxy runtime pins alone do not
authenticate implementations or economic independence. Provider, update and
upgrade monitoring remain release requirements.

Historical accounting 1/2 may retain an explicitly compatible pricing-version-1
single-feed mapping. Its `source`, `source_code_hash`, `max_age` and
`feed_decimals` fields match that old Oracle ABI. It is not a valid current
accounting-3 configuration and must not be copied into a fresh release.

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
