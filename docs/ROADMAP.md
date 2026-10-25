# Engineering roadmap

## Deep cleanup review - 2026-10-25

The [adapted workflow](../reports/deep-cleanup-20261025/ADAPTED_PROMPT.md),
[review](../reports/deep-cleanup-20261025/REVIEW.md) and
[verification](../reports/deep-cleanup-20261025/VERIFICATION.md) separate structural
cleanup, new role logs, evidence-tool fixes and obsolete fixture repairs.
Royalty balance/error declaration reuse preserves execution and economic rights.
Guardian changes and initial keeper/guardian grants are now observable. Public
function encodings and recursive storage remain; declared event/error metadata
changes are explicit. Only Access grows: 45 runtime / 175 creation bytes.

32 scoped Solidity methods and 41 distinct Python methods pass; 37 normal object
gates pass. The normal compiler explicitly binds 44 project + 31 dependency files;
the final AST binds 131 project/test/script + 134 dependency files. The callable
reference remains 31 concrete contracts/608 functions/13 receive hooks, now using
snapshot schema 2 with complete dependency/build bindings. No full regression,
fresh Slither, live qualification or independent audit is claimed. Current
accounting3/governance2/local canonicalV4 and old deployments/journals stay distinct.
Actual services, OpenSea, authorities, operating/gas qualification and independent
audit remain open in the sole Todo. Production NOT APPROVED; no deployment.

## Auditability refactor - 2026-10-25

The [current review](../reports/auditability-refactor-20261025/REVIEW.md) and
[scoped verification](../reports/auditability-refactor-20261025/VERIFICATION.md)
cover shared collect/close settlement, an internal v3 identity validator, separate
LP/royalty converters inheriting one neutral abstract base, and named handoff
phases plus explicit private NFT/bucket identifiers. Permissions, rounding,
accounting, callback order, numeric states and external wire types remain.
The neutral base changes Solidity struct provenance, not ledger ownership.

The reference still covers 31 concrete contracts / 608 functions / 13 receive hooks.
Normal 37-object gates and 131-input typechecking pass. Exact compiler comparison
and targeted execution are recorded in the verification, rather than inferred
from old totals. All 135 event descriptors are preserved. No full regression,
actual service qualification or independent audit is claimed. Existing Anvil,
wallet/website profiles, journals, public signing and services stay unchanged.
Production NOT APPROVED; external release gates in the sole Todo remain open.

## Current smaller architecture - 2026-10-25

Read [the pruning review](../reports/architecture-pruning-20261025/REVIEW.md),
[verification](../reports/architecture-pruning-20261025/VERIFICATION.md) and
[Position3 guide](POSITION_V3.md). Current source removes the zero-delay scheduler,
seven Position provenance fields, unused remote states, zero-asset backing hooks,
single-feed shadow storage and obsolete research/bridge tooling. Direct governance2,
accounting3 and local canonicalV4 are explicit; old deployments/journals stay old.

The source-bound reference now has31contracts/608functions/13receive hooks.
49distinct selected Solidity behaviors and512distinct Python methods pass across
recorded source scopes, not a fresh full regression.127inputs typecheck and36normal
object gates pass. Access total initcode42,177 leaves6,975bytes; Vault runtime22,852
leaves1,724bytes. RoyaltyFactory's69-byte runtime margin remains tight. The two
runtime increases are individually explained in the exact bytecode comparison.

Native website3 integration, actual feeds/routes/VRF/authorities/OpenSea/services,
operating and economic/gas qualification plus independent audit stay open. No
deployment, public transaction, website source/build/server, existing Anvil/NFT/
LP/balance/journal or monitor action. Production NOT APPROVED. The dated sections
below retain their original source/evidence scope and do not qualify newer code.

## October25 consistency and security fixes

The [day review](../reports/daily-security-20261025/REVIEW.md) fixes native-pool
identity admission, makes Buyback use the same immutable ZZZ as activation and
normal exit, removes historical venue reads from funded incumbent dust settlement,
and rejects poisoned indexer log provenance before committing a batch. No new
custody right, token migration setter or automatic history repair is introduced.

