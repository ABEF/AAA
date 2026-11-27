# Source9 website read and unsigned profile

**Mint-profile boundary:** reader/service versions named in this guide retain
their explicit profiles. In particular, source9/schema16/V9 is not V10. The new [SeaDrop mint2/schema17/V10 source](OPENSEA_MINT.md)
adds original-recipient mint books and needs matching reviewed consumers
before adoption. Existing services, checkpoints, journals, served sites and
Anvil signing are not upgraded or relabeled by the new source.


The fresh local website consumer uses **website manifest schema4**, explicitly
selecting source9/accounting7. This is separate from HTTP envelope schema2,
activation draft policy1/2, optional transaction policy1/2 and inventory schema16.
The served historical schema3/accounting3 poplint release is unchanged. Popldemo
remains a separate simulation. Both public build configuration inputs remain null.

## Required bindings

An operator-reviewed immutable build manifest pins the chain/genesis/deployment
anchor, canonical confirmation depth/age, same-origin API prefix, public read RPC,
read/activation/transaction configuration identities, fee reviews, fixed ETH/ZZZ
inputs and complete reviewed reward descriptors. Never discover configuration from
URL parameters, wallet metadata, local storage or an untrusted API response.

`deployment-source9.js` declares the exact required versions and29 browser-pinned
roles. These include current custody/reward/canonical modules, Policy, both LP
execution children and v4 venue dependencies. The browser checks runtime bytes,
typed parent/module bindings, capability versions and canonicalV9 at one canonical
confirmed hash. Six proof reads may run concurrently; duplicate same-block proofs
coalesce. This is a browser proof subset, not a replacement for the backend's
complete reviewed inventory/runtime verification or provider qualification.

Only native ETH and the fixed deployment ZZZ are contribution inputs. Original
royalty currencies have separately reviewed descriptors, including decimals and
bounded symbols; they are not contribution assets. No token peg is inferred.

## Complete wallet reads

Source9/schema4 and source10/schema5 recognize two explicit protocol capabilities.
`wallet_view_profile` is a read capability, not a website/contract schema or a
signing permission. Omitted capability retains the earlier ownership/totals/earnings
readers; unknown capability and failure of an advertised path never silently
downgrade to another profile.

| Capability | Read shape and completeness |
| --- | --- |
| `1` (default) | Existing fixed-block pages cover at most16 NFTs/four descriptors. Earnings need every NFT/currency page; LP and funded ETH summaries count once at currency offset0. Historical profile1 behavior is unchanged. |
| `2` (explicit opt-in) | Collect16-ID ownership/summary pages at `view/{block}/{nftOffset}/0`, then four-currency complete-wallet pages at `aggregate/{block}/{assetOffset}`. NFT pages carry `earnings:null` / `aggregate_earnings_required`; earnings are not repeated on that axis. |

The backend selects capability2 only with reviewed `wallet_read_batch:1`,
accounting7 and configured earnings history. Omitted/0 retains capability1.
This backend key is NOT a browser manifest key. A matching reviewed projection
identity and newly reviewed checkpoint semantic sources are required before
separate adoption; preserve original checkpoint, review, database and journal bytes.

Each aggregate page binds the full sorted current-owner inventory, count and
SHA256, the exact currency inventory, canonical block, history and lifecycle.
Successful financial verification has `verified_count == count` and `complete:true`.
An isolated `earnings_unavailable` envelope has `earnings:null`, `verified_count:0`
and `complete:false`; its full inventory identity does not replace the client's
independently verified ownership pages. Transport429/explicit503 `service_busy`
can also leave earnings unavailable after ownership/totals are complete. Generic
projection503, malformed proofs, conflicting batch replies, history/work failures,
expiry and reorg remain fatal. Never publish a partial currency sum as complete.

Original NFT units, independent LP/royalty components, the full86,400-second
history and current-holdings lifetime scope remain. Claims, conversions and
principal returns are not new income. Raw NFT earnings are summed per currency
before USD rounding; missing prices stay unavailable except exact zero amounts.
LP value and funded ETH totals remain independent of earnings availability.

Capability2 reduces the1,000-NFT/66-descriptor core wallet grid from63*17 to63+17
GETs:63 ownership/summary pages plus17 aggregate currency pages. Protocol and
eight-card/NFT-earnings reads are additional. Request counts are not actual
provider/HTTP/full-normal-F6/V10 freshness acceptance. The original profile1
[compact-wallet record](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/compact-wallet-20261121/REVIEW.md)
retains its narrower three-currency and sixteen-NFT scopes.

