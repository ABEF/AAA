# Current native production inventory and read-only preflight

Current fresh source: **accounting4 / custody3 / canonical holder-exit V5**.
[Collective holder return](HOLDER_COLLECTIVE_EXIT.md) replaces external principal
and royalty custody exits. Governance permanently ends LP and pays actual
ETH+ZZZ by shares; NFTs retain transfers, future royalties and earned rewards.
No external recipient/bridge/return ingress remains. Whole-collection handoff
is available only before exit. Earlier source-scoped evidence and accounting3
service/inventory/website qualification remain historical to their original pins.
See [profile4](POSITION_V4.md); new release qualification remains open.



## Current release scope

[Current scope](SIMPLIFIED_RELEASE.md): ETH/ZZZ-only contributions, actual local LP
fees, no creator inboxes or integrated cross-chain bridge. Preserve same-chain
pool moves, external custody exit/recovery, royalty currencies and complete
collection handoff. Current fee/custody profiles and canonical schema are
explicit; old deployments/journals keep historical profiles.

## Mint qualification boundary

Current release CLI validation requires **schema5, accounting_version3,
fee_intake_version1 and mint_integration_version1**.
Missing/zero/boolean profiles and schema4 are blocked by default. Only explicit
`--historical-consistency` inspects historical layouts, with current_release_gate
false and no production qualification. Library-level legacy consistency remains
available to historical consumers; it must not be used as a release approval.

Current profile1 truthfully blocks OpenSea primary mint because the existing
direct paid Vault mint cannot implement SeaDrop's recipient/payment interface.
See [mint/VRF requirements](MINT_INTEGRATION_QUALIFICATION.md) and the
[scoped verification](../reports/release-services-20261025/vrf-opensea/VERIFICATION.md).
Its code-owned unsupported state cannot be overridden by manifest evidence.

## Reviewed Entry policy

