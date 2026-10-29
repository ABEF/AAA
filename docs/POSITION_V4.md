# Accounting4: collective holder principal return

Current fresh LP protection uses confirmation2 and separate emergency capability1.
Ordinary readiness requires physical/reference same-side range exit (unless a
reviewed policy relaxation or deliberate governance width exception applies).
Reference prices remain the configured dual USD sources, not a newly qualified
market feed. A separate paused governance emergency may explicitly bypass
financial guards; it preserves exact accounting/custody but can cause near-total
economic loss. It is not a user transaction, keeper fallback or API signing
feature. [Policy](LP_EXECUTION_POLICY.md#independent-reference-in-confirmation2),
[emergency procedure](EMERGENCY_REBALANCE.md).

Fresh undeployed profile; no historical deployment or journal migration.
The eight Position words remain: poolId, lpTokenId, idle0, idle1, depositUSD,
centerX96, lastRebalance and status.

Statuses: None0, Active1, Outbound2 (reserved), Dormant3, Parked4, **Exited5**.
Accounting3 rejects status5; historical1/2 retain their 15-word layouts and
different meanings. Never choose a profile from tuple length alone.

Required versions: Vault accounting4, Migration custody3, governance2, fee
intake1, pricing2, routing2, reviewed Entry1 and canonical
`ZZZ_CANONICAL_SAME_CHAIN_HOLDER_EXIT_V5`.

Current maintenance policy2 additionally requires Strategy version2 and Budget
compound capability3. `needsRebalance` uses actual physical range exit or deliberate
range change after the configured hard interval. `compoundReady(bucket)` uses
its independently configurable per-pool interval after last LP creation/replacement
or compound, with raw rebalance priority. This
does not change the Position tuple or reward rights. Fresh accounting4 keeper
work must authenticate the exact matching helper/runtime/version; historical
V1/V2 helper deployments and journals retain their old behavior. Activation configs
for accounting4 must explicitly select maintenance policy1 (historical) or2. See the
[operator procedure](OPERATOR_MANUAL.md#coordinate-compounding-with-rebalancing).

Fresh LP execution additionally declares `lp_routing_version:1`, authenticates
Manager/helper LP_ROUTING_VERSION1, immutable parent/core/state/runtime pins and
explicit reviewed catalog. This is separate from Entry routing2 and does not
change Position4 or canonicalV5. Old LP routing0 readers keep the historical
whole-idle contribution trace; LP1 requires entrant-only balance/put witnesses
and the physical-LP-only marginal baseline. Registry revision is appended; no
installed deployment/journal is relabeled. [Policy](LP_EXECUTION_POLICY.md).

Fresh fee-adjusted execution additionally declares `execution_quality_version:1`.
Strategy, Manager and helper expose EXECUTION_QUALITY_VERSION1; readers bind the
actual Strategy owner/runtime, forwarded cap/MAX and same-block quality revision.
Absent/0 remains historical, not capability detection by failure. LP_ROUTING_VERSION
stays1; current runtime pins distinguish this fresh source. Strategy gains policy
state before its old mappings: this is a new undeployed layout, never a storage
upgrade/relabel of preserved immutable deployments. [Scope](EXECUTION_QUALITY.md).

Fresh sampled confirmation additionally declares `rebalance_confirmation_version:2`.
Strategy, Budget and the immutable Strategy-created `rebalanceConfirmation`
helper expose capability2. Readers authenticate its exact runtime, Strategy and
Access bindings at the same canonical block. `needsRebalance` remains the raw
outside-or-operator-range candidate; `rebalanceReady` and helper `ready` add the
recorded confirmation requirement. A deliberate operator range change keeps its
raw cooldown/price guards and bypasses this observation window. Compound yields
to the raw candidate, so it cannot postpone a ready rebalance; hourly harvest is
independent.

The intended policy is a900-second window, four-minute service checks after the
hard12-hour cooldown and an exact300-second maximum recorded gap, with no grace.
The source constructor's gap0 blocks ordinary rebalancing until reviewed governance
configuration. Gap/duration, review hash and monotonic policy revision are observed;
changed identity/side or a late sample restarts the window. These are bounded
recorded observations, not proof of every intervening market price or a guaranteed
execution time. Historical absent/0 retains its old readers and journals.

`Access.lpExitStarted` permanently stops principal/mint activity independently
of pause/canonical state. Transfers, earned LP claims, future royalties and
royalty claims continue. Closed buckets retain share/membership accounting;
current LP value is verified zero with an explicit terminal metadata label.

The fixed Migration module allocates exact ETH+ZZZ to holders. No custodian,
sweep, conversion exit, external-return ingress or operator-chosen recipient
remains. Same-pair moves/parking remain before exit. Royalty custody APIs are
removed too. [Complete procedure](HOLDER_COLLECTIVE_EXIT.md).

Canonical V5 handoff is available only before LP exit; afterward it stays
blocked because its importer does not carry this terminal payout ledger.
Accounting3 website/inventory and historical evidence do not automatically
qualify this new profile. The current production-inventory gate is explicitly
schema6, separate from API schema2 and activation schema1; it observes17helpers,
including Balancer and confirmation. Missing actual bindings/reviews remain
blocked. [Inventory](PRODUCTION_PREFLIGHT.md) and
[scoped verification](../reports/practical-improvements-20261028/VERIFICATION.md).
Public signing and deployment remain disabled.
