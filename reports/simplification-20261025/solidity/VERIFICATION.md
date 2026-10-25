# Scoped Solidity execution

Two bounded runs passed: **87/87** before the last Access size repair, followed by
**6/6** against the final Access source. Four Access cases repeat, so this is
**89 distinct selected methods**, not 93 independent checks or a full regression.
The [machine receipt](verification.json) binds both scopes, raw results and source
hashes. All 41 final production hashes and the final selected-source hashes match
the current checkout when this receipt was written.

| Selected behavior | Initial passes | Final follow-up |
| --- | ---: | ---: |
| Fixed ETH/ZZZ identity, factory and direct/Entry source boundaries | 9 | — |
| Native LP fee/reward allocation, backing, codecs and donation isolation | 17 | — |
| Native custody exit/return | 6 | — |
| Native canonical classified funding/abort | 7 | — |
| Custody snapshots, conversion/raw exits, budget, recovery and authority | 25 | — |
| Membership dust and incumbent entitlement | 4 | — |
| Token-pull/LP-placement callback and donation boundaries | 2 | — |
| Caller-bound reviewed Entry policy, malformed/retired calls and rollback | 8 | — |
| Sealing, fixed token and retired module admission | 4 | 4 repeated |
| Whole-collection ownership, shares, traits, both ledgers, abort, 1,000 NFT inventory, maximal local domains and dormant continuation | 5 | — |
| Terminal Access states and actual retired-source/unpause path | — | 2 |

The initial native allocation fuzz reports 1,000 trials; custody execution-loss
fuzz reports 1,001 including replay. The final terminal-state fuzz reports 1,000.
They count as three test methods, not thousands of distinct reviewed behaviors.

## Source and compilation boundaries

The [AST-selected harness](run-focused.py) reads successful compiler input/output
and the normal size report, verifies source contents and Cancun/via-IR/optimizer
settings, and resolves the import closure through compiler AST imports. It masks
only unrelated `test*` function spans and attached documentation with whitespace;
selected assertions, constructors, modifiers and all helper bodies stay byte-exact.
It rejects retained references to omitted tests. Dependencies retain the normal
repository remappings. Compilation/execution uses Foundry 1.4.4 and solc 0.8.26,
optimizer runs 1, Yul disabled, and fuzz runs 1,000. No EVM/compiler/size/gas
threshold is relaxed.

The AST7 profile preserves 362 selected/helper function definitions across 58
copied files and omits 105 unrelated methods. The final AST8 profile preserves 169
across 49 files and omits 91 unrelated methods. Original/transformed source hashes,
exact omitted names/spans and retained body hashes are recorded in the manifests.
These transformations limit compilation; they do not establish equivalence or
coverage of unexecuted tests.

Only `ZZZAccessController.sol` changes between production scopes:

- AST7: `def515407c49c343dacf912918d4bde80aa854f4714ed6e5502949af53585929`.
- Final AST8: `52a43030c26e16d3d2556f7ad09535d44fe1000ca02ff755828fa3abd3568174`.

The final change replaces explicit terminal-state equalities with `state > 2`.
The only transition writer admits states 0–4; states 3/4 remain terminal and
impossible higher stored states also fail closed. The follow-up checks both
terminal states against every valid next state and the real retire/unpause path.
The four original Access cases were repeated; unrelated 87-case methods were not.

The earlier Access artifact had 48,872 creation bytes; exact minimum nonempty
role arguments exceeded EIP-3860 by 8 bytes. Foundry unit passes are **not** proof
that this public deployment fits. The separate final normal gate measures 48,835
creation + 288 role-argument bytes = 49,123, with only **29 bytes** of headroom.
Larger role arrays require exact separate qualification. The final 36-object size
report and 122-input typecheck remain separate evidence owned by the main review.

## Raw evidence and reproduction

- [AST7 summary](ast7-focused-summary.json), [raw results](ast7-focused-results.json),
  [full transformation manifest](ast7-focused-transformation.json).
- [Final AST8 summary](ast8-terminal-focused-summary.json),
  [raw results](ast8-terminal-focused-results.json),
  [full transformation manifest](ast8-terminal-focused-transformation.json).
- [Final six-case selection wrapper](run-terminal-guard.py).

Compiler input/output, isolated profiles and normal size artifacts are retained in
the external `simplification-audit-20261025/solidity` workspace. They are large
review artifacts, not deployed dependencies. Reproduction requires a matching
source checkout and the corresponding reviewed artifacts; source drift fails
rather than silently reusing old evidence. The first preparation rejected a
remapping-list mismatch before running a compiler; the harness was corrected to
compare shared production aliases and the full normal Foundry map. No test pass
is attributed to that rejected preparation. The earlier broad closure run was
stopped and supplied no passes.

## Limits

Real Vault/Entry/accounting/controller paths are composed with explicit fixture
feeds, tokens, randomness and liquidity venues. Callback tokens and raw donation
checks are adversarial local fixtures, not actual token/provider approval. Test
gas includes fixture construction and aggregate calls and is not target-chain gas
qualification. No existing Anvil chain, NFT, LP, balance, journal, wallet, server,
service, monitoring state or public transaction was changed.

Actual selected-pool integration, feed/route/VRF qualification, authority settings,
OpenSea, target-chain gas, operating rehearsals and independent audit/remediation
remain open. Production is **NOT APPROVED**.
