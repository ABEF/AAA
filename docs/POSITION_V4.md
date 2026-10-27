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

The current Budget companion additionally exposes compound capability2:
`compoundReady(bucket)` coordinates every standalone compound with the last LP
creation/replacement and compound, with rebalance/adaptive-range priority. It
does not change the Position tuple or reward rights. Fresh accounting4 keeper
work must authenticate the exact matching helper/runtime/version; historical
V1 deployments and journals retain their old behavior. See the
[operator procedure](OPERATOR_MANUAL.md#coordinate-compounding-with-rebalancing).

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
