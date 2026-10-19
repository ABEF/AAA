# Internal royalty reporting review - 2026-10-19

Scope: the API service/profile, raw financial-history replay, configured
same-chain lineage and regenerated event schema in [the verification record](VERIFICATION.md).
This is an internal review of a backend delta, not an independent audit or a
guarantee that the complete protocol has no vulnerabilities.

| Concern | Control reviewed | Remaining boundary |
| --- | --- | --- |
| Conversions inflate claims or earnings | Exact `RoyaltyConverted` ledger events update a separate conversion map. Only actual `Claimed` events update paid totals. Native claimable is read directly and already includes remaining converted ETH. | Consumers must keep denomination changes separate from revenue; gross earnings/USD reporting is unfinished. |
| One currency failure hides healthy entitlements | Explicit profile permits only per-asset metadata/runtime/claimable failure to return null. Native/healthy balances remain readable. Core ledger, admitted inventory, eligibility, lifecycle and snapshot checks stay strict. | A metadata fault is unavailable, not a safe transaction or a reason to accept drift. Wallet inventory retains strict validation. |
| Optional fallback bypasses request limits | `WorkLimit` is rethrown before the narrower per-currency/converter RPC handling. Final canonicality/freshness remains outside partial balance handling. | Actual hosted provider latency, process isolation and ingress still require qualification. |
| Wrong ABI or malicious helper status | New getters require explicit profile and reviewed core runtime pins; helper status checks exact bound address/runtime, controller/ledger and 1% limit. Missing helper qualification cannot manufacture conversion readiness. | Governance/runtime admission and live routes/prices remain independent trust and qualification requirements. |
| Fake conversion/claim events | Raw topics, word widths, minted NFT identity, non-native admitted source, amounts and exact ledger emitter are checked. Old decoder labels are ignored. | A trusted operator SQLite store/RPC provides completeness; no cryptographic inclusion/completeness proof was added. |
| Owner or successor loses/doubles history | Events remain per NFT. Complete pinned lineage merges at verified retirement cutoffs; missing lineage is unavailable and inconsistent configured lineage rejects. Old contracts do not inherit the new profile/converter. | Same-chain only; actual escrow compatibility and cross-chain accounting remain separate work. |
| Incompatible API rollout | The optional profile preserves default strict currency behavior. Operator procedure requires client null/eligibility handling and compatible release/config rollback. | Existing schema-2 clients must be reviewed before profile enablement; no production rollout occurred. |

No additional defect requiring a code correction was identified in this scoped
review. That conclusion is limited to the source, fixtures and reuse checks in
the [evidence](VERIFICATION.md). No custody, signing, gas limit, governance role or
on-chain accounting rule changed. The operator manual and central task ledger
were updated; live service/UI qualification and independent review remain open.
