# Robinhood fee mechanics and the future keeper profile

The read-only campaign found a real keeper accounting mismatch and the source
now has an explicit future-only correction. Robinhood was not charging a sampled
transaction's positive priority fee; the generic Ethereum model counted it.
New keeper `submission_fee_profile:2` fixes the signed priority to zero, so the
existing canonical-base calculation works whether the chain collects tips or
not. Existing configurations, fee defaults and saved reviews keep their original
semantics. No service, wallet, signer instance or journal was changed.

**Complete PoPL target-chain fees are still unqualified.** The ten PoPL payload
reads below measure their posting component, without executing the undeployed
PoPL graph. The real full-operation 20M/24M evidence remains the separately
scoped [controlled local campaign](../../gas-profiles-20261113/evm/REVIEW.md).

## Dated chain evidence

The shared [raw RPC transcript](../network/RPC.json) and
[network interpretation](../network/RESULTS.json) retain all requests/errors.
Fee reads use Robinhood chain 4663 at block **113263446**, hash
`0x2c662ff9ff253f4ea68a1dbd6affdc9547b4c0c8a3bb33f44832c63d3f79bfd5`,
**13 November 2026, 09:50:48 UTC**, with the canonical header rechecked.

| Observation | Result | Scope |
| --- | ---: | --- |
| Inclusion header base fee | 20,100,000 wei/gas | Exact captured block |
| NodeInterface component base fee | 20,110,000 wei/gas | Pinned state estimate |
| `eth_gasPrice` | 20,106,000 wei/gas | Contemporary, not hash pinned |
| Suggested priority fee | 0 | Contemporary suggestion |
| `getCollectTips()` | false | Exact canonical-hash read |
| `arbOSVersion()` raw result | 116 | Getter includes a 55 offset |
| Internal ArbOS version | 61 | Matches encoded header version |
| Reported client | `nitro/v3.12.4+960ca0a-20261110T061047Z` | Provider self-report |

The header's inclusion price, the state-based prospective component price and
the unpinned suggestion describe different moments. They are not required to
be numerically identical. Their source fields remain separate in
[RESULTS.json](RESULTS.json). A self-reported client string is not a binary
attestation; exact advertised-tag source retrieval was unavailable.

## Fees include posting; do not count it twice

