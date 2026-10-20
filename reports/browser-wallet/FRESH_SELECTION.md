# Fresh MetaMask account selection

2026-10-20. Internal scoped verification; release NOT APPROVED.

The user still observed the old account after the preceding fixes. Inspection
found explicit reconnect preferred the saved sender if it remained authorized,
even when a different account was first in the fresh provider response.

## Changes

- Explicit reconnect no longer prefers the stored address.
- The MetaMask button requests fresh account permissions on its user gesture,
  regardless of whether the old address is an admitted fixture account.
- A permission result containing several accounts requires an explicit website
  account choice. The site cannot read the extension's private popup selection.
- An unfinished choice cannot silently restore the prior sender. Remembered
  connection selection is cleared while choosing; transaction journals remain.
- Fresh account authorization, chain/genesis and pending recovery checks remain.
  No signing, approval or transaction is performed by connecting.

## Evidence

`node --test tests/browser-client.test.mjs tests/ui-state.test.mjs`: **90 passes**.
Five new cases cover fresh choice from an admitted previous account, multiple
permissions, cancellation, current provider response and pending preservation.
The multiple-account case also checks that wallet refresh notification cannot
restore the sender and that tentative selection is not saved. The earlier
second-account test now distinguishes reconnect from an explicit selection.

An initial run caught three failures from placing the multi-account guard in
the explicit-account method as well as the connect method. That implementation
mistake was corrected; a subsequent 62-case client run passed, followed by the
final 90-case run after unfinished-selection hardening. Counts are not additive.
Syntax check and `node build.mjs` pass (5,593 files).

Actual Chrome/MetaMask behavior is **not independently verified**. Computer-use
inventory exposed no Chrome tab or wallet extension. Refresh the local app and
click MetaMask; select the intended account in the permission prompt. If it
shares multiple accounts, select the intended address in the website picker.
Rabby's ordinary reconnect is not forced through a permission prompt.

No backend/Solidity change, public transaction, chain/service restart, deployment,
load campaign or monitoring change. [Source bindings](fresh-selection-sha256.json).