The current undeployed pricing-V2 candidate uses
`executeReviewed(Request,uint16 maximumLossBps)` with explicit
`review_policy_version: 1` in activation/release profiles and matching Entry/Pricing
getters. It rejects a captured governed cap above the caller maximum before
funds move, retaining all final price/LP/policy checks. Legacy execute is disabled
on the new code; historical pricing-V1/local deployments retain original ABI.
Read [policy and exact compatibility boundaries](EXECUTION_LOSS_POLICY.md#review-time-policy-binding)
and [scoped evidence](../reports/comprehensive-improvement-20261025/VERIFICATION.md).
Explicit-profile native read/unsigned browser integration is implemented; actual native
deployment/provider/wallet qualification remains open;
no existing chain, website build, journal or public signer was upgraded.


The current candidate uses **schema5**, local Position accounting3, typed routing2,
explicit **`pricing_version: 2`** and governed custody. The offline validator checks declared policy against a
complete pinned observation and required qualification records. A separate
observer reads deployed contracts. Neither tool signs, deploys, seals, moves funds
or authorizes a release. The checked-in example is deliberately unqualified.

Legacy schema 4 keeps its historical interpretation, including its refusal to
approve the governed/native layout. Its previous blocked template is preserved as
[production.legacy-v4.example.json](../config/production.legacy-v4.example.json). Do not relabel old WETH contracts, state or
journals as the current profile. Accounting2/LP-only V3 snapshots likewise remain
historical and are not current localV4 snapshots. Start a separate current-version inventory with exact
deployment-specific runtime hashes, including immutable constructor values.

## What is inventoried

| Area | Current checks |
| --- | --- |
| Core | Access plus its 16 current sealed modules, exact bindings, unique addresses, active canonical state and no bootstrap authority. Access `GOVERNANCE_VERSION=2`, actual `governance()` and zero `pendingGovernance()`; keeper/guardian grants and reviewed actual governance wallet/signature policy. The sole operator may use one signer/threshold1; the existing inventory key `multisig` does not mandate multiple people. No current Timelock roles, schedule/execute methods or delay fields. Retired bridge/receiver/routes/transport slots must be zero. |
| Helpers | Fifteen fixed helpers: activation assets/Entry, Oracle-created contribution pricing, Budget, custody validation, royalty ledger/renderer/claim router, two factories, two converters and three parent-bound v4 executors. Verify pricing `oracle`/`access`, inactive context and every actual getter; do not assume all helpers expose `access()`. |
| USD pricing | Explicit pricing V2, full append-only two-source policies, active IDs/ordinals, source runtime/precision/round/freshness checks and independently recomputed lower/upper/fingerprint. Independent source and proxy/common-mode reviews remain required for each asset; observing agreement never approves it. |
| Native identity | Vault accounting version3, eight-word local Positions and exact `ZZZ_CANONICAL_SAME_CHAIN_NATIVE_LP_ONLY_V4` canonical schema. Current statuses None0/Active1/Outbound2/Dormant3/Parked4. Native currency zero has18decimals and no runtime hash; reward/royalty admission stays separate. No wrapper substitution, invented remote fields or legacy-codec import. |
| Governed policy | Current contribution, maintenance, LP-conversion and royalty-conversion limits must match the reviewed settings at the same block. Hard maxima are 1,000 bps; defaults are not substituted for missing observations. Gas, caller/venue minimums and original custody approval floors remain separate. |
| Principal and conversion | One selected contribution pool, actual ordered currencies, hook/fee/spacing/runtime bindings and independent prices. Direct, typed v3 and typed v4 routes retain separate identities. Conversion pools do not become principal pools merely by being listed. |
| Qualification | Exact-chain asset/feed review, complete inventory history, governance, VRF, content publication, services, gas/recovery rehearsals and independent audit/remediation. Missing decisions remain blockers. |

Current scope is the explicitly supported canonical native deployment and reviewed
same-chain lineage without external creator-reward inboxes. Current Fees exposes
`FEE_INTAKE_VERSION=1`; removed receiver factory/count selectors and helpers cannot
be added to its inventory. The separate historical fee0 inspection still checks
its original zero-receiver requirement; it does not qualify current code. Future-chain
canonical handoff, atomic ETH/WETH principal
moves and legacy-schema import are not enabled by this inventory. External custody
recipients still require explicit governance trust and their own actual recovery
qualification; a pool-migration mechanism does not relocate NFT ownership.

## Two-source pricing records

Every priced token record supplies its complete `price_policy`: policy ID/ordinal,
14-word dual policy, both source observations and independent source/pair review.
The source addresses and declared independence IDs must differ; each runtime must
match its own approved pin, but identical adapter code is not itself forbidden.
Different labels alone do not prove independent markets or reporters. Native ETH
is asset zero, not a WETH-priced alias. USDG and USDC need
actual depeg-aware USD observations. The user-selected agreement tolerance is
300 bps (3%). Production source addresses and freshness settings remain unset.
A price inside that band must still satisfy the separate execution-loss floor.

The observer recomputes policy identity, both normalized bounds and the exact
chain/Oracle/policy/round/sequencer fingerprint at the confirmed timestamp. It
cannot create independent review evidence or repair a missing source. Missing or
disagreeing prices remain unavailable. Legacy single-feed profiles retain their
original code/epoch semantics; they do not qualify this new runtime. See
[implementation and trust boundaries](PRICE_SECURITY.md).

## Prepare and validate the inventory

Run these commands from the repository root with your installed Python command
(`python3` or `python`):

```bash
python3 scripts/validate-production-config.py --config config/production.example.json
```

The example must return blocked. Its known selected-pool references are intended
identities, not passing runtime/feed/provider observations. Unknown PoPL addresses,
wallets, independent ZZZ pricing, routes and service approvals remain unset.

1. Copy the example to a release-specific inventory. Choose the exact source
   commit, network/genesis, public authority addresses and actual deployment.
   Keep private keys, RPC credentials, API tokens and signer material outside it.
2. Review intended module/helper/dependency addresses, immutable bindings and
   deployed runtime pins independently. **Do not copy observed hashes into approved
   pins automatically.** Record current loss settings deliberately, not by assuming
   the defaults. Review [execution policy](EXECUTION_LOSS_POLICY.md).
3. Choose a recent confirmed block with its exact number, hash and timestamp,
   minimum confirmation policy and genesis hash. Retain the reviewed anchor.
4. Collect actual read-only observations, preserving the original inventory:

```bash
python3 scripts/observe-production-config.py --config reviewed.json --rpc-env POPL_RELEASE_RPC_URL --output observed.json
```

`POPL_RELEASE_RPC_URL` names an environment variable containing only the read RPC
endpoint. The tool reads that named variable; it does not discover wallet keys or
print the endpoint. Optional `--block-number N --expected-block-hash 0x...` must
both exactly match the inventory anchor. There is no latest-state fallback.

5. Run the offline gate against the observed manifest and intended revision:

```bash
python3 scripts/validate-production-config.py --config observed.json --expected-commit RELEASE_COMMIT --output preflight.json
```

Replace `RELEASE_COMMIT` with the exact 40-character Git commit. The report lists
paths, blocker groups and corrective actions. A consistent manifest is not proof
that its evidence is authentic; retain original receipts, independent reports and
reviewer decisions. Final approval remains in the [release record](RELEASE_CHECKLIST.md).

## Observation, completeness and failures

The observer uses one EIP-1898 block hash with `requireCanonical`, checks network,
genesis and confirmation depth, and rechecks the anchor before publishing output.
Observed runtime hashes and getters remain separate from approved pins. Missing,
malformed, reverted or mismatched observations are unavailable, not invented zero
values. No observation marks a feed, route, provider or audit as qualified.

Principal-pool and typed-v4-route slot0 observations use exact integer v4
TickMath validation: initialized sqrt price in `[MIN_SQRT, MAX_SQRT)`, stored
tick in `[MIN_TICK, MAX_TICK)`, and
`sqrtAtTick(tick) <= sqrtPriceX96 <= sqrtAtTick(tick + 1)`. Canonical ABI integers,
both packed 12-bit protocol-fee directions (at most 1,000 pips each), and a valid
stored LP fee are required. The offline gate additionally requires the reviewed
static LP fee and applies the same value checks to manually supplied inventories,
not only observer output. A genuine exact downward crossing can leave the stored
tick one below the boundary; retain it rather than replacing it with a floor tick. This validates
existing slot0 fields without adding RPC calls or changing the inventory schema.

Pool and route mappings cannot all be enumerated from their getters. The observer
checks declared IDs; complete creation-to-anchor event/history review is still
required to prove no admitted policy was omitted. Enumerated asset/receiver lists
must reconcile their actual counts and ordered contents. Never truncate history
or omit an unavailable record to obtain a passing report.

Fresh observations and historical qualification have different anchors. The
observer must match the current inventory block exactly. A retained rehearsal
keeps its real earlier block and exact release/deployment/configuration scope;
do not relabel it as a new test. Pool, authority, source-policy, route, asset and
loss-setting changes invalidate the corresponding configuration evidence. Complete
admission history must still reach the current anchor. An unchanged audit or
rehearsal does not need to run again solely because a newer block is observed.
Enabled v4 route evidence also binds the current LP fee and packed directional
protocol-fee configuration. A fee change requires corresponding requalification.
Every actual operation still requires fresh complete simulation and validation;
this observer does not simulate or authorize a financial action.

The observer bounds input/output size, code size, list lengths, total RPC work and
elapsed time. Each getter call also has an explicit 1,000,000 gas read limit;
no network transaction or gas payment is submitted. A supported but expensive inventory can exhaust those budgets:
investigate provider latency and the explicit limits; do not silently drop checks.
HTTP is restricted to loopback; external endpoints require HTTPS.

Observer exit 0 means the scoped reads completed; exit 2 means partial or
mismatched observations; exit 1 means the observation failed. Network/genesis,
anchor/reorg or global failures preserve the previous output. Report replacement
is atomic. Config and output must differ. Errors are sanitized; original RPC
exceptions and credentials are not report content.

The offline gate exits 0 only for consistent reviewed input and 1 when blocked.
It rejects duplicate JSON keys, nonfinite numbers and oversized input. It refuses
to overwrite its own input and writes reports atomically. On output failure,
retain the old report and inspect the concise failure; do not call it current.

After any asset/route/feed/role/cap/deployment change, take a fresh coherent
snapshot, reconcile pending transactions and rerun the affected checks. Historical
evidence retains its original source and deployment scope. No tests or observed
values upgrade a legacy contract or approve a new service automatically.

Actual providers, routes, authorities, OpenSea mint, native website/services and
independent audit remain release tasks in the [single Todo](../TODO.md).

## Configuration digest helpers

Pool and governance qualification records use the maintained projections in
`zzz_ops.production_v2`. Compute their SHA-256 values from reviewed input, then
have the reviewer bind the corresponding original evidence to those values.
Computing a digest does not create a passing review:

```python
import json
from zzz_ops.production_v2 import configuration_hash, pool_configuration, governance_configuration

with open("reviewed.json", encoding="utf-8") as source:
    chain = json.load(source)["chains"][0]
print(configuration_hash(governance_configuration(chain)))
for pool in chain["pools"]:
    print(pool["pool_id"], configuration_hash(pool_configuration(chain, pool)))
```

Keep actual tested blocks, report hashes and independent decisions intact. Do
not update evidence merely to silence a configuration mismatch. See the
[scoped verification](../reports/native-preflight/VERIFICATION.md).
