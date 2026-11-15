# Offline deployment preparation

Use [prepare-deployment.py](../scripts/prepare-deployment.py) to review the **fresh schema17 / mint2 /
canonicalV10 / execution-price1 / LP-routing3** construction graph. It reads the
accepted normal compiler objects and local source files; it does not compile,
contact an RPC, read a key, sign, deploy, configure a contract or seal anything.
Historical deployments, browser signing and running configurations are unchanged.
This plan covers a fresh initial home-chain release, not successor funding,
canonical import, a historical profile upgrade or a deployment resume.

This is a construction and size review, not production approval. The separate
[release bundle](FROZEN_REVIEW_BUNDLE.md) packages audit inputs; the separate
[production preflight](PRODUCTION_PREFLIGHT.md) observes a real deployed graph.
Neither is replaced by this tool.
Use a complete checkout with the exact dependency sources installed, as described
in [Development](DEVELOPMENT.md). Missing or changed local source/artifact bytes
are refused; the planner does not install packages or fetch replacement evidence.

## Inputs and outputs

Start with the deliberately incomplete
[input example](../config/deployment-preparation.example.json). Keep private material out of it.
The tool accepts only its explicit schema; no RPC URL, private key, signer or
broadcast option is supported. Copy the example to a new local review input;
do not fill production templates with invented values to obtain a pass.

| Input group | Required review |
| --- | --- |
| `schema`, `profile`, `chain_id` | Integer `1`, exact `schema17/mint2/V10/execution1/LP3` and decimal string `"4663"`. The canonical home-chain argument uses that chain. A profile label cannot upgrade an old runtime. |
| `planned_addresses` | Public, unique intended addresses for the 25 externally constructed instances. Each is null or a full `0x` address. These are operator assignments, **not calculated CREATE addresses or observed contracts**. |
| `inputs` | Governance, keeper, guardian, future mint payee, sequencer, metadata URI, fixed ZZZ, native venue dependencies, SeaDrop/code hash and buyback ceiling. The example names every key. Native venue/ZZZ and reviewed SeaDrop identities must match this fixed source profile when supplied. |
| `qualification_evidence` | Null or 64 hexadecimal SHA-256 characters, without `0x`, for each named external-review category. A supplied digest remains unverified; the tool does not open it or approve that review. |

Amounts are exact decimal strings, not JSON numbers or human units.
For example, `buyback_maximum_trade_usd:"1000000000000000000000"` encodes
1,000 USD with 18 decimals; it is an encoding example, not an adopted spending
limit. That constructor ceiling must be positive and fit uint128. Roles may
share an address where the contracts allow it; production key separation and
recovery still require review. Known prohibited mint-payee collisions are
rejected; actual getter-discovered payees and callback behavior need live checks.

`sequencer:null` means unresolved; an explicit zero address is constructor-valid
but does not qualify sequencer/liveness policy. The fresh LP converter uses its
native-v4 zero-wrapper constructor; this does not restrict separate royalty
currencies or silently admit a WETH principal route.

From the repository root, after making a reviewed input copy:

```powershell
python scripts/prepare-deployment.py --input path/to/reviewed-input.json --output path/to/new-deployment-plan.json
```

The output directory must already exist and the output file must be new.
Exit 0 means a complete offline input/payload plan, **not permission to submit**;
exit 2 writes an incomplete blocked preview; exit 1 reports invalid/unavailable
preparation or publication uncertainty. Inspect both the exit status and the
result's missing inputs and per-constructor unresolved bindings.

`input_sha256` fingerprints normalized canonical input JSON, not the original
file's whitespace. `manifest_sha256` fingerprints the canonical result with that
field excluded. Neither is an on-chain `reviewHash`, `custodyHash` or address
attestation; do not substitute these tool fingerprints into contract calls.

Nulls are unresolved inputs, not zero addresses or default authorities. A partial
preview remains blocked where it cannot encode exact arguments. A full static
payload still depends on proving that its assigned addresses are the actual
addresses created in the reviewed sequence. The tool deliberately does not
select or reserve deployment nonces, predict addresses, reconcile receipts or
execute a resumable deployment.

Outputs distinguish exact encoded constructor arguments/full initcode from
unresolved symbolic getter references. Fixed-width unresolved addresses can
still have an exact argument **length**; that does not make their **bytes**
known. Dynamic URI length is measured in UTF-8 bytes with ABI padding. An empty
URI is constructor-valid but does not establish artwork availability or mint
readiness. Current renderer syntax permits empty, `ipfs://` or `ar://` URIs;
content, persistence and availability need their separate review.

The result always retains `ready_for_submission:false` and
`production_approved:false`. Do not paste a preview into a wallet or treat a
complete payload as a simulated transaction. Constructor external calls,
deployed runtime immutables, role authority, target gas and live dependencies
are not executed or verified offline.

## What is checked

- The accepted compressed compiler input/output and size record are pinned to
  their original bytes and source closure. Local source or build drift fails;
  historical artifacts are not relabelled. No new compiler or static-analysis
  run is needed for this Python-only tool.
- Constructor signatures and ordered arguments come from the accepted ABI.
  Constructor arguments follow creation code without a function selector.
  Inputs are typed; missing values cannot silently become valid configuration.
