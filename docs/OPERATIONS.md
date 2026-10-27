# Keeper, indexer and service operations

**Production NOT APPROVED.** This is an operating guide, not permission to deploy,
sign publicly or change running services. Start with the [operator manual](OPERATOR_MANUAL.md)
for authority/exact calls and [recovery runbook](KEEPER_RECOVERY.md) for journals.

## Current deployment and configuration

Use explicit accounting4, fee intake1, direct governance2, custody3, pricing2,
routing2 and `ZZZ_CANONICAL_SAME_CHAIN_HOLDER_EXIT_V5` with actual bindings. The
[holder-exit keeper example](../keeper/config.holder-exit.example.json) is dry-run with placeholders,
not a working deployment. Review the operator-owned schema5 production inventory,
all17core/15helper bindings, exact assets/routes/feeds/authorities and gas policy
under [preflight](PRODUCTION_PREFLIGHT.md). The blocked example must stay blocked.

Pin `contracts.principal_exit` and its runtime plus the Access runtime. The
keeper checks fixed module/access ownership and custody version3. Existing
accounting1/2/3 configurations, journals and the old example remain historical
profiles; do not edit their version to use new code. The served poplint artifact
is still an unconfigured accounting3 build, not a deployed profile4 frontend.

Current contributions are native ETH/fixedZZZ, minimum$100 activation/$5growth.
Actual marginal newLP is measured; default2%contribution/1%conversion/3%maintenance
limits are distinct and may be governed up to10%, gas separate. Read live/captured
policy and caller minima; never assume a default or count incumbent funds/idle as
newly deployed LP. Source disagreement3% is a different guard and does not guarantee
an executable quote. Failed final Entry reverts input/LP changes, not earlier
approval or network gas. [Entry flow](ACTIVATION_ENTRY.md), [prices](PRICE_SECURITY.md).

## RPC failure handling

The shared read-only RPC adapter requires a canonical hex chain-ID quantity,
unique JSON object fields, finite numbers and exactly one result/error envelope.
Malformed/oversized/parser-limited replies fail through bounded configured
endpoint retries; WorkLimit still stops request work immediately. Valid finite
fee-history floats and the adapter's checked integer chain-ID return are retained.
A response containing both a result and a missing-block error is malformed,
not evidence of correct unavailable-block handling. Socket inactivity timeouts
are not absolute DNS/header/body deadlines; use the reviewed systemd progress
watchdog below for keeper stall containment. API request workers retain their
separate hard30second supervisor.

On persistent failure, keep pending intents/index state, inspect fixed error
site/type diagnostics and compare the same canonical block with a reviewed
independent endpoint. Do not echo raw provider responses/credentials, reset a
journal, resend a saved transaction or bypass strict decoding. Actual provider
qualification remains open. [Review and evidence](../reports/system-adversarial-20261026/VERIFICATION.md).

## Keeper progress watchdog

The shipped [source unit](../keeper/zzz-keeper.service) opts into120second
systemd supervision, with main-PID notification, control-group SIGKILL and no
core dumps. The keeper sends fixed progress datagrams from its main execution
path after RPC returns and during intentional idle sleep; no background timer
can conceal stalled I/O. Notifications are at most10seconds apart while making
progress, leaving room for the existing90second signer step. A locally overdue
pulse rejects instead of reviving a missed deadline.

