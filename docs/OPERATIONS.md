# Keeper, indexer and service operations

**Production NOT APPROVED.** This is an operating guide, not permission to deploy,
sign publicly or change running services. Start with the [operator manual](OPERATOR_MANUAL.md)
for authority/exact calls and [recovery runbook](KEEPER_RECOVERY.md) for journals.

Fresh fee-quality source uses explicit `execution_quality_version:1` with actual
Strategy/Manager/helper capability/runtime/binding checks and observed policy
owner/revision at one canonical block. Historical absent/0 is not silently
upgraded. Quality RPC failure prevents a new guarded balance review; saved
receipt recovery and independent harvest retain their existing paths. An on-chain
cap setter needs no service restart, but a config/runtime/source rollout requires
the reviewed stop/reconcile/dry-run/restart procedure with journals preserved.
[Fee-adjusted scope and limits](EXECUTION_QUALITY.md).

The current holder-exit example remains deliberately blocked; its2.5Mgas cap is
not adequate evidence for current routing. Earlier balance-only cold fixtures
already exceeded it; complete current operation+25%padding and network-fee budgets
need qualification. Refusal above the cap is correct, not permission to widen it
automatically. Health schema2 now exports confirmed-block quality metadata and
gas review diagnostics; local source hashes identify file bytes, not the running
binary. The matching writer/checker must be rolled out together. See the
[operator procedure](OPERATOR_MANUAL.md#qualify-current-routing-gas-and-telemetry).

## Current deployment and configuration

Use explicit accounting4, fee intake1, direct governance2, custody3, pricing2,
routing2 and `ZZZ_CANONICAL_SAME_CHAIN_HOLDER_EXIT_V5` with actual bindings. The
[holder-exit keeper example](../keeper/config.holder-exit.example.json) is dry-run with placeholders,
not a working deployment. Review the distinct fresh accounting4 inventory,
its exact supported observer bindings, assets/routes/feeds/authorities and gas policy
under [preflight](PRODUCTION_PREFLIGHT.md). Historical schema5/accounting3 records
cannot be relabelled profile4; placeholder inventory remains blocked. LP routing1 additionally needs
exact Manager/balancer/core/state runtime/parent pins and a reviewed execution
catalog; source settings do not qualify a live service.

`rebalance_confirmation_version:1` additionally pins the Strategy-created helper
in `contracts.rebalance_confirmation` and its runtime. The existing
`idle_compounding_budget` address/runtime is also mandatory, even when standalone
compounding is disabled: the actual Vault Budget must advertise confirmation1
and bind the same Vault/Access. An old raw-eligibility-only Budget is rejected.
This profile also requires explicit integer `interval_seconds` from60through300.
It cannot inherit the historical600second default. The outer loop includes work
and receipt latency; even a permitted interval is not an exact sample guarantee.

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

## Versioned health and execution diagnostics

Matching schema2 writer/checker reports the last confirmed quality observation:
canonical block/hash/time, observed head, configuration digest, reviewed runtime
hashes, local source-file hashes and Strategy policy owner/revision/limit. The
current cycle state is separate from `last_confirmed`; an outage preserves old
evidence but labels it unavailable rather than fresh. Source identity is explicitly
`local_files_at_keeper_start_not_runtime_attestation`. A health file is neither
cryptographic proof of running code nor an independent RPC/market attestation.

Quality1/confirmation1 successful statuses are `healthy_v2` or `dry_run_v2`, so
an older checker fails closed. Historical profiles retain their old success
statuses and journal meanings. New checks require schema2 for the new profiles;
missing/mismatched/stale source, configuration, block or policy evidence cannot
report healthy. Deploy writer/checker together only through an authorized
stop/reconcile/dry-run/restart; never patch existing health or journal fields.
Cycles that start with a saved transaction perform no new quality telemetry
reads before recovery.

`gas_review.last_review` exposes the actual estimate,125%-padded gas requirement,
configured gas/gas-price/transaction/day caps and refusal reason. It remains a
simulation estimate, not an inclusion-cost guarantee, and does not raise caps.
`lp_execution_health` and `rebalance_confirmation_health` distinguish confirmed
quality evidence from the last latest-state confirmation observation/reset
backlog; neither is a guaranteed next execution time.

Only successful discovery metadata at the exact same canonical hash and loaded
configuration may be memoized within one cycle. No failure fallback or cross-cycle
cache is used. Pre-simulation and pre-signing checks always reread a fresh header,
runtime and policy. Confirmed telemetry adds bounded read work; the memoization
removes repeated same-block discovery reads, not a claim of universally lower
RPC usage. [Scoped evidence](../reports/practical-improvements-20261028/VERIFICATION.md).

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

## Operator-selected LP policy

[Maintenance policy2](LP_EXECUTION_POLICY.md) implements outside-or-operator-range
eligibility after the configured hard interval, durable service jitter and
independent Budget3 compound cadence. Intended initial values are12hours,
60-600second jitter, hourly eligible inside-range checks and $1m cumulative
per-NFT contributions. The fresh sample observes every60seconds. LP routing1 now
compares up to four reviewed ETH/ZZZ execution venues independently of the LP
destination, using post-close depth, bounded actual-core sizing and zero/one
swap. Contributions balance/deploy only their own amounts; incumbent idle and
compound remains in old NAV for guarded maintenance. [Protection inventory](KEEPER_SAFEGUARDS.md). [Operator calls/restart](OPERATOR_MANUAL.md#operator-selected-lp-policy).

## Reward timing and maintenance schedule

Harvest funds the fixed80/10/5/5 allocation once. The10% is indexed equally across
activated NFTs at that receipt; claiming does not change the denominator or
another NFT's entitlement. Individual and collective LP rewards are claimed
together for the NFT. Compound/buyback reserves stay outside that claim ledger.
[Timing and worked example](ECONOMICS.md#allocation-reinvestment-and-claim-timing).

| Job | Reviewed operating policy | Confirmed evidence |
| --- | --- | --- |
| Harvest | `maintenance.harvest=true`, `harvest_interval_seconds`; permissionless manual `Vault.collectFees` is also available. Contribution/rebalance/compound paths harvest as well. | `FeesCollected`, matching funded `PoolRewardsCredited`/`FeesAllocated`, actual receipt and separate reserves. Uncollected pool fees are not claimable yet. |
| Compound | `maintenance.compound=true`, reviewed local interval/thresholds and actual minimum LP. Fresh accounting4 also requires the exact Budget pin, capability3 and `compoundReady` under policy2; all standalone compounds yield to range maintenance. Rebalance/guarded compound can reinvest the bucket's reserve; contributions only synchronize/release it into incumbent idle/NAV and deploy entrant funds. | `Compounded` or the confirmed contribution/rebalance, actual LP/backing, unchanged NFT shares for reinvested incumbent capital. New swap fees/dust may remain for a later pass. |
| Buyback/burn | Reviewed `buybacks` tasks with `token`, raw `amount` and `pool_id`; at most32 unique input currencies. A direct fixed-ZZZ burn may use zero pool ID because no swap occurs; other inputs need an admitted route. Budget/prices/simulation/actual burn must pass. | `BoughtAndBurned`, actual reserve debit and verified ZZZ supply reduction; a reserve balance alone is not a burn. |
| Claim | Current NFT owner selects funded balances; use bounded ClaimRouter for multiple LP/royalty claims. | Actual `Claimed` payouts, reduced liabilities, preserved other NFT balances/fractions and purpose reserves. No harvest, compound or buyback is triggered by an LP claim. |
| Collective principal delivery | Opt-in accounting4 `principal_distribution` after governance has started exit and closed all buckets. Bounded allocation and direct current-owner payouts, also while paused. No keeper initiation/closure authority. Confirmed Ready batches have a separate default-hourly retry interval and durable first/last priority rotation so receiver deferrals cannot monopolize the transaction lane. | `PrincipalAllocated`/`PrincipalPaid`, exact ledger paid flags and pending recovery. Principal is not income or a holder reward claim. See [configuration/recovery](KEEPER_RECOVERY.md#optional-automatic-principal-delivery). |

The fresh policy2 accounting4 sample polls60seconds and schedules independent standalone
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
Actual physical range exit or an approved width change, cooldown, fresh prices,
snapshot/lifecycle, execution loss and gas checks must pass. Optional reviewed
+/-25/50% width selection in ZZZ-price-in-ETH is explicitly enabled and bounded
by governance's policy; the keeper cannot invent a new range/algorithm.
[Range procedure](RANGE_POLICY_UPDATES.md).

### Recorded rebalance confirmation

Fresh confirmation1 checks ordinary eligibility every300seconds after the hard
cooldown, including when LP remains inside range. The selected observed window
is900seconds with a **strict300-second maximum observation gap**; governance must
configure the helper with the reviewed hash. Source starts with gap0, which stops
ordinary confirmation until configured. There is no latency grace or earlier
poll hidden in the worker: a gap above300seconds makes prior evidence unusable,
and the next successful observation restarts the window.
Receipt/block latency can therefore repeatedly restart it and requires actual
operating qualification. A nonzero gap below the worker's300-second cadence is
reported unsupported rather than spending gas on perpetual restarts.

The worker submits one bounded `observe(bucket)` transaction on each due ordinary
outside check; receipt delay does not suppress the next scheduled renewal.
Observed readiness starts the existing durable60–600second jitter. Five-minute
observations continue during that wait; final readiness is read again before
submission. An approved manual width change bypasses the confirmation window,
including when gap0, but retains cooldown, jitter and every execution guard.
This is sampled evidence, not proof that price stayed outside between samples.

The separate `observed_rebalance_v1` namespace never rewrites historical
`outside_rebalance_v2` scheduling. Startup with an existing candidate, a confirmation/
raw-eligibility read or clock fault, an observed pause, or an interrupted/failed
related observation/rebalance requires a receipt-backed `resetObservation(bucket)`
before extending old evidence. Durable `confirmation_reset_v1` markers survive
restart and clear only after the exact successful canonical reset receipt;
failed/ambiguous resets retain normal retry/nonce recovery. Reset-only binding
checks avoid price reads and the source permits reset during ordinary pause.
Unrelated router metadata, compound reserve, gas-estimate, health or harvest
errors degrade their work but do not erase a healthy confirmation window.

`confirmation_clear_v1` retains the successful canonical clear receipt. Repeated
read failure in that same cleared episode waits for a healthy reread without
paying for repeated resets. A foreign/nonempty candidate on the first recovered
read forces another clear before use. A new observation intent atomically
invalidates the acknowledgement with pending persistence. No cached empty-state
receipt authorizes readiness. Failed related on-chain receipts atomically queue
their reset with fee/nonce recovery; unrelated failed receipts do not.
Incident resets discard only that bucket's fresh jitter. The jitter identity
includes the condition and window's firstSeen, while normal lastSeen renewals do
not redraw it; a newly completed window cannot reuse an old expired delay.
Unknown hidden movements or pause/unpause between observations are not proven.
Hourly harvest and saved-receipt recovery remain independent. [Verification](../reports/practical-improvements-20261028/VERIFICATION.md).

Fresh policy2 accounting4 standalone compounding requires Budget capability3:
`now >= max(lastCompound,lastRebalance) + compoundInterval(poolId)`, plus
no eligible rebalance and no available preapproved adaptive-range selection.
The rule includes no-swap compounds and the first compound after LP creation.
Rebalance eligibility ignores `lastCompound`, preserving range priority. The
independent hourly harvest schedule, funded claims and guarded user contributions
are unaffected; contributions release designated reserves into incumbent idle/NAV
but never use them to satisfy the entrant's LP floor. Configure reviewed idle
compounding thresholds to pick up useful residuals without new fees.

Every due accounting4 compound job, even reserve-only, authenticates
`idle_compounding_budget`, `code_hashes.idle_compounding_budget`, its Vault binding,
capability3 and `compoundReady`. Explicit historical accounting4 policy1 uses
helper2; historical accounting1/2/3/helper1 settings retain
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
