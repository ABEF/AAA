# Numeric provider nonce correction - 2026-10-20

The user reported: `Invalid wallet response: eth_getTransactionCount must be a
hexadecimal quantity (number)`. A new regression reproduced that exact pre-send
failure with nonce 35. Previously only hex strings were accepted by the shared
wallet RPC quantity validator. The actual numeric value from the user's extension
was not captured; no full extension flow is claimed.

## Fix and security boundary

`browser-wallet.js` normalizes provider-returned numeric quantities only if they
are nonnegative safe integers (`Number.isSafeInteger`); negative zero is rejected.
The conversion is directly to BigInt, with no rounding or decimal-string parsing.
Existing bounded hexadecimal strings remain accepted. Prepared transaction inputs
and durable journals still require canonical hex. Outgoing nonces remain hex.

This is a chain-independent provider compatibility correction in the website's
shared signer, not a local fixture or token-name workaround. No special account,
chain ID, method-specific nonce bypass, gas exemption or test-service change is
added. Public signing is still separately gated pending production manifests and
qualification; this does not enable mainnet by itself.

Exact pending nonce comparison, balance/value/gas limits, receipt and canonical
identity checks still run after normalization. Numbers beyond MAX_SAFE_INTEGER,
fractions, NaN, infinities, negatives, booleans, decimal strings and objects fail
closed. Large financial values must remain exact hexadecimal strings; an already
rounded JS number cannot be recovered safely. Ambiguous/invalid post-send data
preserves the original pending hash instead of claiming success.

## Verification

The new numeric-nonce reproduction failed before the fix with the exact reported
message. Afterward, **139 affected signer/client cases pass**, zero failures/skips:

```text
node --test tests/browser-wallet.test.mjs tests/browser-client.test.mjs
```

Five new cases cover numeric nonce 35 to outgoing `0x23`, safe RPC/receipt numbers,
unsafe/ambiguous nonces with zero sends/journal writes, exact mismatch rejection
and canonical prepared input, and financial precision/gas limit rejection.
MAX_SAFE_INTEGER is converted exactly in a synthetic nonce-boundary fixture.
The old invalid-number cases now use a fraction/unsafe integer, since safe numbers
are intentionally supported. Numeric receipt status is not newly supported by
this change; existing status semantics are preserved.

See [test output](numeric-nonce-tests.log) and [source bindings](numeric-nonce-sha256.json).
Syntax and static build checks pass. The local served module matches source;
reload the page to load it. No browser-extension confirmation, public transaction,
new local transaction, chain reset or service restart was performed. No unchanged
contract/backend/artwork suites or deferred load campaign ran.

The exact type mismatch is reproduced and corrected. **Actual MetaMask mint
acceptance remains pending.** Do not relabel the passing provider tests as an
observed extension signing flow or production approval.

Current [operator procedure](../../docs/BROWSER_WALLET.md) and
[central task](../../TODO.md#task-wallet) retain remaining production gates.