Install/review matching source and unit together only through an authorized
rollout. Validate systemd>=240, effective settings and real group cleanup first;
a file containing a setting does not prove the manager applied it. No environment
means the original standalone path, with no hard supervisor. This is a
no-progress watchdog, not a120second whole-cycle SLA, and it does not replace
off-host health checks. [Exact operator/recovery procedure](KEEPER_RECOVERY.md#stalled-rpc-and-progress-watchdog).
No current service or paused monitor was changed.

## Running reviewed services

On a supported Linux/Unix host with Python3.11+, verified configuration and private
runtime paths, these commands perform one default dry-run/observation cycle:

```bash
python3 -m keeper.monitor --config keeper/config.example.json --once
python3 -m indexer.monitor --config indexer/config.example.json --once
```

Placeholder addresses are unusable. Live keeper signing needs independently
reviewed deployment, encrypted external cast keystore/private password file,
sender authority, fee/gas/daily budgets and intact original intent journal.
It is distinct from the user wallet signer. No config flag alone qualifies it.
Read [keeper recovery](KEEPER_RECOVERY.md), [service rehearsals](KEEPER_REHEARSALS.md),
[API ingress](API_INGRESS.md), [concurrency](CONCURRENT_SERVICES.md) and
[indexer recovery](INDEXER_RECOVERY.md) before hosting/changing service units.

<a id="reward-timing-and-maintenance-schedule"></a>

## Reward timing and maintenance schedule

Harvest funds the fixed80/10/5/5 allocation once. The10% is indexed equally across
activated NFTs at that receipt; claiming does not change the denominator or
another NFT's entitlement. Individual and collective LP rewards are claimed
together for the NFT. Compound/buyback reserves stay outside that claim ledger.
[Timing and worked example](ECONOMICS.md#allocation-reinvestment-and-claim-timing).

| Job | Reviewed operating policy | Confirmed evidence |
| --- | --- | --- |
| Harvest | `maintenance.harvest=true`, `harvest_interval_seconds`; permissionless manual `Vault.collectFees` is also available. Contribution/rebalance/compound paths harvest as well. | `FeesCollected`, matching funded `PoolRewardsCredited`/`FeesAllocated`, actual receipt and separate reserves. Uncollected pool fees are not claimable yet. |
| Compound | `maintenance.compound=true`, reviewed local interval/thresholds and actual minimum LP. Fresh accounting4 also requires the exact Budget pin, capability2 and `compoundReady`; all standalone compounds yield to range maintenance. Contributions/rebalances can already reinvest the same bucket's reserve. | `Compounded` or the confirmed contribution/rebalance, actual LP/backing, unchanged NFT shares for reinvested incumbent capital. New swap fees/dust may remain for a later pass. |
| Buyback/burn | Reviewed `buybacks` tasks with `token`, raw `amount` and `pool_id`; at most32 unique input currencies. A direct fixed-ZZZ burn may use zero pool ID because no swap occurs; other inputs need an admitted route. Budget/prices/simulation/actual burn must pass. | `BoughtAndBurned`, actual reserve debit and verified ZZZ supply reduction; a reserve balance alone is not a burn. |
| Claim | Current NFT owner selects funded balances; use bounded ClaimRouter for multiple LP/royalty claims. | Actual `Claimed` payouts, reduced liabilities, preserved other NFT balances/fractions and purpose reserves. No harvest, compound or buyback is triggered by an LP claim. |
| Collective principal delivery | Opt-in accounting4 `principal_distribution` after governance has started exit and closed all buckets. Bounded allocation and direct current-owner payouts, also while paused. No keeper initiation/closure authority. | `PrincipalAllocated`/`PrincipalPaid`, exact ledger paid flags and pending recovery. Principal is not income or a holder reward claim. See [configuration/recovery](KEEPER_RECOVERY.md#optional-automatic-principal-delivery). |

The accounting4 sample polls600seconds and schedules independent standalone
harvests every3600seconds (one hour). It disables standalone compounding and has
an empty buyback list. Historical profiles/example3 retain the original omitted-
field14400second/four-hour schedule; explicit per-bucket/global intervals win. These are inactive/placeholder
choices, not qualified production settings. Choose intervals/batches from actual
revenue, decimals, gas and market depth; a common raw threshold across ETH/ZZZ is
not a common economic value. Network gas is paid by the keeper separately; it is
not taken from a holder's80% or the collective10% by claim logic.

For the exact JSON field, per-bucket override precedence and controlled
config/restart/health procedure, use [change the harvesting interval](OPERATOR_MANUAL.md#change-the-standalone-harvesting-interval).
Editing the sample file does not reconfigure an installed keeper. Its standalone
timer tracks successful keeper harvest receipts, not every implicit/manual harvest.

One submitted transaction uses the serial nonce/receipt path per cycle. LP and
royalty conversions retain their existing three-way turn with maintenance.
Within cycles reaching maintenance, buyback priority alternates with LP/metadata
work, and buyback currencies rotate, so persistent rebalances or a funded first
currency cannot monopolize every opportunity. Optional validated journal fields
`buyback_priority`/`buyback_cursor` are retained on restart; old journals without
them default safely. Do not add, reset or edit them manually. This gives eligible
work opportunities, not a wall-clock execution SLA: pending receipts, pause,
preparation, insufficient reserves, simulation/price/fee/gas guards still defer it.

Monitor successful harvest/compound/burn receipts, outstanding reserve amounts,
deferred/error logs and receipt age. A persistent backlog needs reviewed task
sizing/route/prices/gas repair, not a reserve sweep or automatic loss-cap increase.
Stop/review/restart through the recovery procedure with journals intact; changing
source/config here does not roll out to an installed service. Before production,
qualify actual batch economics, schedule latency and recovery with these jobs on.

Price-dependent range/rebalance/compound RPC failures log `maintenance_deferred`
and degrade health. After bucket identity/status are authenticated, a due,
enabled fee-only harvest may still use its own unchanged simulation, gas, code,
nonce and lifecycle checks, with a fresh deadline after a slow failure. It does
not move principal or waive a price guard for maintenance. Malformed configuration
or ABI values still skip the bucket; invalid identity, pause/canonical locks and
disabled/not-due harvesting never enter this path. A saved pending intent stops
further work immediately, including conversion-error handlers; recover that exact
intent before another action. See [review/evidence](../reports/reward-resilience-20261026/REVIEW.md).

## Maintenance and range policy

The keeper discovers shared custody buckets; it does not rebalance each NFT.
An example600-second poll is an eligibility check, not a guaranteed execution.
Price/range movement or an approved width change, cooldown, fresh prices,
snapshot/lifecycle, execution loss and gas checks must pass. Optional reviewed
+/-25/50% width selection in ZZZ-price-in-ETH is explicitly enabled and bounded
by governance's policy; the keeper cannot invent a new range/algorithm.
[Range procedure](RANGE_POLICY_UPDATES.md).

Fresh accounting4 standalone compounding requires Budget capability2:
`now >= max(lastCompound,lastRebalance) + current minRebalanceInterval`, plus
no eligible rebalance and no available preapproved adaptive-range selection.
The rule includes no-swap compounds and the first compound after LP creation.
Rebalance eligibility ignores `lastCompound`, preserving range priority. The
independent hourly harvest schedule, funded claims and guarded user contributions
are unaffected; successful contributions may still reinvest designated reserves.

Every due accounting4 compound job, even reserve-only, authenticates
`idle_compounding_budget`, `code_hashes.idle_compounding_budget`, its Vault binding,
capability2 and `compoundReady`. Historical accounting1/2/3/helper1 settings retain
their explicit old meaning. Helper readiness is not a substitute for keeper
authorization, pause/lifecycle, simulation, fee or execution guards. If a
preapproved adaptive action is available but local range scheduling is disabled,
compound can wait indefinitely: review/enable that job or deliberately adjust
the approved policy, rather than bypassing it. No running config/service changes
follow from these source instructions.

Enable LP/royalty conversion, idle-only compounding, buyback and metadata watching
only under their reviewed configs/bindings/budgets. They are separate jobs;
harvesting, conversion and payout are different accounting actions. Native ETH
fees need no conversion. ZZZ conversion at default1% requires a cheaper qualified
route than the selected pool's recorded effective fee. Unconverted balances stay
backed; failure is not permission to widen a caller floor. Noncanonical converter
or route Boolean flags are errors/deferred work, not legitimate disabled controls;
valid0remains off. Preserve degraded telemetry while independent upkeep continues. Do not schedule creator
inbox, remote reward/ACK or bridge jobs: those current modules are removed.

## Optional metadata notifications

Watcher defaults disabled. Observe revealed state, current marked valuation and
evolution at a confirmed block, then use the bounded keeper transaction/receipt
path for metadata notifications. Up to50mint ordinals per range notification;
ordinals are not hashed token IDs. ERC-4906 is a notification, not proof of an
instant marketplace cache refresh. No LP action is needed just to refresh art.
[Metadata/hosting](NFT_METADATA.md), [artwork publication](ARTWORK_PUBLICATION.md).

## Stop, recovery and restart

The heartbeat now includes `configuration_sha256`, a hash of the exact loaded
configuration. `keeper.ops health` requires the same hash, not merely chain and
sender. Old/missing/malformed or mismatched artifacts return `configuration_mismatch`.
Deploy matching writer/checker together only through an authorized rollout and
require a fresh matching cycle after a reviewed config change. Never patch the
hash, edit/reset a journal or assume this digest authenticates the host/provider.
There is no in-process config reload: finalize config before constructing Keeper.


Stop new signing and preserve journal/lock/health/config/receipt evidence before
repair or host migration. Resolve saved transaction hashes and nonce/fee reviews;
do not delete pending intents, repeat approvals, auto-resend ambiguous broadcasts
or reset budgets. Reconcile chain state and original receipts before restart.
Keeper downtime does not erase LP or accrued rights; it can leave out-of-range
inventory unproductive until safe upkeep succeeds. Gas/market loss remains possible.

Guardian pause/mint-only pause/pool disable affect different paths. Paused local
parking retains principal inside the Vault. Governance can instead start an
irreversible collective exit: close all fixed ETH/ZZZ buckets without swaps,
allocate actual returned principal by frozen NFT shares, then distribute it in
bounded batches to current owners. Rejecting recipients retain an owner-only
fallback claim. No external-custody address exit, bridge or generic sweep exists.
Pending compound joins principal; earned LP/royalty claims and designated buyback
reserves remain separate. NFTs transfer and retain future royalty eligibility.
`lp_exit_started` prevents all new LP/mint work even after unpause. Confirmed
pending transaction recovery still runs; previously earned conversions and
configured buybacks may continue. Optional automatic allocation/direct delivery
is source-implemented but disabled by default; the keeper never initiates exit or
closes buckets. No service was enabled here. See
[delivery configuration](KEEPER_RECOVERY.md#optional-automatic-principal-delivery).
[Containment and exact management procedures](OPERATOR_MANUAL.md).

The old staging heartbeat is paused, not continuous monitoring evidence. Existing
Anvil/services/journals and historical profiles must remain unchanged unless a
specific operating change is authorized. Rehearse off-host restore, alerts and
current target-chain runtime/provider/gas before production approval.

Current paid-revert reporting uses `confirmed_reverts`,
`active_revert_cooldowns` and `next_revert_retry_after`; matching writer/checker
deployment is required. An active existing action cooldown reports
`revert_cooldown` even after restart or an unrelated successful harvest. Other
eligible work and existing loop backoff continue unchanged. Its expiry permits
a retry, not a claim that execution/market conditions recovered. Unknown markers
or chain time cannot report healthy. See the
[recovery procedure](KEEPER_RECOVERY.md#logs-health-and-fallback) and
[scoped evidence](../reports/manipulation-hardening-20261027/VERIFICATION.md).
