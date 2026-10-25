# Scoped integration qualification verification

The existing offline schema-5 gate now has an explicit current mint profile 1.
It reports the actual code-owned Vault direct-mint capability and blocks an
invented OpenSea primary drop, even if generic staged flags are supplied.
Historical profile zero remains readable as manifest consistency and explicitly
cannot qualify the current production release. The CLI now fails closed by
default on old schema/omitted/zero/boolean mint profiles; only explicit
`--historical-consistency` allows a labeled historical consistency inspection.
It cannot hide an incompatible current integration. The current template selects
1 and remains blocked with unselected provider/authority data.

The new randomness profile records the actual request ABI and two words, fixed
nonzero lane, original-request validity through refund/expiry and recovery to the
same original result. Funding remains an external subscription reserve. These
are evidence requirements; they do not implement a new randomness provider,
adapter, paid mint path, mint authority, reroll or public wallet action.

Verification is **68 distinct Python test methods**: 15 new adversarial/current-
profile/CLI methods and 53 existing affected methods. The first run passes 54
methods. One additional malformed-integration method was then added and run
separately. The CLI change then passes 13 affected methods, including the legacy
UTF-8 inspection changed to request historical mode explicitly. Unchanged
methods were not repeated for a larger count.
Read [machine scope](VERIFICATION.json), [source bindings](source-scope.json),
[first run](python-verification.log) and
[additional malformed case](python-malformed-verification.log) and
[CLI scope checks](python-cli-verification.log). The [actual template CLI
summary](template-cli-summary.json) records expected exit 1, explicit current
profile and the honest unimplemented-primary-mint blocker; its full raw output
is retained externally with the recorded SHA-256, not promoted to live evidence.

Tests cover explicit legacy/current scope, rejection of fabricated SeaDrop
capability, secondary-product mismatch, original draw request/result changes,
irreversible expiry/refund/reroll, missing negative-proof evidence, funding from
locked LP, profile/type confusion and malformed current integration records.
They use synthetic manifests, not real provider or marketplace acceptance.

The user's subsequent mint-price decision is recorded in the guide/research:
0.05 ETH buyer gross, actual platform fee deducted from creator proceeds, gas
separate. No platform fee is assumed and no Solidity integration is implemented.
This documentation-only clarification did not repeat unchanged tests.

The separate public observation has **16 successful logical checks and 32 HTTP
JSON-RPC posts**, including the existing client's per-operation chain-ID checks.
It was bounded to 60 seconds, 20 logical calls and 40 posts. Only one documented
public provider was used, with canonical hash-pinned code/storage reads and a
reference recheck. Runtime presence and empty standard EIP-1967 slots do not
establish code/source equivalence, safety, lack of alternate administrative
controls or OpenSea product registration. The initial sandbox transport failure
was not treated as a missing contract; the authorized network-capable run passed.

Production Solidity, website, shared signer, services, existing Anvil state and
journals are unchanged. No unchanged Solidity/size suite was rerun, no public
transaction was sent, no current service was qualified and no independent audit
was performed. Production remains **NOT APPROVED**.
