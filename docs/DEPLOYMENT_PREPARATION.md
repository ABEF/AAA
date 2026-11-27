# Offline deployment preparation

The [current F6 construction rehearsal](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/f6-construction-20261120/REVIEW.md)
verifies all25CREATE/19binding transactions,39instances,112binding/state assertions
and172additional defaults with real normal Access/Registry. Its separate unsealed
control fixture verifies35permission calls. Full target release arguments, real
dependencies, fees and seal/public-opening approval remain unqualified.

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

## Select the exact reviewed build

The default trusted build is **`activation-final-six-20261118`**, using the accepted
normal compiler family and fresh Factory6/allocation2 immutable Royalty bytes. Exact logical LP/royalty rights and canonicalV10 wire records remain unchanged. Private LP carry uses a MAX128 sentinel/full256-bit spill; royalty books use223 compact coefficient bits/full256-bit spill and16-bit bounded status fields. Pricing Basis/marks/list share the transaction-only execution scope and clear explicitly per operation, without an extra operator step. Chain/URI, artwork-root, reservation identity, source/control and financial guards remain. See the [current review](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/activation-final-six-20261118/REVIEW.md).
Input `profile` stays `schema17/mint2/V10/execution1/LP3`;
the distinct build ID authenticates exact bytes. Output `build_profile` and
`accepted_build.profile` record it. Unknown IDs, mixed artifacts or changed
source bytes fail; there is no fallback to an older build to bypass drift.

```powershell
python scripts/prepare-deployment.py --build-profile activation-final-six-20261118 --input path/to/reviewed-input.json --output path/to/new-plan.json
```

The closed registry also retains **`activation-gas-20261118`** (Factory5), **`royalty-rounds-20261118`**, **`q03-allocation-20261117`**, **`operator-seal-20261117`**, **`metadata2-20261116`** and
**`manual-reference-20261115`** with their original pins. Historical planning
requires the corresponding exact old source checkout; selecting an older family
in the current checkout correctly refuses source drift. Old local evidence can
still be checked offline against its authenticated historical artifacts without
relabeling it current. A build profile, content SHA or plan manifest is not an
on-chain `reviewHash`, permission, runtime attestation or release approval.

After a future contract change, review a new exact closed compiler/source family
and extend the trusted registry deliberately. Never rewrite existing family pins,
copy local addresses into production inventories or install evidence-supplied
hashes as the trust root. The current build retains48normal size gates and the
original compiler settings. AccessController full initcode is48,580bytes, leaving572bytes below49,152. Size admission does not verify constructors, bindings, target fees or deployment readiness. Earlier [17November source evidence](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/test-seal-deep-review-20261117/REVIEW.md) and construction captures retain their exact original scope; no historical gas is refreshed by selecting a new build.

## Inputs and outputs

Start with the deliberately incomplete
[input example](../config/deployment-preparation.example.json). Keep private material out of it.
The tool accepts only its explicit schema; no RPC URL, private key, signer or
broadcast option is supported. Copy the example to a new local review input;
do not fill production templates with invented values to obtain a pass.

| Input group | Required review |
| --- | --- |
| `schema`, `profile`, `chain_id` | Integer `1`, exact `schema17/mint2/V10/execution1/LP3` and decimal string `"4663"`. The canonical home-chain argument uses that chain. A profile label cannot upgrade an old runtime. |
| `planned_addresses` | Public, unique intended addresses for the 25 externally constructed instances. Each is null or a full `0x` address. These are operator assignments in this component, **not calculated CREATE addresses or observed contracts**. The separate [sequence wrapper](DEPLOYMENT_SEQUENCE.md) can fill conditional top-level predictions from a public direct-EOA sender/explicit nonce. |
| `inputs` | Governance, keeper, guardian, future mint payee, sequencer, metadata URI, fixed ZZZ, native venue dependencies, SeaDrop/code hash and buyback ceiling. The example names every key. Native venue/ZZZ and reviewed SeaDrop identities must match this fixed source profile when supplied. |
| `qualification_evidence` | Null or 64 hexadecimal SHA-256 characters, without `0x`, for each named external-review category. A supplied digest remains unverified; the tool does not open it or approve that review. |

