# Bounded operating flexibility review

Reviewed31October2026, Europe/Paris. Local source implementation authorized by
the user, including explicitly approved future-only mint/entry/payee settings.
No public transaction, deployment, sealing, worker/site/Anvil/journal/signing
change or publication. **Production NOT APPROVED.** [Evidence](VERIFICATION.md).

## Implemented behavior

| Area | Change and boundary |
| --- | --- |
| Shared policy | Separately predeployed ProtocolPolicy1, fixed Access binding before consumers. No funds, approvals, arbitrary execute or custody recipient. Normal values are governable within bounds; module identity remains fixed. |
| Future sales / contributions | Default0.05ETH mint/$100activation/$5growth preserved. Reviewed price, accepted future payee and action minima configurable. Entry2 binds exact scoped policy; fresh mint binds sale AND VRF. Callback or change-and-restore policy mutations cannot commit an old review. |
| Idle | Separate entry/maintenance defaults500bps, bounds0–4000. Captured operation policy, actual marginal deployment and retained-value guards remain distinct; old idle cannot subsidize entrant LP. |
| Gas / buyback | Governed payout/source/optional-sync budgets100k–1m with original defaults. Current batch captures payout budget; failed recipients remain backed. Reviewed buyback maximum may change without altering the fixed5% reserve or fixed ZZZ. |
| LP geometry | Portfolio2 exposes per-pool main6000–9999bps and positive aligned residual gap; manual ranges may extend below100% within coupled Registry/tick rules. At most two same-pool Vault-owned LPs. Defaults60/40, one spacing and half-side residual remain. |
| VRF / metadata | Planned provider/lane/subscription/payment rotation only after every old draw finalized. Original pending callbacks can drain, no reroll/retarget. Cosmetic thresholds govern appearance, not economic rights; exact1000 prepared-artwork mapping remains. |
| Readers / tooling | Explicit accounting6/schema8/Entry2/Portfolio2/Policy1 readers, keeper and inventory. CanonicalV6 admits only compatible policy semantics. Old profiles/receipts/journals remain historical. Enabled source6 conversion jobs require explicit profile, with pending recovery first. |

Main cannot be configured below60%: lowering that approved envelope was not
authorized. Fixed80/10/5/5, rarity/5% royalty request, final traits/supply, ETH/ZZZ,
shares/backing/current-owner rights and terminal holder return remain unchanged.
Lower minima affect future participation economics and require operator review.

## Correctness and auditability improvements

- Mint review includes current VRF configuration as well as sale terms, preventing
  provider changes between review and execution from silently changing the draw.
- Scoped revisions avoid mint, cosmetic or gas tuning resetting unrelated LP
  samples. Per-pool allocation/gap revisions distinguish deliberate geometry.
- Fixed read-only companions now share mint validation, maintenance proof and
  attributed-idle valuation. Lean gas views avoid decoding full policy tuples in
  size-constrained consumers. No financial/ownership guard was removed for size.
- NFT finite pure artwork lookup resides in its existing immutable renderer;
  the draw state, tables, quotas and ordered finalization remain unchanged.
- A new canonical regression caught a threshold-compatibility check mistakenly
  placed in export. It now belongs to import/capture/validation; retired source
  inspection remains readable after the successor changes cosmetic thresholds.
- The obsolete dollar source-patch tool refuses source6 before copying/compiling
  or creating output. Separately authorized isolated tests use governed minima;
  historical compatible snapshots keep their explicit legacy behavior.
- Current operator/manual/callable/Todo/config references explain exact inputs,
  bounds, events, lifecycle, fingerprint and rollback/recovery distinctions.

## Operational and trust limits

ProtocolPolicy is permanent code, not a generic future upgrade mechanism.
Governance can still choose harmful configurations or dependencies; bounded
values and review hashes do not prove good economics. A provenance reviewHash is
not authorization or proof of human review. Gas bounds do not qualify a provider
or full batch. The Pyth adapter retains its separate immutable300k inner cap.

Pending VRF failure cannot be repaired by rotating around the drain rule.
Coordinator codehash does not freeze proxy implementations or attest proof
security. Original callback identity, provider funding/recovery and actual
qualification remain necessary. No admin-selected traits or rerolls were added.

CanonicalV6 is a semantic admission change despite retained eight-word Position
and record shapes. Existing deployments cannot be relabelled source6. Configure
successor policy before importing; threshold values must match during handoff.
No cross-chain transport, custody sweep or post-exit replacement is introduced.

Source6 services need actual reviewed configurations, runtime pins and operating
rehearsals. Include ProtocolPolicy in a fresh indexer contract inventory/database;
raw policy events are not earnings. Existing examples remain explicitly
historical/unqualified. Public signing stays disabled and sites stay unchanged.

Actual feeds/routes/VRF/authorities/OpenSea, constructor/gas/market economics,
metadata hosting, service recovery and independent audit/remediation remain in
the [sole Todo](../../TODO.md). Older static reports do not audit this new source.
