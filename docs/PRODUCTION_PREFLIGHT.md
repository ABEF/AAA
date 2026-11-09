# Current production inventory and read-only preflight

Fresh source: [accounting7 / exact LP1 / custody5 / portfolio2](POSITION_V7.md),
canonicalV10 and inventory17. **Undeployed; production NOT APPROVED.** The
[exact-LP integration record](../reports/exact-lp-integration-20261106/VERIFICATION.md)
binds its changed LP ledger, typed canonical companion and consumers. Earlier
[moving-market](../reports/moving-market-flows-20261106/VERIFICATION.md) and
[factory/claims](../reports/factory-claims-20261105/REVIEW.md) reports retain their
original runtime/source scopes. Authenticate the complete matching graph before
any fresh deployment; source publication never upgrades existing Anvil, service,
website, inventory or journal identities.
Real dependencies, operating rehearsals and independent audit remain open.

The [schema17 example](../config/production.example.json) is deliberately
unqualified. Unknown deployment/authority/provider addresses, source/route
qualification and observations stay null. Intended settings and known Robinhood
dependency references are not fresh on-chain evidence. No command below signs,
deploys, seals, changes a service or authorizes spending.

Fresh custody5 makes terminal principal allocation and distribution governance-only;
NFT-owner reward claims and owner fallback remain unchanged. Schema9/custody4
is retained verbatim in [the historical example](../config/production.direct-entry3.example.json)
and only the explicit historical CLI mode can inspect it. Fresh read/keeper
configs require custody_version5; new keeper principal_distribution must remain
disabled. Runtime/config/receipt provenance is never upgraded by changing a label.

## Current release scope

One fixed ZZZ/native ETH pair, one contribution destination at a time, independent
NFT share/reward accounting and optional bounded main/residual custody. No creator
inboxes, bridge, remote ownership ledger or external custody-address exit.
Governance may move to another reviewed native ETH/ZZZ pool, park all legs, or
permanently return actual principal to current NFT owners. Same-chain canonical
handoff remains pre-exit only and requires no live residual during parked export.

Schema17 explicitly requires royalty settlement4/recovery2/reporting5,
accounting7, LP-allocation1, custody5, governance2, fee intake1,
Strategy maintenance3, confirmation3, portfolio2, Budget compound4, emergency2,
LP routing2, quality1, Entry routing3, pricing2, entry-review-policy2 and mint
integration2/helper1. The predeployed metadata renderer is passed as the third
NFT constructor argument; the collection-specific mint helper is bound once
before sealing/any mint. A matching
canonicalV10 wire does not make an old accounting profile current. Unknown,
missing, boolean and inconsistent versions fail closed.

There are 17 modules including Access, 20 logical callable helpers and exactly
2 inert factory code-data children. Optional creator inboxes, Entry conversion,
royalty conversion and bridge helpers are removed. The LP converter and its v4
executor remain separate from original-currency royalty claims. Budget, Balancer, PortfolioPolicy and Confirmation are
standalone fixed-controller companions whose parent getters resolve the sealed
Access module with reciprocal binding; no mutable parent setter is admitted.
Manager's fixed typed physical executor is a contract, not a new human operator.
Verify its Manager/core/state/PosM/Permit2/router wiring, the Balancer arithmetic
child, actual runtime pins and every code-owned getter. Never assume all helpers
have the same interface or expose `access()`.

Rewards creates one immutable `ZZZRewardsCanonical` companion. Verify
Rewards.canonicalModule(), child access()/rewards(), Handoff.moduleAt(3),
Rewards.LP_ALLOCATION_VERSION()==1 and MAX_ASSETS()==2 with their exact runtime
pins. LP reward backing remains in Rewards; principal stays Vault-managed. The
child has only typed canonical authority.
LP funding assets are exactly native ETH plus the fixed ZZZ, separately from
original-currency royalties. V10 retains V9's pending whole units, high/low phase and
direct credits; historical6/V8 indices are not translated or relabeled. The
terminal holder-return record keeps the accounting6/custody4-format wire under
custody5; it is separate from the exact LP-reward domain retained within V10.

Historical [schema16](../config/production.schema16.example.json),
[schema15](../config/production.schema15.example.json),
[schema14](../config/production.schema14.example.json), [schema13](../config/production.schema13.example.json), schema12,
schema10/custody5, schema9/custody4/direct Entry3 and schema8/routed Entry2 remain
available only through explicit
`--historical-consistency`, using its own observer and validator. The current
example has no Entry conversion descriptor or child; it is never rewritten to
schema8 to obtain a pass. Live qualification and actual rollout remain separate.

