# Explicit Parked emergency recovery preparation

Reviewed15November2026 against baseline `fce0ac27952997d8501098a96743603d4ff2a236`.
This is a source-only extension to the unsigned operator tool. Production is not
approved; no contract, service, site, chain or journal is deployed or changed.

The missing capability was preparation, not a missing contract recovery function.
`Migration.emergencyRebalance(request)` already supports paused Parked buckets.
The old schema1 adapter deliberately accepts only Active B/C/D. Extending that
old request implicitly would change what previously reviewed inputs can mean.

## Implemented

- Explicit selection schema2 requires `action:"D"` and
  `expected_position_status:"parked"`. Old schema1 remains Active-only; full
  rendered B/C/D artifacts match the baseline byte for byte, including request,
  review commitment and calldata. No contract/API profile is relabelled.
- Authenticate the existing current-pool native ETH/fixed-ZZZ key, admitted
  configuration, pool reservation, registered bucket inventory and positive NFT
  shares. Parked requires zero main ID and no residual association, proved by the
  exact executor-domain and execution fingerprints. Missing reads never become
  invented zero; no Active-only position0 ownership/geometry calls are attempted.
- Recover only attributed idle plus designated compound. Explicit swap input
  cannot exceed that exact Parked inventory in either direction; there is no
  future LP harvest to forecast. Reward, buyback, royalty and other-bucket backing
  stay separate. Existing Active D keeps its future-harvest lower-bound semantics.
- Expose every retained/bypassed safeguard category. Parked cannot retain bit1
  ordinary trigger/cooldown or bit16 sampled confirmation: both require an Active
  main. They reject with a specific sanitized reason, never silently clear.
  Bits2/4/8 are explicit caller choices; bit4 still requires USD data without2.
- Preserve governance-only on-chain authority and the existing direct empty-code
  governance EOA preparation restriction; sealed/paused/operating/pre-exit
  lifecycle, admitted structural dependencies, exact custody/balances/callbacks,
  explicit caller floors and original expiry remain. Mask0 is not permission to
  use unknown assets/venues or redirect funds; it can accept severe economic loss
  or inactive placement. No mask or floor is chosen by the tool.
- Bind selection/source state and exact custody/control snapshot into the review.
  Simulate identical calldata at confirmed state and a later canonical tip, with
  unchanged fee/gas/funding limits and25% padding. Changed funds, shares,
  permissions, runtime, policy, nonce/epoch, lifecycle or canonicality abort.
  Publication remains exclusive/atomic and unsigned; readiness/production flags
  remain false. No nonce reservation, signing, resend, auto-route or force fallback.

## Operator effect

Use the [complete schema2 inputs and command](../../docs/MANUAL_LP_PREPARATION.md#parked-emergency-recovery-explicit-schema2).
Recovery redeploys into **one main in the current pool**, preserves shares and
earned rights, and remains paused. Separately inspect actual receipt/post-state
and reconcile pending work before governance unpause. Guarded unpaused `resume`
remains the alternative for normal re-entry or another admitted same-pair pool;
no preparer switches to emergency automatically on failure.

The [operator manual](../../docs/OPERATOR_MANUAL.md),
[parking guide](../../docs/CUSTODY_PARKING.md), feature reference, sole Todo,
roadmap, release/findings records and repository context now reflect this source
milestone. Existing contract call tables remain valid: no ABI or permission changed.

## Verification and remaining work

**19 unique new focused methods pass**:17 first, then only2 additional methods.
All earlier17 test/helper bodies are unchanged in the final file. Tests use the
real Projection/Reader with injected responses, not EVM execution. All32 masks,
both exact input boundaries, execution1/LP3, late changes and failed publication
are covered. Two internal read-only peer reviews found no blocking source issue.
See [verification](VERIFICATION.md), including baseline failures and fixture
corrections; overlapping stages are not summed into extra coverage.

All61 production Solidity files,100 normal compiler inputs and current strict
source pins match existing evidence. No unchanged contract/compiler/static,
old Python or browser suite was rerun. Four unrelated dirty files remain exact.
The unchanged website is clean at `206892a`; signer stays Anvil-only and both
public configurations remain null. No heartbeat was resumed.

Actual matching deployment/configuration, provider honesty/canonical support,
complete fees, full governance C/D gas, contract-wallet envelopes and operating
rehearsal remain unqualified. Source completion does not close the broader
[operation-review task](../../TODO.md#task-operation-review), independent audit
or release approval. Broken tokens/core/chain cannot be repaired by bypasses.
