# Simplification verification

This is an internal, source-scoped candidate review. It is not a fresh full
regression, real-market qualification, published CI result or independent audit.

## Completed evidence

| Check | Scope and result |
| --- | --- |
| Production build | 41 production Solidity inputs, normal 0.8.26/Cancun/via-IR profile; 36 runtime/initcode object gates pass. Compiler inputs are frozen before compilation and a changed source rejects the report. |
| Exact Access constructor size | Creation 48,835 bytes plus 288 bytes for one proposer/one executor is 49,123: **29 bytes below EIP-3860**. Larger role arrays require exact qualification and may not fit. Actual authority configuration remains unset. |
| Vault size | Runtime 23,889 bytes: 687 bytes below EIP-170, compared with 313 bytes before this simplification. |
| Whole Solidity typecheck | Snapshot 8 checks all 122 current production/test/script inputs with ABI/AST output and zero errors. This does not execute financial assertions. |
| Backend inventory/observer | [40 distinct scoped methods](BACKEND_VERIFICATION.json), including version separation, exact current helper inventory, source identity, removed-intake rejection and fixed exit identity/code pins. Failed intermediate fixtures and their repaired reruns retain their own scope. |
| API/keeper profile | Six distinct new methods pass: explicit LP-only schema, unsupported profile rejection, ETH/ZZZ source binding, retired job/submission rejection, preserved journal identity and exact fee-controller runtime/version requirements. Offline RPC fixtures only. |
| Callable reference | 31 contracts, 649 functions, 31 constructors and 14 receive hooks; zero missing function/caller/native-value explanations and zero unannotated top-level inputs. Outputs retain exact ABI types; 144 positions rely on the function purpose rather than a dedicated output note. |

The initial Registry initcode exceeded the normal limit. A fixed noncustodial
factory repaired construction without changing custody/configuration powers.
A later exact-argument check caught Access eight bytes over the limit; replacing
two terminal-state equalities with the equivalent bounded-state comparison fixed
that issue. States 3/4 remain terminal; impossible higher states fail closed.
Object-only dynamic constructor checks were strengthened to include minimum
nonempty role arrays. No optimizer, EVM or size threshold was relaxed.

## Targeted execution

The first AST-selected campaign passed87/87 methods on its recorded pre-terminal-
comparison source: source policy9, callback boundary2, native fees17, native
custody6, native canonical7, custody25, dust4, reviewed Entry8, Access4 and
canonical5. After the equivalent terminal-guard size repair, only six affected
final-source methods were run: five Access (including the new terminal fuzz) and
one actual retirement/unpause case;6/6 passed. Four repeated Access methods are
not extra distinct coverage: **89 distinct selected behaviors across two source
scopes**, not a fresh full final-source regression. Only Access production source
changed between those scopes.

The external AST-selected harness keeps selected assertions and all helper bodies
byte-identical, while whitespace-omitting unrelated test methods to limit
compilation. It records original/transformed hashes and all omitted methods.
Native allocation and terminal-state fuzz each use1,000 runs; custody loss uses
1,001 including its recorded replay. No omitted case is counted as executed.
The earlier uncompleted broad-closure run was stopped after the user replaced the
governed-token design with fixed deployment identity; it supplied no passes.

Two additional indexer methods verify new fixed-identity/custody events, malformed
address rejection and preservation of historical custody topic decoding. They
are separate from the six API/keeper methods; no old event schema was removed.

## Retired tests and historical deployments

[Archived fixtures](retired-test-fixtures/) preserve removed creator/bridge and
obsolete wrapped-pool cases. The old Entry suite is preserved under
`test/legacy/` with its retirement receipt. Removed cases are not counted as passes.
Mixed local LP, royalty, callback, custody and handoff assertions remain active.
The former wrapped/Pons fork evidence does not qualify this native hookless
candidate. A reviewed current selected-pool fork rehearsal remains open.

No existing Anvil/NFT/LP/balances/journals, website source/build/server, signer,
service, public transaction or paused monitor was changed. Current public
DEPLOYMENT stays null, signing stays Anvil-only, and production is NOT APPROVED.
Actual feeds/routes/VRF, authorities, OpenSea compatibility, target-chain gas,
operating rehearsals and independent audit/remediation remain required.

The retired native fork fixture makes current real fork qualification explicitly
blocked before RPC/Forge, not silently passed. The published HEAD-only runner
patch passes16 affected offline unit methods; the preserved dirty working tree
passes21. They are separate source scopes, not added counts. Source consistency
also passes for41files; it remains a narrow text/import inventory check.

Read the separate publication receipt and Git for what is committed/pushed;
local verification does not imply publication or deployment.
