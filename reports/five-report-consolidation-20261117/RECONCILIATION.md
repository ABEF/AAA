# Reconciled issues from the latest five report families

Baseline `1c18379b03b067de722d250cee1cc173acc4d635`. [Machine registry](RECONCILIATION.json) links repeat mentions to one substantive issue/obligation. It is not a count of test methods, all310older records, or independently verified vulnerabilities.

The64rows comprise37resolved historical corrections/selected-verification gaps,9accepted policies,7structural limits,2historical evidence limits,7open release-qualification buckets and2new corrections (evidence admission and omitted pool-stop diagnostics). Tight bytecode headroom is correctly classified as an engineering constraint: current normal gates pass. The new checker is documented in [EVIDENCE_ADMISSION.md](EVIDENCE_ADMISSION.md).

## Resolved findings

| ID | Issue | Current disposition |
| --- | --- | --- |
| R01 | Manual review gas envelope was reported but not frozen | resolved tool |
| R02 | Dangling output preflight missed occupied destination | resolved tool |
| R03 | Converter control notes described wrong units | resolved documentation |
| R04 | Nested tuple notes lost field explanations | resolved documentation |
| R05 | Shared struct examples reused another operation meaning | resolved documentation |
| R06 | Empty artwork root could be sealed irreversibly | resolved source |
| R07 | Slow keeper reads could miss newly due harvest or compound | resolved source |
| R08 | Canonical-preparation positive fixture failed before body | resolved test or fixture |
| R09 | Royalty recovery fuzz allowed permanent remainder | resolved test or fixture |
| R10 | Foreign-home Vault construction was accepted | resolved source |
| R11 | Bare immutable artwork scheme consumed setup | resolved source |
| R12 | Wrong fresh reservation ID consumed permanent capacity | resolved source |
| R13 | Between-anchor tests mutated the first pinned block | resolved test or fixture |
| R14 | Exact-source import test lacked a negative tamper case | resolved test or fixture |
| R15 | Legacy annotation compatibility checked only two fields | resolved test or fixture |
| R16 | Documentation semantic assertions searched whole page | resolved test or fixture |
| R17 | Enabled harvest test did not assert due submission | resolved test or fixture |
| R18 | Seal tests accepted unrelated reverts | resolved test or fixture |
| R19 | Payout and callback tests omitted economic rollback state | resolved test or fixture |
| R20 | Tiny royalty coverage lacked tranche rotation and transfer | resolved test or fixture |
| R21 | Current financial venue fixtures lacked execution readers | resolved test or fixture |
| R22 | Native balance cheatcodes invalidated rollback modeling | resolved test or fixture |
| R23 | Invariant replacement plans lacked validation child | resolved test or fixture |
| R24 | Positive fixtures retained bare artwork schemes | resolved test or fixture |
| R25 | Normal profile validator rejected approved read permission | resolved tool |
| R26 | Pre-seal readiness requested private storage getter | resolved tool |
| R27 | Current trusted build admission and stale test family labels | resolved tool |
| R28 | Last manual head could orphan final simulated anchor | resolved tool |
| R29 | Default97% test wrongly rejected98% deployment | resolved test or fixture |
| R30 | Explicit99% policy test wrongly rejected99% deployment | resolved test or fixture |
| R31 | Native donation assertion omitted19 earned units | resolved test or fixture |
| R32 | Royalty window test was named FullDay | resolved test or fixture |
| R33 | Repairing fixtures did not prove dependent economic behavior | resolved selected verification |
| R34 | New pre-seal planner dereferenced unknown SeaDrop terms | resolved tool |
| R35 | Enabled composite execution source allowed8decimals | resolved tool |
| R36 | Mutually matching wrong native pins passed offline plan | resolved tool |
| R37 | Protocol implementations could masquerade as external feeds/VRF | resolved tool |
| N01 | Passing count alone could admit substituted evidence methods | resolved this consolidation |

## Accepted decisions, actual limits and missing release evidence

