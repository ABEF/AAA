# Served current3 website profile and fresh contract boundary

Fresh source now defaults to300bps total contribution loss (97% marginal LP).
This does not widen an independently approved client ceiling200, change old
runtime state or upgrade a saved review. Such a ceiling remains2% and refuses
a governed300 cap until separately re-reviewed. See [policy](EXECUTION_LOSS_POLICY.md).

**Mint-profile boundary:** accounting7 backend configuration explicitly selects
`mint_integration_version:2` for [SeaDrop mint2/schema17/V10](OPENSEA_MINT.md);
omitted/default1 retains direct-mint/V9. The local source9 website retains the
schema16/V9 contract profile and does not implement that V10 consumer. Reviewed matching deployment,
configuration and operating acceptance are still required. Existing services,
checkpoints, journals, served sites and Anvil signing are not upgraded or relabeled.


The separately served [poplint integration target](SITE_ENVIRONMENTS.md) uses the
explicit current3 reader/unsigned-review profile below. Its reviewed deployment
configuration remains absent. The fresh contract candidate is now
[accounting7/LP-allocation1/custody5/Portfolio2/direct Entry3](POSITION_V7.md)
with [mint2/canonicalV10/schema17](OPENSEA_MINT.md), which this website profile
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
| Budget | Explicit reviewed maximum contribution cap; an explicitly reviewed200bps ceiling permits98% marginal deployed LP. Captured actual governance cap and stronger caller/venue minima still apply |

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

## Local source9 implementation and fresh V10 boundary

The local [source9 frontend](SOURCE9_WEBSITE_PROFILE.md) implements the prior
V9/schema16 read/unsigned profile. It verifies accounting7/
LP-allocation1/custody5/portfolio2 and canonical
`ZZZ_CANONICAL_SAME_CHAIN_EXACT_LP_V9`, the immutable Rewards canonical child,
Manager/typed LP child/Balancer/math/policy,
execution-quality1/maintenance3/compound4/confirmation3 capabilities, exact runtimes
and both physical LP IDs/owners/keys/ticks at one canonical block. Desired-disabled
residuals remain included until merged; eight Position words alone are not compatibility.
It must distinguish terminal zero LP from unavailable data, unpaid holder
principal from rewards, and continuing royalty rights from ended LP earnings.
A matching eight-word Position alone does not establish browser compatibility.
The source9 schema16 graph has19 callable helpers plus2
inert Factory data children, including fixed Rewards.canonicalModule()/child
access()/rewards()/Handoff.moduleAt(3) bindings. Factory payload3 retains
FORMAT2 and is release-time verification, not per-claim data-child reads. Fresh7
raw earnings use exact LP books; checkpoint1 cannot seed them, while explicit
checkpoint2 is implemented for earnings endpoints. Actual matching service/site,
providers and workload qualification remain open; served current3 is unchanged.

Fresh mint2 instead requires canonicalV10/schema17 and20 callable helpers plus2
inert Factory data children, including the new mint helper. Its explicit backend
read/claim profile is implemented; source9 website support is not V10 support.
Review a matching consumer and configuration before adoption, rather than changing
an old manifest's schema or runtime labels.

The separate source8/accounting6/V8 read/unsigned candidate retains its own
source scope and is not fresh7 acceptance. Do not deploy fresh contracts under
served schema3, or relabel either old build/runtime/manifest as7.

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
independent audit. It is not fresh7/source9 acceptance. Production remains **NOT APPROVED**.
