# Wallet lifecycle review - 2026-10-20

## Conclusion and scope

Reviewed website provider discovery, connection restoration, account selection,
network setup, typed preparation, approval/Entry sequencing, signing, pending
recovery, receipt observation and confirmed-state rendering. Corrected concrete
lifecycle and presentation problems without replacing the signer or relaxing
transaction checks. This is a scoped internal review, not an independent security
audit or production approval.

**The user's MetaMask pre-prompt failure remains unconfirmed.** The latest
clarification says the website's confirmation button fails before an extension
transaction prompt opens. Do not describe it as a reverted or submitted mint.
Direct local-node preflight passes; the actual extension response is still needed
to establish the cause. Chrome inspection encountered a Computer Use app approval
timeout. No extension screenshot, permission change or transaction was captured.

## Standards and design decisions

- [EIP-6963](https://eips.ethereum.org/EIPS/eip-6963): keep each announced provider
  object distinct; use the shared legacy injection only as fallback. Do not
  identify a wallet from another extension's `isMetaMask` compatibility flag.
- [EIP-1193](https://eips.ethereum.org/EIPS/eip-1193): account/chain events invalidate
  a previous review. Provider failures and user rejection are different outcomes.
  An unavailable response does not prove a transaction was never submitted.
- [MetaMask account API](https://docs.metamask.io/metamask-connect/evm/reference/json-rpc-api/eth_accounts/):
  site-authorized accounts are the available interface, not a private popup's
  selected account. Explicit permission choice and automatic read-only restoration
  serve different purposes. SDK-specific connection behavior must not be assumed
  for this direct injected-provider integration.
- [Rabby integration](https://rabby.io/docs/integrating-rabby-wallet): bind the
  selected EIP-6963 provider instead of relying on the shared injection.
- [EIP-1474](https://eips.ethereum.org/EIPS/eip-1474): keep prepared transaction
  quantities canonical. Existing bounded padded-hex tolerance applies only to
  provider responses, with field-specific diagnostics.

No connector SDK was installed. It would not replace the application-specific
intent, deployment, allowance, gas, journal and receipt checks. Provider names and
rdns remain display hints, not authenticated extension identities.

## Findings and corrections

| Observed code problem | Correction and boundary |
| --- | --- |
| Modern announcements and immediate legacy registration could produce competing wallet choices. | Modern providers take precedence; late announcements replace the fallback list. Duplicate/malformed announcements are bounded and ignored. Legacy providers are generically labeled. |
| A cancelled account choice could leave `requireAccountChoice` set through another connection. | Explicit connect/disconnect/demo reset that flag. Pending transaction guards still prevent switching while unresolved. |
| Adding a network did not ensure a switch; setup was not protected against pending work/provider changes. | Explicit switch after addition when needed, bounded requests, current-provider check, fresh account/chain/genesis verification. Same-ID wrong-genesis networks still fail. |
| Account/chain events and late provider restoration could leave readiness unverified. | Revalidate asynchronously; ignore stale responses. Transaction preparation and UI actions both require verified connection state. No automatic signing or permission prompt. |
| Generic confirming/review dialogs mixed preflight, wallet response, receipt and projection stages. | Separate stages and exact escaped errors. Distinguish unsent failure, definitive rejection, unresolved saved transaction, revert and confirmed receipt. UI callbacks cannot change the signer's send/recovery path. |
| Review abbreviated the sender and hid the selected extension identity. | Display full sender and selected extension; connected control identifies the extension. |
| Operator documentation accumulated contradictory reconnect and timeout instructions. | Consolidated the wallet guide, removed duplicate introductory fragments from the manual and retained historical evidence as history. |

## Preserved safety and UX requirements

- Only the explicit local profile signs; public hosting remains simulation.
- The exact provider, account, chain/genesis, target code, intent/calldata, native
  value, nonce, balance, simulation and reviewed gas policy remain checked.
- Exact ERC20 allowance when required, then a separately reviewed Entry action.
  Existing sufficient allowance skips approval. Native ETH needs no ERC20 approval.
  Unsupported reset-only tokens are not silently approved without bounds.
- The recovery journal is saved before one send request. Timeout/reload never
  resends. A definitive rejection clears only that unsent request; ambiguous
  outcomes remain recoverable. Canonical observation precedes acknowledgement.
- Account/network changes discard unsent reviews. Sent work keeps its original
  account/genesis identity; account-specific Web Locks do not establish
  distributed or production capacity guarantees.
- Approval or submission never updates LP/evolution as successful. Confirmed
  on-chain LP changes drive target-NFT artwork; claims refresh balances.
- Read failures remain unavailable, not invented zero balances. Recovery
  preserves exact transaction identity and original paid-gas limits.

## Verification

203 affected website cases pass, zero failures/skips:

```text
node --test tests/wallet-lifecycle.test.mjs tests/browser-wallet.test.mjs tests/browser-client.test.mjs tests/browser-intent.test.mjs tests/contribution-flow.test.mjs tests/ui-state.test.mjs
```

This is the final scoped inventory, not a sum of intermediate reruns. It includes
six lifecycle/discovery/presentation cases, network addition/switch, wrong genesis,
pending guards, disconnect during setup, unverified preparation, account events,
late response rejection, cancelled-choice recovery and late provider restoration.
Signer regressions cover progress ordering and preflight failure without sending.
Existing affected intent, approval, receipt and UI-state checks were included.
See [test output](lifecycle-tests.log) and [source bindings](lifecycle-sha256.json).

All five modified production JS files pass `node --check`. `node build.mjs`
produces 5,593 files. Six served wallet modules on local port 8900 match source
hashes and return `Cache-Control: no-store`; an already-open page needs reload.

[Read-only preflight](lifecycle-preflight.json) replays the latest saved mint
transaction through the current signer against the actual local RPC, with a fresh
review expiry. It verifies chain/genesis/code, nonce/balance/gas and simulation.
It performs no send, journal write or wallet-extension request. It does not verify
the failing MetaMask interaction or authorize reusing an expired unsigned draft.

No Solidity/backend changes or unchanged contract/backend/artwork suites were
run. No chain reset, service restart, public deployment, public transaction,
monitor change or deferred load campaign occurred.

## Open acceptance and release gates

1. Capture the exact current MetaMask field/stage diagnostic if preflight fails;
   test the actual extension permission, rejection, successful mint and receipt
   flow. The local-node result does not close this.
2. Qualify actual MetaMask/Rabby account/network changes and pending recovery
   across reload. User-reported Rabby success is useful but not full acceptance.
3. Replacement/cancellation discovery is still an operator recovery case.
   Do not delete pending records or blindly resend to clear it.
4. Independently qualify production Robinhood deployment manifests, fee/RPC
   semantics, routes/feeds, service hosting and security. The local 31337 profile
   is not a public signer. Production capacity remains unverified; the deferred
   load campaign was not resumed.

Current procedure: [browser wallet guide](../../docs/BROWSER_WALLET.md).
Task status remains in the [central ledger](../../docs/project-todo.json).
