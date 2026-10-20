# Wallet RPC quantities and submission-stage diagnostics

2026-10-20. Internal scoped verification, production NOT APPROVED.

## Observations and limits

The user reported `Invalid transaction quantity` after confirming mint, then
provided the website review (0.05 ETH, Wallet A, calldata 0x21bf772d), without a
transaction hash. Read-only checks verified the live 8900 manifest matched the
preserved RPC/genesis. At observed head 319, Wallet A's latest/pending nonce was
0x23 and Wallet B's 0x4, with no pending transactions. The latest two mint drafts
used A's nonce 0x23 and had no observed hash/outcome. The latest mined A operation
was the earlier LP increase at block 0x12b with receipt status 1.

This does not capture Chrome's provider response or prove what MetaMask displayed.
The actual rejected field and whether hexadecimal padding caused this incident
remain unconfirmed. Do not represent mock compatibility tests as real extension
acceptance or claim the mint succeeded.

## Change

Wallet RPC numbers accept only strings of 1-64 unsigned hexadecimal digits with
0x prefix, including leading zeros. Values remain exact BigInts; missing fields,
decimal strings, numbers, negatives, fractions and oversized values fail closed.
Prepared transaction/policy/journal encoding remains canonical. No chain, sender,
nonce, target, calldata, value, gas envelope or receipt checks were removed.

Invalid RPC quantity diagnostics identify method/field and value type, not raw
provider contents. Polling retains that safe diagnostic. Failed preflight is
marked not-submitted only before a new submission journal/send exists. The UI
shows Refresh balances for that state. Submitted/uncertain operations retain
their original recovery journal and hash; there is no automatic resubmission.

## Verification

`node --test tests/browser-wallet.test.mjs tests/browser-client.test.mjs`:
**123 passes**, including four new regressions:

- Padded RPC numbers through send/receipt/acknowledgement, while padded review
  input remains rejected.
- Seven invalid estimate forms rejected with exact method, zero sends/journals.
- Missing confirmed transaction chainId preserves the original hash; repaired
  RPC data recovers with one total mocked submission.
- Numeric (non-hex) receipt gas usage remains unresolved and retains the hash.

`node --check local-view.js` and build pass (5,593 files).
[Source bindings](rpc-quantities-sha256.json). No unchanged Solidity/backend
suites, public transaction, local reset, service restart, load campaign,
monitoring change or public deployment.