| ID | Issue | Treatment |
| --- | --- | --- |
| L01 | Extra compound waiting rule is service-only | Do not silently add an on-chain restriction; monitor/revoke/pause using existing roles. |
| L02 | Unallocated royalty recovery uses inclusion-time active weights | Preserve approved economics; no retrofit expected-cohort parameter. |
| L03 | Terminal principal sends ETH and ZZZ atomically per NFT | No silent partial-payment/accounting redesign; retry or owner fallback where usable. |
| L04 | Opening/zero-cohort/unadmitted royalties are not always immediately allocated | Do not promise no unallocated funds at every instant or award everything to first late activator. |
| L05 | LP dust barrier is a split exception | Do not use global90% arithmetic across such barriers. |
| L06 | Emergency governance may omit financial protections | No keeper force fallback or always-success promise. |
| L07 | Per-operation caps do not bound cumulative turnover losses | Monitor realized costs/turnover; do not fabricate attacker net profit. |
| L08 | Generic seal does not prove selected SeaDrop/converter release binding | Use selected-release checklist; omission after seal needs compatible replacement/reconstruction. |
| L09 | Expired nonzero mint end cannot be reopened | Delay initial deadline write until viable, or reconstruct before funds. |
| L10 | Wrong-but-nonempty content or fixed venue/token graph is irreversible | Qualify before funds/seal; no arbitrary token/core mutation after seal. |
| L11 | Pending unanswered VRF can block rotation and replacement | Pause new minting; require actual provider funding/callback qualification. |
| L12 | Permanent reservation, terminal exit and canonical retirement do not unpause open | Use explicit lifecycle recovery, never generic unpause or hidden sweep. |
| L13 | Arbitrary tokens and rejecting receivers cannot be forced to work | Conventional admission, per-currency healthy claims, isolated payouts and explicit retry/fallback remain. |
| L14 | Raw fixed-ZZZ LP claims remain deliberate recovery | No silent entitlement removal; royalties remain original currencies with no swaps. |
| L15 | Own-swap proof and jitter do not provide manipulation immunity | Independent market/depth qualification and economic monitoring are still required. |
| L16 | Generic revert, staged metadata and missing raw logs limit assurance | Preserve limits rather than rerun unchanged tests for counts or manufacture evidence. |
| L17 | Old wrapped/Pons fork and royalty-converting cases remain historical | Use explicit current native harness; skipped legacy tests do not qualify markets. |
| Q01 | Independent ETH/ZZZ sources and usable bidirectional routes/depth | actual market/source snapshots; genuine independent exposures and postwithdrawal execution depth |
| Q02 | Complete target fees, RPC capacity and final constructor/operation gas | exact current deployment/operation envelopes, complete fee components and provider history/tracing capacity |
| Q03 | Maximum-state gas and activation/currency/claim workload | measured cold64currency and maximum-state workloads; count ceilings alone never approve gas |
| Q04 | Authorities and contract-wallet envelopes | actual reviewed authority identities, key recovery and manual outer-wallet envelope execution |
| Q05 | OpenSea, VRF and immutable content delivery | actual onboarding, gross fee/net terms, funding/callback and complete immutable artwork retrieval |
| Q06 | Integration rollout, hosting and restart/backup/recovery operation | matching installed consumers, source-bound state and real operational outage/restore evidence |
| Q07 | Independent audit and release remediation/approval | independent review plus closed remediation and explicit release sign-off |
| Q08 | Tight runtime/initcode headroom | preserved normal gate; future justified changes need measured size-safe placement, no cap/compiler relaxation |

## Review and evidence scope

All37Markdown files in the five publication-selected families were ingested and pinned through [SCOPE.json](SCOPE.json). Substantive reviews, findings, risk/scope supplements and the two per-method matrices were read against current code and historical verification. Large generated Python/Solidity corpus tables were ingested as navigation/fixture inventories; that is not a fresh manual audit of every declared method. The registry records source hashes and original report anchors rather than relabelling prior observations.

Rights/accounting reconciliation confirms that current-owner claims, exact-unit rights, original-currency royalty cutoff/deferred/recovery cohorts, terminal principal separation and lossless canonical backing retain their explicit source rules. No additional production-rights defect was confirmed by this finite reconciliation. Accepted current-weight recovery, atomic ETH+ZZZ principal payments, unsupported-token/receiver constraints and raw-ZZZ LP recovery are not silently redesigned.

No old report is edited, no old test campaign reruns, and no production Solidity, economics, permission, deployment, service, signing, chain or journal action occurs. The maintained current index may summarize earlier limitations, but original absent logs, intermediate source scopes, synthetic seams and unrun workloads remain visible.

## Added diagnostic correction

| ID | Issue | Current disposition |
| --- | --- | --- |
| N02 | Complete pre-seal input omitted disabled ordinary-pool stop | resolved this consolidation; two real-planner methods pass, no configuration change |
