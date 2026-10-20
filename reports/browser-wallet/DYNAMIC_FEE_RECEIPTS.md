# Canonical EIP-1559 fee verification - 2026-10-20

## Incident and root cause

The user supplied mint hash
`0xa7f91ea39f9fd3e8c771e94b518e11009ced31d7bac9c568dd4af274ffac3891`.
It succeeded at block 351 (`0x15f`). The old browser verifier rejected the node's
reported gas price against the original review, retried, then showed a generic
recovery error. No second mint was submitted to investigate.

The signed type-2 transaction has maxFeePerGas and maxPriorityFeePerGas of
1,000,000,007 wei. Block base fee is 7 wei. Anvil reports transaction gasPrice and
receipt effectiveGasPrice as 1,000,000,014, but the account balance delta confirms
345,099 gas charged at 1,000,000,007, exactly 345,099,002,415,693 wei excluding the
0.05 ETH mint payment. The block contains that one transaction. This is a derived
RPC reporting discrepancy, not evidence that the approved fee was exceeded.

## Generic correction, not a testnet tolerance

[EIP-1559](https://eips.ethereum.org/EIPS/eip-1559) defines the effective execution
price as min(maxFeePerGas, block.baseFeePerGas + maxPriorityFeePerGas).
These caps are signed transaction fields; effectiveGasPrice is a derived RPC
field, not part of the consensus receipt payload.

The shared website signer and `zzz_ops/ethereum_fees.py` derive type-2 prices
from the signed caps and authenticated-by-RPC canonical block. No chain-ID,
account, token, hash or numerical tolerance exception exists. The local observer
uses the same rule, independently of the browser. This does not authenticate an
untrusted RPC cryptographically or account for chain-specific extra data fees;
production provider/fee qualification stays open.

- Signed fee cap remains within the original review and hard policy.
- Priority fee above cap, base fee above cap, missing/invalid values and unsupported
  transaction types fail closed. Legacy/type-1 behavior retains existing checks.
- Exact sender, target, calldata, value, nonce and chain still match the review.
  Gas used, fee per unit and total paid cost retain original limits.
- Canonical block identity is checked; browser rechecks block/base fee before
  confirmation. Derived fee and raw reported fee are stored separately.
- Deterministic quantity/receipt mismatches immediately return a specific recovery
  reason. Transient missing receipts still use bounded same-hash polling.
- Neither errors nor recovery resend a transaction or delete an unresolved journal.

The prepared transaction format remains unchanged. This change supports canonical
observation of a wallet's type-2 transaction; it does not claim a complete new
production EIP-1559 quoting policy or enable public signing.

## Verification and operating update

142 affected website signer/client tests pass; 40 independent local observer tests
pass. Three new signer cases cover dynamic-fee calculation, reporting discrepancies,
cap/base/priority/unknown-type/gas failures and an effective fee below cap. Two new
observer cases verify retained raw evidence and rejection of bad caps/missing base.
A temporary duplicate declaration during editing was corrected before the passing
runs. No unchanged contract/artwork suites or load campaign were run.

Read-only replay of the user's exact mined transaction passes in the browser
signer and independent Python observer. A memory-only browser journal is used for
that replay; actual browser/session records are not rewritten. Derived fees match
the actual historical account balance delta. No claim of extension UI acceptance.

See [signer tests](dynamic-fee-signer-tests.log),
[observer tests](dynamic-fee-observer-tests.log),
[actual receipt replay](dynamic-fee-replay.json),
[web recovery](dynamic-fee-web-recovery.json) and
[source bindings](dynamic-fee-sha256.json). Syntax and 5,593-file build pass.

The checked web worker was replaced (21472 -> 18456) to load the observer update.
Anvil PID 10988, genesis, RPC, session token, deployment/manifest and all 12 NFT
ownership/LP records remained unchanged. Journals were authenticated before the
restart. Normal state reads mine empty local confirmation blocks; no holder or
operator transaction was submitted. External snapshots retain the local session
secret outside reports/Git. No public server or paused monitor changed.

Reload the current page and recover the saved hash. Do not mint again. A successful
recovery may run the fixture's normal original mock-reveal handling; this review
itself did not invoke it. If a new mismatch is reported, preserve the same record
and diagnose that exact field. Production release remains NOT APPROVED.
