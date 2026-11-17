# Conditional offline deployment sequence

Use `scripts/prepare-deployment-sequence.py` to derive the25 top-level CREATE
addresses for the current44-transaction fresh-deployment phase, then feed them
into the unchanged [constructor reviewer](DEPLOYMENT_PREPARATION.md). This is
offline preparation: **no RPC, key, signature, transaction submission, nonce
reservation, configuration adoption or sealing** is performed.

Contract addresses depend on the creating account and its transaction nonce.
Bindings consume sender nonces too, even though they create no top-level contract.
Predicting25 consecutive creations without accounting for the binding steps would
therefore produce wrong addresses.

## Required inputs

Start with a reviewed copy of the existing [constructor-input example](../config/deployment-preparation.example.json).
Keep unknown authorities/dependencies null; do not invent them to obtain a pass.
The new tool uses that same schema and existing64KiB input/16MiB output bounds.

| Input | Meaning |
| --- | --- |
| `--input` | Existing constructor JSON: governed roles, fixed native dependencies, URI, constructor ceiling and qualification references. |
| `--deployer` | Public nonzero address of the assumed **direct EOA** that will create Access and send all44 ordinary transactions. This is not automatically the governance/keeper address. Known protocol/dependency addresses reject. |
| `--starting-nonce` | Exact nonnegative decimal string for the first creation's sender nonce: no hex, sign, leading zeros, Boolean or guessed live state. |
| `--output` | A new exclusive file in an existing owner-controlled directory. Existing/dangling paths are never replaced. |
| `--build-profile` | Optional exact closed trusted build ID; default `operator-seal-20261117`. Unknown IDs fail and source drift never falls back to older artifacts. |

From the repository root, replace every placeholder:

```sh
python scripts/prepare-deployment-sequence.py --input /review/constructor-input.json --deployer REVIEWED_PUBLIC_EOA_ADDRESS --starting-nonce REVIEWED_DECIMAL_NONCE --output /review/new-sequence.json
```

No private key or RPC URL belongs in these inputs. Rejected argument values are
not echoed; abbreviated options are rejected. A zero starting nonce is merely
an encoding example, not a selected wallet or adopted nonce.

## Sequence and address checks

The source-bound phase contains:

- 25 top-level creations in the reviewed constructor order;
- 1 separate ProtocolPolicy binding;
- 16 Access module bindings;
- 2 helper bindings for the LP converter and SeaDrop mint helper.

Each is one ordinary successful transaction from the same assumed bootstrap EOA.
The12 later configuration checklist entries are **not** nonce-assigned transactions.
No seal calldata or generic administrative transaction envelope is prepared.

For example, with starting nonce0, Access creation uses0, ProtocolPolicy creation1,
its binding2 and MigrationBudget creation3. The last two helper bindings use42/43;
the next sender nonce would be44. Internally created helpers use their creator's
own nonce context, not an extra EOA transaction number.

