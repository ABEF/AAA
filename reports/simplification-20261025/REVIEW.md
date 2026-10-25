# Obsolete-surface audit and simplification

## Scope and decisions

The user selected a hookless native ETH/ZZZ pool, removed optional creator-payment
inboxes, limited contribution inputs to ETH/ZZZ, and removed integrated cross-chain
scope. The review follows actual callers, custody and recovery rather than deleting
contracts solely to reduce the ABI count.

Implemented source changes remove unused creator receivers/factory, remote fee
intake and bridge interfaces/types, unused bridge asset mapping, proof-based
remote custody completion, and always-reverting legacy entrypoints. Same-chain
custody exit/recovery and complete collection handoff remain. Royalty receipt,
outage isolation and conversion remain independent of contribution inputs.

## Material findings addressed

| Finding | Improvement and security boundary |
| --- | --- |
| Creator intake remained optional but complicated every contribution and handoff. | Only physically received local Vault LP fees can enter Fees. No creator inbox, external synchronization or unbacked remote allocation is retained. |
| A new member caused repeated global inbox/dust passes. | One Vault-authenticated global dust settlement precedes contribution. Current-pool swap fees still settle under incumbent weights before new shares. Callbacks cannot classify donations or enter another Vault maintenance call. |
| Old fee export rows contained retired receiver/remote fields. | A smaller explicit codec and new canonical schema reject incompatible records. Donation quarantine, exact reserves, full abort and lifecycle barriers remain. |
| Stablecoin admission contradicted the two-input product rule. | Contract source admission is limited to ETH and the reviewed ZZZ identity, including direct Vault input paths. Pool valuation and royalty currencies remain separate. |
| Optional remote-proof code suggested integrated bridge support. | Custody requests are source-chain operations; no remote proof/verifier or remote-valued completion exists. An external custodian is a disclosed trust boundary. |
| Current services could probe removed getters or replay old snapshots under new layouts. | Explicit fee/custody profiles bind the new schema and inventory. Legacy journals/readers retain their old meaning, with no silent downgrade. |
| One-time token setup could be omitted before irreversible seal. | Seal requires nonzero matching contribution/normal-exit ZZZ identities; unset or mismatched setup preserves bootstrap for correction. Raw exit remains independent. |
| Registry embeds its source-policy implementation in initcode. | Normal EIP-3860 checks caught a size failure. A fixed noncustodial factory splits construction without adding execution/configuration power. Exact constructor arguments still require normal limits. |
| ABI documentation exposed operations that always reverted. | Remove those selectors and regenerate source-matching callable documentation. Exact historical-selector rejection remains covered. |

## Exclusions

- Keep separate principal, LP reward, royalty, compound/buyback and donation ledgers;
  merging these would obscure backing and ownership.
- Keep complete same-chain handoff and funded abort; removing it would discard the
  user's requirement to preserve ownership and unclaimed rewards on replacement.
- Keep historical event/profile readers, reserved rejected module identifiers and
  stable position ABI/status meanings. They do not enable a new bridge.
- Keep typed conversion infrastructure for ETH/ZZZ input into a future supported
  pair and for earned-reward conversion; a source-token restriction does not imply
  that every internal or royalty asset is ETH/ZZZ.
- No arbitrary sweep, recipient executor, automatic fallback, holder principal
  redemption, new timelock or change to economic percentages is introduced.

## Verification and limits

See [verification](VERIFICATION.md) for exact source bindings and completed checks.
Existing fixtures that depend solely on removed features are retired explicitly;
their historical results are not current passes. Mixed LP, royalty and handoff
coverage must retain its financial assertions after fixture adaptation.

No existing local chain, journals, website build, server, service, signer or monitor
is changed. Real routes/feeds/VRF, authorities, OpenSea, operating qualification and
independent audit remain release blockers. Governance and external custody remain
trusted. Removing unused features is not proof of absence of vulnerabilities.
