# Bounded royalty-balance read policy

The new `royaltyBalanceGas()` setting separates the maximum token balance-read
allowance from the existing complete royalty sync allowance. Its default is
**50,000 gas**. Governance may call
`setRoyaltyBalanceGas(uint32 gasLimit, bytes32 reviewHash)` with an integer from
10,000 through 1,000,000 and a nonzero review fingerprint.

This is an engineering interval, not qualification of every value. A higher
value requires a new complete workload review. The read value is a maximum:
EIP-150 and the remaining complete-sync budget can limit actual forwarding.
A cheap read can complete at a 1M ceiling, while a token needing nearly that
entire allowance may exhaust the complete sync and be deferred. Default 50k/1M
qualification belongs to the separate actual activation workload, not these
policy tests.

The existing four-word `GasPolicy` ABI, `setGasPolicy` arguments,
`royaltySyncGas()` default of 1M and `gasFingerprint()` encoding remain unchanged.
The new setter advances the existing gas-policy revision, so changing and then
restoring the read allowance cannot revive an earlier gas review. The complete
configuration hash commits the default cap and every reviewed change. Other
financial, mint and metadata domains retain their existing inputs and meaning.

The same governance, preparation, canonical-state and reentrancy restrictions
as other gas-policy writes apply. No ownership, royalty weights, amounts,
recipient, fee allocation, contribution safeguard or transaction budget changes.

## Focused verification

All three **new** methods pass:

| Method | Evidence |
| --- | --- |
| `testRoyaltyReadPolicyDefaultCommitsFiftyKAndRetainsExactGasTupleAndFingerprint` | Default 50k, exact 128-byte legacy gas tuple, unchanged gas-hash formula and constructor configuration commitment. |
| `testRoyaltyReadPolicyBoundsRevisionReviewAndExistingSetterRemainIndependent` | Accepted endpoints, event/revisions, changing and restoring settings, independent old setter and unchanged financial/mint domains. |
| `testRoyaltyReadPolicyRejectsBadBoundsMissingReviewAndUnauthorizedOrFrozenWritesAtomically` | Both rejected endpoints, zero review, wrong caller, preparation/canonical locks, exact unchanged state after rejection and authorized post-seal-context write. |

The test host is an exact minimal dependency copy of the actual Policy and its
new test. Its small authority context supplies Access's relevant answers; this
is not a rehearsal of the complete sealed graph. Every compiled source matches
its compiler metadata Keccak and the original filesystem SHA. Forge's CRLF-to-LF
compiler-text normalization is recorded separately. Source copies and selected
repository sources stayed unchanged throughout. The repository configuration
was never modified. No old method, normal full-project build, live chain, signer
or service was run by this policy verification.

See [results and compiled source identities](policy/RESULT.json) and
[exact invocation and source pins](policy/START.json). The full fresh graph,
normal size gates, real token fault paths and cold 20M-plus-20% workload require
their separate source-pinned evidence.
