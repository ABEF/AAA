# Authorized accounts and fresh wallet picker

2026-10-20. Internal scoped verification; production NOT APPROVED.

The user identified two issues: the previous account warning appeared before
choosing a wallet, and MetaMask's old site-authorized account differed from the
account visible in its popup. The app cannot inspect the extension's private
popup selection. It can request permission and let the user choose among the
accounts actually authorized through EIP-1193.

## Implemented behavior

- Opening a fresh picker resets only presentation of the prior attempt. Internal
  connection errors still block transactions; pending recovery remains visible.
- After provider selection, admitted accounts returned by that provider appear
  as selectable Test Wallet A/B buttons. An older first account does not prevent
  selecting another authorized account. No silent fixture-account substitution.
- Selection rereads accounts/network, binds the exact provider and verifies the
  local genesis. Reconnection and reload retain the explicit choice only while
  it remains authorized. Actual accountsChanged events continue to invalidate
  reviews and update wallet state.
- The signer requires membership of the exact reviewed sender in the current
  valid authorized list, rather than equality to its first element. Event
  revision guards, nonce/code/genesis/economic checks and canonical receipts
  remain. Revoked authorization cannot sign.
- Permission prompts remain explicit. An account absent from the provider's
  authorized list must be granted access by the user in the wallet. A pending
  transaction prevents account switching; its journal is never cleared.

## Verification and limits

171 existing cases passed across browser-client, browser-wallet, ui-state and
domain test files after the source changes. Nine new focused cases then passed
using `--test-name-pattern='authorized (account|second|accounts)'`, without
rerunning unchanged cases. **180 distinct affected cases total**, not a complete
website or contract regression. New cases cover second-account selection,
reconnect/restore, missing permission, wrong network/genesis, pending journals,
explicit sender submission and revocation before signing. Test sends are mocked.

`node --check local-view.js` and `node build.mjs` pass (5,593 files).
[Source bindings](authorized-accounts-source-sha256.json) identify this scope.
No actual holder transaction, backend/contract change, chain/service restart,
public deployment, load campaign or monitor change. The clean-picker visibility
change has source/syntax review; actual MetaMask UI acceptance remains open.
