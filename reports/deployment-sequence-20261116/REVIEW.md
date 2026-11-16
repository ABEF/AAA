# Conditional offline deployment sequence — 16 November 2026

Implemented the authorized offline address/nonce planner on baseline main
`4a3b30dd8d85d923d97d1892568280eec8328ce1`. It derives25 conditional top-level
CREATE addresses across44 same-bootstrap-EOA transactions, including19bindings,
then supplies them to the unchanged trusted constructor reviewer.
**No RPC, signature, deployment, sealing, nonce reservation or live adoption.**

New files: [sequence module](../../zzz_ops/deployment_sequence.py),
[CLI](../../scripts/prepare-deployment-sequence.py), and two focused test modules.
The existing constructor planner, accepted normal builds, all61 Solidity sources,
accounting, economic rights and safety/default/size limits remain unchanged.
Factory/helper/data-child addresses remain getter-discovered, not predicted.

## Implemented checks

| Area | Behavior |
| --- | --- |
| Sender/nonce | Explicit public nonzero assumed direct-EOA sender and canonical decimal starting nonce. Known dependencies reject; EIP-2681 bounds and an exhausted construction endpoint reject. No live code/control/confirmed/pending nonce is inferred. |
|44-call schedule |25creations, separate policy binding,16module bindings and2helper bindings. Frozen reviewed graph/order digests reject sequence drift. All12 later setup checklist items are excluded from nonce assignment. |
| Address mathematics | Canonical RLP(sender,nonce), Ethereum Keccak and final20bytes. Zero/single-byte/length-boundary encoding is handled. Formula is chain-independent; this profile still fixes chain4663 and requires separate live verification. |
| Dependencies/targets | Creation references must point backward to created roles; bindings require their actual source-defined targets/instances to have been created. All calls conditionally use the same bootstrap EOA. |
| Input addresses | Null top-level assignments are filled. Existing nonnull assignments must match or reject. Original constructor/authority/native/collision validation runs again after derivation. Caller input is not mutated. |
| Constructor composition | Embed the unchanged strict `constructor_plan`, its accepted build/ABI/source/size checks and manifest. Link per-creation initcode hashes. Missing settings stay blocked; getter-derived child arguments remain unresolved. |
| Truthful outputs | Outer predictions are explicitly conditional; embedded old component still treats its inputs as unverified assignments. Readiness/authority/binding/production approval stayfalse. No ready-to-send binding calldata, signer, arbitrary queue, setup/seal call or resume capability. |
| Publication | Existing64KiB input/16MiB output and flushed exclusive publication remain. Existing files, aliases/collisions and uncertain output are preserved. No overwritten artifact or automatic approval. |

Access's actual CREATE sender becomes bootstrap. A selected governance wallet
cannot silently replace it for pre-seal bindings. Safe/contract/factory/batch/
user-operation/delegated-account/authorization-list paths are not modeled.
Every listed operation must be one ordinary successful transaction from that
same sender in exact order. Unexpected/failed/replaced/cancelled nonce use requires
reviewed reconciliation; this fresh-phase tool cannot resume a partial deployment
or shift saved wallet/journal nonces automatically.

`next_nonce` and remaining legal transaction capacity are reported. The sequence
rejects complete nonce exhaustion, but an endpoint with only one legal send left
does **not** prove later setup/sealing can finish. Additional operations/counts,
live authority/state, available addresses, constructor receipts/runtime immutables,
getters, bindings, market/provider/VRF/OpenSea/fees and approval remain separate.

The chosen derivation follows [geth's CREATE implementation](https://raw.githubusercontent.com/ethereum/go-ethereum/master/crypto/crypto.go),
canonical [RLP](https://ethereum.org/developers/docs/data-structures-and-encoding/rlp/)
and [EIP-2681](https://eips.ethereum.org/EIPS/eip-2681). It does not calculate
permissionless factory nonces; unrelated callers can change those child addresses.

## Verification actually performed

**38 distinct new methods pass across recorded stages:18 core and20 CLI/publication.**
The core passes first try in three disjoint selections (1math,1current-build
composition,16others). The CLI has one representative and18other initial successes;
one failed new method repeats after the narrowly scoped correction below. No
unchanged tests, compiler/static/EVM/browser suites or deployment/node work ran.

The core covers independent offline Cast CREATE vectors, canonical boundaries,
all44nonce offsets, all25predicted addresses against accepted actual receipts,
strict inputs/overflow/exhaustion, graph/order/caller/dependency guards, matching/
conflicting assignments, collision controls, current constructor preparation,
blocked settings, input immutability and preserved old limits/false flags.
CLI checks inject preparation and exercise exact input/argument forwarding,
bounded parsing/output, exclusive actual file publication,0complete/2preview,
safe errors and possible complete-artifact uncertainty.

One new CLI check found **ambiguous option abbreviation**: standard argparse could
interpret `--deploy` as `--deployer`. It created no deployment capability but was
an unclear interface. The parser now requires exact flags. Only the affected
failed method was repeated; the other19CLI successes remain source/AST-bound.
Core module is byte-identical across that parser-constructor-only change.

Accepted historical44receipt/transaction members and their hashes provide an
independent address/nonce witness. Address math does not depend on initcode, so
the old record can check25predictions/19bindings without executing transactions.
**This is not new metadata2 constructor/runtime/gas or target-chain acceptance.**
Offline Cast computes addresses only; no RPC, key, signature or EVM is used.
See [verification](VERIFICATION.md) and the [lossless evidence inventory](EVIDENCE.json).

Internal source/CLI reviews found no additional concrete nonce/accounting defect.
They are not independent production audit. Hash-only preservation verifies all
61 Solidity,14 semantic and742 existing Python files plus6281 earlier report
files; four unrelated dirty files stay exact and unpublished. Existing normal
artifact/constructor evidence keeps its original source scope, with no new
compiler/gas/CI-green claim.

## Operator procedure and release boundary

Use [the complete sequence guide](../../docs/DEPLOYMENT_SEQUENCE.md) and the
[single operator manual](../../docs/OPERATOR_MANUAL.md#prepare-deployment-addresses-and-nonces).
The public sender/nonce and manifest hashes are planning inputs/fingerprints,
not on-chain `reviewHash` values, authority proofs or nonce reservations.

The [deployment-initcode task](../../TODO.md#task-deployment-initcode) stays In
progress for actual release inputs, EOA/control/code/confirmed-pending nonce,
receipt/runtime/getter reconciliation, complete fees and independent approval.
No actual addresses are adopted into production inventories. Existing Anvil,
NFT/LP/balances, databases/checkpoints/journals, signer/public-null configs,
websites/services and user-paused heartbeat were not contacted or changed.
