# Served current3 website profile and fresh4 boundary

The separately served [poplint integration target](SITE_ENVIRONMENTS.md) uses the
explicit current3 reader/unsigned-review profile below. Its reviewed deployment
configuration remains absent. The fresh contract candidate is now
[accounting4/custody3/canonical V5](POSITION_V4.md), which this website profile
does not support. Neither source publication nor changing a manifest's version
upgrades the served build, a schema1/native2 deployment or an existing journal.
Public signing remains disabled.

| Boundary | Required value |
| --- | --- |
| Website manifest | `schema: 3`, `mode: "read-and-prepare"` |
| Contract versions | `accounting_version: 3`, `governance_version: 2`, `fee_intake_version: 1`, `pricing_version: 2`, `routing_version: 2`, `review_policy_version: 1` |
| Canonical schema | Exact `CURRENT_CANONICAL_SCHEMA` from `deployment-native.js`, matching `ZZZ_CANONICAL_SAME_CHAIN_NATIVE_LP_ONLY_V4` |
| Browser runtime pins | Distinct reviewed `access`, `nft`, `vault`, `entry`, `claim_router`, `oracle`, `pools`, `budget`, `activation_assets`, `contribution_pricing`, `fees`, `handoff` |
| Inputs | Exactly native ETH/zero/18 and the fixed deployment ZZZ; reviewed runtime, decimals, policy IDs, typed route and enabled state |
| HTTP response schema | Remains schema2; website manifest and API envelope versions are independent |
| Position data | Accounting3/local eight-word codec selected by the backend; its status/valuation rules do not implement accounting4's terminal holder-exit state |
| Budget | Explicit reviewed maximum contribution cap; default200bps permits98% marginal deployed LP. Captured actual governance cap and stronger caller/venue minima still apply |

At a canonical pinned block, the browser verifies reviewed runtime code,
versions, parent/module bindings, sealed governance and canonical chain/schema,
fixed ZZZ identity and admission/price/route policy. It does not infer compatibility
from tuple length or accept an API version label in place of these checks. The
backend independently retains its complete approved projection/transaction pins.

Current DTOs reject retired remote/inbound states, incompatible accounting
versions, inconsistent activation/rarity/share fields and contradictory valuation
states. Actual LP, ETH claimable and history may be unavailable independently;
never invent zero or display an unconverted source balance as ETH. A confirmed
claim is a payout, not new income or an artwork evolution.

## Fresh4 integration still required

A new explicitly versioned frontend profile must verify accounting4/custody3,
canonical `ZZZ_CANONICAL_SAME_CHAIN_HOLDER_EXIT_V5`, current Manager/Balancer,
execution-quality and rebalance-confirmation capabilities, exact runtimes and
their parent/core bindings.
It must distinguish terminal zero LP from unavailable data, unpaid holder
principal from rewards, and continuing royalty rights from ended LP earnings.
The backend's current accounting4 support or a matching eight-word position
length does not establish browser compatibility. Do not deploy fresh contracts
under schema3 or relabel the current3 artifact as fresh4.

The earlier downloadable dormant-metadata defect was corrected in website source
`cae44a1d`: reference JSON and the generator preserve fixed rarity1/2/3 independently
of activation eligibility. The2,784SVGs, manifest, historical72metadata, signer
and public configuration were preserved. Source publication did not rebuild or
deploy a site or qualify an IPFS bundle. Current3's confirmed upgrade audio/effects
remain a separate consumer gap. See [source correction](../reports/whole-project-execution-20261029/REVIEW.md)
and [original findings](../reports/whole-project-audit-20261029/REVIEW.md).

## Configuration and rollout

1. Keep `integration-config.js` null until actual chain/genesis/deployment block,
   runtimes, complete asset policies and same-origin API configuration have been
   independently reviewed. Do not use fixture addresses from tests.
2. Obtain a consistent configuration from the reviewed inventory and API hashes.
   Preserve every standard freshness, gas/value, native ETH, canonical block,
   currency and lineage bound. The enabled origin and Nginx `connect-src` must
   explicitly admit reviewed read endpoints; do not add wildcard RPC access.
3. Use only the integration build and installer. Check `site-identity.json`,
   source revision and SHA256SUMS, then follow the [environment procedure](SITE_ENVIRONMENTS.md).
   An unconfigured landing page is a valid fail-closed state, not live acceptance.
4. Qualify real holdings, earnings/history coverage, exact ZZZ approvals,
   activation/growth quotes, ETH claims, account changes and provider failures
   against that exact deployed configuration before release sign-off.
5. Public submission remains unavailable. Local Anvil signing and saved-hash
   recovery retain their existing code/profile; this change does not authorize
   extending the signer, public minting or real-fund transactions.

The served-profile [verification](../reports/current3-website-20261026/VERIFICATION.md)
uses actual Python projection/preparation DTO code with synthetic RPC, venue,
price and authority dependencies. It verifies integration behavior, not real
prices, provider authenticity, deployed contracts, marketplace operation or an
independent audit. It is not fresh4 acceptance. Production remains **NOT APPROVED**.
