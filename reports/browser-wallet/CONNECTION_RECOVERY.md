# MetaMask connection and approval recovery

2026-10-20. Internal, scoped follow-up to the
[original browser-wallet evidence](VERIFICATION.md). Production is NOT APPROVED.

## Observed problem and correction

The user imported test account A but encountered connection/network prompts and
then an unresolved approval. Importing or selecting an account in MetaMask does
not establish which account it exposes to this website. The adapter now explains
site-connected account permissions, shows the exposed address on mismatch, and
distinguishes wrong chain ID from an incorrect local RPC/genesis. Reconnecting an
already authorized provider uses fresh public account/chain reads and verifies
the deployment; failed verification does not restore a ready account.

The user-reported MetaMask approval is independently confirmed on the existing
local chain:

- Hash: `0xfbcd791c19b9ccaa2a41fb08df90e8b04cf26d36588a0b110265f7e07a0c86e7`.
- Block 219, successful status; sender, target, input, value, nonce and chain
  match the saved review.
- Reviewed gas limit `0xdfa9`; wallet-submitted limit `0x11793`.
- Paid gas `0xba62`; effective price matches the reviewed `0x3b9aca07`.
- This is an approval only. It does not activate an NFT or add LP.

The original signer required identical gas limits. That rejected the already
successful approval because MetaMask added headroom. The signer and local observer
now tolerate gas-limit padding inside hard gas/price/cost policy, while keeping
the submitted gas price at or below its reviewed ceiling. The canonical receipt
must prove paid gas and price are within both submitted and reviewed limits, and
paid cost within the original reviewed maximum. Exact economic fields and nonce
are unchanged. Pending or unverifiable evidence never becomes success.

The original review is retained. No payment or approval is resubmitted, and no
browser journal is cleared by an operator. These checks detect wallet-modified
requests after execution; they cannot prevent a user changing a wallet request.

## Focused verification

- Connection adapter: 41 passing cases, including eight new regressions.
- Receipt signer: 44 passing cases, including seven new regressions. This
  includes missing receipts, excessive hard limits, excess paid gas/price,
  malformed receipt usage and changed economic fields.
- Backend receipt observer: 31 passing cases, including four new regressions.
  [Backend evidence](backend-gas-padding-evidence.json) retains the exact scope
  and source bindings. These are not a fresh broad regression.
- Updated `BrowserWallet` successfully reconciled the existing approval through
  read-only RPC calls and an isolated in-memory journal. Acknowledgement also
  reverified its canonical receipt. The actual Chrome journal was not accessed.
- Static website build succeeded with 5,593 output files.

[Approval observation](metamask-approval-observation.json) contains public
transaction/receipt evidence. [Read-only recovery](approval-recovery-verification.json)
records the isolated signer check. [Source bindings](connection-source-sha256.json)
identify this follow-up separately from the original integration report.

## Running service recovery

The fixed helper was reviewed and checked before replacing only Python process
10672 with process 25784. Original Anvil process 10988 and RPC port 61752 remain
running. The recovery authenticated the original genesis, deployment/runtime
pins, session, persisted journal hashes, operation revisions, canonical receipts
and absence of pending account nonces.

[Post-update observation](web-recovery-verification.json) confirms all six NFT
owners, LP values, activation states and claimable balances are unchanged. The
original browser review and session remain intact. Observing the existing
approval advances the operation ledger from revision 18 to 19; repeating that
observation returns the same revision and hash. No holder or operator transaction
was submitted. Existing state synchronization mines empty confirmation blocks.
Chrome's own pending record is untouched; its normal recovery/acknowledgement
should now complete after refresh.

The one-session helper and captured transport session remain outside Git at
`EXT/browser-wallet-work/recover-browser-web.py` and
`EXT/browser-wallet-work/gas-padding-recovery/`. It does not start or terminate
Anvil. This is a fixed-fixture web-process recovery, not persistent chain backup
or a production service-restart mechanism.

No unchanged Solidity suite, public transaction, large load campaign, production
deployment or paused-monitor restart is included. Full MetaMask mint/activation/
growth/claim acceptance remains open; one confirmed approval is narrower evidence.

## Network selection

The user requires the production wallet prompt to request **Robinhood Chain**,
using a separately reviewed production chain/RPC/deployment configuration.
The current local signing profile remains Anvil 31337. This follow-up does not
enable public signing or treat the fixture manifest as production configuration.

Use the [operator procedure](../../docs/BROWSER_WALLET.md) and the
[central wallet task](../../TODO.md#task-wallet).
