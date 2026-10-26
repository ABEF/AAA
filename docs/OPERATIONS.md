# Keeper, indexer and service operations

**Production NOT APPROVED.** This is an operating guide, not permission to deploy,
sign publicly or change running services. Start with the [operator manual](OPERATOR_MANUAL.md)
for authority/exact calls and [recovery runbook](KEEPER_RECOVERY.md) for journals.

## Current deployment and configuration

Use explicit accounting3, fee intake1, direct governance2, custody2, pricing2,
routing2 and canonical localV4 with actual runtime/module bindings. The existing
[keeper example](../keeper/config.example.json) is dry-run with placeholders,
not a working deployment. Review the operator-owned schema5 production inventory,
all17core/15helper bindings, exact assets/routes/feeds/authorities and gas policy
under [preflight](PRODUCTION_PREFLIGHT.md). The blocked example must stay blocked.

Current contributions are native ETH/fixedZZZ, minimum$100 activation/$5growth.
Actual marginal newLP is measured; default2%contribution/1%conversion/3%maintenance
limits are distinct and may be governed up to10%, gas separate. Read live/captured
policy and caller minima; never assume a default or count incumbent funds/idle as
newly deployed LP. Source disagreement3% is a different guard and does not guarantee
an executable quote. Failed final Entry reverts input/LP changes, not earlier
approval or network gas. [Entry flow](ACTIVATION_ENTRY.md), [prices](PRICE_SECURITY.md).

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

## Maintenance and range policy

The keeper discovers shared custody buckets; it does not rebalance each NFT.
An example600-second poll is an eligibility check, not a guaranteed execution.
Price/range movement or an approved width change, cooldown, fresh prices,
snapshot/lifecycle, execution loss and gas checks must pass. Optional reviewed
+/-25/50% width selection in ZZZ-price-in-ETH is explicitly enabled and bounded
by governance's policy; the keeper cannot invent a new range/algorithm.
[Range procedure](RANGE_POLICY_UPDATES.md).

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

Guardian pause/mint-only pause/pool disable affect different paths. Paused custody
parking and approved external exit use their own governance/snapshot/raw minima;
no scheduler, bridge or generic sweep exists. Raw exit never becomes an automatic
fallback. External custody is trusted and cannot be forced to return funds.
[Containment and exact management procedures](OPERATOR_MANUAL.md).

The old staging heartbeat is paused, not continuous monitoring evidence. Existing
Anvil/services/journals and historical profiles must remain unchanged unless a
specific operating change is authorized. Rehearse off-host restore, alerts and
current target-chain runtime/provider/gas before production approval.
