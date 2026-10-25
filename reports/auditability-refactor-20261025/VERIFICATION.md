# Scoped verification - 2026-10-25

This verifies the four authorized auditability refactors against baseline
`ba91651805051a974070b8a07543fa18d20d3551`. This is an undeployed candidate,
not a full regression, real dependency qualification, formal equivalence proof,
independent audit or production approval. [Review and changes](REVIEW.md).

## Compiled compatibility and size

The unchanged 0.8.26/Cancun/via-IR/optimizer1/Yulfalse normal production profile
compiles all 44 production sources and passes **37 object size gates**. A fresh
all-source ABI/AST pass covers **131 inputs**, including the final test-only
version assertion repair. Full compiler payloads remain external, hash-bound by
[build bindings](build-bindings.json), [normal size gates](solidity/production-size-gates.json)
and the final fixture receipt.

[Compiler comparison](compiler-comparison.md) checks 101 common project objects:
function/constructor/input/output names and order, tuple fields, external types,
mutability, errors and event indexing remain. Recursive storage slots, offsets,
member names and types match. Only six converter struct-owner `internalType`
paths and three byte-identical duplicate error entries are normalized. These
are explicit ABI metadata differences; raw JSON ABI identity is not claimed.
Solidity source integrations constructing the policy structs use the neutral
base type. The public surface remains 31 concrete contracts, 608 functions,
31 constructors and 13 receive hooks, with no explanation/input-note gaps.

| Object | Runtime before -> after | Change / remaining runtime margin |
| --- | ---: | ---: |
| LiquidityManager | 21,113 -> 20,769 | -344 / 3,807 |
| ActivationEntry | 17,985 -> 17,956 | -29 / 6,620 |
| LPRewardConverter | 16,952 -> 16,830 | -122 / 7,746 |
| RoyaltyConverter | 16,952 -> 16,830 | -122 / 7,746 |
| CanonicalHandoff | 20,895 -> 21,034 | +139 / 3,542 |
| Vault | 22,852 -> 22,852 | 0 / 1,724 |

Access total initcode remains 42,177 with 6,975 bytes below 49,152. Registry creation
shrinks 29 bytes; its runtime stays 10,269. RoyaltyFactory still has 69 bytes of
runtime margin. The internal v3 library emits a 62-byte compiler object without
an external callable ABI or linked deployment dependency; normal gates include it.
Named typed phase constants cause different Handoff code generation under the
same settings. Its 139-byte increase is accepted for clarity and recorded rather
than called a saving. No gas optimality or fresh maximal target-chain gas proof.

Vault/Migration executable runtimes are identical after metadata stripping.
The separate [known-metadata comparison](embedded-metadata-comparison.json) proves
their creation differences are confined to two recorded compiler metadata regions
each. Handoff executable bytes differ. [Static readability comparison](readability-body-comparison.json)
checks 53 Vault, 26 Migration and 25 Handoff bodies after explicit private aliases,
20 unchanged constant values and formatting normalization. Static comparisons
are separate from actual EVM execution and do not establish absence of exploits.

## Solidity execution

**26 distinct selected methods pass across two explicitly recorded fixture scopes.**
The first campaign executes 25 selected bodies and two inherited repeats. Its
pinned driver returns an incomplete-selection status because it does not model
inherited test discovery. The original [raw summary](solidity/focused-raw-summary.json)
is retained. [Strict reconciliation](solidity/focused-reconciled-summary.json)
proves every selected method passed, no method is missing, and the only two
extras are the exact compiler-AST-defined base methods inherited by
`EntryReviewPolicyTest`, without setup/state/modifier overrides. They are not
counted as two additional behaviors. Forge itself returns success.

Review also found a pre-existing unselected NativeVaultFlows assertion expecting
accounting version 2 against current version 3. Only that single byte was repaired,
with the exact preimage and diff retained. It lies entirely in an omitted method
span of the earlier 25-case profile; all earlier retained methods/helpers and all
production source hashes remain exact. Fresh final 131-input typechecking and
only the corrected activation/growth/value method ran afterward. The
[combined receipt](solidity/combined-selected-summary.json) binds both scopes
and does not portray the earlier 25 as rerun against a later fixture.

Four new methods test native settlement callback disarming/recipient read order
for collect/close, matching v3 endpoint orders, and all six mismatch stages with
poisoned later getters. Other selected methods cover exact ERC20 encoding,
conversion loss/ownership rollback, incumbent-only earned LP and royalties,
wrapper outage recovery, prefunds, callback isolation, installed-v4 native
conversion, reviewed growth floors, failed placement, share/fee checkpoints,
repeated rebalancing/current-owner claims and full converted-native handoff.

The [runner and selection scope](solidity/SELECTION.md) retain the exact chosen
bodies, constructors and helpers and omit only unselected test spans. MockAccess,
prices, tokens/venue and local installed-core substitutes retain their fixture
limitations. The recipient-order tests do not imply real sealed modules are
rebindable. This uses isolated temporary EVM profiles, not persistent Anvil,
live RPC/VRF, actual market services or an operating rehearsal.

## Event/schema and documentation

**20 distinct affected Python methods pass**, including two new nested-source
regressions. [Final evidence](event-schema-tests.json) preserves all 135 event
descriptors, including 33 historical descriptors, exactly. No schema file rewrite,
descriptor drop or alias rename was used to hide the refactor.

The two new controls first fail under top-level-only discovery. A plain recursive
attempt then exposes a Windows ordering alias regression. Exact failed scripts,
logs and reasons remain in the report. Deterministic depth/POSIX-path discovery
fixes both while retaining canonical top-level names and rejecting incompatible
indexed layouts. Retries are counted once. These are generator checks, not actual
indexer/provider qualification.

Source consistency, generated callable reference and sole Todo checks pass.
Local Markdown target checks and artifact hashes are recorded at publication.
The operator manual, component map, architecture, features, roadmap, release
record and repository memories document this refactor without changing task
statuses or introducing a second Todo.

## Unchanged operating boundary

ETH/fixed ZZZ contributions; separate LP/royalty ledgers; 80/10/5/5 allocation;
2/1/3% default limits with 10% maxima; gas separate; direct governance2;
accounting3/local canonicalV4 and all ownership/custody rights remain unchanged.
No public transaction, deployment/seal, service or monitor action, website
source/build/server, existing 8902/Anvil/NFT/LP/balance/journal/dist-overlay change.
Signing stays Anvil-only, public DEPLOYMENT null and monitoring paused.

Actual website3/provider acceptance, feeds/routes/VRF/authorities/OpenSea,
strategy and maximal gas qualification, operating rehearsals and independent
audit/remediation remain open. Main only; preserve unrelated drafts. A local
save is not a push: inspect the separate publication receipt. Production
NOT APPROVED.
