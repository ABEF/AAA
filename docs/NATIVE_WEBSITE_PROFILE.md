## Scope: published native2 website profile

This document records the existing published website read/unsigned profile2.
The newer contract candidate uses [accounting3/localV4](POSITION_V3.md); it needs
an explicitly matching website integration and qualification. Do not relabel the
profile2 table below or any existing Anvil journal as version3. Public DEPLOYMENT
remains null and signing Anvil-only; no website build/server change is implied.

# Native-V2 website read and unsigned reviews


## Current release simplification - 2026-10-25

[Current scope](SIMPLIFIED_RELEASE.md): ETH/ZZZ-only contributions, actual local LP
fees, no creator inboxes or integrated cross-chain bridge. Preserve same-chain
pool moves, external custody exit/recovery, royalty currencies and complete
collection handoff. Current fee/custody profiles and canonical schema are
explicit; old deployments/journals keep historical profiles.

The website has an explicit **schema-2 manifest** for accounting2, pricing2,
routing2 and reviewed Entry1. It is locally implemented; the public configuration
remains null. Nonlocal submission is disabled. The shared signer, browser client
and transaction coordinator are unchanged and remain Anvil-only. This does not
qualify real native wallet/provider flows or approve deployment.

Read [scope and verification](../reports/native-readiness-20261025/VERIFICATION.md),
[existing hosting/session procedure](DEPLOYMENT_WEBSITE.md),
[Entry review policy](EXECUTION_LOSS_POLICY.md#review-time-policy-binding) and
[RPC qualification](RPC_PREPARATION_QUALIFICATION.md).

## Select the matching deployment profile

Keep schema1 for an existing historical WETH/local deployment. Its original
valuation asset, 1% policy, ABI and journals retain their meaning. Do not change
an old manifest's version to make new code appear compatible. Explicit current
version data cannot silently pass as a historical profile.

For schema2, start with the reviewed manifest fields in the existing guide and
make these additions/changes. No actual production addresses are supplied here.

| Field | Native-V2 requirement |
| --- | --- |
| Versions | `schema: 2`, `accounting_version: 2`, `pricing_version: 2`, `routing_version: 2`, `review_policy_version: 1`. All explicit. |
| Contract pins | Existing `access`, `nft`, `vault`, `entry`, `claim_router`, `oracle`, plus `pools`, `budget`, `activation_assets`, `contribution_pricing`. Ten distinct nonzero addresses, each with the reviewed exact deployed `runtime_code`. |
| Contribution ceiling | `limits.maximum_contribution_loss_bps`, integer0-1000. This is the independently approved website ceiling, not a value discovered from the API. Normally200 for the current2% default; a different value requires review. Zero is a real zero cap, never a missing/default value. |
| Every input | Existing symbol/address/decimals/route/enabled/runtime fields, plus approved `price_policy_id`, `asset_policy_id` and `route_kind`. Both IDs are nonzero hashes. |
| Native ETH input | Address and `valuation_asset` both zero,18decimals, `runtime_code: null`. Never query a deployed runtime at address zero or substitute WETH. |
| ERC20 input | Valuation address equals the actual token; exact reviewed runtime and decimals. WETH is not another activation selector. |
| Route | Kind0 only with zero route ID; typed nonzero route ID is kind1 or2. Native routed input requires kind2. Enabled admission, policy IDs and route kind must match confirmed state. |
| Reward inventory | Complete reviewed union, at most49 unique currencies, including native ETH/zero/18. Native LP projection is bounded33 rows and royalties17 rows; both must include exactly one ETH entry. Missing entries fail rather than becoming a partial claim total. |

All other chain/genesis/anchor, confirmation, age, API identity, gas/value and
same-origin/HTTPS restrictions remain. Choose public production configuration
only after independent deployment/service approval. Do not add credentials,
signing flags, query-selected manifests or automatic runtime fallbacks.

## What each review verifies

At the canonical confirmed block, the client verifies version getters, deployed
runtime and Access/module/parent bindings. The helper caches successful immutable
checks for at most four block hashes; failed checks are removed. A new confirmed
hash requires new verification. Prices, caps and source policies are checked for
the actual quote snapshot, not taken from an old successful balance read.

The source policy IDs and exact token identity/precision must match. Oracle
`priceBounds` must return exactly three ABI words: positive ordered USD bounds
and a nonzero fingerprint. The reviewed Oracle implementation enforces source
age, discrepancy and independence-policy rules. This does not itself establish
that real providers are independent or market-correct; qualification remains
separate. NFT earnings USD marks retain the reviewed API/configuration trust
boundary; the browser does not independently re-read every historical currency's
Oracle policy.

Activation targets at least$100 at the lower source price with only minimal
raw-unit rounding; growth starts at$5. The execution floor uses **upper input
USD rounded up**, less the captured allowed fraction rounded down. Added LP is
the independently checked simulated marginal deployed amount, not attributed
idle or an optimistic gross contribution. A wider valid price band can therefore
make a quote unavailable even before the nominal loss cap is exhausted.

The current on-chain contribution cap must fit the manifest ceiling, equal the
API's captured execution cap and equal its reviewed caller maximum. The client
reconstructs the exact `executeReviewed` selector and all ten ABI words, including
the maximum. Target, sender, value, input amount, route, deadline, LP/liquidity
floors and complete network-fee review must match. Gas remains separate.

An ERC20 approval replaces allowance with exactly the chosen contribution and
requires a fresh complete Entry preparation afterward; approval creates no LP.
Claims select positive funded native LP and royalty rows separately in one exact
batch. A missing native ledger cannot be silently dropped to prepare a smaller
claim. Rarity affects royalties only; the existing ledgers remain unchanged.

## Presentation, errors and rollout

The form distinguishes the approved ceiling from the actual captured review
limit. Reviews show the captured maximum, minimum added LP, simulated added LP
when available, and separate gas. Prices, configuration or caps outside the
approved review reject preparation; no automatically widened quote follows.

Per-NFT history now uses the same complete-currency/raw/current-price/period
arithmetic checks as wallet history. Invalid or incomplete history stays
unavailable while valid current LP can remain displayed. Claims and conversions
remain distinct from new earnings. Missing prices or native ledger rows never
become a complete numeric total.

Unsigned review and token approval do not change LP or artwork. The existing
Anvil coordinator still requires the matching Entry receipt and confirmed active
position before activation/growth presentation. Claims refresh balances without
marking artwork as evolving. No signer or pending-journal behavior was changed.

The source update was built outside the existing website dist directory; its
repair overlay, local chain and journals are preserved. Do not deploy that old
overlay. Future rollout needs a clean separately approved build, matching API
configuration, exact RPC CSP/CORS, real routes/feeds, confirmed-native wallet and
recovery acceptance, marketplace qualification and independent release approval.
Publishing source is not enabling public signing or deploying services.
