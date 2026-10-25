# Readiness improvement: exact verification scope

Read [findings and limits](REVIEW.md), the [operator guide](../../docs/NATIVE_WEBSITE_PROFILE.md)
and the separate publication receipt. **Production NOT APPROVED.** No full fresh
regression, independent audit, release approval or actual native financial
transaction is claimed.

| Boundary | Evidence actually obtained | Scope and limits |
| --- | --- | --- |
| Vault private refactor | [12 distinct scoped Solidity cases](vault/VERIFICATION.md), normal37 object gates across42 final production sources, exact public ABI and normalized recursive storage layout equality. | Installed local v4 lifecycle/placement/failure, cap/reentry, pool movement, custody consolidation/return and cold accounting-capacity gate. Source/test dependencies retain their declared substitutions. No actual target-chain gas qualification. |
| Size and gas | Vault24,263 runtime/313margin; creation including96argument bytes47,102/2,050margin. Cold activation11,510,987 under unchanged12M. | Compiler/optimizer/runtime/initcode/gas limits unchanged. One cached verbosity repeat captures the named gas metric, not another distinct case. No controlled before/after gas-reduction claim. |
| Native browser/API contract | [119 final affected Node cases](website-staged/post-review/VERIFICATION.md):39 native,4 UI,76 affected legacy API/earnings.31 selectors and4 module IDs independently checked. | Exact current Python protocol/NFT/preparation DTOs use synthetic dependencies and prices. Positive native LP+royalty ETH claim, both missing-ledger failures and malformed-history controls are included. No real extension, chain or live service acceptance. |
| Earlier native candidate | [121 earlier passes](website-staged/VERIFICATION.md), including27 unchanged coordinator cases. | Explicit pre-review source scope. Later119 is not added to121 as a distinct final regression. The final financial-validation delta does not change signer/coordinator code. |
| Headless browser | [Four final cases](website/browser-results.json):native activation, growth, exact token approval, combined native LP+royalty claim. | Actual DOM/modules and current Python DTOs over mocked RPC; synthetic readiness/inventory and unavailable optional history. Only address authorization wallet methods are permitted; no signer/send call. First packaging attempt lacked the new fifth fixture; final fixture/case set fixes that harness mismatch. |
| Website build/preservation | [Syntax/asset/build receipt](website/build-result.json):5,599 isolated build files;5,598 existing dist files remain byte-identical. | Existing signer/client/coordinator/null public configuration are byte-identical. Source applied locally after explicit permission; clean build is external. No static server/service/chain/journal action. |
| RPC implementation | [18 distinct affected Python methods](../real-service-readiness-20261025/VERIFICATION.md), including negative controls against original false qualification. | Fake RPC, actual local transport/error boundaries and discarded simulation structure. No real provider is approved by those tests. |
| Public reads | [Dated observation](../real-service-readiness-20261025/public-rpc/README.md):Pinax11 basic checks pass; documented public endpoint HTTP403 from this environment. | User-authorized bounded read-only mainnet requests. Independent explorer corroboration also403; identity-pinned preparation/Approval(0) trace was not run publicly. No price source, redundant-provider/SLA/archive/history/fee/throughput/finality approval. |

## Applied versus staged and reused evidence

The earlier website-staged record preserves the initial rejected source write and
pre-fix candidate. The user then explicitly approved local source integration.
The final [application record](website/applied-site.json) binds the actual source
to the post-review tests and build. Its source hashes match the tested isolated
copy. No attempt bypassed the approval rejection. The separate read-only public
probe also ran only after explicit permission; initial environment failures remain
recorded instead of being counted as provider capability failures/passes.

Historical Entry/Pricing, economics, rewards, royalties, metadata, keeper,
canonical handoff, migration and broader native-port reports retain their exact
original source scope. Unchanged suites were not rerun merely to increase counts.
The new Vault changes are limited to the three reviewed private refactors.
ABI/storage equality is structural evidence, not formal semantic equivalence.

Actual complete native wallet/deployment/preparation traces, independently
qualified pricing/conversion/input routes and VRF, authority addresses, OpenSea,
content publication, sustained operating/recovery rehearsals, full target-chain
gas/strategy economics and independent audit/remediation remain open. Public
DEPLOYMENT is null and the signer remains Anvil-only. No public transaction,
deployment, sealing, key access, service/monitor restart, existing test-chain
reset or journal deletion occurred. Main-only publication is recorded separately.
