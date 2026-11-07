# Fixed royalty deployment code storage

Fresh source candidate; **production NOT APPROVED**. This changes how the fixed
royalty deployment bytes are stored and read. It changes no NFT ownership,
royalty allocation, claim, liquidity or governance rights. No existing contract,
service, site or journal is upgraded by source publication.

## Purpose and fixed format

The earlier factory stored the complete royalty creation payload in ordinary
storage slots. The new factory keeps it in **two immutable data-only children**,
then copies and verifies the same payload before creating the royalty receiver.
This removes repeated storage writes/reads from deployment. It does not lower
royalty activation or holder-claim gas, and it does not solve aggregate currency
synchronization limits.

The format is `CODE_STORAGE_VERSION()==2`:

| Item | Exact rule |
| --- | --- |
| Child runtime prefix | `0x5f5ffd`: `PUSH0`, `PUSH0`, `REVERT`, requiring the selected Cancun-compatible environment. |
| Payload offset |3 bytes; exclude the prefix when reconstructing creation code. |
| Maximum data per child |24,573 bytes; maximum runtime24,576 bytes. |
| Child count |Exactly two, with distinct nonzero addresses. A zero-length second payload still has the three-byte revert runtime; it is not absent code. |
| Payload order |Part0 followed by part1. Never swap, omit, repeat or truncate a part. |
| Current25,522-byte payload shape |Part0 data24,573/runtime24,576; part1 data949/runtime952. Recheck the exact final compiler artifacts rather than adopting these sizes for another source revision. |
| Constructor inputs to the receiver |The verified creation payload plus only the typed caller NFT address, as before. |

Every ordinary call to a data child, including a call carrying native ETH,
reverts without executing the embedded data. A child has no ABI functions,
controller key, configuration, storage writer, approval, payout or self-destruct
path. Forced ETH and ERC20 transfers are still possible on the EVM. Such
unsolicited balances are outside protocol accounting and are not recoverable
through these data children. Never use their addresses as royalty recipients,
wallets, treasuries or custody destinations.

## Hashes and bindings

| Factory read | Meaning |
| --- | --- |
| `controller()` |The fixed controller that created this factory. |
| `CODE_STORAGE_VERSION()` |Fixed format identifier2, not the royalty accounting version. |
| `creationCodeLength()` |Length of the complete receiver creation payload, excluding both prefixes and the NFT constructor argument. |
| `royaltyCodeHash()` |Keccak256 of that complete creation payload. It is not the deployed receiver runtime hash or an operator `reviewHash`. |
| `part0()` / `part1()` |The fixed two data-child addresses. |
| `part0CodeHash()` / `part1CodeHash()` |Keccak256 of each child's complete runtime, INCLUDING its three-byte prefix. |
| `create()` |Create the same typed receiver and bind the fixed controller atomically. No code, recipient, salt or value argument is accepted. |

The factory derives its payload from the reviewed compiled
`ZZZRoyaltyRewards.creationCode`, rather than caller input. Construction validates
the data children. Each `create()` checks their exact lengths and runtime hashes,
copies only the data bytes in order, then checks the complete creation hash before
CREATE. A mismatch reverts; there is no mutable pointer, code setter, generic
executor, delegatecall or fallback code source.

The receiver still binds its NFT and controller. The NFT constructor verifies
that relationship and stores one immutable receiver for the collection. Ordinary
NFT mints and holder claims do not call this deployment factory or read its data
children. Public creation of an unused sibling cannot replace the canonical NFT's
fixed receiver or obtain its rights.

## Fresh inventory boundary

Use the explicit **schema16** deployment inventory. Schema15 is archived exactly
for historical inspection. Code-storage FORMAT2 is unchanged, but fresh payload3
has separate source-owned bytes/pins; never substitute historical payload2. Keep **19 logical callable
helpers plus two inert code-data children**; do not describe the extra addresses
as new custody authorities or conceal them in the deployed graph. There are17
module records,19 helper records and2 code-data records, with external dependency
records separate. The data children have no getter ABI; authenticate them with
bounded `eth_getCode`, not invented `access()` or `controller()` calls.

