# Authorized local mint reconciliation - 2026-10-22

The user explicitly approved reconciling the one unmined local mint while
preserving NFTs, LP and balances and archiving its evidence. This supersedes the
earlier read-only limitation for this specific cleanup only. No production
signing, generic pending-record discard or chain reset was authorized or added.

## Completed on the node

Target: `0x7df63aa0d6bf24461b7fdf1858b778c7d1e051d904a11a86ad0dd538a9400cc6`.
The script pinned the original chain 31337/genesis/RPC, sender, Vault runtime,
mint selector, 0.05 test ETH value and nonce 35; it required no receipt and a
transaction pool containing only that exact hash. The node expected nonce 25.

Anvil 1.4.4's targeted `anvil_dropTransaction` returned null and left this queued
transaction present. After rechecking the receipt, account nonce and singleton
pool, `anvil_removePoolTransactions` for Wallet A removed it. No other sender or
transaction was removed. The pool is now empty; the mint was never executed.

The complete chain stateRoot before/after is identical:
`0x78326a082d37d866e4f674a0e77776e9c534502ffe8d7e988f93fccf974ce76e`.
Both Wallet A/B balances and nonces match exactly. All contract storage, including
NFT ownership, attached LP and rewards, is therefore unchanged at these observations.
No holder transaction, balance/nonce edit, mining instruction, service restart,
paused-monitor restart or public-chain operation was performed by this cleanup.
See [the before/after record](reconciliation.json).

The initial preflight accidentally checked the mint destination against the NFT
role rather than the Vault. The identity assertion rejected it before any mutation;
the corrected role/runtime check passed. The execution record distinguishes the
initial ineffective hash removal from the successful sender-scoped removal.

## Browser step still required from the user

The website's recovery journal resides in the browser used for minting. It has
not been read or changed by this task. MetaMask's activity/nonce history is also
unchanged. The user is going to sleep; record these as pending, not complete.

1. In MetaMask select Test Wallet A `0x7099...79c8` and the **PoPL local network**.
   Go to **Settings > Developer tools > Delete activity and nonce data**. Use
   [MetaMask's current procedure](https://support.metamask.io/managing-my-wallet/resetting-deleting-and-restoring/how-to-clear-your-account-activity-reset-account/).
   Do not reset the wallet or use a public network for this step.
2. Refresh `http://127.0.0.1:8902/#my-nfts` in that same browser. Close an older
   recovery dialog if needed. The one-time panel appears only if the exact
   authorized saved mint exists in that browser's local storage.
3. Confirm the local nonce-history step and click **Archive the abandoned mint
   and reconnect**. The control verifies exact origin, manifest, account, hash,
   economic fields, unchanged nonce 25, matching genesis and absent transaction/
   receipt twice. It takes the same wallet Web Lock, saves and verifies a byte-exact
   journal archive, then releases only that original pending key and reloads.
   Any mismatch, active operation or archive failure retains recovery.
4. Confirm fresh balances/NFTs. No new mint is automatically submitted. Check the
   next explicit review uses the current node nonce. A removed mempool entry is
   not cryptographic cancellation; never rebroadcast the old signed mint.

Archive key: `popl-local-abandoned-archive-v1:<genesis>:<transactionHash>`.
Do not delete it after recovery; it retains the complete original journal.
An absent repair panel can mean this is a different browser; never infer that
MetaMask or the original browser journal has been reconciled.

## Temporary local artifact and restoration

The control is appended **only** to local `dist/deployment-view.js`, pinned to
origin 8902, RPC 57306 and this exact genesis/hash. Production source, shared signer,
website main source and the public static release 9aaedec remain unchanged.
The external pending-fix directory holds the original build bytes and overlay
hashes; [overlay record](local-repair-overlay.json) identifies them. It is not a
new public recovery feature. Never package this temporary build for deployment.

After the user completes archival, verify the browser outcome and the still-absent
transaction. Restore the local dist module from its matching committed source,
preserving the browser archive and chain. A normal website build also removes
the overlay; if the user has not completed recovery, do not erase this handoff
requirement. Never restart Anvil to remove the panel.

## Focused verification and limits

Thirteen isolated checks pass: exact archival, repeat absence, wrong origin/chain/
hash/nonce, missing user confirmation, mined/rebroadcast transaction, changed
account nonce/genesis, another tab's lock, failed archive persistence and concurrent
journal change. Other storage keys remain unchanged.

One isolated headless browser scenario passes against the actual local manifest
and read-only RPC, with a synthetic journal. It checks the control, required
checkbox, byte-exact archival and reload. It does not use the user's browser or
MetaMask. The initial headless context denied loopback access; granting it only
for 8902 inside that disposable test context allowed verification. Actual browser
permissions remain untouched. See [browser evidence](repair-browser.json) and
[test log](repair-tests.log). No unchanged production suites or load campaign ran.

Reports capture one exact historical fixture; do not rerun their scripts against
another network. Task statuses remain in the central Todo. Public transaction
integration and release approval remain open. Production NOT APPROVED.

A read-only Anvil state backup is saved outside Git. [Backup hash](chain-backup.json)
identifies it; this is not complete historical/browser recovery and does not authorize
a chain restart. The existing live fixture should be preserved.
