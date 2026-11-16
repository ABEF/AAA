# Complete operator-function and input-validity review

Started16November2026; documentation/publication finalized after the local
17November date boundary. Baseline `72e519797659158eb48cfe5da582fb8c88b90bfa`.
Production remains **NOT APPROVED**. This is an internal source/input audit with
focused injected-wire verification, not a new full EVM campaign or independent
security approval.

## Result

The complete catalogue contains **1,016 exact ABI entries across40 concrete
contracts**:963 functions,40 constructors and13 receive hooks. It includes
**92 governance/bootstrap/keeper/nominated actions**:72 configuration/governance,
11 bootstrap,7 keeper and2 nominated acceptances. Roles are primary documentation
classes; source-defined alternatives such as a guardian's pause-only permission
remain explicit. Not every ABI row is a management transaction.

All92 operator actions received source/input review, with333 input records
including containers,317 leaves and137 nested records. The full machine
inventory also preserves read, module, holder, public and callback boundaries.
Those counts are documentation/source coverage, **not1,016 dynamic test passes**.
Each row and its linked family assessment declare their limits.

Confirmed changes correct the unsigned execution envelope, output preservation
and input documentation. **All61 production Solidity files remain byte-identical**.
No permission, economic right, loss cap, gas default, runtime profile or custody
guarantee was changed. Existing source-bound normal/static/EVM evidence retains
its original scope; no unchanged test suite was rerun.

## Fixed findings

| ID | Finding and consequence | Correction / evidence |
| --- | --- | --- |
| OIA-01 / TOOL-01 | Manual B/C/D and Parked D simulated at the cap but did not prove their reported smaller gas limit. The returned transaction lacked gas, and later estimates could change its envelope. | Freeze initial full25%-padded gas in the returned transaction; exact-gas call at both anchors; higher later requirement rejects; lower estimate cannot reduce fee/funding proof. [Baseline](tool-baseline.json), [source and verification](TOOLS_REVIEW.md). |
| OIA-02 / TOOL-02 | Dangling management output paths were missed by `exists()`, causing input/RPC work before eventual exclusive-publication rejection. | `lexists()` refuses before input/network work. Existing exclusive publication still protects races. [Evidence](tool-verification.json). |
| OIA-03 | Three LP converter setters described boolean/BPS inputs as native mint-payment wei. | Correct actual units and bounds for enabled/route-enabled/conversion-loss controls. [Input inventory](INVENTORY.md). |
| OIA-04 | The function-reference producer discarded nested tuple explanations, leaving critical request fields without their own units/meaning. | Strict optional nested notes preserve ABI order and legacy string compatibility. All operator input leaves now carry reviewed prose. |
| OIA-05 | Expanded operator examples were deduplicated only by struct name, conflating the same struct's close/consolidate/replacement semantics. | Key by reviewed parameter/example content; preserve operation-specific anchors and add field meaning/unit column. [Catalogue](../../docs/CONTRACT_FUNCTIONS.md), [manual](../../docs/OPERATOR_MANUAL.md#operator-call-tables). |

No additional reproducible Solidity defect was established in the source paths
inspected. This does not prove absence of contract bugs. Source inspection and
synthetic test coverage cannot substitute for independent review and actual
market/provider/operator acceptance.

## What the audit checked

* [Every exact overload, caller and input](INVENTORY.md), with the full
  [machine inventory](inventory.json). All functions remain traceable rather
  than filtered by a management-related name.
* [Core contract paths](CONTRACT_REVIEW.md): governance, assets, pool admission,
  pricing, ordinary/manual LP management, both physical positions, backing,
  fixed fee allocation, conversions, buybacks and terminal holder return.
* [Additional code paths](ADDITIONAL_SOURCE_REVIEW.md): mint2/NFT/royalties,
  typed SeaDrop forwarding, randomness, metadata, canonical progress/abort,
  keeper scheduling, receipt recovery and read-only diagnostics.