Amounts are exact decimal strings, not JSON numbers or human units.
For example, `buyback_maximum_trade_usd:"1000000000000000000000"` encodes
1,000 USD with 18 decimals; it is an encoding example, not an adopted spending
limit. That constructor ceiling must be positive and fit uint128. Roles may
share an address where the contracts allow it; production key separation and
recovery still require review. Known prohibited mint-payee collisions are
rejected. Governance cannot equal a planned protocol instance or a fixed
venue/token/SeaDrop dependency: these implementations cannot operate governance.
The existing controller-specific diagnostic remains. Unknown EOAs/contract
wallets and getter-discovered children still require live authority/callback
review; this offline check does not authenticate wallet control.

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
execute a resumable deployment. The separate [offline sequence wrapper](DEPLOYMENT_SEQUENCE.md) now derives conditional top-level addresses for25 creations/19 bindings and supplies them to this unchanged reviewer. It reserves no nonce, observes no account and does not predict factory children. Live reconciliation and all approval boundaries remain.

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

Current normal runtime bytes/headroom: Royalty24,562/14, Oracle23,406/1,170,
Rewards23,983/593, Manager24,459/117 and Vault24,544/32. Access full initcode is48,580/49,152. Tight Royalty/Vault/Manager margins remain material; no size limit is relaxed. These figures belong to the exact accepted source; any constructor, dependency or compiler change needs a fresh reviewed build. All13 controlled cold activation/growth calls fit20M with full20%, worst16,460,899 raw/19,753,079 padded, but this is not constructor/provider/fee or release approval. The12M default and all operating safeguards remain unchanged.

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

## Isolated local construction rehearsal

The separate [local rehearsal runner](../scripts/rehearse-local-deployment.py)
creates its own disposable loopback Anvil process, port and genesis. It never
connects to a caller-supplied RPC or the existing Anvil instance. The offline
planner above stays unsigned and uses its explicitly selected trusted build;
this runner performs **local test
transactions only**, using disposable impersonation without reading wallet keys.
It never prepares or calls `seal()`.

The rehearsal constructs the exact selected trusted normal PoPL objects, binds Policy,
all 16 Access modules, the LP converter and SeaDrop helper, then discovers and
checks all 39 instances. Constructor simulations and actual receipts distinguish
expected runtime templates from the actual immutable-patched code. Internal
children are part of their parent creation transaction, not extra deployments
or extra gas to add again. The intended run has 25 creation transactions and
19 binding transactions,44 in total, all with zero native value.

### Current F6 evidence and supplementary checks

The [20November F6 record](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/f6-construction-20261120/REVIEW.md) runs the
maintained graph unchanged against current normal objects, with no compiler run.
The worst padded NFT creation is14,214,479/32M;44transactions use144,113,280 raw
gas in total. These are controlled local measurements, not target ETH/USD fees.

The report-owned campaign adds172defaults and a second small Access/Policy fixture
with DISTINCT bootstrap/governance. Its35permission probes use only `eth_call`,
with separate exact-error recording; they do not alter roles or weaken the original
success-only wire admission. Bootstrap alone configures before sealing; a keeper
mapping grant is not `keeperAuthorized` until sealing. Both nodes are stopped.

For a separately authorized repetition from the exact reviewed checkout:

```powershell
python reports/f6-construction-20261120/run_campaign.py --anvil "C:/reviewed-tools/anvil.exe" --output "C:/local-reviews/new-f6-campaign"
```

The helper requires the exact reviewed binary hash, a new exclusive output path
and its frozen case manifests. It accepts no RPC/key/seal/public-signing input.
Do not repeat it merely to refresh evidence dates. Never adopt its addresses,
constructor doubles or controlled URI: that nonempty root consumes the one-time
choice and is not production content.

Extract the [campaign archive](../reports/f6-construction-20261120/evidence.zip)
into a NEW directory. The archive's `attempt1/full-graph` is the verifier input:

```powershell
python reports/f6-construction-20261120/verify_execution.py --evidence "C:/local-reviews/extracted/attempt1/full-graph" --output "C:/local-reviews/new-f6-check.json"
```