## Immutable factory code-data records

The current `factory_code` section declares fixed code-storage version2, whole
creation length/hash and exactly two ordered child records. Each record contains
its own nonzero address, source-derived data/runtime lengths and full runtime
hash. Addresses and observations in the template remain null. The fixed source
artifact is [factory-code-storage-v3.json](../config/factory-code-storage-v3.json):
payload identity3, while the immutable runtime FORMAT remains2. Historical
schema14/15 retain their separate payload2 artifact;
it is not generated from live getter answers or adopted RPC hashes.

The observer adds two bounded `eth_getCode` reads using the same canonical block
selector as all contract reads. It verifies the exact `0x5f5ffd` revert prefix,
both ordered full-runtime lengths/hashes and reconstructed original creation
length/hash. Missing, swapped, duplicate, truncated or unexpected parts fail
closed; a failed read clears prior positive observations. Factory typed getters
must bind those same pointers/hashes. Children cannot alias protocol modules,
helpers, dependencies, tokens or the future mint-payment recipient.

Keep the factory-code qualification review and full independently reviewed
runtime pins. CanonicalV10 does not explicitly enumerate the factory/data-child
hashes; the full schema17 release graph authenticates
them separately. Ordinary mint, LP and claim operations add no child-code reads.
These inert children are neither authorities nor royalty recipients. See the
[fixed code-storage procedure](FACTORY_CODE_STORAGE.md) for exact format,
constructor boundaries, failure handling and actual target-gas qualifications.

## Current buyback maximum and creation history

