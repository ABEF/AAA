# Double-check of9 November2026 changes

Baseline main:`d81185684d768b0afccfed4801a443ed4ccca60d`. Scope is the six
commits after`2138dd6`, using Europe/Paris dates, plus the separately published
source9 website changes through`a41dbf8`. This is an internal source review,
not an independent audit, complete exploit search or production approval.

## Result and corrections

No additional actionable Solidity defect was established in the inspected mint,
NFT/metadata, canonical accounting and contribution-default changes. Two concrete
offline preflight defects were fixed; operator documentation and one focused
decoder-coverage gap were corrected. Ownership, custody, rewards, financial
limits, function permissions and on-chain runtimes are unchanged by this review.

| Finding | Why it matters | Correction |
| --- | --- | --- |
| P2: phase observation only checked as0–3 | An inventory could report TEAM during PUBLIC or PUBLIC after the recorded sale end while still passing its component checks. This is an offline admission defect, not an on-chain mint bypass. | Recompute the inclusive phase from the pinned block timestamp and configured windows. Require agreement; valid pre-sale, gaps and ended sales remain phase0. |
| P3: disabled mint-family counts accepted boolean zero | Python equality treated`False` as integer0 in a supposedly typed observation. | Require exact integer0 for signer and token-gate counts. |
| Stale operating guidance | The policy guide still called the current sale a direct Vault mint, the callable price note said OpenSea was unfinished, and20+2 helpers was labeled21 addresses. | Explain current SeaDrop vs historical direct mint; coordinate price/proof/drop changes, including uint80 SeaDrop price capacity. Correct22 helper/data addresses plus17 modules; keep external dependencies separate. Clarify source9/V9 versus mint2/V10 adoption. |
| Funded trace lacked a small mutation regression | Actual growth had exercised two-phase accounting, but the compact frozen regression only covered the initial empty bucket. | Add actual saved funded-growth replay plus missing, duplicate, changed and misplaced epoch observations. No new fork or duplicate raw trace. |

The phase check does not require the sale to be open and does not change
eligibility or claim behavior. The observer remains a source of observations,
not a cryptographic proof of RPC honesty or independent release approval.

## Review coverage

| Change | Source and interactions examined | Conclusion / limit |
| --- | --- | --- |
| `949422e`: source9 consumer | Read/unsigned manifest versions, pinned roles/runtime bindings, separate data sources and wallet capability boundary | Source9 remains V9 and cannot silently adopt V10. Public configuration stays null and signing remains Anvil-only. |
| `ff4b502`: actual Entry3 follow-up | Fixed ZZZ getter, initial/funded epoch order, entrant-only LP measurement, exact approvals, explicit gas2 envelopes | No new production decoder defect established. Added funded replay negatives; earlier synthetic-depth/controlled-feed EVM evidence keeps its original scope. |
| `1579186`: unsigned operator management | Actual Migration ABI, pause/canonical/phase guards, raw floors, both legs, exact late simulation, gas/funding/expiry and payout count semantics | No authority bypass, implicit force fallback or payout-recipient override established. Inclusion-time ownership/cursor movement remains an explicit manual reconciliation boundary. |
| `99a01e9`: SeaDrop and V10 | Actual pinned upstream payment guard/order, reserved batch counts,1000 cap, AL1/team/public rules, original recipients through transfer/import, VRF callbacks, metadata extraction and API/observer/preflight | Two offline preflight fixes above. No confirmed Solidity accounting/payment defect; platform/provider/batch acceptance remains open. |
| `793c8e0`: market qualification | Dated source/feed independence, fee/depth/size distinctions, actual failures versus synthetic successes and unchanged unset operating policies | Evidence does not qualify feeds/routes. Neither report quotes nor a new total cap substitutes for current executable depth and independent prices. |
| `d811856`: total contribution3% | Initializer-only source change, dynamic getter/caller maxima,97% actual marginal LP and independent venue/NET/spot/idle checks | Existing stored caps and saved200-bps reviews stay unchanged. Old market2% failures are not relabeled as3% successes. |

The [contract review](contracts/REVIEW.md), [consumer findings](consumers/REVIEW.md)
and their machine records identify inspected source/reference hashes. The
[scope record](scope.json) proves all59 production Solidity files remain exact
to the starting revision. Review conclusions do not mean every unchanged feature
was retested or that all possible vulnerabilities have been excluded.

## Important fixed dependencies and remaining work

V10 canonical replacement requires the **same SeaDrop address/runtime** across
peers. It cannot rotate a failed/obsolete mint transport. This is now explicit in
the mint procedure and operator manual; acceptance or a separately reviewed
design is needed before sealing if transport rotation is required. No guard or
commitment was silently loosened to add it.

The NFT/helper checks finish before SeaDrop's later fee/creator callbacks.
Cached upstream payment values/recipient and the outer payment guard are the
real boundary; do not claim a post-payment NFT fingerprint check. Existing
source-bound tests do not independently establish the precise live-batch case
where a later NFT's provider/receiver fails after an earlier item succeeds.
Include that sequence in actual provider/batch acceptance; an atomic design
argument is not a new verified operating result.

Actual independent ETH/fixedZZZ feeds, executable routes/depth and1% LP conversion,
VRF/OpenSea onboarding/fees/payers, authorities, target gas, matching hosted
services/site and wallets, long-lived history/recovery and independent audit
remain open. Earlier market guard failures remain unresolved observations.

## Verification and environments

[Verification](VERIFICATION.md) distinguishes new focused checks from exact
unchanged evidence. No unchanged Solidity suite, public quote campaign or live
fork was repeated. The only production implementation edit in this review is
the offline Python inventory validator; the Solidity ABI and callable inputs
are unchanged. All958 operator example rows are preserved; their reference
commitment is rebound to corrected explanations.

No deployment, public transaction, service/site rollout, stored cap, existing
Anvil/NFT/LP/balance, signer, journal or heartbeat change. The four protected
dirty files and unrelated drafts remain outside publication. Original documents
were archived externally before editing; historical reports remain immutable.
The sole [Todo](../../TODO.md) retains every release gate.