This offline supplement authenticates all132preflight calls/260nonce reads and
44local receipt headers, preserving the historical checker's weaker original
scope. It starts no node and submits nothing. The whole campaign ZIP is not the
old standalone checker's direct-ZIP layout; use the extracted full-graph directory.
Keep existing states/journals/services and all false approval flags intact.

### Controlled dependencies and gas scope

The node uses Cancun, a 32M block gas ceiling and normal runtime/initcode limits,
without code-size exemptions. External periphery dependencies are explicit
constructor doubles; the archived exact SeaDrop runtime is seeded locally.
Those are not public deployments or approved live dependencies. Registry's
native runtime pins and market configuration are not qualified by these doubles.
No live pool, price, VRF, mint phase, activation, LP, royalty or sealing campaign
is performed by this rehearsal.

Each transaction records estimated gas, a full 25% padded local limit, exact
padded-call simulation and actual receipt gas. This is a **local construction
and binding measurement**, not a Robinhood fee quote or spending-policy change.
The Manager's constructor reads controlled getter doubles; real dependency
execution costs can differ. Public deployment gas, L2 posting fees and approved
fee ceilings remain separate. Legacy12M defaults, the selected32M/full20% contribution candidate and24M/full25% maintenance remain unchanged; local construction is a distinct25% measurement.

### Running, stopping and interpreting a rehearsal

Run only from the reviewed checkout with exact accepted artifacts/dependencies
and the reviewed local Anvil binary. Unknown build/source refusal happens before
creating a new output directory or starting a node. Use a new directory for each run;
never select an old chain state, website dist, journal or existing rehearsal
directory. The runner must verify its child process owns the loopback listener
before mutation and retain its fresh chain/genesis identity. An occupied or
unverified listener fails closed; it is never reset or taken over.

The current launcher supports Windows and requires its exact socket/PID check;
it does not silently skip that check on another operating system. Example from
the repository root, with your reviewed binary and a new evidence directory:

```powershell
python scripts/rehearse-local-deployment.py --build-profile activation-final-six-20261118 --anvil "C:/reviewed-tools/anvil.exe" --output "C:/local-reviews/new-construction-run"
```

This example selects the new current build for a separately authorized fresh
rehearsal; it is not a command that ran in the historical captures below.
The current controlled F6 full graph is verified in the linked20November record; older construction captures retain their original runtime scope, with no target-release approval implied.
There is no RPC, key, existing-state, public-deployment or sealing option. The
controlled role addresses, metadata URI and buyback ceiling are test inputs,
not production choices. Output includes the process/genesis identity, dependencies,
source pins, 44 transaction records, 25 CREATE traces, 39 instance proofs, binding
reads, a plan reconciled to actual local addresses and shutdown evidence.

The [first source-bound rehearsal](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/local-deployment-rehearsal-20261115/REVIEW.md)
completed all 44 transactions. The largest was NFT construction: 11,337,831 gas
used, with a 14,172,289 padded limit. Total receipt gas was 141,382,621 across many
blocks, not one transaction or block. These are controlled local measurements,
not reusable production transaction limits or ETH cost estimates. That run used
the historical manual-reference family. Five later metadata objects changed;
the [historical selective metadata2 rehearsal](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/metadata2-rehearsal-20261116/REVIEW.md) verified those five changed constructors and required children locally.
AccessController changed again in the17November family; the earlier receipts
do not measure that new constructor or qualify its deployment gas.
Final public release construction/dependencies and actual target fees remain
unqualified.
Do not replay44transactions merely to refresh a report date; qualify changed
constructors and real release inputs through an authorized targeted campaign.

Independent review found a request-recording alias in that original run. Its
transactions, receipts, CREATE traces and getter results reconcile, but earlier
preflight gas/nonce/gasPrice descriptions cannot be treated as exact wire input.
The current recorder fixes this with immutable request/response snapshots; a
new focused regression verifies the fix without repeating the 44 transactions.
Original captures retain their source and limitation, not a corrected label.

To inspect the published capture without starting a node:

```powershell
python scripts/check-local-deployment-evidence.py --evidence reports/local-deployment-rehearsal-20261115/evidence.zip --output path/to/new-offline-result.json
```