- Runtime size remains at most 24,576 bytes. **Full initcode, including ABI
  constructor arguments, remains at most 49,152 bytes**, including internal
  creations. No compiler/EVM limit or financial safeguard is raised.
  These are the [EIP-170](https://eips.ethereum.org/EIPS/eip-170) and
  [EIP-3860](https://eips.ethereum.org/EIPS/eip-3860) limits; encoding follows
  [Solidity0.8.26 ABI rules](https://docs.soliditylang.org/en/v0.8.26/abi-spec.html).
- The two RoyaltyFactory code-data carriers use their actual returned
  `0x5f5ffd || payload slice` runtime and exact dynamic bytes constructor data.
  The generic compiled `ZZZRoyaltyCodeData` runtime is not their deployed code.
- Source-defined construction and binding order is explicit. Internally created
  helpers are not offered as independent deployment transactions. All runtime
  template hashes remain templates, never observed immutable-specific pins.

The reused normal build has only **3 runtime bytes for Oracle, 32 for Vault and
101 for Manager** remaining. Oracle creation code is 49,009 bytes; with its
64 argument bytes it totals 49,073, leaving
**79 initcode bytes**. These margins belong to the accepted source; changing a
constructor, dependency or compiler profile requires a new reviewed build.

## Binding and setup order

The output is an ordered review checklist, not an executable transaction queue.
Its graph contains 25 explicit constructions, 12 internally created contracts and
2 inert data carriers: 17 core contracts, 20 callable helpers and 2 inert children.

| Stage | Ordering constraint and verification |
| --- | --- |
| Controller | Review three nonzero role addresses. Its constructor creates RoyaltyFactory, both inert carriers and ActivationAssetsFactory. Record actual constructor receipts/getters. `Access.bootstrap()` is the actual CREATE sender, not automatically any of those three roles. |
| Policy | Construct ProtocolPolicy with the controller and valid mint recipient; bind it once through Access before policy consumers. Before sealing, configuration authority is bootstrap, not automatically the future governance wallet. |
| Standalone companions | Construct the fixed-controller Budget, renderer, Balancer, PortfolioPolicy and Confirmation before their respective Vault, NFT, Manager and Strategy consumers. Check reciprocal parent/core/venue getters. |
| Core and companions | Bind Vault in Access **before constructing VaultCanonical**, whose constructor reads that binding. NFTCanonical and FeesCanonical must refer to the same bound NFT/Fees modules. Bind each of the16 supported module IDs exactly once; never substitute a helper for a module. |
| Constructor children | Discover NFT royalty ledger/ClaimRouter, Registry assets/Entry, Manager executor, Balancer Math, Oracle Pricing, RewardsCanonical, Migration's CustodyValidation and Converter executor through their actual getters and receipts. Do not deploy duplicates. |
| Fixed ZZZ | Configure reviewed dual USD policies, then ActivationAssets' fixed ZZZ, Rewards' ZZZ asset and Migration's ZZZ identity with the same immutable Buyback token. Admit execution sources only after the fixed ZZZ is established. Native ETH remains the other principal asset. |
| Mint2 and rewards | Construct/bind the exact SeaDrop mint helper before sealing or minting. Helper configuration alone does not synchronize upstream SeaDrop: NFT-keyed drop/root/payout/fee-recipient/payer settings must match, unused signed/token-gated paths must be empty, and NFT's official mint end must match the final public stage. Bind the LP reward converter to Rewards before sealing; original-currency royalties do not use it. Recheck all constructor-bound parents and runtime identities. |
| Operating configuration | Separately review actual pools, bounded swap routes, prices, thresholds, fees, VRF/subscription, mint phases/payers, confirmation settings, host and gas budgets. Constructor success does not supply these settings. |
| Pre-seal review | Reconcile actual creation addresses/code/getters/permissions and all live prerequisites using the production inventory and release approval record. **This tool generates no seal call and does not authorize sealing.** |

RoyaltyFactory and ActivationAssetsFactory expose permissionless `create()`.
Unrelated callers can advance their creation nonces between transactions.
Accordingly, the ledger and assets addresses are getter-discovered references,
not promises based on fresh factory nonces. The two code-data children are
created atomically inside the factory constructor; that distinction matters.

## Remaining deployment requirements

The native Registry's chain, fixed ZZZ and venue address constants must match
the intended release. Matching public address text does not verify live code
hashes, proxy controls, venue wiring, market depth or usable execution. Optional
price-reader deployment and admission remain separate, qualified decisions;
they are not silently added to the principal deployment graph.

Access sealing checks policy/module presence, distinct modules, canonical
parents, contribution/exit token identity, mint recipient and home-chain VRF
configuration. It does **not** qualify SeaDrop onboarding, subscription funding,
independent sources, routes, metadata, deployment gas or service operation.
Use the [operator manual](OPERATOR_MANUAL.md#offline-deployment-preparation),
[address inventory](DEPLOYMENT_ADDRESSES.md),
[OpenSea procedure](OPENSEA_MINT.md) and
[release approval record](RELEASE_CHECKLIST.md) for those separate requirements.

On a rejected input, fix the specific input and create a new output; do not
overwrite historical reviews. If an output already exists, preserve it. If the
process reports uncertain publication, inspect that exact output before retrying
under a new name. An offline rerun changes no chain state and recovers no
deployment; any later deployment/resume requires separately authorized tooling,
actual receipts and fresh address/nonce/binding reconciliation.