The wrapper derives each top-level address using canonical RLP of sender/nonce,
Ethereum Keccak and the final20bytes, following the [client implementation](https://raw.githubusercontent.com/ethereum/go-ethereum/master/crypto/crypto.go).
The formula itself does not include a chain ID; this planning profile is fixed
to4663 and still requires a separate live network check.

Every nonnull `planned_addresses` input must match the derived address exactly;
null assignments are filled conditionally. The original constructor/collision/
authority checks run again after filling. Forward constructor dependencies,
inconsistent binding targets, changed graph/order and known address collisions
reject. The original source/build/ABI/runtime/full-initcode limits stay intact.
No Solidity or compiler settings change.

The new result embeds the old `constructor_plan` unmodified. That component still
labels supplied addresses as unverified assignments and reports that it did not
perform predictions; the outer wrapper records its own conditional calculation.
Neither component claims actual deployed code, successful constructors, wallet
control or verified bindings. Per-creation hashes link to the exact prepared
initcode in the embedded plan; binding rows provide reviewed targets/method names,
not ready-to-send administrative calldata.

## Bootstrap and factory boundaries

Access sets `bootstrap` to its actual constructor CREATE sender. All reviewed
pre-seal bindings require that same sender. Governance may be another selected
wallet; assuming it can substitute for bootstrap would be wrong.

The tool assumes a direct EOA path, not a Safe/contract deployer, factory,
user operation, batching, delegated account or authorization-list transaction.
It does not observe sender code or account control. Independently verify the
chosen actual path before using any predictions.

Permissionless royalty/assets factories can be used by other callers. Their
nonces are not frozen by this plan. All14 internal/helper/data-child addresses
remain unpredicted and must be obtained from authenticated actual getters;
unresolved getter-sourced constructor arguments stay unresolved. Do not infer
actual runtime pins or populate production inventories from these predictions.

## Nonce bounds, changes and recovery

[EIP-2681](https://eips.ethereum.org/EIPS/eip-2681) rejects transaction nonces
at or above2^64−1. The wrapper requires all44 planned transactions to fit and
rejects a phase that would leave bootstrap fully nonce-exhausted. It reports
`next_nonce` and `remaining_legal_transactions`. Leaving one legal transaction
does **not** establish enough room for all later configuration/sealing calls.
Their counts, execution and capacity remain separately reviewed.

The required assumption is the exact successful transaction sequence. An extra,
omitted, failed, cancelled or replaced transaction from the same sender changes
that premise. Other transactions or nonce-consuming authorization behavior must
not be silently ignored. No nonce is reserved on-chain or written to a wallet,
journal or running service.

Before any later authorized deployment, verify the actual chain, direct caller,
confirmed/pending nonce and lack of unresolved wallet work. Inspect actual CREATE
receipts, runtime immutables, bootstrap/getters and each binding as the phase
proceeds. A failed or changed phase requires explicit reconciliation with the
original records. This is **not a resume tool**: do not automatically shift saved
nonces, restart a partial deployment as fresh or relabel existing contracts.

## Outputs, status and publication

The result records public sender/nonces,25 conditional addresses,44 nonce-bearing
steps, source-bound order/graph hashes, exact constructor-plan linkage, unprepared
setup requirements and false authority/readiness/approval flags. Unknown settings
stay unknown. `manifest_sha256` is the canonical result fingerprint excluding
that field; input hashes likewise use normalized JSON, not file whitespace.
These hashes are not on-chain `reviewHash`, `custodyHash`, permission or live
runtime attestations.

| Exit | Meaning |
| --- | --- |
|0 | Sequence and top-level constructor inputs are complete offline; actual authority/code/nonces/fees/dependencies and release remain unverified. |
|2 | A blocked preview was written with missing constructor/settings inputs. Never treat predictions as missing-data defaults. |
|1 | Invalid/unavailable input or uncertain publication. Preserve existing files; inspect the output path because complete unapproved output can exist after a late failure. |

Output creation reuses the existing flushed, exclusive hard-link publication.
Unsupported filesystems fail without an overwrite fallback. Use a fresh path
after inspection; no artifact is installed or automatically approved. Actual
provider/market/VRF/OpenSea/fees, deployment, host operation and independent audit
remain release gates. Source publication does not change existing Anvil state,
wallet signer restrictions, services, websites, journals or paused monitoring.

See the [source-scoped report](../reports/deployment-sequence-20261116/REVIEW.md)
and the [single operator manual](OPERATOR_MANUAL.md#prepare-deployment-addresses-and-nonces).

The separate [unsigned pre-seal configuration planner](PRESEAL_CONFIGURATION.md) now
validates/orders the twelve configuration families using the trusted current
ABI, while leaving unknown inputs blocked and live-state/authority/readiness
unverified. It includes human-price orientation and fixed NFT-forwarded
SeaDrop setup. Constructor/sequence tools and old evidence stay unchanged;
no configuration is installed, no seal call prepared and no release approved.
