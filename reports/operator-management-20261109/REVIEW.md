# Unsigned operator custody and holder-return preparation

The new `scripts/prepare-operator-management.py` prepares seven explicitly
selected Migration operations. It fetches exact custody/ledger inputs, builds a
source-bound review hash, checks current governance and simulates identical
calldata/gas at a confirmed snapshot and a later canonical tip. It never signs,
sends, reads or edits an operating journal, reserves a nonce, chooses raw floors,
advances a queue or changes a guarded operation into an emergency fallback.

Production is **not approved**. No Solidity, runtime, ABI, financial right,
website, signer, service, Anvil or heartbeat changes are made by this work.

## Scope delivered

| Action selection | Contract function | Result and boundary |
| --- | --- | --- |
| `park` | `Migration.park(r)` | Paused governance closes both physical legs into attributed Vault idle. Preparation-time draining is supported only while canonically operating. |
| `resume` | `Migration.resume(id,pool,minimum,deadline)` | Unpaused guarded redeployment of parked principal into the same or another reviewed native ETH/fixed-ZZZ pool. No forced fallback. |
| `close_residual` | `Migration.closeResidual(r)` | Paused governance closes only the registered residual. Main and desired mode stay unchanged; returned principal needs separate reinvestment. |
| `collective_exit_begin` | `Migration.beginCollectiveExit(reviewHash)` | Explicit irreversible confirmation required. Starts retirement; no principal is paid yet. |
| `close_bucket` | `Migration.closeBucket(bucket,minETH,minZZZ,deadline)` | Closes this snapshotted Active/Parked bucket and classifies actual principal. No swap or reward claim. |
| `allocate_principal` | `Migration.allocatePrincipal(maximum)` | Allocates the next1–32 mint ordinals. It pays no holder and works paused or unpaused. |
| `distribute_principal` | `Migration.distributePrincipal(ids)` | Attempts the exact1–32 selected IDs, paying current owners. It works paused or unpaused; individual failures remain backed. |

The existing Active-state B/C/D preparer keeps its selection format and behavior.
Its shared policy validation was extracted without changing defaults. New actions
use a separate strict selection format; no old deployment or journal is relabelled.
The adapter remains restricted to direct empty-code governance EOAs. Contract
wallets and delegated accounts require a separately constructed outer envelope;
this tool does not change their on-chain authority.

## Safety and operational improvements

- Exact runtime/module/helper bindings, current governance, canonical lifecycle,
  preparation state, fixed ZZZ and operation-specific phases are authenticated.
  Raw park/residual/terminal paths do not require healthy USD feeds, automatic
  swap venues, token decimals or ordinary operations-enabled flags.
- Parking fields, including both-leg execution fingerprint, shares, nonce and
  epoch, are fetched from the captured chain state. The operator still supplies
  explicit raw minima, added/new liquidity floors and original expiry. Explicit
  zero raw floors remain zero; there is no invented safe floor.
- Healthy spot/amount/price-round movement is re-evaluated through the second
  exact simulation. Changed physical custody, shares, controls, payout owners or
  allocation progress require a fresh review. Both LP legs remain accounted.
- Every transaction includes its reviewed gas limit. Ordinary calls freeze the
  first25%-padded estimate. Distribution preserves the explicitly configured,
  block-bounded gas budget: its cheap successful early break must not determine
  the batch budget. Gas price, full budget cost and governance funding are checked
  again without automatic increases.
- Distribution's return value is a count, not a list or a paid prefix. Partial
  success is labelled; zero successful payouts cannot produce a useful executable
  review. All selected IDs and their classifications remain visible. No automatic
  retry, recipient override or abandoned-rights reallocation is added.
- Local blockers have stable codes and a failure stage. Opaque transport/simulation
  errors remain unavailable rather than a guessed financial diagnosis. Errors
  never echo raw provider text or credentialed endpoints.
- Output is published exclusively and atomically using the existing durable
  writer. Existing files are preserved before RPC work. A post-publication
  durability failure explicitly says an artifact may exist; inspect it rather
  than overwriting it or assuming any transaction was submitted.

## Important limits

Only park, resume, residual close and bucket close carry the chosen expiry as an
on-chain deadline. The other actions have an off-chain review expiry only.
`allocatePrincipal` uses the cursor at inclusion, and distribution pays the
current owner at inclusion. Later transactions can change either after the final
review. The unchanged ABI cannot bind those fields; the artifact states this and
requires operator revalidation and actual receipt/ledger reconciliation.

This extension does not prepare the existing Parked-state forced emergency path.
The manual Explorer procedure remains available; it is never selected implicitly.
Normal resume keeps its financial guards. Failed core/token contracts cannot be
repaired by a stronger off-chain review or financial bypass.

Read consistency follows [EIP-1898](https://eips.ethereum.org/EIPS/eip-1898).
Canonical-hash `eth_estimateGas` support is a provider qualification requirement,
not guaranteed by that EIP's method list. Gas estimates alone do not prove the
gas-sensitive batch outcome; the exact limit is also simulated. See the
[JSON-RPC documentation](https://ethereum.org/developers/docs/apis/json-rpc/)
and [Solidity ABI specification](https://docs.soliditylang.org/en/v0.8.26/abi-spec.html).

## Verification and operation

[Verification](VERIFICATION.md) records70 distinct focused methods, comprising
41 new methods and29 existing B/C/D checks, plus a later overlapping one-method
CLI diagnostic correction and independent offline encodings for all seven calls.
These use injected RPC and the actual current validators/catalogues. They are
not live EVM/operator/provider or target-gas qualification. Unchanged Solidity
normal/static suites were not rerun.

The maintained [operator guide](../../docs/OPERATOR_MANUAL.md) and
[input procedure](../../docs/MANUAL_LP_PREPARATION.md) explain exact files,
parameters, pause/restart steps, raw closure versus reinvestment, and post-receipt
reconciliation. The sole [Todo](../../TODO.md) retains actual deployment/provider,
fees/gas, wallet envelope, hosted operation and independent audit gates.