* [Per-action input validity, guard interactions, recovery and economics](OPERATIONS_AND_RISKS.md),
  including evolving prices, external liquidity, transaction ordering, callbacks,
  one/two-leg transitions, holder activation/growth/claim/transfer and long-term
  operational limits.
* [Unsigned preparation tools](TOOLS_REVIEW.md), with unchanged custody/authority
  rules, exact calldata/floors/expiry, gas/funding and safe unknown errors.

Important verified distinctions: current tick moves while existing bounds stay
fixed; `portfolioFingerprint` excludes L while physical execution fingerprints
include it; same-main consolidation already reinvests and atomically modeOFF;
raw residual close leaves attributed idle and preserves desired mode; full
replacement does not itself disable future residual creation. `maxPositionUSD`
is cumulative contributed USD per NFT, not live NAV. Keeper observation writes
are authorized; fee harvesting is public under its live/lifecycle guards.

## Verification and preservation

**30 distinct targeted methods passed:**16 new and14 adapted. Tool results are
10 new+14 adapted in [tool-verification.json](tool-verification.json); six new
documentation/input cases are recorded separately. Failures during test-fixture
construction and one nonexistent requested method are retained and explained;
they are not additional passing tests. No complete unchanged suite was selected.

Checks of deterministic generated references, Todo, current source bindings,
local links, exact publication imports and preservation are recorded in
`completion.json`. These are consistency checks, not additional EVM behavior
tests. Independent read-only review of the gas/output/rehearsal patch found no
new regression; exact-gas execution remains conditional on the observed anchor.

The rehearsal helper now respects the explicit frozen transaction limit, with
historical fallback kept separate. Its compatibility checks do not rerun the
old chain rehearsal or relabel old receipts. `padded_gas` remains an observed
per-anchor requirement; `transaction_gas` is the fixed returned envelope.

Baseline hashes retain the four unrelated dirty files and all61 Solidity files.
No browser/chain/provider/market campaign, new compiler/static run, signing,
deployment, sealing, service/site rollout, existing Anvil/DB/journal change or
monitoring restart occurred. Public signing stays disabled.

## Remaining risks and decisions

1. **Compounding's extra in-range wait is service-only.** A different authorized
   keeper can ignore that extra policy where contracts still permit compounding.
   Existing on-chain budgets/custody checks remain. Enforcing a stricter rule
   on-chain would be a behavioral change, not an invisible audit correction.
2. **Spot-source independence, depth and manipulation remain real-market gates.**
   Own-swap authentication fixes self-rejection, not correlated manipulation or
   adverse pre-inclusion ordering. Jitter cannot provide MEV immunity.
3. **Emergency governance can deliberately omit financial protections.** This
   accepted authority can lose nearly all principal; no keeper/public actor gains
   it. Force is never an automatic fallback and cannot repair failed tokens/core.
4. **Per-operation caps do not bound cumulative turnover loss.** The user declined
   a cumulative cap; monitor net execution cost and turnover. No attacker-profit
   number is fabricated from price changes or synthetic depth.
5. **Token and receiver failures limit delivery.** Backed liabilities, isolated
   payout retries and owner fallback remain; universal payout for every malicious
   or unavailable asset/recipient is impossible.
6. **Actual release qualifications stay open:** independent sources/routes,
   complete fees/provider capacity, maximum-state gas/currency workloads,
   authorities/contract-wallet envelopes, SeaDrop/OpenSea/VRF and real operating
   recovery. Source review and examples close none of those external approvals.

These remain with their existing owners in the [sole Todo](../../TODO.md),
including strategy/manipulation, infrastructure, gas and release qualification.
The [operator manual](../../docs/OPERATOR_MANUAL.md#read-input-units-and-validity)
now explains exact inputs, units, fresh reads, gas and safe next actions. Historical
reports keep their original source scope.
