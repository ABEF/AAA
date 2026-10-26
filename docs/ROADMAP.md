# Engineering roadmap

Reviewed 2026-10-27. This page explains dependencies and sequence; [TODO.md](../TODO.md)
is the only status list. [Feature reference](IMPLEMENTATION_STATUS.md) records what
exists, while [release approval](RELEASE_CHECKLIST.md) remains NOT APPROVED.

## 1. Close immutable integration boundaries

Qualify and finish [OpenSea primary mint](../TODO.md#task-opensea-mint), preserving
canonical NFT recipient,0.05ETH gross buyer price and net recipient proceeds,
fixed inventory, original randomness, mint pause and atomic failure. Select and
qualify the actual proof-verifying randomness provider. Direct mint/mock VRF
tests do not establish that integration.

Approve artwork root, fixed ZZZ identity, authority/module bindings, conversion
and custody/recovery behavior before sealing. Issuer token migration uses external
custody and a fresh deployment; no replacement-token setter or integrated bridge
is required. Same-chain collection handoff and its real backing must retain all
ownership/reward rights. See [current boundaries](SIMPLIFIED_RELEASE.md).

## 2. Qualify real dependencies alongside integration

Select independently reviewed ETH/ZZZ feed pairs, source freshness/updater/RPC
policies, actual contribution/conversion routes and fixed-ZZZ burn semantics.
The selected pool's recorded fee exceeds the default1% conversion cap, so qualify
a cheaper route or make an explicit governed policy decision; never silently
widen caller limits. Complete [creator questions](../TODO.md#creator-tasks--zzz-team)
about token/source controls; creator-payment funding is no longer a launch feature.

Authentic complete event history, archive access and same-block observations are
required for earnings. Current credit/dust/head reconciliation does not prove
every receipt/timestamp. Verify original source-currency history at today's prices
without conflating earned, claimable and claimed amounts.

## 3. Integrate the exact current deployment profile

Use the separate [poplint integration target](SITE_ENVIRONMENTS.md) for the
explicit current3 website/API reader and unsigned reviews. Preserve the existing
popldemo simulation, root, configuration and content; do not roll integration
changes into that live demo. Public signing remains disabled. Existing native2 or legacy Anvil profiles
are not upgraded by relabeling. Rehearse approval/contribution/claim/recovery and
account/network changes against the exact reviewed configuration. See
[website boundary](NATIVE_WEBSITE_PROFILE.md) and [wallet task](../TODO.md#task-wallet).

Use the corrected config-bound health/strict conversion controls and explicit
current3 rehearsal source, then qualify hosted services, concurrent request budgets, index recovery, keeper
restart/nonce/fee-review recovery, backups, monitoring and operator rotation.
Validate real target-chain maximum-state gas and range/maintenance economics;
local synthetic tests do not establish capacity or uninterrupted uptime.
Qualify the [separate revenue jobs](OPERATIONS.md#reward-timing-and-maintenance-schedule)
with actual batch sizes, gas, harvest/conversion/compound/burn latency and backlog
alerts. The local claim-conservation and buyback-fairness checks do not enable
the placeholder service or turn allocated reserves into executed trades.
Exercise [maintenance-outage harvest isolation and claim-integrity checks](../reports/reward-resilience-20261026/REVIEW.md)
under actual provider/service conditions, including degraded health and saved
pending recovery. Local fault fixtures do not close those operating gates.

For market/input acceptance, retain the [exact slot0 consistency checks](../reports/market-adversarial-20261026/REVIEW.md)
and exercise both out-of-range directions, valid tick boundaries and actual
funded donations against the qualified deployment. Consistent observations do
not authenticate an RPC, and funded fee history does not prove organic volume.
The [current selected-pool fork](../reports/current-pool-fork-20261026/VERIFICATION.md)
adds11distinct successful real-venue methods with explicit mock services and
retained failed/repaired attempts; it is not a fresh whole final suite. Native
and fixed-ZZZ entry, small growth, actual fee harvest/transfer rights and
unfillable-growth rollback are covered at one pinned block. These cases do not
close actual independent pricing, cheaper conversion routes, keeper economics,
provider/service or operating gates.

The [per-callable adversarial matrix](../reports/system-adversarial-20261026/COVERAGE.md)
provides an exact source-review starting point for the independent auditor, not
proof of execution for every scenario. Retain the stricter RPC/holder-input
boundary behavior and main-progress systemd watchdog in actual provider/recovery
rehearsals, including stalled DNS/header/body, killed signer descendants and
no-resend pending recovery. A valid provider
identity, inventory checksum or local pass is not authentic-history or release
approval.

## 4. Freeze and approve a complete release

Select exact source/configuration/authorities. Run the relevant final release
checks, independent audit and remediation, then named reviewer sign-off in the
release record. Reuse unchanged evidence with exact hashes; avoid repeating
unaffected suites during routine documentation or backend fixes.

Deployment, public signing and real-fund rehearsal require separate authorization.
The three verification layers remain local adversarial tests, selected Robinhood
mainnet fork and Robinhood Testnet/operator rehearsals. External custody is trusted
and can perform outside bridging; future-chain canonical NFT/ledger relocation
and post-halt recovery are outside this release.
