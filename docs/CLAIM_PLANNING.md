# Gas-aware unsigned claim planning

**Mint-profile boundary:** backend source implements explicit opt-in
`mint_integration_version:2` on accounting7 for V10 reads and owned reward claims.
Omitted/default1 on accounting7 retains V9; source9/schema16 website configuration
remains its exact prior profile. [SeaDrop mint2/schema17/V10](OPENSEA_MINT.md)
requires separately reviewed deployment/configuration and operating acceptance.
No service, checkpoint, journal, served site or signer is automatically adopted,
upgraded or relabeled.


The optional `POST /v1/claims/plan` endpoint prepares **one next claim batch**
within the existing gas and network-fee limits. It never signs, broadcasts,
queues later transactions or changes a ledger. The existing
`/v1/transactions/prepare` retains historical/default1 direct mint and claim
behavior. Explicit mint integration2 supports V10 owned claims here but rejects
direct mint preparation with "Use OpenSea" before RPC/simulation. Public signing
remains disabled; the shared browser signer remains Anvil-only.
Accounting7 admission authenticates exact LP1 and the fixed Rewards canonical
companion, with V9 under omitted/default1 or V10 under explicit2. The latter
also verifies independently pinned `seadrop_mint`/`seadrop` runtime and fixed
NFT/helper/controller/implementation bindings at the same canonical block;
mutable sale prices, phases and proof eligibility never gate existing claims. LP funded claims are exact whole units in
ETH or fixed ZZZ; original royalty currencies remain separate. Historical policy1 keeps schema1; optional policy2 returns schema2 with the same explicit claim selection; no historical6 runtime is relabeled.

The exact-host cold32-entry rehearsal consumed31,085,813raw execution gas,
above the unchanged12M service budget. It used16NFTs across four buckets and
both LP currencies in a1,000-minted/900-active fixture; this is NOT an approved
32-entry operating batch or target-chain fee measurement. Let the planner test
smaller prefixes, publish only a fresh successful draft and replan the remainder
after confirmation. A direct single-currency cold claim measured1,259,505raw gas
in its explicit fixture. Neither measurement fixes the size of future batches;
see [source/gas evidence](../reports/exact-lp-integration-20261106/VERIFICATION.md).

The same controlled cold fixture's8entries (four NFTs/all four buckets) measured
8,819,431raw gas. It fits that test's12M budget, but is not universal8-entry
approval: recipient/token behavior, tree state, other currencies and transaction
overhead differ. The ordinary exact final simulation/estimate remains mandatory.

This is a local source feature, not a deployed endpoint or target-chain gas
qualification. Enabling it on an operating service requires a separate reviewed
rollout. The default read API remains GET-only. The existing reviewed
`--transaction-config` opt-in enables unsigned preparation and this planning
method through the same isolated workers and preparation admission limits.
The checked-in Nginx template has an exact POST-only allowlist entry for this
path on the existing8787 backend. No operating proxy was changed or reloaded;
actual ingress qualification is still required.

## Request

Use the same explicit claim selection as ordinary preparation. No wallet-wide
discovery, arbitrary contract call, recipient, gas override or RPC URL is accepted.
Replace the owner and token ID in this template with confirmed values first:

```json
{
  "action": "claim",
  "wallet": "0xREPLACE_WITH_CURRENT_OWNER",
  "claims": [
    {
      "token_id": "REPLACE_WITH_DECIMAL_TOKEN_ID",
      "asset": "0x0000000000000000000000000000000000000000",
      "royalty": true
    }
  ]
}
```

| Field | Meaning |
| --- | --- |
| `wallet` | Current owner of the claims to execute. An approved NFT operator is not the claim owner. |
| `claims` | One to32 distinct `(token_id, asset, royalty)` entries, in the preferred order. |
| `token_id` | Canonical decimal string; JSON numbers can lose precision. |
| `asset` | Exact admitted currency address; zero means native ETH. |
| `royalty` | `true` for the royalty ledger; `false` for the LP rewards ledger. |

Royalties retain their original currencies. LP conversion is a separate
operation: this endpoint does not swap tokens, unwrap assets or invent an ETH
equivalent. Amounts for different assets are never added together. Neither a
price feed nor a liquidity valuation is needed merely to plan funded claims.

## Result and continuation

The result has `kind: "unsigned_claim_plan"` (schema1 for historical policy1, schema2 for explicitly reviewed policy2) and contains:

| Field | Use |
| --- | --- |
| `next_batch` | One ordinary `unsigned_transaction_draft`, or `null`. Only this object contains reviewed transaction calldata and gas/fee details. |
| `entries` | Every original selection, its index, identity, status, reason and observed raw amount when available. Missing amounts stay `null`. |
| `remaining_claims` | Every selection outside the next batch that still needs assessment/action, including blocked or unavailable entries. Zero-balance entries are identified in `entries` rather than silently discarded. |
| `planning` | Trial count, exact selection indices, result categories, actual effective gas cap and bounded-work policy. It does not guarantee the mathematically largest possible batch. |
| `provenance` | Confirmed block/hash/time, reviewed configuration identities and explicit accounting/custody/royalty profile; opt-in2 additionally states mint_integration_version2. |
| `expires_at` | Client review expiry. It is not an on-chain deadline added to the claim router. |

| Entry status | Meaning |
| --- | --- |
| `in_next_batch` | Included in the freshly prepared, simulated next draft. Review its `claim_operations` and `network_gas`. |
| `zero` | The confirmed claimable read returned zero. This is not a promise that future receipts will remain zero. |
| `blocked` | A verified condition prevents this selection, such as another owner, no mint ordinal, an unadmitted ledger currency, unopened royalty window, or an individually unfillable reviewed execution budget. |
| `unavailable` | Currency verification, a claim view or an individual execution could not be established. An opaque execution refusal is **not** a diagnosis of a bad token. |
| `unassessed` | Outside the next batch, or the fixed planning-attempt limit was reached. Replan it; it is not assumed successful, zero or unsafe. |

Submit nothing automatically. If the owner chooses to proceed, the wallet must
perform its existing account/network/deployment/expiry, latest simulation and gas
checks before signing **only `next_batch`**. After its transaction is confirmed,
request a new plan for the remaining selection against new confirmed state. Do
not pre-sign later batches or reuse an old plan as a continuation token. If a
wallet already submitted a transaction, recover that saved hash before starting
another action. The planner does not manage pending nonces or resend transactions.

## How batching works

All planning reads and EVM trials use one confirmed canonical block. The planner
checks deployment/lifecycle, complete admitted-currency identity and selected
NFT ownership, then reads the selected funded balances. It tries an ordered
batch and, when necessary, smaller prefixes. Known gas/fee/balance limits can
require a smaller batch. An opaque execution refusal can also lead to bounded
smaller probes, while its cause remains unclassified.

Before publication, the selected batch is prepared again through the **existing
transaction preparer**, with fresh same-snapshot ownership, claimable amounts,
lifecycle, exact calldata simulation, estimate, gas price and wallet balance.
Final canonicality and freshness checks must pass. A previously good trial is
not published if final verification fails.

Recognized transport, rate-limit, missing-block, parameter or internal-provider
failures invalidate the plan with no draft. Optional metadata failures cannot
hide a detectable global RPC failure. Only sanitized execution refusals may be
probed; malformed return values or gas quantities are rejected. Successful smaller
simulation proves that selected batch, not the reason a larger batch failed.

Successful identity/admission metadata may be reused **only within this request
at the same block hash**. This includes the exact LP capability and typed
canonical-module parent links, not tree balances or claimable components. Some
of those settings are configurable across blocks.
Owners, claimable/wallet balances, lifecycle, simulations, estimates, fee prices,
heads and canonicality checks are not cached. No cache is retained across users,
requests or blocks.

## Strict bounds and errors

- At most32 selected operations and10 planning trials, plus one final preparation.
- Policy1 retains12M. Explicit [policy2](FRONTEND_TRANSACTIONS.md#reviewed-gas-policy2-operator-configuration) uses the lesser of the reviewed operator cap and authenticated confirmed-block gas limit, with full20% estimate headroom. Changed same-hash block policy aborts the entire plan. No automatic widening, client override or change to fee/balance/work budgets.
- Confirmed snapshots must meet the existing preparation freshness limit of at
  most120seconds; reviews last at most60seconds and never outlive that snapshot.
- Nested work shares the ordinary25-second request budget,1024logical RPC calls
  and2048HTTP posts. Existing isolated-worker supervision remains30seconds.
- Existing HTTP host/framing checks,16KiB body limit, duplicate-key rejection,
  bounded JSON nesting, no-store responses and preparation rate/concurrency limits
  apply to the new endpoint too.

Malformed selections return the existing sanitized400 input error. A service,
provider, canonicality or final-review failure returns503
`claim_planning_unavailable`, with no transaction draft. The absence of a draft is
not a token balance of zero and does not authorize a broader financial limit.
Large or faulted currency populations can exhaust these bounds; they require
smaller explicit selections and actual provider/gas qualification, not guessed
readiness or an increased running-service limit.

Source files: [planner](../frontend_api/claim_planner.py),
[transaction preparer](../frontend_api/transactions.py),
[HTTP adapter](../frontend_api/server.py) and [workers](../frontend_api/worker.py).
Tests cover synthetic exact adapters and the real loopback HTTP/worker dispatch;
they do not qualify deployed services, arbitrary tokens, target-chain capacity,
public signing or independent security review.
