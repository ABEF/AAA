# Pending nonce diagnosis - 2026-10-22

Internal scoped review. Signing remains local Anvil only; production NOT APPROVED.

## Observed failure

The user's saved mint `0x7df63aa0d6bf24461b7fdf1858b778c7d1e051d904a11a86ad0dd538a9400cc6`
was visible on the reviewed Anvil node with nonce **35**, no block and no receipt.
Wallet A's latest and pending transaction counts were both **25**. Repeated receipt
polling could not make this queued transaction executable. See the adjacent
[read-only observation](pending-nonce/observed-transaction.json).

The actual browser review/journal and extension internals were not inspected.
MetaMask retaining activity from an earlier development chain is a plausible
cause, consistent with its [development-network guide](https://docs.metamask.io/metamask-connect/evm/guides/best-practices/run-devnet/),
but is not an observed extension diagnosis. Do not say the mint succeeded.

## Change and safety boundary

The user explicitly approved this narrowly scoped read-only shared BrowserWallet
change after automatic approval review required clarification. That permission
supersedes earlier byte-identical instructions only for confirmation diagnostics.
Public/nonlocal signing remains disabled. BrowserClient and coordinator are unchanged.

- Read transaction and receipt concurrently, and validate the submitted transaction
  against its original review before waiting for a receipt.
- Immediately report a changed nonce or non-executable predecessor queue on this
  node. A consumed nonce with no matching receipt stays unresolved. A missing
  transaction stays pending; it is never treated as permission to retry.
- Stop the confirmation wait for actionable failures. Normal polling and canonical
  receipt, genesis, calldata, fee, sender, reorganization and paid-cost guards remain.
- Show wallet-confirmation text only during the wallet request. Hide the send
  button after submission and keep Close available. Closing is not cancellation.
- Preserve the original hash/journal. No automatic resend, replacement discovery,
  nonce editing, acknowledgement of unmined transactions, or journal deletion.

## Verification

**175 affected tests pass**: shared wallet and deployment transaction suites,
including their imported API/session cases. Eight new cases cover queued/changed/
consumed nonces, invisible hashes, pending transaction mutations, repeated recovery,
later canonical inclusion and numeric-nonce compatibility. Command from the website:

```sh
node --test tests/browser-wallet.test.mjs tests/deployment-transactions.test.mjs
```

**Two headless Chrome scenarios pass** with mocked node/wallet/API responses:
changed nonce and nonce gap. Each checks stage labels, enabled Close, three
read-only recoveries, one simulated send and preserved journal. No actual
extension or transaction is used. See [results](pending-nonce/browser-result.json).

**Six actual node recovery reads pass**, using isolated in-memory reconstructed
reviews at nonce 35 and nonce 25, never the user's saved browser record. Maximum
observed recovery was 21 ms; this is a local sample, not a latency guarantee.
The real mint remained unmined and the account nonce stayed 25. No wallet request,
send, drop, state reset or user storage access occurred. See [replay](pending-nonce/replay.json).

JavaScript syntax and the 5,598-file build pass. No backend or Solidity changes;
their unchanged suites and the deferred load campaign were not rerun. Evidence
and source hashes are in [bindings](pending-nonce/bindings.json). The captured
probe scripts reference their original external fixture directory; do not execute
them against another deployment. Historical evidence retains its original scope.

## Remaining operator action

This patch detects the queue problem; it does not resolve the user's unmined
nonce 35 transaction. Preserve the pending hash and original review. Inspect wallet
activity and the reviewed node before deciding how to reconcile it. Never fill
the gap with dummy transactions, advance the chain nonce, clear a journal, or
reset Anvil to make this mint appear successful. An explicit local cleanup plan
would need to address both the node queue and wallet activity and retain the
evidence; removing a local mempool entry alone cannot invalidate a signed transaction.

Actual extension acceptance and controlled cleanup remain open. NFTs, LP, balances,
running services, paused monitoring and public configuration were not changed by
this fix. Static publication is recorded separately.