[Scoped verification](../reports/daily-security-20261025/VERIFICATION.md):28 distinct
Solidity behaviors across recorded fixture scopes,35 affected Python methods,
124-input ABI/AST and36 normal object gates. Current reference:31 contracts,
643 functions. Registry runtime10,131; Vault23,889 with687 bytes of headroom.
Access retains only29 bytes with minimal role arguments; actual release arrays
remain unqualified. Older sections below retain their original source scope.
Real services, marketplace/authority rehearsals and independent audit remain open.
Production NOT APPROVED; no running deployment, website or service changed.

## Residual obsolete-code cleanup - 2026-10-25

[Review and removal boundaries](../reports/obsolete-code-20261025/REVIEW.md): unused
Registry wrapper records and creator-payment measurement tooling are retired;
actual converter wrappers, historical decoding/recovery, same-chain handoff and
custody rights remain. Current reference:31contracts/644functions. New Registry
runtime9,987bytes; Access's29-byte minimal initcode margin remains a release gate.
No running deployment/service or website changed; production NOT APPROVED.

## Current release simplification - 2026-10-25

[Current scope](SIMPLIFIED_RELEASE.md): ETH/ZZZ-only contributions, actual local LP
fees, no creator inboxes or integrated cross-chain bridge. Preserve same-chain
pool moves, external custody exit/recovery, royalty currencies and complete
collection handoff. Current fee/custody profiles and canonical schema are
explicit; old deployments/journals keep historical profiles.

## Current dependency progress - 2026-10-25

Optional Pyth Core source compatibility, explicit mint/VRF qualification and a
frozen-source reviewer handoff are implemented. Qualify real independent sources
and updater operations; no ZZZ pair is established. The current mint cannot yet
support OpenSea: implement gross0.05ETH buyer price/net platform-fee recipient
accounting and the correct canonical buyer path before sealing. Select a VRF
with compatible original-request recovery; actual candidates are not qualified.

Run current CLI/schema5/mint profile1; legacy consistency never approves this
release. Use the exact committed review package for independent audit/remediation
and real operating qualification. Authority addresses remain deferred. The
[service review](../reports/release-services-20261025/REVIEW.md) records capability,
actual observations and still-open external decisions separately.

Reviewed 2026-10-25. **Production NOT APPROVED.** The [sole Todo](../TODO.md)
owns task status and acceptance criteria; the [feature/evidence reference](IMPLEMENTATION_STATUS.md)
describes implemented candidates, and the [release record](RELEASE_CHECKLIST.md)
owns approval. This roadmap sets dependencies and order, not another checklist.

## 1. Close required immutable capability and safety boundaries

The current candidate implements native ETH accounting/routing V2, pricing V2,
typed v3/v4 conversions, governed bounded loss limits, one contribution pool,
same-pair moves, explicit external custody and same-chain canonical handoff.
Read [architecture](ARCHITECTURE.md) and [the internal audit](../reports/preproduction-audit-20261025/REVIEW.md).
Do not redo completed behavior or unchanged tests merely to increase a pass count.