Use a new output file in an existing directory. The checker authenticates the
trusted build pins before reading build files, then reconciles receipts,
constructors, runtimes, exact submitted transaction fields and all112distinct
required binding/state observations. It independently derives constructor roles,
arguments/parents and getter expectations from the closed graph, permits only
the recorded read methods and intended sends/impersonation, and verifies exact
inert carrier payloads. Deleting or duplicating observations cannot satisfy
coverage. Captures with an explicit build ID must match its trusted files and
plan/result identity; missing IDs are accepted only for exact historical pins.
It reports the original
capture limitation explicitly and never supplies deployment/sealing approval.

The final evidence must show `Access.isSealed()==false`, the original bootstrap
still present, canonical state0, all module/helper links correct and no NFT/LP
positions created. Converter and mint-helper bindings do not enable them or
configure markets. Success never means production approved or ready to seal.

On failure, preserve the output and receipts and start a new owned chain/output
after correcting the specific cause. Do not resend into an unknown process or
try to resume a partial rehearsal. Shutdown terminates only the child this run
created; it never kills Anvil by name or administers the existing node. The
[source-scoped report](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/local-deployment-rehearsal-20261115/REVIEW.md)
records actual receipts, gas, verification and remaining qualifications.
## Selective metadata2 local evidence

The [historical metadata2 selective rehearsal](https://github.com/ABEF/AAA/blob/fdd599c7698d0e1c0709a4a8b50130e5557ba508/reports/metadata2-rehearsal-20261116/REVIEW.md)
executed only its five changed top-level normal constructors: AccessController,
NFTMetadata, Migration, NFT and NFTCanonical. Seven necessary constructor-created
children yield 12 real instances; three Access module bindings and 63 expected
getter/state observations are reconciled. Full initcode/runtime limits remain
49,152/24,576bytes. Worst full 25%padded constructor14,208,779 fits 32M; eight actual
receipts use41,327,001 gas total. These are local costs, not Nitro complete fees.

Nineteen valid cold `tokenURI` snapshots plus a nonexistent-token rejection use
actual normal code, ten distinct controlled read counterparts and temporary
storage overlays. Full-width IDs and a 41-byte test URI yield worst 826,831 gas,
992,198 with 20% padding. All estimate/padded responses match the exact reference;
the cold trace records SLOAD 2100. No preset 470,966 warmed observation, fixture
estimate or successful-but-degraded response qualifies a production read budget.
Actual Oracle/source cost, final URI, provider/timeouts and OpenSea need their
own read-only qualification with expected semantic fields.

The source-frozen one-campaign scripts and captures are archival report evidence,
not a new public deployment CLI. The older full-graph checker still requires its
original 39-instance/112-observation capture; never weaken it to accept this
different 12-instance/63-observation scope. Both families retain exact pins.
The new node is stopped and the partial graph stays unsealed/bootstrap-owned/
unminted. Local addresses/fixture runtime pins must never populate release
inventories or existing journals. No service/watcher/server restart is needed
for the report or documentation update; no running profile is adopted.

## Remaining deployment requirements

The native Registry's chain, fixed ZZZ and venue address constants must match
the intended release. Matching public address text does not verify live code
hashes, proxy controls, venue wiring, market depth or usable execution. Optional
price-reader deployment and admission remain separate, qualified decisions;
they are not silently added to the principal deployment graph.

Access sealing checks policy/module presence, distinct modules, canonical
parents, contribution/exit token identity, mint recipient and home-chain VRF
configuration, plus a nonempty artwork base before permanently sealing it.
That root check is structural, not a remote content/hosting check. Sealing does
**not** qualify SeaDrop onboarding, subscription funding, independent sources,
routes, artwork availability, deployment gas or service operation.
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

The separate [unsigned pre-seal configuration planner](PRESEAL_CONFIGURATION.md) now
validates/orders the twelve configuration families using the trusted current
ABI, while leaving unknown inputs blocked and live-state/authority/readiness
unverified. It includes human-price orientation and fixed NFT-forwarded
SeaDrop setup. Constructor/sequence tools and old evidence stay unchanged;
no configuration is installed, no seal call prepared and no release approved.