Royalty settlement4/recovery2 and reporting5 remain unchanged. Fresh accounting7/
LP-allocation1/canonicalV9 and its fixed Rewards canonical companion are separate
identities. Schema15 and older runtime/config
profiles remain historical; do not add mandatory data-child fields by silently
relabeling a deployed instance or saved configuration.

Expected bytes, lengths and hashes must come independently from the exact
reviewed compiler creation payload. A factory getter or an RPC reply is an
observation, not permission to adopt a new pin. At one canonical pinned block,
verify the factory/controller binding and runtime, both part pointers, both full
runtime hashes and exact lengths, the revert prefix, ordered reconstruction,
whole payload length/hash and address non-aliasing. Missing, swapped, duplicate,
extra or malformed parts fail closed. Keep unconfigured values unavailable;
local example addresses are not production addresses.

Canonical `deploymentCommitment()` binds module/domain runtimes, the Access
runtime containing its immutable factory address and ProtocolPolicy. It does
not explicitly enumerate factory/data-child runtime hashes. The separate source-
bound schema16 constructor/release verification must inspect that full fixed
graph. Code-storage FORMAT2 alone does not choose the canonical wire version; fresh7
independently usesV9. No coordinator bypass is introduced. Reviewed different-code replacements retain their existing
governance trust boundary.

## Exact compiler artifact family

The current payload3 artifact `config/factory-code-storage-v3.json` and
`zzz_ops.factory_code_v3` bind the reviewed87-source compiler input and the
whole25,522-byte creation hash
`0x0b5b619ca10d338f29e7a76fd3f9069b2e034864112bbd3101bbc20a279c50aa`.
Its part0 is unchanged from payload2; part1 metadata differs. Artifact payload3
is not CODE_STORAGE_VERSION3: the runtime format remains2.

The preserved historical schema14/15 payload2 artifact pins its own compiler output: royalty
creation length25,522 and hash
`0x4a520b4af1c8ded6fe2539ec7f3ec4f6d9a1c7fbdd710a53ccffd3412bfce831`.
An independent Forge build can normalize source line endings or add unused
auto-detected remappings to its metadata,
changing Solidity metadata and creation bytes despite equivalent compiler
settings and behavior. Those artifacts are not interchangeable with these pins.
Use the exact reviewed compiler artifact family for any later deployment. A
rebuild with different bytes requires independent full review and corresponding
source-artifact/runtime/profile re-pinning; never copy new observed hashes into
the current inventory merely to obtain consistency. No deployment is authorized.

## Operator procedure

1. Build the exact reviewed source with the supported compiler/settings. Retain
   its full creation bytes/hash, part bytes/hashes/lengths and normal size record.
2. Use the typed controller/NFT deployment workflow. The factory constructs both
   data children itself; no separate manual data deployment, funding or binding
   call is needed. This guide does not authorize deployment or sealing.
3. Read the returned factory/part addresses and authenticate the full schema16
   graph at one confirmed block against independently reviewed pins. Inspect the
   typed constructor's exact receiver NFT/controller binding too.
4. Verify actual target initcode/runtime limits, constructor arguments, transaction
   and block gas, provider behavior and complete wallet deployment costs before
   approval. A lower local constructor measurement is not target qualification.
5. If any byte, length, hash, pointer or parent binding is wrong, stop. There is
   no repair setter or unsafe fallback. A fresh deployment and new review are
   required; do not change expected pins merely to make an observation pass.

After deployment these addresses/bytes are fixed. An unchanged data child needs
no keeper task, allowance, periodic sync, top-up, service restart or holder
transaction. A future royalty implementation requires the separately reviewed
replacement/deployment procedure; this factory cannot be repointed after sealing.

See the [deployment Todo](../TODO.md#task-deployment-initcode),
[current profile](POSITION_V7.md), [operator manual](OPERATOR_MANUAL.md), and
[release approval record](RELEASE_CHECKLIST.md). Actual providers, authorities,
OpenSea integration, operating workloads and independent audit remain separate.