The [reviewed Entry V1 implementation](EXECUTION_LOSS_POLICY.md#review-time-policy-binding)
now binds the caller maximum through Entry/Pricing, exact preparation/trace and
inventory profiles. The [native website read/unsigned profile](NATIVE_WEBSITE_PROFILE.md)
now implements that interface locally. Qualify actual native wallets/chain/services before
public signing; historical clients must reject the new ABI rather than silently
fall back. Retain old local deployments and journals unchanged. [Latest review](../reports/comprehensive-improvement-20261025/REVIEW.md).

Bounded two-pass placement and safe idle reinvestment have scoped local evidence;
qualify actual thin-market depth/quotes without relaxing captured LP floors.
Explicit inverse orientation and reviewed two-width keeper policy still need
real threshold/turnover/MEV and operating qualification. Indexed-history outage
handling and fixed rarity-weight metadata are separately improved; actual
provider/backfill/marketplace acceptance remains open.

The current release uses guarded same-chain pool movement and explicit source-chain
custody exit to an operator-controlled address. That custodian performs external
token migration or bridging; integrated bridges and future-chain canonical NFT/
reward transport are deferred optional scope, not launch gates. Atomic ETH/WETH
or other different-pair conversion remains unsupported; external custody is a
distinct trusted workflow, not that algorithm. Retain and qualify same-chain whole-
collection handoff. It does not solve future-chain or post-halt ownership recovery.

Keep normal runtime/initcode and gas limits. The [private Vault refactor](../reports/native-readiness-20261025/vault/VERIFICATION.md)
historically left313 runtime bytes. The current [simplification](../reports/simplification-20261025/VERIFICATION.md) leaves687; Access exact constructor arguments still need qualification. Use the latest exact-source receipt.
Any bytecode change needs fresh normal runtime and initcode gates. Review
complete custody/liability invariants, callbacks and abort/return paths before
accepting further changes. Immediate governance/external recipients remain trusted.

## 2. Qualify real dependencies in parallel with integration

The selected Robinhood pool is static hookless native ETH/ZZZ
`0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b`.
Qualify its actual directional fees, liquidity, native execution and gas. At the
default 1% conversion limit its observed approximately 1.101% combined fee does
not qualify full ZZZ-to-ETH conversion at reference prices: require a cheaper
reviewed route, not an automatic policy increase.

Prioritize two genuinely independent USD sources per economic asset. Review
shared upstreams/proxies, ages, depegs, outage/recovery and cost; neither a pool
spot estimate nor two proxies for the same provider establishes independence.
Qualify actual ETH/ZZZ/USDG/USDC routes and complete execution/trace/fee evidence.
Use the [read-only capability probe](RPC_PREPARATION_QUALIFICATION.md), then real
deployment-specific traces and operating rehearsals; a basic public-node pass is insufficient.
Creator-team pricing/token/market answers remain relevant; Pons creator funding
is optional historical scope for the current hookless pool.

Select supported funded proof-verifying VRF and production authorities, publish
verified permanent artwork, and qualify OpenSea primary mint/royalty recipients
and contract-owner compatibility. Local direct mint and local substitutes cannot
close these external gates. Keep schema-5 inventory genuinely blocked until its
actual identities, observations and independent reviews exist.

## 3. Integrate the exact native deployment and rehearse operation

Use reviewed versioned API/indexer/website profiles, complete confirmed history,
current-price USD and explicit unavailable states. Confirm owner rights, exact
approvals and original-hash recovery. Public website stays simulated and signing
Anvil-only until separately authorized and qualified. Existing local fixtures,
journals and dist repair overlay must not be reset or deployed as production.

Rehearse on supported Linux and the target chain: durable fee-review recovery,
included/separate L1 semantics, outages, reorgs, lost/stale backups, old-host
fencing, signer rotation and off-host alerts. Use [operator procedures](OPERATOR_MANUAL.md)
and [keeper recovery](KEEPER_RECOVERY.md). A pause is not a custody freeze; an
already approved paused exit can still move assets. Ten-minute polling is not
an execution guarantee or protection against all out-of-range time.

Qualify maximum actual assets/inboxes, strategy economics/MEV and service capacity.
The dedicated 10/25/100-user campaign remains user-deferred, not passed. Keep
monitoring paused as requested; historical chat observations do not establish uptime.

## 4. Approve an exact release, then a separate public rehearsal

Use local tests, the Robinhood mainnet fork and Robinhood Testnet for their
different purposes. Improve focused harnesses and prove their meaningful paths
before rerunning affected tests; keep reuse and limitations source-bound.
Complete independent security/economic review, remediation and exact-release
CI/static/fork/size/gas/configuration and operator sign-off.

A real-funds rehearsal needs separate named contracts, explicit budget and
execution authorization. Final collection identity is fresh. No burn/reset,
arbitrary sweep, public deployment or sealing follows from this roadmap.
Record publication and operations separately; keep [Todo maintenance](TODO_WORKFLOW.md),
operator guidance and both repository memories synchronized.
