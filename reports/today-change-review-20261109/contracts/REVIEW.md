# Today contract review — source d811856

Read-only review of the six commits after2138dd6. No confirmed actionable Solidity defect was found in the inspected mint/helper/NFT/canonical/default-cap changes. This is a scoped internal review, not an independent audit or a claim of exploit absence.

Reviewed the actual source and pinned verified SeaDrop implementation, including its embedded Solmate guard/transfers, rather than accepting report conclusions alone. The JSON records exact source/reference hashes and file/line review anchors.

- Payment: the fixed caller and zero-value NFT callback preserve atomic upstream gross/fee/net settlement; no general executor or custody authority was added.
- Quotas: whole batches reserve before callbacks;1000cap, independent phases, team reservations, AL1 and original-recipient lifetime limits persist through transfers/import.
- VRF: one original two-word request/NFT and existing request/generation/callback protections remain; dormant mints gain no LP/royalty entitlement.
- Canonical: V10 preserves original recipient/stage separately from owner, restores counters in order, and retains deployment/policy commitments.
- Metadata: compared with prior NFT behavior, dormant/failed/terminal valuation and threshold/URI semantics are preserved; the renderer becomes a separately authenticated fixed deployment dependency.
- Contributions: d811856 changes only the stored default to300bps. Stronger independent limits remain;97%LP+3%backed idle is distinct from a3%realized-loss permission.

## Remaining concerns

1. NFT/helper completion precedes upstream payment callbacks. Do not claim post-payment NFT fingerprint validation; cached upstream payouts and its outer guard are the real boundary.
2. V10 requires the same SeaDrop address/runtime and mint plan across peers. Replacing the collection through this codec cannot rotate an obsolete/failed primary-mint transport. Document that constraint; a future requirement to rotate it needs reviewed source design before sealing.
3. Real provider/batch acceptance should include failure on a later request or receiver after an earlier batch item succeeds. The existing named outage/rejecting-receiver cases do not independently demonstrate that precise sequence. No new testing was run here.

Prior mint/full-handoff evidence retains its original source/default200 scope. The later default300 evidence contains13 distinct selected Solidity successes and1explicit offline fork skip, not a newly executed whole handoff or qualified live market. Actual OpenSea/VRF/gas/wallet/provider/operating acceptance and independent audit stay open.

No repository edits or runtime changes were made by this review.