Robinhood documents ETH fees with execution and Ethereum posting included in
the ordinary gas charge. Its standard estimator includes both components.
Therefore a real target-chain `eth_estimateGas` result multiplied by the reviewed
price is the inclusive estimate; adding another posting quote would double
count it. [Robinhood fee documentation](https://docs.robinhood.com/chain/gas-and-fees/).

The Nitro component interface separates total gas, posting gas, base fee and
parent-price estimate. It is virtual RPC functionality at `0xc8`, so an empty
runtime there is not evidence that the feature is absent.
[NodeInterface reference](https://docs.arbitrum.io/arbitrum-essentials/nodeinterface/reference).

`gasEstimateComponents` executes the destination while estimating. In contrast,
`gasEstimateL1Component` can quote posting bytes even when destination execution
would fail. Its result cannot establish an activation/rebalance's full cost.
Preserve the actual destination, sender, value, fee envelope and calldata.
[Pinned interface](https://github.com/OffchainLabs/nitro-contracts/blob/4341b132cfbdcc980ead03765ca5224ff6cb5d97/src/node-interface/NodeInterface.sol#L68-L113).

The ABI comment and upstream implementation differ about internal L1 padding:
the inspected Nitro implementation applies its own posting-price adjustment.
Use the returned values; do not remove or invent padding from a prose comment.
The project's required full 20%/25% headroom remains separate and unchanged.
[Inspected implementation](https://github.com/OffchainLabs/nitro/blob/v3.11.2/execution/nodeinterface/node_interface.go#L403-L518).

## What the ten payload reads establish

All ten exact prior transaction payloads returned a posting-component quote.
The original controlled fixture sender, value and gas field are preserved;
there is no state override, target deployment, signing or target execution.
The native activation/growth values remain the original test fixture's 100 ETH
and 5 ETH because those feeds price ETH at $1. These are not real $100/$5 native
amounts for Robinhood. Some workflows have identical calldata and share the
same component result; ten reads are not ten independently different payloads.

| Payload | Posting gas units |
| --- | ---: |
| ETH activation / growth | 1,003 / 995 |
| ZZZ activation / growth | 1,062 / 1,062 |
| Main / two-leg harvest | 546 / 546 |
| Compound | 629 |
| Single replacement / hybrid open / hybrid replacement | 629 / 629 / 629 |

Each uses component base fee 20,110,000 wei/gas. A real `approve(0)` witness also
returned total **34,144**, posting **549** and compute **33,595** gas units; its
separate direct estimate was 34,144. That proves the sampled non-PoPL witness's
decomposition, not a complete PoPL operation. Earlier zero posting observations
retain their dated scope; this newer sample is nonzero. Parent pricing may
change again. [Estimation model](https://docs.arbitrum.io/arbitrum-essentials/how-to-estimate-gas).

For scale only, multiplying the observed unpinned price by the 20M/24M caps
gives **0.00040212 / 0.000482544 ETH**. These are conditional arithmetic examples,
not measured PoPL fees, approved spending limits or future-price guarantees.

## Confirmed mismatch and implemented correction

The actual positive-tip transaction
`0xf269696c59813665b4e02717d7ae96f21b5a29536eacc3b318c2b6d8f0fc9e91`
has signed maximum 650,900,000 and priority 50,000,000 wei/gas. At the captured
20,100,000 base, its receipt reports 20,100,000. The unchanged Ethereum helper
calculates 70,100,000. For 56,722 gas, the helper counts 3,976,212,200,000 wei
against the receipt-accounted 1,140,112,200,000: **2,836,100,000,000 wei excess**.
That can exhaust a keeper's daily budget prematurely. It does not transfer the
excess funds or establish a new NFT accounting loss. Legacy fixed-price
assumptions are also unsuitable without separate qualification; this campaign
did not collect a legacy witness.

Upstream Nitro can collect or ignore tips depending on version, chain policy
and message path. This is why a zero priority suggestion alone was insufficient
proof. [Nitro fee processing](https://github.com/OffchainLabs/nitro/blob/v3.12.2/arbos/tx_processor.go#L922-L968),
[public policy getter](https://github.com/OffchainLabs/nitro/blob/v3.12.2/precompiles/ArbOwnerPublic.go#L107-L110).

The source correction avoids adding a mutable chain-policy interpreter:

- Future profile 2 is explicit, integer-valued and restricted to chain 4663,
  reviewed `included` accounting and zero separate L1 allowance.
- Its existing one gas-price read moves before its simulation. Initial call,
  estimate and final ordinary-LP call use type 2, the same `maxFeePerGas` and
  priority zero. No conflicting `gasPrice` field, price bump or wider retry is
  introduced. Original gas/transaction/day/funding checks remain.
- The keeper's Cast command adds `--priority-gas-price 0` only for profile 2.
  Its durable `fee_review` schema 2 adds only
  `execution_fee_model: "eip1559_zero_tip"` to the original fields. Recovery
  requires the actual signed transaction to be type 2 with priority zero and
  the receipt price to equal the canonical derived base fee.
- Omission/profile 1 retains its original command, read order and schema 1.
  A pending review is interpreted from its saved schema, regardless of new
  future settings. No existing record is upgraded or corrected automatically.
  `zzz_ops/ethereum_fees.py` remains byte-identical.

Some providers require enough native currency for the full initial simulation
ceiling when fee fields are explicit, even if the final padded operation would
cost less. Fund and qualify that reviewed ceiling. A refusal stops without an
intent, signing, state override or fee-budget increase.

The separate actual zero-tip transaction
`0xaecc8ba944a66d9387db33ae32a63b5a77bdc0af2b3521868b78b88349b7f129`
matches the canonical base calculation. Its original transaction/receipt/header
fields are replayed through keeper recovery with a clearly constructed test
journal, not represented as a transaction sent by PoPL.

## Verification and safe adoption boundary

**14 new focused methods pass once**, with no old method executed. They cover
typed envelopes, original caps, exact review/price/type checks, schema 1
preservation, invalid future settings, provider refusal, real zero-tip data,
revert charging and durable timeout/no-resend behavior.
[Focused receipt](KEEPER_FOCUSED.json) and [log](KEEPER_FOCUSED.log).

One installed Foundry 1.4.4 keyless `cast mktx --raw-unsigned` construction used
a clean child environment and a closed loopback endpoint. Strict decoding shows
exactly nine unsigned type-2 fields: chain 4663, priority zero, max fee
20,106,000, gas 24M, original target/calldata and no signature fields. It used no
wallet or public RPC. It does not qualify actual keystore signing, submission
or recovery on a live service. [Record](CAST_UNSIGNED.json).

The new module is listed once by the keeper runner. The inventory check executes
no test bodies. No Solidity/EVM/compiler suite or unchanged Python/browser suite
was rerun. All production Solidity, contract limits, economic rights, public-null
website configurations and shared Anvil-only browser signer remain unchanged.

Before any adoption, separately review complete actual deployment calls,
trace-provider reliability/capacity, inclusive fees, all workload sizes, original
operator caps, funding and Linux signer/recovery operation. Candidate settings
do not approve any of these. Preserve pending work and its original review
when upgrading. Finish schema-2 pending recovery before downgrading to an older
build that cannot decode it. Never downgrade, relabel or delete that record to bypass
recovery. The operator manual supplies the coordinated adoption procedure.

`python reports/rpc-fees-20261113/fees/reconcile.py` checks the frozen payloads,
strict ABI/RLP decoding, actual receipt interpretation and unsigned construction
offline. [Primary sources](PRIMARY_SOURCES.json) and
[source assessment](SOURCE_ASSESSMENT.json) distinguish upstream evidence, actual
observations, code correction and remaining qualification.