Fresh schema17 requires `chains[].buyback_maximum_usd18`: the reviewed current
`Buyback.maxTradeUSD()` in USD18, positive and at most uint128.max. It is matched
to the exact pinned live getter. `operating_buyback_usd18` must not exceed it.
`constructor.maximum_buyback_usd18` remains the original creation value; do not
rewrite it after `setMaximumTradeUSD` or use it as a fallback for missing current
configuration. Raise/lower ordering remains in the [operator procedure](OPERATOR_MANUAL.md#future-operating-settings).

Incomplete records must be reviewed/completed for their actual profile and observed again;
missing/invalid current declarations and non-object chain records fail before
RPC. The example remains null/unqualified. Historical profiles retain their own
formats; neither this field nor an on-chain setting change upgrades a journal,
service or old runtime.

## Selected contribution reservation

`contribution_reservation` contains `pool_id`, current/alias/canonical bucket IDs,
`target_registered`, actual bucket count and maximum 4. The observer derives
registration only from its own successful complete `bucketAt/bucketCount`
inventory at the exact anchor. Registration is private; no public
`registeredBucket` getter exists. Failed/incomplete reads or prepopulated JSON
are not proof. No guessed zero/false defaults are admitted.

The offline `contribution_reservation_status` is a consistency diagnostic,
not transaction approval. Price, route, pool admission, current owner, execution,
capacity, lifecycle and gas still need independent qualification. See the
[operator procedure](OPERATOR_MANUAL.md#one-contribution-pool-at-a-time).

<a id="current-schema6-observation-and-offline-validation"></a>

## Current schema17 observation and offline validation

[Validator](../zzz_ops/production_v15.py) and
[observer](../zzz_ops/production_observer_v15.py) authenticate schema17/mint2/V10,
original-recipient/phase/lifetime mint books, the fixed helper/SeaDrop graph and
reviewed current drop configuration. They retain residual-reinvest1 on
Migration/Vault/Budget/Policy/Pricing and raw-exit1 on the fixed closure graph.
Exact runtime/configuration consistency does not approve opaque proof contents,
actual onboarding, fees/payers, provider operation or deployment. The current
seal function does not prove this entire semantic/runtime graph; preflight it
before irreversible binding.
They operate directly on the fresh layout; no manifest is rewritten as accounting4
to obtain a historical pass. All contract/code/native-balance reads share one
EIP-1898 block hash with `requireCanonical`. Genesis, confirmation depth, final
canonical anchor/time and runtime/parent bindings must remain coherent.

Each active bucket records its actual main ID plus explicit portfolio:

- Zero or one secondary, both Vault-owned, no reused or third physical ID.
- Exact PoolKey hash, packed periphery1.0.3 PoolId prefix/subscriber flag, signed
  physical ticks, spacing and positive uint128 liquidity for each leg.
- Each leg's token amounts, independently recomputed from current slot0, actual
  bounds and liquidity; the portfolio total must equal their exact sum. Raw
  liquidity values from different ranges are never added as a NAV measure.
- Stable `portfolioFingerprint` binds physical IDs, keys/bounds and custody.
  Separate `executionPortfolioFingerprint` also binds liquidity for custody
  manifests. Both encodings are checked independently.
- Desired mode/geometry/trigger and actual applied revision remain separate from
  auxiliary presence. A disable request can legitimately leave a live residual
  until guarded merge; enabled mode can have no useful residual.
- Exact `PortfolioPolicy.controlFingerprint`, monotonic
  applied<=geometry<=global revisions and review hashes for nondefault controls.
  Complete registered inventory must match global `activeSecondaryCount<=4`.

No physical portfolio is invented for parked/closed/empty custody. Pending
compound, idle, buyback and earned-reward backing keep separate classifications.
The configured main floor(default60%, governed6000–9999bps) and complementary
residual ceiling(default40%) form a post-adjustment invariant using the captured
vector, not a continuously enforced ratio inferred from today's inventory.
Actual execution/economic qualification must cover its operation boundary.

<a id="confirmation2-and-emergency1-inventory"></a>

### Confirmation3 and emergency2 inventory

The selected initial policy is 600 seconds sampled confirmation, strict 300 second
maximum confirmed gap and 240 second source checks. Gap0 stops ordinary readiness;
constructor defaults are not qualification. Observe actual review hashes,
revisions, helper/Budget/Strategy capabilities and inactive emergency context.

Ordinary threshold sides are independently recomputed using 85% of actual
centre-to-main-boundary ZZZ-in-ETH price distance, not a tick/sqrt fraction or
an 85% token-price change. Physical/reference same-side samples can exist during
cooldown while raw execution need and readiness remain false. Stored samples,
raw need, cooldown and final readiness are distinct records. Side1/2 are raw
pool-ratio directions; side1 means higher ZZZ-in-ETH price, side2 lower.

Manual width/mode/active residual-geometry repair preserves the hard cooldown and
ordinary financial/price checks but skips threshold interpolation. Its threshold
sides/reference are unavailable rather than guessed zero. This permits repair
of an old centre outside emergency bounds. Ordinary invalid geometry remains
fail-closed. Pause/preparation/terminal state suppresses new readiness without
erasing historical observations. Source late enrollment of paid observations
is a scheduling/gas rule, not an additional on-chain parameter or proof of the
preceding cooldown's market history.

The observer enumerates at most 4buckets and 1,000mint ordinals. NFT shares,
settlement snapshots, frozen counts/cursors, cumulative-floor allocations,
paid/claimable flags and actual remaining ETH/ZZZ backing must reconcile. A
collective exit remains terminal for new principal/mint release readiness;
old reward claims and future royalties are separate. Prefunds may exceed
liabilities but cannot become fabricated income or allocated principal.

## Exact build provenance

The current factory-code artifact is derived from the final closed normal
compiler output and its complete87-source/settings snapshot. Its receiver
creation hash is
`0x0b5b619ca10d338f29e7a76fd3f9069b2e034864112bbd3101bbc20a279c50aa`.
Forge can normalize source line endings or add unused auto-detected remappings
to metadata, producing different
creation bytes with equivalent settings. A different artifact family is not a
matching release. Use the reviewed exact artifacts, or review and re-pin the
complete new build and graph. The observer never replaces these expected pins
with live or independently rebuilt values. Local comparison gas and normal size
checks retain their own artifact scopes; neither establishes target acceptance.

## Run the current tools

Copy the current example to a reviewed public-data inventory, independently
supply actual addresses/pins/source commit, confirmed anchor and review records.
Keep credentials, keys and endpoints outside the manifest. Then run:

```bash
python3 scripts/observe-production-config.py --config reviewed-schema17.json --rpc-env POPL_RELEASE_RPC_URL --output observed-schema17.json
python3 scripts/validate-production-config.py --config observed-schema17.json --expected-commit RELEASE_COMMIT --output preflight-schema17.json
```

`POPL_RELEASE_RPC_URL` names a read-only endpoint environment variable; its
contents are never printed. Optional `--block-number N --expected-block-hash H`
must both exactly match the reviewed anchor. There is no latest-state fallback.
`RELEASE_COMMIT` is the exact40-character commit, not a moving branch name.

The observer is bounded to 12,000RPC reads and 60 seconds, with bounded code/input/
output sizes and an explicit getter gas ceiling. These are safeguards, not proof
that a1,000-NFT inventory completes on a particular provider. A timeout or
partial read stays unavailable; never omit records to make the budget pass.
Actual provider capacity, cost, freshness and target-host latency remain gates.

`inventory_consistent` means supplied-data consistency. `ready` and
`deployment_authorized` stay false: actual OpenSea primary-drop integration is
not supplied by the current direct mint, and metadata cannot add that interface.
Real feeds/routes/VRF/authorities, complete history, current services/gas and
independent audit/remediation remain mandatory.

## Historical inspection only

The [profile4 scaffold](../config/production.holder-exit.example.json), frozen
[schema6 validator](../zzz_ops/production_v4.py) and [observer](../zzz_ops/production_observer_v4.py)
retain accounting4/custody3 single-position meanings. Schema5/accounting3 and
[earlier example](../config/production.legacy-v4.example.json) remain older scopes.
Both CLIs require explicit historical inspection; neither qualifies the new release:

```bash
python3 scripts/observe-production-config.py --config reviewed-historical.json --historical-consistency --rpc-env POPL_RELEASE_RPC_URL --output observed-historical.json
python3 scripts/validate-production-config.py --config observed-historical.json --historical-consistency --output preflight-historical.json
```

Do not relabel old contracts, journal namespaces, observed fields, provider
rehearsals or source reports as profile7. Historical6/V8 remains explicit. Earlier
evidence keeps exact original
pins, failures and limitations. A fresh inventory is not automatic state migration.

## Reviewed Entry policy

`executeReviewed(Request,uint16 maximumLossBps,bytes32 expectedContributionPolicy)` binds current owner, exact native
value or token allowance, source policy/route, original contribution value and
caller maximum and exact entry-policy fingerprint before funds move. Actual marginal LP and full final accounting
still must pass. Production inputs are only fixed ZZZ/native ETH. Original-currency royalty
currencies do not add contribution assets; only LP conversions retain swap venues. Defaults 3%/1%/3%,
10% governance ceilings, source agreement 3%, spot/venue and caller floors are
separate. [Entry](ACTIVATION_ENTRY.md), [loss policies](EXECUTION_LOSS_POLICY.md).

## Two-source pricing records

Every priced asset needs two independently reviewed USD sources, full append-only
policy/active identity, runtimes, precision, positive fresh rounds and independently
recomputed conservative bounds/fingerprint. Native ETH is asset0, not a WETH alias.
Two addresses or agreeing answers do not prove independence. Review upstream
proxies/admins, common reporters/markets, liveness, updates and costs. No presumed
stable peg, single-feed or target-pool-spot fallback is selected. Intended 3%
agreement does not waive a tighter execution-loss guard. [Price rules](PRICE_SECURITY.md).

## Observation, completeness and failures

Observed hashes never replace approved pins. Declared route/pool mappings are
not proof no other policy was admitted; retain complete creation-to-anchor event
history. Enumerated bucket, asset and ordinal lists must match actual counts and
ordered contents. Source/role/route/policy changes require matching fresh review
and observation, not relabeled old test evidence.

Exact v4 slot0 validation preserves real downward-boundary tick semantics,
initialized sqrt/tick bounds, static LP fee and both packed protocol-fee directions.
It proves state consistency, not organic trading volume or provider independence.
Failures are sanitized; raw credentialed provider exceptions do not enter reports.
Previous output survives global/anchor failures and atomic report replacement.
Config and output must differ. Duplicate JSON keys/nonfinite values are rejected.

Observer exit0 means scoped reads completed;2means partial/mismatched observations;
1means failure. Validator returns a blocked diagnostic when release requirements
are missing; no report authorizes deployment, sealing, signing, journals or a
service/site rollout. Raw receipt/operating evidence and final approval belong in
the [release record](RELEASE_CHECKLIST.md) and [sole Todo](../TODO.md).

## Configuration digest helpers

Use code-owned normalized policy/hash helpers in the validator with the exact
reviewed source. A copied hash, manually guessed field or local file digest is
not independent approval, remote attestation or provider qualification. Regenerate
only affected review records when intended configuration changes, preserve the
original evidence, and reconcile pending transaction truth separately.
