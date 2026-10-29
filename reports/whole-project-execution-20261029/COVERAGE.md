# Coverage and limits

This is a completed internal source-review pass and implemented repair campaign,
not exhaustive execution, independent audit or production approval.

| Surface | Actual depth and evidence |
| --- | --- |
| Solidity/authority/custody | All33concrete components,3bases,6libraries and5interface files read;644project function/modifier bodies bound to exact AST extents and case reasoning in [ledger](body-coverage.json).742ABI entries include696functions/33constructors/13receivers;297generated getter rows are not644handwritten bodies or tests. |
| Imported implementations |77selected reachable dependency bodies plus actual PositionManager/PoolManager/Permit2 settlement/approval semantics reviewed.228dependency bodies inventoried; unreferenced package behavior and generated/virtual lowering are not certified. [Compiler/dependencies](COMPILER_DEPENDENCIES.md). |
| Economics/user journeys | Mint/reveal/transfer; activation/growth/original budget/share-NAV; actual fee split/fractions/collective membership; royalty fault cohorts/conversion/claims; harvest/compound/burn; normal/emergency rebalance; parking/move; holder exit/payout; complete pre-exit same-chain handoff/abort/forwarding traced. Prior scoped verification is reused only at exact applicable pins; two new composed emergency methods executed. |
| Keeper/health/recovery | Pending/nonce/spend/canonical receipts, sampled evidence/reset/cadence/jitter/priority, optional jobs, harvest/compound/buyback, runtime/config/health/locking/retry/terminal payout paths read.153named/nested rows across11modules are a static navigation ledger, not test counts.64focused methods pass; actual strict timing and Linux/host recovery remain unqualified. |
| Backend/financial data | Indexer atomicity/reorgs/raw events; read API lifecycle/custody/ownership; unsigned reviews/admission; per-NFT/collection/current-price earnings, lineage/conversion/claims; strict RPC/ABI/JSON; observers/review bundle/state inspected. [Inherited body ledger](backend-body-review.json) and [wrapper ledger](wrapper-body-review.json) include previously deferred helper bodies.96methods:92pass/4Unix skips. |
| Website/wallet | Prior16feature-family/account/provider/session/receipt/approval/recovery/cards analysis reused at source pins for unchanged modules, including shared signer. New preview/generator/reference metadata changes checked separately:3methods cover all2784states without rendering. No fresh4/browser extension/public transaction/100user/marketplace acceptance claimed. |
| Artwork/publication | Strict static/resource/JSON/reference/archive behavior verified by14focused methods; existing2784SVGs checked against every approved hash. New fixed rarity reference metadata is source-only. No texture regeneration, pinning/CID/marketplace/rendering/refresh qualification. |
| Tooling/operations/build | [Tooling ledger](TOOLING.md) records actual wrapper/generator/build/CI reads, guarded loopback tests and publication boundaries. Catalogue admission now survives optimized Python. Normal compiler/build/39gates are reused only after exact78source and settings comparison; exact constructor/target gas remain separate. |
| Docs/operator/release | Sole task ledger, callable explanations, prompts, feature/reference/roadmap/approval/manual/context updated; source and report links checked. Documentation/signatures/source publication do not authorize operating rollout or transactions. |

The earlier [whole-project report](../whole-project-audit-20261029/COVERAGE.md)
retains its original494pending body rows and122output gaps. Those are historical
to its exact source. The new body review/notes above address that depth gap;
they do not retroactively relabel old reports or establish every possible case.