The read tool uses pinned constructor-only bytecode in canonical creation
`eth_call`, with fixed bounded STATICCALL getters and finite return data. It
does not deploy code, override state, sign or send value. Each constructor call
covers at mostfour NFTs; prefetch accepts at most16 IDs and four royalty
currencies. The24M call allowance is read-RPC execution, not a raised transaction gas policy.
Actual provider support and maximum workloads still require qualification.

Current-profile GETs retain one active request, starts at least one second apart
and at most32 queued, with no automatic retry. All pages and final canonical,
identity and freshness checks must pass, including the check after independently
confirmed card reads. Cancellation or supersession rejects the result. Cards are
not claimed to share the fixed financial block. Signing and public configurations
remain unchanged. See the [backend wire](FRONTEND_API.md),
[operator manual](OPERATOR_MANUAL.md) and [current review](../reports/CURRENT_REVIEW.md).

## Reads and user reviews

| Flow | Fresh behavior |
| --- | --- |
| Holdings and collection | Reuse complete bounded inventories and same-block aggregation. Verify both physical LP identities, share context, current owner and lifecycle. Missing or inconsistent data is unavailable/error. |
| Earnings | Whole-unit LP and original-currency royalty history; current prices, complete raw24-hour suffix and explicit checkpoint2. Claims, conversions and principal returns are not income. |
| Rewards | Claimable ETH includes credited LP conversion and ETH royalties. Pending LP ZZZ remains a separate exact source quantity. Original non-ETH royalties remain separate currencies; no cross-currency sum or royalty swap. |
| Activation/growth | Read scoped Policy minima/fingerprint, stronger pool minima and two-source price bounds at the same hash. Reconstruct direct Entry3's seven-field tuple plus reviewed loss maximum and policy hash. Verify entrant-only marginal LP proof and exact final simulation. No Entry conversion route fields. |
| Approval | Exact selected ZZZ amount to pinned Entry only. Approval adds no LP; a confirmed approval requires complete fresh preparation. No unlimited approval or automatic reset/retry. |
| Claims | Explicit selection, bounded gas-aware plan, all entries classified. Only the next batch has executable unsigned calldata. No automatic queue, omitted entries, signing or sending. Replan remaining entries after confirmation. |
| Terminal exit | Separate ETH/ZZZ principal allocation/remaining/paid state and current beneficiary. No principal-distribution action is added to the user reward flow. NFTs retain old rewards and royalties; contributions remain disabled. |
| Artwork | Governed metadata thresholds, confirmed valuation and existing four variants. LP-exited uses the on-chain activated-image fallback with an explicit exited label. No image or sound is updated by an unsigned review. |
| Mint | Website mint remains a demonstration; fresh source9 exposes no direct mint review, including on loopback. Actual OpenSea integration remains unqualified. |

## Gas policies and operation

The manifest must choose `transaction_policy_schema:1` or `2`. Policy1 retains
the12M historical budget. Policy2 requires matching reviewed configuration,
confirmed-block gas limit and full20% estimate headroom, bounded by the64M
engineering ceiling and the operator's lower website ceilings. Activation is
separately selected: absent/1 `activation_policy_schema` retains schema1/12M;
explicit2 requires activation configuration/draft schema2 with reviewed
`max_gas_limit` and `max_network_fee_wei`, the same confirmed block gas limit and
full20% headroom. Website `limits.gas` caps both; policy1 claims remain capped
at12M even if activation2 uses a higher limit. No automatic widening occurs.
These are unsigned engineering checks, not gas reimbursement or target-chain
capacity approval.

1. Select actual deployment/API/provider/fee manifests and independently review
   exact runtime/profile bindings. Do not reuse old source8/current3 identities.
2. Prepare a separately reviewed `integration-config.js` source9 manifest. Keep it
   null until those real inputs exist. Source9 never constructs the local signer.
3. Run the website checks and build to a **new** `dist-poplint-*` directory. Preserve
   existing dist, local chain, wallets and journals. Inspect `site-identity.json`
   and checksums; a new build is not a running-site update.
4. Separately authorize any API/configuration/site rollout and rehearse actual
   runtime responses, feeds, history/archive, original-currency faults, large claim
   batches and moving-price contribution traces. Keep popldemo isolated.
5. Recover from a bad source/configuration release by restoring its reviewed
   integration artifact; never rewrite or relabel saved transaction journals.

No service restart, public signing, chain reset, deployment or heartbeat restart
is part of source publication. See [verification](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/source9-website-20261109/REVIEW.md)
and the [environment map](SITE_ENVIRONMENTS.md). The [actual fork follow-up](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/source9-actual-entry-20261109/REVIEW.md)
verifies ETH/ZZZ activation/growth through real unsigned consumer/API reviews,
with explicit synthetic external depth and controlled feeds/VRF. Unmodified
market depth failed safely. Actual market/provider/browser-wallet acceptance,
authorities, OpenSea, hosting and independent audit remain open.
