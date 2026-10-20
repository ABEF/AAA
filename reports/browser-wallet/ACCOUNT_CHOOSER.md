# In-page wallet account chooser

2026-10-20. Scoped internal verification; production NOT APPROVED.

The user reports Rabby works, while MetaMask exposes 0xbc9e...6972 despite
displaying fixture account 0x7099...79C8. Inspection shows reconnect uses fresh
eth_accounts, rather than a saved address, but lacks an explicit way to reopen
wallet permissions. The exact live extension/provider state was not inspected.

The connection dialog now offers **Choose a different account in MetaMask**
(or the selected extension's name). Only that explicit click requests
`wallet_requestPermissions` with `[{eth_accounts:{}}]`. The permission response
is not trusted as an account selection: bounded fresh eth_accounts/eth_chainId
reads and existing connection/deployment checks determine readiness.

Ordinary reconnect remains read-only when authorized. Expected accountsChanged
events during the chooser are accepted before final revalidation. A rejected,
unsupported or already-open prompt gives a useful error; there is no automatic
fallback permission request or silent account substitution. Permission waits
are bounded at 60 seconds and final reads at 15 seconds each. A late prompt
completion never directly establishes verified readiness. Unresolved transaction
journals block this action. No wallet send, token approval or signing is involved.

## Checks and limits

- `node --test tests/browser-client.test.mjs`: **49 passes**, seven new cases.
- `node --check local-view.js`: passes.
- `node build.mjs`: passes, **5,593 files**.
- New cases cover previous permissions, account events during selection,
  cancellation/unsupported/already-open prompts, exact provider targeting,
  pending-transaction exclusion, invalid/unadmitted accounts and button wiring.

[Source bindings](account-chooser-source-sha256.json) identify the checked files.
No unchanged signer/backend/Solidity suites rerun, no holder transactions,
service restart, public website deployment or paused-monitor change. Actual
MetaMask UI acceptance remains open; unit tests do not prove extension behavior.

Reference: [MetaMask permission management](https://support.metamask.io/more-web3/dapps/manage-dapp-permissions/)
and [EIP-2255](https://eips.ethereum.org/EIPS/eip-2255).
