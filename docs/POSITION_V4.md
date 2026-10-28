# Accounting4: collective holder principal return

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
or compound, with rebalance/adaptive-range priority. This
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
qualify this new profile. Public signing and deployment remain disabled.
